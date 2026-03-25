"""Test WebSocket connection and basic functionality"""
import pytest


@pytest.mark.skip(reason="需要运行中的 WebSocket 服务，作为集成测试单独运行")
@pytest.mark.asyncio
async def test_websocket_connection(db_session, test_user):
    """Test WebSocket connection establishment (skipped - requires server)."""
    pytest.skip("需要运行中的 WebSocket 服务")


@pytest.mark.skip(reason="需要运行中的 WebSocket 服务，作为集成测试单独运行")
@pytest.mark.asyncio
async def test_websocket_start_interview(db_session):
    """Test starting interview via WebSocket (skipped - requires server)."""
    pytest.skip("需要运行中的 WebSocket 服务")


@pytest.mark.skip(reason="需要运行中的 WebSocket 服务，作为集成测试单独运行")
@pytest.mark.asyncio
async def test_websocket_pause_resume(db_session):
    """Test pause and resume interview via WebSocket (skipped - requires server)."""
    pytest.skip("需要运行中的 WebSocket 服务")


if __name__ == "__main__":
    print("Running manual WebSocket test...")
    print("Note: This requires the FastAPI server to be running")
    print("Start the server with: uvicorn app.main:app --reload")
