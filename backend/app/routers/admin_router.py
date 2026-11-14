from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import CreateDraftRequest, SOPVersionDetail, ApproveResponse, UserInfo
from ..auth import require_manager
from ..services.sop_service import sop_service

router = APIRouter(prefix="/v1/admin", tags=["Admin / Manager Studio"])

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
