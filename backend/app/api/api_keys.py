from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.api_key import ApiKey, ApiKeyModelPermission
from app.models.user import User
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
)
from app.services.auth_service import get_current_user
from app.services.api_key_service import create_api_key

router = APIRouter(prefix="/api/keys", tags=["API Key 管理"])


def _build_response(api_key: ApiKey) -> dict:
    return {
        "id": api_key.id,
        "user_id": api_key.user_id,
        "name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "key_suffix": api_key.key_suffix,
        "is_active": api_key.is_active,
        "expires_at": api_key.expires_at,
        "created_at": api_key.created_at,
        "last_used_at": api_key.last_used_at,
        "allowed_model_ids": [m.id for m in api_key.allowed_models],
        "allowed_model_names": [m.display_name for m in api_key.allowed_models],
    }


@router.get("", response_model=list[ApiKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "admin":
        keys = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    else:
        keys = (
            db.query(ApiKey)
            .filter(ApiKey.user_id == current_user.id)
            .order_by(ApiKey.created_at.desc())
            .all()
        )
    return [_build_response(k) for k in keys]


@router.post("", response_model=ApiKeyCreatedResponse)
def create_key(
    request: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key, full_key = create_api_key(
        db=db,
        user_id=current_user.id,
        name=request.name,
        model_ids=request.model_ids,
        expires_at=request.expires_at,
    )
    resp = _build_response(api_key)
    resp["full_key"] = full_key
    return resp


@router.get("/{key_id}", response_model=ApiKeyResponse)
def get_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權限存取此 API Key")
    return _build_response(api_key)


@router.put("/{key_id}", response_model=ApiKeyResponse)
def update_key(
    key_id: int,
    request: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權限修改此 API Key")

    if request.name is not None:
        api_key.name = request.name
    if request.is_active is not None:
        api_key.is_active = request.is_active
    if request.model_ids is not None:
        # Clear existing permissions and set new ones
        db.query(ApiKeyModelPermission).filter(
            ApiKeyModelPermission.api_key_id == key_id
        ).delete()
        for model_id in request.model_ids:
            perm = ApiKeyModelPermission(api_key_id=key_id, model_id=model_id)
            db.add(perm)

    db.commit()
    db.refresh(api_key)
    return _build_response(api_key)


@router.delete("/{key_id}")
def revoke_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    if current_user.role != "admin" and api_key.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="無權限撤銷此 API Key")

    api_key.is_active = False
    db.commit()
    return {"message": "API Key 已撤銷"}
