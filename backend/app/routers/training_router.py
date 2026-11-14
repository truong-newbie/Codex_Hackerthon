from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SOP, SOPVersion, TrainingSession, Turn, TrainingResult
from ..schemas import (
    TrainingStartRequest, TrainingSessionResponse, 
    TrainingTurnRequest, TrainingTurnResponse, 
    FinalResultResponse, EvaluationEvidence, ModuleDraft,
    StepItem, RubricItem, UserInfo
)
from ..auth import get_current_user_context
from ..config import settings
from ..services.ai_service import ai_service
from ..services.scoring_engine import compute_deterministic_result

router = APIRouter(prefix="/v1/training", tags=["Training & Simulation"])

@router.post("/start", response_model=TrainingSessionResponse)
def start_training_session(
    payload: TrainingStartRequest,
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    sop = db.query(SOP).filter(
        SOP.id == payload.sop_id,
        SOP.tenant_id == current_user.tenant_id
    ).first()
    
    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy SOP hoặc SOP không thuộc cửa hàng của bạn"
        )
        
    if not sop.active_version_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SOP này chưa có phiên bản nào được phê duyệt (Approved)"
        )
        
    active_version = db.query(SOPVersion).filter(SOPVersion.id == sop.active_version_id).first()
    if not active_version or active_version.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phiên bản SOP đang kích hoạt không hợp lệ"
        )
        
    steps = [StepItem(**s) for s in active_version.steps_json]
    rubric = [RubricItem(**r) for r in active_version.rubric_json]
    
    # AI Compiler generates ModuleDraft
    module_draft = ai_service.compile_module(sop.title, steps, rubric)
    
    # Enforce schema integrity: Reject any criteria IDs that do not exist in the approved rubric
    valid_rubric_ids = {r.id for r in rubric}
    module_draft.criteria = [cid for cid in module_draft.criteria if cid in valid_rubric_ids]
    if not module_draft.criteria:
        module_draft.criteria = list(valid_rubric_ids)
        
    # Create session with pinned SOP version
    session = TrainingSession(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        sop_version_id=active_version.id,
        module_json=module_draft.model_dump(),
        completed=False
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return TrainingSessionResponse(
        session_id=session.id,
        tenant_id=session.tenant_id,
        sop_version_id=session.sop_version_id,
        sop_title=sop.title,
        module=module_draft,
        completed=False,
        turns_count=0,
        ai_mode=settings.AI_MODE
    )

@router.post("/{session_id}/turn", response_model=TrainingTurnResponse)
def submit_training_turn(
    session_id: str,
    payload: TrainingTurnRequest,
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.tenant_id == current_user.tenant_id,
        TrainingSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phiên học không tồn tại")
        
    if session.completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phiên học này đã kết thúc")
        
    turns_count = len(session.turns)
    if turns_count >= 4:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Đã đạt giới hạn tối đa 4 lượt đối thoại. Vui lòng nhấn Nhận đánh giá."
        )
        
    module_data = ModuleDraft(**session.module_json)
    sop_version = db.query(SOPVersion).filter(SOPVersion.id == session.sop_version_id).first()
    steps = [StepItem(**s) for s in sop_version.steps_json]
    
    history = [
        {"turn": t.turn_no, "employee": t.employee_text, "customer": t.customer_text}
        for t in session.turns
    ]
    
    customer_reply = ai_service.simulate_customer(
        situation=module_data.situation,
        opening_message=module_data.opening_message,
        steps=steps,
        history=history,
        employee_text=payload.message
    )
    
    turn = Turn(
        session_id=session.id,
        turn_no=turns_count + 1,
        employee_text=payload.message,
        customer_text=customer_reply.customer_message
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    
    new_turns_count = turns_count + 1
    is_last_turn = (new_turns_count >= 4)
    
    return TrainingTurnResponse(
        session_id=session.id,
        turn_no=turn.turn_no,
        employee_text=turn.employee_text,
        customer_text=turn.customer_text,
        remaining_turns=max(0, 4 - new_turns_count),
        completed=is_last_turn,
        ai_mode=settings.AI_MODE
    )

@router.post("/{session_id}/evaluate", response_model=FinalResultResponse)
def evaluate_training_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.tenant_id == current_user.tenant_id,
        TrainingSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phiên học không tồn tại")
        
    # Idempotent response: If already evaluated, return the saved result
    if session.result:
        return FinalResultResponse(**session.result.payload_json)
        
    if not session.turns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần hoàn thành ít nhất 1 lượt đối thoại trước khi yêu cầu đánh giá"
        )
        
    # Retrieve the SOP version that was PINNED when the session was created
    sop_version = db.query(SOPVersion).filter(SOPVersion.id == session.sop_version_id).first()
    steps = [StepItem(**s) for s in sop_version.steps_json]
    rubric = [RubricItem(**r) for r in sop_version.rubric_json]
    
    transcript = [
        {"turn": t.turn_no, "employee": t.employee_text, "customer": t.customer_text}
        for t in session.turns
    ]
    employee_texts = [t.employee_text for t in session.turns]
    
    # 1. AI extracts exact quotes and provides draft judgments
    eval_draft = ai_service.evaluate_session(steps, rubric, transcript)
    
    # 2. Server deterministic scoring engine verifies quotes and calculates final score
    score, passed, critical_failure, evidence_list = compute_deterministic_result(
        rubric=rubric,
        judgments=eval_draft.judgments,
        employee_transcript=employee_texts
    )
    
    final_payload = FinalResultResponse(
        session_id=session.id,
        sop_version_id=session.sop_version_id,
        score=score,
        passed=passed,
        critical_failure=critical_failure,
        evidence=evidence_list,
        coaching_tip=eval_draft.coaching_tip,
        ai_mode=settings.AI_MODE
    )
    
    # Save training result and mark session complete
    session.completed = True
    result_record = TrainingResult(
        session_id=session.id,
        score=score,
        passed=passed,
        critical_failure=critical_failure,
        payload_json=final_payload.model_dump()
    )
    db.add(result_record)
    db.commit()
    
    return final_payload
