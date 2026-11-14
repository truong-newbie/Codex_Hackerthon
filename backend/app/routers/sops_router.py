from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SOP
from ..schemas import SOPDetailResponse, UserInfo
from ..auth import get_current_user_context
from ..services.sop_service import sop_service

router = APIRouter(prefix="/v1/sops", tags=["SOPs"])

@router.get("", response_model=List[SOPDetailResponse])
def list_tenant_sops(
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    return sop_service.get_tenant_sops(db, current_user.tenant_id)

@router.get("/{sop_id}", response_model=SOPDetailResponse)
def get_sop_detail(
    sop_id: str,
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    sops = sop_service.get_tenant_sops(db, current_user.tenant_id)
    matched = next((s for s in sops if s.id == sop_id), None)
    if not matched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOP không tồn tại hoặc không thuộc cửa hàng của bạn")
    return matched
