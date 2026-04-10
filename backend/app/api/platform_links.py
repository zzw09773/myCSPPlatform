from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.platform_link import PlatformLink
from app.models.user import User
from app.schemas.platform_link import (
    PlatformLinkCreate,
    PlatformLinkUpdate,
    PlatformLinkResponse,
)
from app.services.auth_service import get_current_user, require_admin

router = APIRouter(prefix="/api/platform-links", tags=["平台連結"])


@router.get("", response_model=list[PlatformLinkResponse])
def list_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(PlatformLink)
        .filter(PlatformLink.is_active == True)
        .order_by(PlatformLink.sort_order)
        .all()
    )


@router.post("", response_model=PlatformLinkResponse)
def create_link(
    request: PlatformLinkCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = PlatformLink(**request.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.put("/{link_id}", response_model=PlatformLinkResponse)
def update_link(
    link_id: int,
    request: PlatformLinkUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = db.query(PlatformLink).filter(PlatformLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="連結不存在")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(link, field, value)

    db.commit()
    db.refresh(link)
    return link


@router.delete("/{link_id}")
def delete_link(
    link_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = db.query(PlatformLink).filter(PlatformLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="連結不存在")
    link.is_active = False
    db.commit()
    return {"message": "連結已刪除"}
