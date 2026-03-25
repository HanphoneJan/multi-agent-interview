"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import MilvusClient, close_redis, get_redis
from app.database import check_db_health
from app.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown resources."""
    await get_redis()

    milvus = MilvusClient()
    await milvus.connect()
    await milvus.create_collection()

    db_healthy = await check_db_health()
    if not db_healthy:
        raise RuntimeError("Database connection failed")

    print("[OK] All services connected")

    yield

    await close_redis()
    milvus = MilvusClient()
    await milvus.disconnect()
    print("[OK] All services closed")


app = FastAPI(
    title="Recommendation API",
    version="1.0.0",
    lifespan=lifespan,
)

setup_middleware(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "recommendation-api"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    from app.core import get_redis

    db_healthy = await check_db_health()

    try:
        redis = await get_redis()
        await redis.ping()
        redis_healthy = True
    except Exception:
        redis_healthy = False

    if db_healthy and redis_healthy:
        return {"status": "ready"}
    return {"status": "not ready", "db": db_healthy, "redis": redis_healthy}


from app.api.v1.users import router as users_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.learning import router as learning_router
from app.api.v1.career import router as career_router
from app.api.v1.recommendation import router as recommendation_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.tts import router as tts_router
from app.api.v1.interview_crew import router as interview_crew_router
from app.websockets.interview import router as interview_ws_router
from app.websockets.interview_realtime import router as interview_realtime_ws_router
from app.websockets.interview_crew import router as interview_crew_ws_router

app.include_router(users_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")
app.include_router(evaluations_router, prefix="/api/v1")
app.include_router(learning_router, prefix="/api/v1")
app.include_router(career_router, prefix="/api/v1")
app.include_router(recommendation_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(tts_router, prefix="/api/v1")
app.include_router(interview_crew_router, prefix="/api/v1")
app.include_router(interview_ws_router, prefix="/api/v1")
app.include_router(interview_realtime_ws_router, prefix="/api/v1")
app.include_router(interview_crew_ws_router, prefix="/api/v1")
