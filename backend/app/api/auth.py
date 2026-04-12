from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    PasswordChangeRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_tokens,
    get_current_user,
    _load_user_from_payload,
)
from app.utils.security import decode_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["認證"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
        )
    return create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    user = _load_user_from_payload(payload, db, "refresh")
    return create_tokens(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/password")
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目前密碼不正確",
        )
    current_user.hashed_password = hash_password(request.new_password)
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    db.refresh(current_user)
    return {"message": "密碼已更新，請重新登入", **create_tokens(current_user)}
