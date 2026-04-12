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
    RegisterRequest,
)
from app.services.auth_service import (
    authenticate_user,
    create_tokens,
    get_current_user,
    _load_user_from_payload,
    PENDING_APPROVAL_SENTINEL,
)
from app.utils.security import decode_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["認證"])


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="帳號已被使用")
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
        role="user",
        is_active=True,
        is_approved=False,
    )
    db.add(user)
    db.commit()
    return {"message": "註冊成功，請等待管理員核准後再登入"}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    result = authenticate_user(db, request.username, request.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
        )
    if result is PENDING_APPROVAL_SENTINEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="等待核准中，請通知 admin",
        )
    return create_tokens(result)


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
