import time
import re
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SOP, SOPVersion, TrainingSession, Turn, TrainingResult, generate_uuid
from ..schemas import (
    TrainingStartRequest, TrainingSessionResponse, 
    TrainingTurnRequest, TrainingTurnResponse, 
    FinalResultResponse, ModuleDraft, TurnDetail,
    StepItem, RubricItem, UserInfo,
    SessionSummaryItem, TrainingSessionDetailResponse
)
from ..auth import get_current_user_context
from ..config import settings
from ..services.ai_service import ai_service
from ..services.scoring_engine import compute_deterministic_result
from ..services.operation_service import (
    complete_evaluate, complete_start, complete_turn, fail, payload_sha256,
    reserve_session, reserve_start,
)

router = APIRouter(prefix="/v1/training", tags=["Training & Simulation"])


def _operation_key(raw: str | None) -> str:
    if raw is None:
        # Legacy clients get state protection but cannot replay after timeout.
        return str(uuid.uuid4())
    key = raw.strip()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{8,80}", key):
        raise HTTPException(status_code=422, detail="Idempotency-Key không hợp lệ")
    return key


def _ai_mode_for_session(session: TrainingSession) -> str:
    return (session.execution_profile_json or {}).get("mode", "unknown")


def _require_execution_profile(profile: dict | None) -> None:
    if not profile:
        return  # Legacy session: provenance is unknown, kept for compatibility.
    if profile.get("mode") != settings.AI_MODE or (
        profile.get("mode") == "live" and profile.get("model") != settings.GEMINI_MODEL
    ):
        raise HTTPException(status_code=503, detail="Cấu hình AI của phiên không còn khả dụng; vui lòng tạo phiên mới")

@router.get("/sessions", response_model=List[SessionSummaryItem])
def list_user_sessions(
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(TrainingSession)
        .filter(
            TrainingSession.tenant_id == current_user.tenant_id,
            TrainingSession.user_id == current_user.id
        )
        .order_by(TrainingSession.created_at.desc())
        .limit(20)
        .all()
    )
    summaries = []
    for s in sessions:
        sop_ver = db.query(SOPVersion).filter(SOPVersion.id == s.sop_version_id).first()
        sop = db.query(SOP).filter(SOP.id == sop_ver.sop_id).first() if sop_ver else None
        summaries.append(
            SessionSummaryItem(
                session_id=s.id,
                sop_id=sop.id if sop else "",
                sop_title=sop.title if sop else "SOP",
                sop_version_id=s.sop_version_id,
                sop_version_no=sop_ver.version_no if sop_ver else 1,
                completed=s.completed,
                turns_count=len(s.turns),
                score=s.result.score if s.result else None,
                passed=s.result.passed if s.result else None,
                critical_failure=s.result.critical_failure if s.result else None,
                ai_mode=_ai_mode_for_session(s),
                created_at=s.created_at,
                state=s.state,
            )
        )
    return summaries

@router.get("/{session_id}", response_model=TrainingSessionDetailResponse)
def get_training_session_detail(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phiên học không tồn tại hoặc không thuộc quyền truy cập của bạn"
        )
        
    sop_ver = db.query(SOPVersion).filter(SOPVersion.id == session.sop_version_id).first()
    sop = db.query(SOP).filter(SOP.id == sop_ver.sop_id).first() if sop_ver else None
    
    turns_list = [
        TurnDetail(
            turn_no=t.turn_no,
            employee_text=t.employee_text,
            customer_text=t.customer_text,
            created_at=t.created_at
        )
        for t in session.turns
    ]
    
    result_obj = FinalResultResponse(**session.result.payload_json) if session.result else None
    
    return TrainingSessionDetailResponse(
        session_id=session.id,
        tenant_id=session.tenant_id,
        sop_id=sop.id if sop else "",
        sop_title=sop.title if sop else "SOP",
        sop_version_id=session.sop_version_id,
        sop_version_no=sop_ver.version_no if sop_ver else 1,
        module=ModuleDraft(**session.module_json),
        completed=session.completed,
        turns=turns_list,
        result=result_obj,
        ai_mode=_ai_mode_for_session(session),
        created_at=session.created_at,
        state=session.state,
        revision=session.revision,
        pending_operation_id=session.busy_operation_id,
    )

