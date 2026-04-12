from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.api_key import ApiKey, ApiKeyModelPermission
from app.models.model_registry import ModelRegistry
from app.models.user import User, UserModelPermission
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    AdminResetPassword,
    AllowedModelItem,
    UserAllowedModelsUpdate,
)
from app.services.auth_service import get_current_user, require_admin
from app.utils.security import hash_password

router = APIRouter(prefix="/api/users", tags=["使用者管理"])


@router.get("", response_model=list[UserResponse])
def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("", response_model=UserResponse)
def create_user(
    request: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="使用者名稱已存在")

    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    request: AdminResetPassword,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    user.hashed_password = hash_password(request.new_password)
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    return {"message": f"已重設使用者「{user.username}」的密碼，現有權杖已失效"}


@router.get("/me/allowed-models", response_model=list[AllowedModelItem])
def get_my_allowed_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        models = db.query(ModelRegistry).filter(ModelRegistry.is_active == True).all()
    else:
        models = current_user.allowed_models
    return [{"id": m.id, "display_name": m.display_name, "model_type": m.model_type} for m in models]


@router.get("/{user_id}/allowed-models", response_model=list[AllowedModelItem])
def get_user_allowed_models(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    models = user.allowed_models
    return [{"id": m.id, "display_name": m.display_name, "model_type": m.model_type} for m in models]


@router.put("/{user_id}/allowed-models")
def update_user_allowed_models(
    user_id: int,
    request: UserAllowedModelsUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")

    new_ids = set(request.model_ids)

    # Validate model IDs
    if new_ids:
        valid_count = db.query(ModelRegistry).filter(ModelRegistry.id.in_(new_ids)).count()
        if valid_count != len(new_ids):
            raise HTTPException(status_code=400, detail="包含不存在的模型 ID")

    # Overwrite user_model_permissions
    db.query(UserModelPermission).filter(UserModelPermission.user_id == user_id).delete()
    for mid in new_ids:
        db.add(UserModelPermission(user_id=user_id, model_id=mid))

    # Cascade: remove revoked models from all this user's API keys (non-admin users only)
    cascade_count = 0
    if user.role != "admin":
        user_keys = db.query(ApiKey).filter(ApiKey.user_id == user_id).all()
        for key in user_keys:
            q = db.query(ApiKeyModelPermission).filter(
                ApiKeyModelPermission.api_key_id == key.id
            )
            if new_ids:
                q = q.filter(~ApiKeyModelPermission.model_id.in_(new_ids))
            deleted = q.delete(synchronize_session=False)
            cascade_count += deleted

    db.commit()
    return {
        "message": f"已更新使用者「{user.username}」的可用模型，並同步調整 {cascade_count} 筆 API key 權限"
    }


@router.post("/{user_id}/approve")
def approve_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if user.is_approved:
        return {"message": f"使用者「{user.username}」已是核准狀態"}
    user.is_approved = True
    db.commit()
    return {"message": f"已核准使用者「{user.username}」"}


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    user.is_active = False
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    return {"message": "使用者已停用"}
