from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Account, Membership, Tenant
from ..schemas import LoginRequest, TokenResponse, UserInfo
from ..auth import verify_password, hash_password, create_access_token, get_current_user_context

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(
        (Account.username == payload.username_or_email) | 
        (Account.email == payload.username_or_email)
    ).first()
    
    if not account or not account.active or not verify_password(payload.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác"
        )

    membership = db.query(Membership).filter(Membership.user_id == account.id).first()
    if not membership or not membership.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được gán vào bất kỳ cửa hàng nào"
        )
        
    tenant = db.query(Tenant).filter(Tenant.id == membership.tenant_id).first()

    if not account.password_hash.startswith("pbkdf2_sha256$"):
        account.password_hash = hash_password(payload.password)
        db.commit()
    
    token_data = {
        "sub": account.id,
        "username": account.username,
        "tenant_id": tenant.id,
        "role": membership.role,
        "token_version": account.token_version,
    }
    access_token = create_access_token(data=token_data)
    
    user_info = UserInfo(
        id=account.id,
        username=account.username,
        email=account.email,
        full_name=account.full_name,
        role=membership.role,
        tenant_id=tenant.id,
        tenant_name=tenant.name
    )
    
    return TokenResponse(access_token=access_token, user=user_info)

@router.get("/me", response_model=UserInfo)
def get_me(current_user: UserInfo = Depends(get_current_user_context)):
    return current_user
