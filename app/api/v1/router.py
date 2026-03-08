from fastapi import APIRouter

from app.api.v1 import health


router = APIRouter(prefix="/api/v1")

# Include domain routers
router.include_router(health.router)

# Future domain routers will be added here:
# router.include_router(auth.router)
# router.include_router(task.router)
# router.include_router(device.router)
# router.include_router(user.router)
