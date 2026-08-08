from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.database.connection import init_db
from app.database.seed import run_seed
from app.utils.logger import logger

from app.api.v1.health_router import router as health_router
from app.api.v1.candidate_router import router as candidate_router
from app.api.v1.curriculum_router import router as curriculum_router
from app.api.v1.interview_router import router as interview_router
from app.api.v1.feedback_router import router as feedback_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up InterviewAI backend service...")
    init_db()
    run_seed()
    logger.info("Database initialized and seeded.")
    yield
    logger.info("Shutting down InterviewAI backend service.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Adaptive Technical Interview Agent Platform built with FastAPI and LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in settings.BACKEND_CORS_ORIGINS if origin != "*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during request processing.",
                "detail": str(exc) if settings.DEBUG else None
            }
        }
    )

# Include Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(health_router, prefix=api_v1_prefix)
app.include_router(candidate_router, prefix=api_v1_prefix)
app.include_router(curriculum_router, prefix=api_v1_prefix)
app.include_router(interview_router, prefix=api_v1_prefix)
app.include_router(feedback_router, prefix=api_v1_prefix)

@app.get("/")
def root():
    return {
        "message": "Welcome to InterviewAI Backend API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
