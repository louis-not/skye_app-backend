from fastapi import APIRouter

from app.api.v1 import health
from app.api.v1 import conversation


router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(conversation.router)
