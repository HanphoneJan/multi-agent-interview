"""Tests for app.tasks (cleanup, recommendation, evaluation)"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.tasks.celery_app import celery_app

# Run tasks synchronously in tests
celery_app.conf.task_always_eager = True

from app.tasks.evaluation_tasks import (
    evaluate_answer_task,
    generate_report_task,
)
from app.tasks.cleanup_tasks import (
    cleanup_expired_sessions_task,
    cleanup_expired_cache_task,
    cleanup_temporary_files_task,
    _run_redis_cache_cleanup,
)
from app.tasks.recommendation_tasks import train_recommendation_model_task


class TestCleanupTasks:
    """Test cleanup Celery tasks"""

    def test_cleanup_expired_sessions_success(self):
        """Test cleanup_expired_sessions when DB returns count"""
        with patch("app.tasks.cleanup_tasks.asyncio.run") as mock_run:
            mock_run.return_value = 3
            ret = cleanup_expired_sessions_task.apply()
            result = ret.result if hasattr(ret, "result") else ret
            assert result.get("cleaned_sessions") == 3
            assert result.get("status") == "success"

    def test_cleanup_expired_sessions_error(self):
        """Test cleanup_expired_sessions on error"""
        with patch("app.tasks.cleanup_tasks.asyncio.run") as mock_run:
            mock_run.side_effect = Exception("DB error")
            ret = cleanup_expired_sessions_task.apply()
            result = ret.result if hasattr(ret, "result") else ret
            assert result.get("cleaned_sessions") == 0
            assert result.get("status") == "error"
            assert "error" in result

    def test_cleanup_temporary_files(self):
        """Test cleanup_temporary_files returns skipped"""
        ret = cleanup_temporary_files_task.apply()
        result = ret.result if hasattr(ret, "result") else ret
        assert result.get("cleaned_files") == 0
        assert result.get("status") == "skipped"

    def test_cleanup_expired_cache_success(self):
        """Test cleanup_expired_cache when Redis is healthy"""
        with patch("app.tasks.cleanup_tasks.Redis") as MockRedis:
            mock_client = MagicMock()
            MockRedis.from_url.return_value = mock_client
            result = _run_redis_cache_cleanup()
            assert result["status"] == "success"
            assert "cleaned_entries" in result
            mock_client.ping.assert_called_once()
            mock_client.close.assert_called_once()

    def test_cleanup_expired_cache_error(self):
        """Test cleanup_expired_cache on Redis error"""
        with patch("app.tasks.cleanup_tasks.Redis") as MockRedis:
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Connection refused")
            MockRedis.from_url.return_value = mock_client
            result = _run_redis_cache_cleanup()
            assert result["status"] == "error"
            assert "error" in result


class TestRecommendationTasks:
    """Test recommendation Celery tasks"""

    def test_train_recommendation_model_all(self):
        """Test train_recommendation_model with model_type=all (hybrid path)"""
        ret = train_recommendation_model_task.apply(kwargs={"model_type": "all"})
        result = ret.result if hasattr(ret, "result") else ret
        assert result.get("status") == "completed"
        assert result.get("model_type") == "all"

    def test_train_recommendation_model_collaborative(self):
        """Test train_recommendation_model with model_type=collaborative"""
        ret = train_recommendation_model_task.apply(kwargs={"model_type": "collaborative"})
        result = ret.result if hasattr(ret, "result") else ret
        assert result.get("status") == "completed"
        assert result.get("model_type") == "collaborative"

    def test_train_recommendation_model_content(self):
        """Test train_recommendation_model with model_type=content"""
        ret = train_recommendation_model_task.apply(kwargs={"model_type": "content"})
        result = ret.result if hasattr(ret, "result") else ret
        assert result.get("status") == "completed"
        assert result.get("model_type") == "content"

    def test_train_recommendation_model_unknown(self):
        """Test train_recommendation_model with unknown model_type"""
        ret = train_recommendation_model_task.apply(kwargs={"model_type": "unknown"})
        result = ret.result if hasattr(ret, "result") else ret
        assert result.get("status") == "skipped"
        assert "error" in result


class TestEvaluationTasks:
    """Test evaluation Celery tasks (Qwen LLM)"""

    def test_evaluate_answer_task_no_qwen_key(self):
        """Test evaluate_answer returns placeholder when QWEN_API_KEY not set"""
        with patch("app.tasks.evaluation_tasks.get_settings") as mock_settings:
            mock_settings.return_value.QWEN_API_KEY = ""
            ret = evaluate_answer_task.apply(
                kwargs={"question_id": 1, "answer_text": "我的回答"}
            )
            result = ret.result if hasattr(ret, "result") else ret
        assert result["question_id"] == 1
        assert "evaluation_text" in result
        assert "请配置 QWEN_API_KEY" in result["evaluation_text"]
        assert result["score"] == 0.5

    def test_evaluate_answer_task_with_qwen(self):
        """Test evaluate_answer calls Qwen when key is set"""
        with patch("app.tasks.evaluation_tasks.get_settings") as mock_settings:
            mock_settings.return_value.QWEN_API_KEY = "sk-test"
        with patch(
            "app.tasks.evaluation_tasks._evaluate_answer_with_qwen",
            new_callable=AsyncMock,
        ) as mock_eval:
            mock_eval.return_value = {
                "evaluation_text": "表现良好",
                "score": 0.85,
                "strengths": ["清晰"],
                "weaknesses": ["可更详细"],
            }
            ret = evaluate_answer_task.apply(
                kwargs={"question_id": 1, "answer_text": "我的回答"}
            )
            result = ret.result if hasattr(ret, "result") else ret
        assert result["question_id"] == 1
        assert result["evaluation_text"] == "表现良好"
        assert result["score"] == 0.85
        assert result["strengths"] == ["清晰"]
        assert result["weaknesses"] == ["可更详细"]

    def test_generate_report_task_no_data(self):
        """Test generate_report returns placeholder when no session data"""
        with patch(
            "app.tasks.evaluation_tasks._generate_report_with_qwen",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = {
                "session_id": 1,
                "user_id": 0,
                "overall_score": "0",
                "overall_evaluation": "暂无面试记录",
                "help": "请完成面试后再生成报告",
                "recommendation": "",
            }
            ret = generate_report_task.apply(
                kwargs={"session_id": 1, "user_id": 0}
            )
            result = ret.result if hasattr(ret, "result") else ret
        assert result["session_id"] == 1
        assert "overall_evaluation" in result
