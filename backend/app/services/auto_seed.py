"""Auto-register models and platform links from environment variables on startup."""
import json
import logging
from app.config import settings
from app.database import SessionLocal
from app.models.model_registry import ModelRegistry
from app.models.platform_link import PlatformLink
from app.models.user import User
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


def auto_seed():
    """Run on startup: create admin, auto-register models & links from env vars."""
    db = SessionLocal()
    try:
        # 1. Ensure admin user exists
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.flush()
            logger.info(f"已建立管理員帳號: {settings.ADMIN_USERNAME}")

        # 2. Auto-register models from AUTO_REGISTER_MODELS env
        # Two passes: first register base models, then agents (which may reference base models)
        if settings.AUTO_REGISTER_MODELS:
            try:
                models_config = json.loads(settings.AUTO_REGISTER_MODELS)

                # Pass 1: register non-agent models first
                for m in models_config:
                    if m.get("model_type") == "agent":
                        continue
                    existing = db.query(ModelRegistry).filter(
                        ModelRegistry.name == m["name"]
                    ).first()
                    if not existing:
                        model = ModelRegistry(
                            name=m["name"],
                            display_name=m.get("display_name", m["name"]),
                            model_type=m.get("model_type", "llm"),
                            endpoint_url=m["endpoint_url"],
                            api_version=m.get("api_version", "v1"),
                            description=m.get("description", ""),
                            context_window=m.get("context_window"),
                        )
                        db.add(model)
                        logger.info(f"自動註冊模型: {m['name']} -> {m['endpoint_url']}")
                    else:
                        if existing.endpoint_url != m["endpoint_url"]:
                            existing.endpoint_url = m["endpoint_url"]
                            logger.info(f"更新模型端點: {m['name']} -> {m['endpoint_url']}")

                db.flush()  # Ensure base models have IDs

                # Pass 2: register agent models (may reference base_model by name)
                for m in models_config:
                    if m.get("model_type") != "agent":
                        continue
                    existing = db.query(ModelRegistry).filter(
                        ModelRegistry.name == m["name"]
                    ).first()

                    # Resolve base_model by name
                    base_model_id = None
                    base_model_name = m.get("base_model")
                    if base_model_name:
                        base = db.query(ModelRegistry).filter(
                            ModelRegistry.name == base_model_name
                        ).first()
                        if base:
                            base_model_id = base.id
                        else:
                            logger.warning(
                                f"Agent {m['name']} 的底層模型 '{base_model_name}' 未找到"
                            )

                    if not existing:
                        model = ModelRegistry(
                            name=m["name"],
                            display_name=m.get("display_name", m["name"]),
                            model_type="agent",
                            endpoint_url=m["endpoint_url"],
                            api_version=m.get("api_version", "v1"),
                            description=m.get("description", ""),
                            context_window=m.get("context_window"),
                            base_model_id=base_model_id,
                        )
                        db.add(model)
                        logger.info(
                            f"自動註冊 Agent: {m['name']} -> {m['endpoint_url']}"
                            f" (底層: {base_model_name or '無'})"
                        )
                    else:
                        if existing.endpoint_url != m["endpoint_url"]:
                            existing.endpoint_url = m["endpoint_url"]
                        if base_model_id and existing.base_model_id != base_model_id:
                            existing.base_model_id = base_model_id
                            logger.info(f"更新 Agent 底層模型: {m['name']} -> {base_model_name}")

            except json.JSONDecodeError as e:
                logger.error(f"AUTO_REGISTER_MODELS JSON 解析失敗: {e}")

        # 3. Auto-register platform links from AUTO_REGISTER_LINKS env
        if settings.AUTO_REGISTER_LINKS:
            try:
                links_config = json.loads(settings.AUTO_REGISTER_LINKS)
                for idx, link_data in enumerate(links_config):
                    existing = db.query(PlatformLink).filter(
                        PlatformLink.name == link_data["name"]
                    ).first()
                    if not existing:
                        link = PlatformLink(
                            name=link_data["name"],
                            url=link_data["url"],
                            icon=link_data.get("icon", ""),
                            description=link_data.get("description", ""),
                            sort_order=link_data.get("sort_order", idx + 1),
                        )
                        db.add(link)
                        logger.info(f"自動註冊平台連結: {link_data['name']}")
            except json.JSONDecodeError as e:
                logger.error(f"AUTO_REGISTER_LINKS JSON 解析失敗: {e}")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"自動初始化失敗: {e}")
    finally:
        db.close()
