"""Pytest configuration"""
import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from dotenv import load_dotenv

# Load test environment variables
env_path = Path(__file__).parent / ".env.test"
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Set test environment - use existing ai_interview database
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:123456@localhost:5432/ai_interview")
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
os.environ["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
os.environ["CELERY_BROKER_URL"] = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ["CELERY_RESULT_BACKEND"] = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# Set Hugging Face mirror for China
os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
os.environ["HF_HUB_OFFLINE"] = "1"  # Use cached models only in tests

from app.main import app
from app.core.security import create_access_token

# Test database URL
TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# Create test engine - use NullPool to avoid connection reuse issues
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)
test_async_session = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_test_database():
    """Setup test database"""
    from app import database
    # Override engine
    database.engine = test_engine
    database.async_session_factory = test_async_session
    yield
    # Cleanup
    await database.engine.dispose()


@pytest.fixture
async def db():
    """Create test database session"""
    async with test_async_session() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture
async def db_session():
    """Create test database session with transaction rollback"""
    async with test_async_session() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture
async def client():
    """Create async test client without database"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def async_client():
    """Create async test client with database"""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
async def test_user(db_session):
    """Create a test user (unique username per run to avoid conflict)"""
    import uuid
    from app.services.auth_service import create_user
    from app.schemas.user import UserCreate
    from app.models.user import users
    from sqlalchemy import select

    suffix = uuid.uuid4().hex[:8]
    user_data = UserCreate(
        username=f"testuser_{suffix}",
        email=f"test_{suffix}@example.com",
        password="testpass123",
        name="Test User",
    )

    user = await create_user(db_session, user_data)
    result = await db_session.execute(select(users).where(users.c.id == user["id"]))
    return result.first()


@pytest.fixture
async def admin_user(db_session):
    """Create an admin test user (unique username per run)"""
    import uuid
    from app.services.auth_service import create_user
    from app.schemas.user import UserCreate
    from app.models.user import users
    from sqlalchemy import select

    suffix = uuid.uuid4().hex[:8]
    user_data = UserCreate(
        username=f"admin_{suffix}",
        email=f"admin_{suffix}@example.com",
        password="adminpass123",
        name="Admin User",
    )

    user = await create_user(db_session, user_data)
    result = await db_session.execute(select(users).where(users.c.id == user["id"]))
    return result.first()


@pytest.fixture
async def user_token(test_user):
    """Create access token for test user"""
    token = create_access_token(data={"user_id": test_user.id})
    return token


@pytest.fixture
async def test_user_token(user_token):
    """Alias for user_token (used by recommendation tests)."""
    return user_token


@pytest.fixture
async def admin_token(admin_user):
    """Create access token for admin user"""
    token = create_access_token(data={"user_id": admin_user.id})
    return token


@pytest.fixture
def mock_ai_engine():
    """Mock AI evaluation engine"""
    engine = AsyncMock()
    engine.evaluate_answer = AsyncMock(return_value={
        "score": 85,
        "feedback": "Good answer",
        "confidence": 0.9
    })
    engine.analyze_resume = AsyncMock(return_value={
        "score": 80,
        "summary": "Strong candidate"
    })
    engine.analyze_facial_expressions = AsyncMock(return_value={
        "confidence": 0.8,
        "expressions": {"smile": 0.7}
    })
    return engine


@pytest.fixture
def auth_headers(user_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Create admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def setup_redis():
    """Setup Redis for testing"""
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/15")
    redis_client = redis.from_url(redis_url)
    
    try:
        # Test connection
        redis_client.ping()
        print("Redis connection established")
        
        # Clear test database
        redis_client.flushdb()
        print("Redis test database cleared")
    except Exception as e:
        print(f"Redis connection warning: {e}")
        redis_client = None
    
    yield redis_client
    
    if redis_client:
        # Clean up after tests
        redis_client.flushdb()
        redis_client.close()


@pytest.fixture(autouse=True)
def mock_embedding_service(monkeypatch):
    """Mock EmbeddingService to avoid Hugging Face downloads in tests"""
    from unittest.mock import MagicMock, patch
    import numpy as np

    # Create mock embedding service
    mock_service = MagicMock()
    mock_service.embedding_dim = 384
    mock_service.get_embedding.return_value = np.random.randn(384).tolist()
    mock_service.get_embeddings_batch.return_value = [np.random.randn(384).tolist() for _ in range(5)]
    mock_service.compute_similarity.return_value = 0.85
    mock_service.compute_similarities.return_value = [0.8, 0.7, 0.6, 0.5, 0.4]
    mock_service.get_top_k_similar.return_value = [(1, 0.9), (2, 0.8), (3, 0.7)]
    mock_service.build_resource_text.return_value = "Test resource text"

    # Patch the EmbeddingService class
    with patch("app.recommenders.embedding_service.EmbeddingService", return_value=mock_service):
        with patch("app.recommenders.rag_recommender.EmbeddingService", return_value=mock_service):
            with patch("app.recommenders.content_based.EmbeddingService", return_value=mock_service):
                yield mock_service
