"""Background task to periodically check model endpoint health."""
import asyncio
import logging
from datetime import datetime, timezone
import httpx
from app.database import SessionLocal
from app.models.model_registry import ModelRegistry
from app.config import settings

logger = logging.getLogger(__name__)


async def check_model_health(model_id: int, endpoint_url: str) -> str:
    """Check a single model endpoint. Returns 'online', 'connecting', or 'offline'."""
    base_url = endpoint_url.rstrip("/")
    health_paths = ["/health", "/v1/models", "/"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            for path in health_paths:
                try:
                    resp = await client.get(f"{base_url}{path}")
                    if resp.status_code < 500:
                        return "online"
                except httpx.ConnectError:
                    continue
                except httpx.TimeoutException:
                    return "connecting"
    except Exception as e:
        logger.debug(f"健康檢查異常 (model_id={model_id}): {e}")

    return "offline"


async def _health_check_loop():
    """Periodically check all registered model endpoints."""
    while True:
        try:
            db = SessionLocal()
            try:
                models = (
                    db.query(ModelRegistry)
                    .filter(ModelRegistry.is_active == True)
                    .all()
                )

                for model in models:
                    status = await check_model_health(model.id, model.endpoint_url)
                    if model.health_status != status:
                        logger.info(
                            f"模型 {model.name} 狀態變更: {model.health_status} -> {status}"
                        )
                    model.health_status = status
                    model.health_checked_at = datetime.now(timezone.utc)

                db.commit()
            finally:
                db.close()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"健康檢查迴圈錯誤: {e}")

        await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)


async def start_health_checker() -> asyncio.Task:
    """Start the background health checker task."""
    task = asyncio.create_task(_health_check_loop())
    logger.info("模型健康檢查背景任務已啟動")
    return task
