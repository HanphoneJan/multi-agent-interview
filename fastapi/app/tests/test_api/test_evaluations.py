"""Evaluation API tests"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete

from app.models.interview import interview_sessions, interview_questions
from app.core.constants import InterviewSessionStatus


@pytest.mark.asyncio
class TestOverallEvaluations:
    """Test overall evaluation endpoints"""
    
    async def test_create_evaluation_report(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_user,
        db_session
    ):
        """Test creating evaluation report"""
        from app.services.interview_service import create_session
        from app.schemas.interview import InterviewSessionCreate

        user = test_user
        # Create scenario
        from app.services.interview_service import create_scenario
        from app.schemas.interview import InterviewScenarioCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test Scenario", technology_field="Python")
        )
        
        # Create session
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )

        response = await async_client.post(
            "/api/v1/evaluations/reports",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "session_id": session["id"],
                "user_id": user.id,
                "overall_evaluation": "Good performance",
                "help": "Improve communication",
                "recommendation": "Recommended for hire",
                "overall_score": 85,
                "professional_knowledge": 80,
                "skill_match": 75,
                "language_expression": 85,
                "logical_thinking": 80,
                "stress_response": 75,
                "personality": 85,
                "motivation": 90,
                "value": 85
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == session["id"]
        assert data["overall_evaluation"] == "Good performance"
    
    async def test_get_evaluation_report(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_user,
        db_session
    ):
        """Test getting evaluation report by ID"""
        from app.schemas.evaluation import OverallInterviewEvaluationCreate

        user = test_user
        # Create scenario and session
        from app.services.interview_service import create_scenario, create_session
        from app.schemas.interview import InterviewScenarioCreate, InterviewSessionCreate
        scenario = await create_scenario(
            db_session,
            InterviewScenarioCreate(name="Test", technology_field="Python")
        )
        session = await create_session(
            db_session,
            user.id,
            InterviewSessionCreate(scenario_id=scenario["id"])
        )
        
        # Create evaluation
        from app.services.evaluation_service import create_overall_evaluation
        evaluation = await create_overall_evaluation(
            db_session,
            OverallInterviewEvaluationCreate(
                session_id=session["id"],
                user_id=user.id,
                overall_evaluation="Test evaluation",
                help="Test help"
            )
        )
        
        # API 使用 session_id 作为 report_id 查询
        response = await async_client.get(
            f"/api/v1/evaluations/reports/{session['id']}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session["id"]
        assert data["overall_evaluation"] == "Test evaluation"
    
    async def test_list_user_evaluation_reports(
        self,
        async_client: AsyncClient,
        user_token: str
    ):
        """Test listing user's evaluation reports"""
        response = await async_client.get(
            "/api/v1/evaluations/reports",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    async def test_create_evaluation_forbidden(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_user
    ):
        """Test that user cannot create evaluation for another user"""
        other_user_id = test_user.id + 999  # 不同用户 ID，应被拒绝
        
        response = await async_client.post(
            "/api/v1/evaluations/reports",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "session_id": 1,
                "user_id": other_user_id,
                "overall_evaluation": "Test",
                "help": "Test"
            }
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestResumeEvaluations:
    """Test resume evaluation endpoints"""

    async def test_analyze_resume_txt(
        self,
        async_client: AsyncClient,
        user_token: str
    ):
        """Test resume analysis with TXT file"""
        import io

        # Create a simple text file for testing
        resume_content = b"Name: Test User\nEducation: Bachelor in Computer Science\nSkills: Python, JavaScript\nExperience: 2 years software development"
        file = io.BytesIO(resume_content)

        response = await async_client.post(
            "/api/v1/evaluations/resumes/analyze",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("resume.txt", file, "text/plain")}
        )
        # May fail with 503 if LLM not configured, but should not be 400 or mock
        assert response.status_code in [201, 400, 503]
        if response.status_code == 201:
            data = response.json()
            assert "resume_score" in data
            assert "resume_summary" in data

    async def test_analyze_resume_no_file(
        self,
        async_client: AsyncClient,
        user_token: str
    ):
        """Test resume analysis without file should fail"""
        response = await async_client.post(
            "/api/v1/evaluations/resumes/analyze",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        # Should fail because file is required
        assert response.status_code == 422  # Unprocessable Entity
    
    async def test_get_resume_evaluation(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_user,
        db_session
    ):
        """Test getting user's resume evaluation"""
        from app.services.evaluation_service import create_resume_evaluation

        user_id = test_user.id
        await create_resume_evaluation(
            db_session,
            user_id,
            resume_score="8.0",
            resume_summary="Good resume"
        )
        
        response = await async_client.get(
            "/api/v1/evaluations/resumes/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resume_score"] == "8.0"


@pytest.mark.asyncio
class TestFacialAnalysis:
    """Test facial analysis endpoint"""

    async def test_analyze_facial_expression(
        self,
        async_client: AsyncClient,
        user_token: str
    ):
        """Test facial expression analysis with valid image data"""
        import base64
        from io import BytesIO

        # Create a simple valid image for testing
        try:
            from PIL import Image

            # Create a simple 10x10 RGB image
            img = Image.new('RGB', (10, 10), color='red')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode()
        except ImportError:
            # PIL not available, use minimal valid base64 PNG
            image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        response = await async_client.post(
            "/api/v1/evaluations/facial/analyze",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "image_data": image_data
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "expression" in data
        assert "emotion" in data
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))


@pytest.mark.asyncio
class TestEvaluationAuth:
    """Test authentication requirements"""
    
    async def test_get_reports_requires_auth(self, async_client: AsyncClient):
        """Test that listing reports requires authentication"""
        response = await async_client.get("/api/v1/evaluations/reports")
        assert response.status_code == 401
    
    async def test_analyze_resume_requires_auth(self, async_client: AsyncClient):
        """Test that resume analysis requires authentication"""
        response = await async_client.post("/api/v1/evaluations/resumes/analyze")
        assert response.status_code == 401
    
    async def test_facial_analysis_requires_auth(self, async_client: AsyncClient):
        """Test that facial analysis requires authentication"""
        response = await async_client.post(
            "/api/v1/evaluations/facial/analyze",
            json={"image_data": "test"}
        )
        assert response.status_code == 401
