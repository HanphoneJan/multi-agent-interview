"""Interview API tests"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete

from app.models.interview import interview_scenarios, interview_sessions
from app.core.constants import InterviewSessionStatus


@pytest.mark.asyncio
class TestInterviewScenarios:
    """Test interview scenario endpoints"""
    
    async def test_create_scenario(self, async_client: AsyncClient, admin_token: str):
        """Test creating interview scenario"""
        response = await async_client.post(
            "/api/v1/interviews/scenarios",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Python 面试",
                "technology_field": "Python",
                "description": "Python 相关面试",
                "requirements": "熟悉 Python 基础语法",
                "is_realtime": True
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Python 面试"
        assert data["technology_field"] == "Python"
        assert "id" in data
    
    async def test_list_scenarios(self, async_client: AsyncClient):
        """Test listing interview scenarios"""
        response = await async_client.get("/api/v1/interviews/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    async def test_get_scenario(self, async_client: AsyncClient, db_session):
        """Test getting scenario by ID"""
        # Create scenario
        from app.services.interview_service import create_scenario
        from app.schemas.interview import InterviewScenarioCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(
                name="Test Scenario",
                technology_field="Python"
            )
        )
        
        response = await async_client.get(f"/api/v1/interviews/scenarios/{scenario['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scenario["id"]
        assert data["name"] == "Test Scenario"
    
    async def test_update_scenario(self, async_client: AsyncClient, db_session, admin_token: str):
        """Test updating scenario"""
        from app.services.interview_service import create_scenario
        from app.schemas.interview import InterviewScenarioCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Old Name", technology_field="Python")
        )
        
        response = await async_client.put(
            f"/api/v1/interviews/scenarios/{scenario['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "New Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
    
    async def test_delete_scenario(self, async_client: AsyncClient, db_session, admin_token: str):
        """Test deleting scenario"""
        from app.services.interview_service import create_scenario
        from app.schemas.interview import InterviewScenarioCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Delete Me", technology_field="Python")
        )
        
        response = await async_client.delete(
            f"/api/v1/interviews/scenarios/{scenario['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # Verify deletion
        result = await db_session.execute(
            select(interview_scenarios).where(interview_scenarios.c.id == scenario["id"])
        )
        assert result.first() is None


@pytest.mark.asyncio
class TestInterviewSessions:
    """Test interview session endpoints"""
    
    async def test_create_session(self, async_client: AsyncClient, user_token: str, db_session):
        """Test creating interview session"""
        # Create scenario first
        from app.services.interview_service import create_scenario
        from app.schemas.interview import InterviewScenarioCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test Scenario", technology_field="Python")
        )
        
        response = await async_client.post(
            "/api/v1/interviews/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"scenario_id": scenario["id"]}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["scenario_id"] == scenario["id"]
        assert data["status"] == InterviewSessionStatus.CREATED
        assert data["is_finished"] is False
    
    async def test_get_session(self, async_client: AsyncClient, user_token: str, db_session):
        """Test getting session by ID"""
        from app.services.interview_service import create_scenario, create_session
        from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test Scenario", technology_field="Python")
        )
        
        # Create user and session
        from app.models.user import users
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        response = await async_client.get(
            f"/api/v1/interviews/sessions/{session['id']}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session["id"]
        assert "scenario" in data
    
    async def test_list_user_sessions(self, async_client: AsyncClient, user_token: str):
        """Test listing user's sessions"""
        response = await async_client.get(
            "/api/v1/interviews/sessions",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    async def test_pause_session(self, async_client: AsyncClient, user_token: str, db_session):
        """Test pausing session"""
        from app.services.interview_service import create_scenario, create_session, update_session
        from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate, InterviewSessionUpdate
        from app.models.user import users
        
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        # Set to in_progress
        await update_session(
            db_session,
            session["id"],
            InterviewSessionUpdate(status=InterviewSessionStatus.IN_PROGRESS)
        )
        
        response = await async_client.put(
            f"/api/v1/interviews/sessions/{session['id']}/pause",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == InterviewSessionStatus.PAUSED
        assert data["paused_at"] is not None
    
    async def test_resume_session(self, async_client: AsyncClient, user_token: str, db_session):
        """Test resuming session"""
        from app.services.interview_service import create_scenario, create_session, update_session
        from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate, InterviewSessionUpdate
        from app.models.user import users
        
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        # Pause first
        await update_session(
            db_session,
            session["id"],
            InterviewSessionUpdate(status=InterviewSessionStatus.PAUSED)
        )
        
        response = await async_client.put(
            f"/api/v1/interviews/sessions/{session['id']}/resume",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == InterviewSessionStatus.IN_PROGRESS
        assert data["resumed_at"] is not None
    
    async def test_end_session(self, async_client: AsyncClient, user_token: str, db_session):
        """Test ending session"""
        from app.services.interview_service import create_scenario, create_session
        from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate
        from app.models.user import users
        
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        response = await async_client.post(
            f"/api/v1/interviews/sessions/{session['id']}/end",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == InterviewSessionStatus.COMPLETED
        assert data["is_finished"] is True
        assert data["end_time"] is not None
    
    async def test_cancel_session(self, async_client: AsyncClient, user_token: str, db_session):
        """Test cancelling session"""
        from app.services.interview_service import create_scenario, create_session
        from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate
        from app.models.user import users
        
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        response = await async_client.post(
            f"/api/v1/interviews/sessions/{session['id']}/cancel",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == InterviewSessionStatus.CANCELLED
        assert data["end_time"] is not None


@pytest.mark.asyncio
class TestInterviewQuestions:
    """Test interview question endpoints"""
    
    async def test_create_question(self, async_client: AsyncClient, user_token: str, db_session):
        """Test creating question"""
        from app.services.interview_service import create_scenario, create_session, create_question
        from app.schemas.interview import (
            InterviewScenarioCreate,
            InterviewSessionCreate,
            InterviewQuestionCreate
        )
        from app.models.user import users
        
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        response = await async_client.post(
            f"/api/v1/interviews/sessions/{session['id']}/questions",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "question_text": "请介绍一下 Python 的 GIL",
                "question_number": 1
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["question_text"] == "请介绍一下 Python 的 GIL"
        assert data["question_number"] == 1
        assert data["session_id"] == session["id"]
    
    async def test_list_questions(self, async_client: AsyncClient, user_token: str, db_session):
        """Test listing session questions"""
        from app.services.interview_service import (
            create_scenario,
            create_session,
            create_question
        )
        from app.schemas.interview import (
            InterviewScenarioCreate,
            InterviewSessionCreate,
            InterviewQuestionCreate
        )
        from app.models.user import users
        
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        result = await db_session.execute(select(users).limit(1))
        user = result.first()
        
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        # Create questions
        await create_question(
            db_session,
            session["id"],
            InterviewQuestionCreate(question_text="Q1", question_number=1)
        )
        await create_question(
            db_session,
            session["id"],
            InterviewQuestionCreate(question_text="Q2", question_number=2)
        )
        
        response = await async_client.get(
            f"/api/v1/interviews/sessions/{session['id']}/questions",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["question_number"] == 1
        assert data[1]["question_number"] == 2


@pytest.mark.asyncio
class TestInterviewAuth:
    """Test authentication requirements"""
    
    async def test_create_session_requires_auth(self, async_client: AsyncClient):
        """Test that creating session requires authentication"""
        response = await async_client.post(
            "/api/v1/interviews/sessions",
            json={"scenario_id": 1}
        )
        assert response.status_code == 401
    
    async def test_get_sessions_requires_auth(self, async_client: AsyncClient):
        """Test that listing sessions requires authentication"""
        response = await async_client.get("/api/v1/interviews/sessions")
        assert response.status_code == 401
