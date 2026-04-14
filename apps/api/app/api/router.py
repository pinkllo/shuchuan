from fastapi import APIRouter

from app.api.routes.admin_logs import router as admin_logs_router
from app.api.routes.admin_users import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.catalogs import router as catalogs_router
from app.api.routes.deliveries import router as deliveries_router
from app.api.routes.demands import router as demands_router
from app.api.routes.health import router as health_router
from app.api.routes.processors import router as processors_router
from app.api.routes.task_callbacks import router as task_callbacks_router
from app.api.routes.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(admin_logs_router)
api_router.include_router(catalogs_router)
api_router.include_router(demands_router)
api_router.include_router(tasks_router)
api_router.include_router(task_callbacks_router)
api_router.include_router(deliveries_router)
api_router.include_router(processors_router)