@router.post("/start", response_model=TrainingSessionResponse)
def start_training_session(
    payload: TrainingStartRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None),
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    def snapshot_approved_sop() -> dict:
        sop = db.query(SOP).filter(
            SOP.id == payload.sop_id, SOP.tenant_id == current_user.tenant_id,
        ).first()
        if not sop:
            raise HTTPException(status_code=404, detail="Không tìm thấy SOP thuộc cửa hàng của bạn")
        if sop.archived_at or not sop.active_version_id:
            raise HTTPException(status_code=400, detail="SOP chưa có phiên bản được duyệt hoặc đã lưu trữ")
        version = db.query(SOPVersion).filter(
            SOPVersion.id == sop.active_version_id, SOPVersion.sop_id == sop.id,
            SOPVersion.status == "approved",
        ).first()
        if not version:
            raise HTTPException(status_code=400, detail="Phiên bản SOP đang kích hoạt không hợp lệ")
        return {
            "sop_id": sop.id, "sop_title": sop.title,
            "sop_version_id": version.id, "sop_version_no": version.version_no,
            "steps": version.steps_json, "rubric": version.rubric_json,
            "profile": {
                "mode": settings.AI_MODE,
                "model": settings.GEMINI_MODEL if settings.AI_MODE == "live" else None,
                "prompt_version": "v1.1",
                "reserved_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    reservation = reserve_start(
        db, current_user.tenant_id, current_user.id, _operation_key(idempotency_key),
        payload_sha256({"sop_id": payload.sop_id}), snapshot_approved_sop,
    )
    response.headers["X-Operation-ID"] = reservation.operation_id
    if reservation.replayed:
        return TrainingSessionResponse(**reservation.response)

    snapshot = reservation.snapshot
    steps = [StepItem(**item) for item in snapshot["steps"]]
    rubric = [RubricItem(**item) for item in snapshot["rubric"]]
    try:
        _require_execution_profile(snapshot["profile"])
        t0 = time.perf_counter()
        module_draft = ai_service.compile_module(snapshot["sop_title"], steps, rubric)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        valid_rubric_ids = {item.id for item in rubric}
        module_draft.criteria = [cid for cid in module_draft.criteria if cid in valid_rubric_ids]
        if not module_draft.criteria:
            module_draft.criteria = [item.id for item in rubric]
    except Exception:
        fail(db, reservation, "COMPILER_FAILED")
        raise

    session = TrainingSession(
        id=generate_uuid(), tenant_id=current_user.tenant_id, user_id=current_user.id,
        sop_version_id=snapshot["sop_version_id"], module_json=module_draft.model_dump(),
        execution_profile_json=snapshot["profile"], state="active", completed=False,
    )
    result = TrainingSessionResponse(
        session_id=session.id, tenant_id=session.tenant_id,
        sop_id=snapshot["sop_id"], sop_version_id=session.sop_version_id,
        sop_version_no=snapshot["sop_version_no"], sop_title=snapshot["sop_title"],
        module=module_draft, completed=False, turns_count=0,
        ai_mode=snapshot["profile"]["mode"], latency_ms=latency_ms,
        state="active", revision=0, operation_id=reservation.operation_id,
    )
    complete_start(db, reservation, session, result.model_dump(mode="json"))
    return result

@router.post("/{session_id}/turn", response_model=TrainingTurnResponse)
def submit_training_turn(
    session_id: str,
    payload: TrainingTurnRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None),
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
        
    sop_version = db.query(SOPVersion).filter(SOPVersion.id == session.sop_version_id).first()
    snapshot = {
        "revision": session.revision,
        "turns_count": len(session.turns),
        "steps": sop_version.steps_json,
        "history": [
            {"turn": t.turn_no, "employee": t.employee_text, "customer": t.customer_text}
            for t in session.turns
        ],
    }
    reservation = reserve_session(
        db, session, "turn", _operation_key(idempotency_key),
        payload_sha256({"session_id": session_id, "message": payload.message}), snapshot,
    )
    response.headers["X-Operation-ID"] = reservation.operation_id
    if reservation.replayed:
        return TrainingTurnResponse(**reservation.response)

    snapshot = reservation.snapshot
    module_data = ModuleDraft(**session.module_json)
    steps = [StepItem(**item) for item in snapshot["steps"]]
    try:
        _require_execution_profile(session.execution_profile_json)
        t0 = time.perf_counter()
        customer_reply = ai_service.simulate_customer(
            situation=module_data.situation,
            opening_message=module_data.opening_message,
            steps=steps,
            history=snapshot["history"],
            employee_text=payload.message,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
    except Exception:
        fail(db, reservation, "SIMULATOR_FAILED")
        raise

    turn_no = snapshot["turns_count"] + 1
    result = TrainingTurnResponse(
        session_id=session.id, turn_no=turn_no, employee_text=payload.message,
        customer_text=customer_reply.customer_message,
        remaining_turns=max(0, 4 - turn_no), completed=turn_no >= 4,
        ai_mode=_ai_mode_for_session(session), latency_ms=latency_ms,
        dialogue_exhausted=turn_no >= 4, evaluation_completed=False,
        operation_id=reservation.operation_id,
    )
    complete_turn(
        db, reservation, session.id, payload.message,
        customer_reply.customer_message, result.model_dump(mode="json"),
    )
    return result

@router.post("/{session_id}/evaluate", response_model=FinalResultResponse)
def evaluate_training_session(
    session_id: str,
    response: Response,
    idempotency_key: str | None = Header(default=None),
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
        
    if session.result:
        if session.result.operation_id:
            response.headers["X-Operation-ID"] = session.result.operation_id
        return FinalResultResponse(**session.result.payload_json)

    sop_version = db.query(SOPVersion).filter(SOPVersion.id == session.sop_version_id).first()
    snapshot = {
        "revision": session.revision,
        "turns_count": len(session.turns),
        "sop_version_id": sop_version.id,
        "sop_version_no": sop_version.version_no,
        "steps": sop_version.steps_json,
        "rubric": sop_version.rubric_json,
        "transcript": [
            {"turn": t.turn_no, "employee": t.employee_text, "customer": t.customer_text}
            for t in session.turns
        ],
    }
    reservation = reserve_session(
        db, session, "evaluate", _operation_key(idempotency_key),
        payload_sha256({"session_id": session_id}), snapshot,
    )
    response.headers["X-Operation-ID"] = reservation.operation_id
    if reservation.replayed:
        return FinalResultResponse(**reservation.response)

    snapshot = reservation.snapshot
    steps = [StepItem(**item) for item in snapshot["steps"]]
    rubric = [RubricItem(**item) for item in snapshot["rubric"]]
    try:
        _require_execution_profile(session.execution_profile_json)
        t0 = time.perf_counter()
        eval_draft = ai_service.evaluate_session(steps, rubric, snapshot["transcript"])
        latency_ms = int((time.perf_counter() - t0) * 1000)
        score, passed, critical_failure, evidence_list = compute_deterministic_result(
            rubric=rubric,
            judgments=eval_draft.judgments,
            employee_transcript=[turn["employee"] for turn in snapshot["transcript"]],
        )
    except Exception:
        fail(db, reservation, "EVALUATOR_FAILED")
        raise

    final_payload = FinalResultResponse(
        session_id=session.id,
        sop_version_id=session.sop_version_id,
        sop_version_no=snapshot["sop_version_no"],
        score=score,
        passed=passed,
        critical_failure=critical_failure,
        evidence=evidence_list,
        coaching_tip=eval_draft.coaching_tip,
        ai_mode=_ai_mode_for_session(session),
        latency_ms=latency_ms,
        operation_id=reservation.operation_id,
    )
    result_record = TrainingResult(
        session_id=session.id,
        score=score,
        passed=passed,
        critical_failure=critical_failure,
        payload_json=final_payload.model_dump(mode="json"),
        scoring_version="legacy-deterministic-v1",
        evidence_schema_version="v1",
        transcript_revision=snapshot["revision"],
        transcript_sha256=payload_sha256({"transcript": snapshot["transcript"]}),
    )
    complete_evaluate(db, reservation, session.id, result_record, final_payload.model_dump(mode="json"))
    return final_payload
