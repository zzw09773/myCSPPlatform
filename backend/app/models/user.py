from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class UserModelPermission(Base):
    __tablename__ = "user_model_permissions"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    model_id = Column(
        Integer, ForeignKey("model_registry.id", ondelete="CASCADE"), primary_key=True
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # 'admin' / 'user'
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, nullable=False, default=True, server_default="true")
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    allowed_models = relationship(
        "ModelRegistry",
        secondary="user_model_permissions",
        backref="allowed_users",
        lazy="select",
    )
