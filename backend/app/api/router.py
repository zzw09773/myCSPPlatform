from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.api_keys import router as api_keys_router
from app.api.models import router as models_router
from app.api.usage import router as usage_router
from app.api.users import router as users_router
from app.api.platform_links import router as platform_links_router
from app.api.proxy import router as proxy_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(api_keys_router)
api_router.include_router(models_router)
api_router.include_router(usage_router)
api_router.include_router(users_router)
api_router.include_router(platform_links_router)
api_router.include_router(proxy_router)
