from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user_context
from ..database import get_db
from ..models import Operation
from ..schemas import OperationStatusResponse, UserInfo


router = APIRouter(prefix="/v1/operations", tags=["Operations"])


@router.get("/{operation_id}", response_model=OperationStatusResponse)
def get_operation_status(
    operation_id: str,
    current_user: UserInfo = Depends(get_current_user_context),
    db: Session = Depends(get_db),
):
    operation = db.query(Operation).filter(
        Operation.id == operation_id,
        Operation.tenant_id == current_user.tenant_id,
        Operation.user_id == current_user.id,
    ).first()
    if not operation:
        raise HTTPException(status_code=404, detail="Không tìm thấy thao tác")
    return OperationStatusResponse(
        operation_id=operation.id,
        kind=operation.kind,
        status=operation.status,
        attempt=operation.attempt,
        response=operation.response_json if operation.status == "succeeded" else None,
        error_code=operation.error_code,
        lease_until=operation.lease_until,
    )
