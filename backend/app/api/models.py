import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.model_registry import ModelRegistry
from app.models.user import User
from app.schemas.model_registry import ModelCreate, ModelUpdate, ModelResponse
from app.services.auth_service import get_current_user, require_admin

router = APIRouter(prefix="/api/models", tags=["模型管理"])


@router.get("", response_model=list[ModelResponse])
def list_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    models = db.query(ModelRegistry).order_by(ModelRegistry.model_type, ModelRegistry.name).all()
    return models


@router.post("", response_model=ModelResponse)
def create_model(
    request: ModelCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(ModelRegistry).filter(ModelRegistry.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模型名稱已存在")
    model = ModelRegistry(**request.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.put("/{model_id}", response_model=ModelResponse)
def update_model(
    model_id: int,
    request: ModelUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}")
def deactivate_model(
    model_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    model.is_active = False
    db.commit()
    return {"message": "模型已停用"}


@router.post("/{model_id}/health-check")
async def trigger_health_check(
    model_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Try common health endpoints
            for path in ["/health", "/v1/models", "/"]:
                try:
                    resp = await client.get(f"{model.endpoint_url.rstrip('/')}{path}")
                    if resp.status_code < 500:
                        model.health_status = "online"
                        model.health_checked_at = datetime.now(timezone.utc)
                        db.commit()
                        return {"status": "online", "detail": f"端點 {path} 回應正常"}
                except httpx.ConnectError:
                    continue

            model.health_status = "offline"
            model.health_checked_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "offline", "detail": "無法連線到模型端點"}
    except Exception as e:
        model.health_status = "offline"
        model.health_checked_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "offline", "detail": str(e)}
