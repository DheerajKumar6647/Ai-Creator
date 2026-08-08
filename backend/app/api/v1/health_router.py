from fastapi import APIRouter
from app.schemas.schemas import HealthResponse
from app.config.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version="1.0.0"
    )
