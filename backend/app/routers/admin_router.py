from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TrainingSession, TrainingResult, SOPVersion, SOP, Account
from ..schemas import (
    CreateDraftRequest, CreateSOPRequest, SOPDetailResponse, SOPVersionDetail, ApproveResponse, UserInfo,
    TenantAnalyticsResponse, ManagerSessionRecord, EvaluationEvidence
)
from ..auth import require_manager
from ..services.sop_service import sop_service

router = APIRouter(prefix="/v1/admin", tags=["Admin / Manager Studio"])

@router.post("/sops", response_model=SOPDetailResponse, status_code=201)
def create_sop(
    payload: CreateSOPRequest,
    current_manager: UserInfo = Depends(require_manager),
    db: Session = Depends(get_db),
):
    return sop_service.create_sop(
        db=db, tenant_id=current_manager.tenant_id, title=payload.title,
        steps=payload.steps, rubric=payload.rubric,
    )

@router.post("/sops/{sop_id}/draft", response_model=SOPVersionDetail)
def create_sop_draft(
    sop_id: str,
    payload: CreateDraftRequest,
    current_manager: UserInfo = Depends(require_manager),
    db: Session = Depends(get_db)
):
    return sop_service.create_draft_version(
        db=db,
        sop_id=sop_id,
        tenant_id=current_manager.tenant_id,
        steps=payload.steps,
        rubric=payload.rubric
    )

@router.post("/sop-versions/{version_id}/approve", response_model=ApproveResponse)
def approve_sop_version(
    version_id: str,
    current_manager: UserInfo = Depends(require_manager),
    db: Session = Depends(get_db)
):
    approved_v = sop_service.approve_version(
        db=db,
        version_id=version_id,
        tenant_id=current_manager.tenant_id,
        manager_id=current_manager.id
    )
    return ApproveResponse(
        message=f"Đã phê duyệt thành công phiên bản v{approved_v.version_no}!",
        active_version_id=approved_v.id,
        version_no=approved_v.version_no
    )

@router.get("/analytics", response_model=TenantAnalyticsResponse)
def get_tenant_training_analytics(
    current_manager: UserInfo = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Lấy thống kê năng lực đào tạo & bằng chứng thực hành của toàn bộ nhân viên trong cửa hàng (BR-01 Tenant Isolation).
    """
    aggregate = (
        db.query(
            func.count(TrainingSession.id),
            func.count(TrainingResult.id),
            func.coalesce(func.sum(case((TrainingResult.passed.is_(True), 1), else_=0)), 0),
            func.coalesce(func.sum(TrainingResult.score), 0),
            func.coalesce(func.sum(case((TrainingResult.critical_failure.is_(True), 1), else_=0)), 0),
        )
        .outerjoin(TrainingResult, TrainingResult.session_id == TrainingSession.id)
        .filter(TrainingSession.tenant_id == current_manager.tenant_id)
        .one()
    )
    total_sessions, completed_sessions, passed_count, total_score_sum, critical_failure_count = aggregate

    sessions = (
        db.query(TrainingSession)
        .filter(TrainingSession.tenant_id == current_manager.tenant_id)
        .order_by(TrainingSession.created_at.desc())
        .limit(50)
        .all()
    )
    
    records = []
    
    for s in sessions:
        emp = db.query(Account).filter(Account.id == s.user_id).first()
        sop_ver = db.query(SOPVersion).filter(SOPVersion.id == s.sop_version_id).first()
        sop = db.query(SOP).filter(SOP.id == sop_ver.sop_id).first() if sop_ver else None
        
        score = None
        passed = None
        crit_fail = None
        evidence_list = []
        coaching_tip = None
        
        if s.completed and s.result:
            score = s.result.score
            passed = s.result.passed
            crit_fail = s.result.critical_failure
            payload = s.result.payload_json or {}
            evidence_list = [EvaluationEvidence(**ev) for ev in payload.get("evidence", [])]
            coaching_tip = payload.get("coaching_tip")
            
        records.append(
            ManagerSessionRecord(
                session_id=s.id,
                employee_id=s.user_id,
                employee_username=emp.username if emp else "unknown",
                employee_name=(emp.full_name or emp.username) if emp else "Nhân viên",
                sop_id=sop.id if sop else "",
                sop_title=sop.title if sop else "SOP",
                sop_version_id=s.sop_version_id,
                sop_version_no=sop_ver.version_no if sop_ver else 1,
                completed=s.completed,
                turns_count=len(s.turns),
                score=score,
                passed=passed,
                critical_failure=crit_fail,
                evidence=evidence_list,
                coaching_tip=coaching_tip,
                created_at=s.created_at
            )
        )
        
    pass_rate = round((passed_count / completed_sessions) * 100.0, 1) if completed_sessions > 0 else 0.0
    avg_score = round(total_score_sum / completed_sessions, 1) if completed_sessions > 0 else 0.0
    
    return TenantAnalyticsResponse(
        tenant_id=current_manager.tenant_id,
        tenant_name=current_manager.tenant_name,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        pass_rate=pass_rate,
        average_score=avg_score,
        critical_failure_count=critical_failure_count,
        recent_sessions=records
    )
