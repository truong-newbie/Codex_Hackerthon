import hashlib
import hmac
import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import Account, Membership, Tenant
from .schemas import UserInfo

security = HTTPBearer()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 310000
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt_hex, expected_hex = hashed_password.split("$", 3)
            iterations = int(rounds)
            if not 100000 <= iterations <= 1000000:
                return False
            actual = hashlib.pbkdf2_hmac(
                "sha256", plain_password.encode("utf-8"), bytes.fromhex(salt_hex), iterations
            )
            return hmac.compare_digest(actual, bytes.fromhex(expected_hex))
        except (ValueError, TypeError):
            return False

    # Legacy demo database hashes are accepted once and upgraded at login.
    if len(hashed_password) != 64:
        return False
    legacy = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), b"shiftlens_salt_2026", 100000
    )
    return hmac.compare_digest(legacy.hex(), hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserInfo:
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu thông tin user_id hoặc tenant_id"
        )
        
    account = db.query(Account).filter(Account.id == user_id).first()
    if not account or not account.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại")
    if payload.get("token_version") != account.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập đã hết hiệu lực")
        
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.tenant_id == tenant_id
    ).first()
    
    if not membership or not membership.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền truy cập vào cửa hàng này")
        
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    return UserInfo(
        id=account.id,
        username=account.username,
        email=account.email,
        full_name=account.full_name,
        role=membership.role,
        tenant_id=tenant.id,
        tenant_name=tenant.name
    )

def require_manager(current_user: UserInfo = Depends(get_current_user_context)) -> UserInfo:
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hành động yêu cầu quyền Quản lý (Manager)"
        )
    return current_user
