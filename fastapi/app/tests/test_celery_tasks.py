"""Tests for Celery async tasks"""
import pytest
import base64
from unittest.mock import patch, MagicMock
from celery.result import AsyncResult

from app.workers.celery_app import celery_app
from app.workers.task_manager import TaskManager, task_manager
from app.workers import tasks


class TestCeleryApp:
    """Test Celery app configuration"""

    def test_celery_app_config(self):
        """Test Celery app is properly configured"""
        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.enable_utc is True

    def test_celery_queues(self):
        """Test task queues are configured"""
        queues = celery_app.conf.task_routes
        assert "app.workers.tasks.process_audio_task" in queues
        assert queues["app.workers.tasks.process_audio_task"]["queue"] == "audio"
        assert queues["app.workers.tasks.process_video_task"]["queue"] == "video"
        assert queues["app.workers.tasks.generate_report_task"]["queue"] == "reports"
        assert queues["app.workers.tasks.send_notification_task"]["queue"] == "notifications"


class TestTaskManager:
    """Test task manager"""

    def test_task_manager_init(self):
        """Test task manager initialization"""
        manager = TaskManager(celery_app)
        assert manager.celery == celery_app

    def test_submit_audio_task(self):
        """Test submitting audio processing task"""
        with patch.object(celery_app, 'send_task') as mock_send:
            mock_send.return_value = MagicMock(id="test-task-id")

            task_id = task_manager.submit_audio_task(
                audio_data_b64="data",
                session_id="123",
                user_id=1,
                audio_format="wav"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "app.workers.tasks.process_audio_task"
            assert call_args[1]["queue"] == "audio"
            assert task_id == "test-task-id"

    def test_submit_video_task(self):
        """Test submitting video processing task"""
        with patch.object(celery_app, 'send_task') as mock_send:
            mock_send.return_value = MagicMock(id="test-task-id")

            task_id = task_manager.submit_video_task(
                frame_data_b64="data",
                session_id="123",
                user_id=1,
                frame_format="jpeg",
                timestamp=123456.0
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "app.workers.tasks.process_video_task"
            assert call_args[1]["queue"] == "video"

    def test_submit_report_task(self):
        """Test submitting report generation task"""
        with patch.object(celery_app, 'send_task') as mock_send:
            mock_send.return_value = MagicMock(id="test-task-id")

            task_id = task_manager.submit_report_task(
                session_id="123",
                user_id=1
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "app.workers.tasks.generate_report_task"
            assert call_args[1]["queue"] == "reports"

    def test_submit_notification_task(self):
        """Test submitting notification task"""
        with patch.object(celery_app, 'send_task') as mock_send:
            mock_send.return_value = MagicMock(id="test-task-id")

            task_id = task_manager.submit_notification_task(
                user_id=1,
                message="Test notification",
                notification_type="info"
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "app.workers.tasks.send_notification_task"
            assert call_args[1]["queue"] == "notifications"

    def test_get_task_status(self):
        """Test getting task status"""
        with patch('app.workers.task_manager.AsyncResult') as mock_result:
            mock_result.return_value = MagicMock(status="SUCCESS")

            status = task_manager.get_task_status("test-task-id")

            mock_result.assert_called_once_with("test-task-id", app=celery_app)
            assert status == "SUCCESS"

    def test_is_task_ready(self):
        """Test checking if task is ready"""
        with patch('app.workers.task_manager.AsyncResult') as mock_result:
            mock_instance = MagicMock()
            mock_instance.ready = lambda: True
            mock_result.return_value = mock_instance

            is_ready = task_manager.is_task_ready("test-task-id")

            assert is_ready is True

    def test_is_task_successful(self):
        """Test checking if task was successful"""
        with patch('app.workers.task_manager.AsyncResult') as mock_result:
            mock_result.return_value = MagicMock(successful=lambda: True)

            is_successful = task_manager.is_task_successful("test-task-id")

            assert is_successful is True

    def test_get_task_result_value(self):
        """Test getting task result value"""
        test_result = {"success": True, "data": "test"}

        with patch('app.workers.task_manager.AsyncResult') as mock_result:
            mock_instance = MagicMock()
            mock_instance.ready.return_value = True
            mock_instance.result = test_result
            mock_result.return_value = mock_instance

            result = task_manager.get_task_result_value("test-task-id")

            assert result == test_result

    def test_get_task_result_value_not_ready(self):
        """Test getting result when task is not ready"""
        with patch('app.workers.task_manager.AsyncResult') as mock_result:
            mock_instance = MagicMock()
            mock_instance.ready.return_value = False
            mock_result.return_value = mock_instance

            result = task_manager.get_task_result_value("test-task-id")

            assert result is None

    def test_revoke_task(self):
        """Test revoking a task"""
        with patch.object(celery_app.control, 'revoke') as mock_revoke:
            task_manager.revoke_task("test-task-id", terminate=True)

            mock_revoke.assert_called_once_with("test-task-id", terminate=True)


class TestCeleryTasks:
    """Test Celery task functions"""

    @pytest.mark.skip(reason="Requires Celery worker running")
    def test_process_audio_task_success(self):
        """Test audio processing task"""
        audio_data = base64.b64encode(b"test audio").decode()

        result = tasks.process_audio_task(
            MagicMock(),  # self (bind=True)
            audio_data,
            session_id="123",
            user_id=1,
            audio_format="wav"
        )

        assert result["success"] is True
        assert "transcript" in result

    @pytest.mark.skip(reason="Requires Celery worker running")
    def test_process_video_task_success(self):
        """Test video processing task"""
        frame_data = base64.b64encode(b"test frame").decode()

        result = tasks.process_video_task(
            MagicMock(),  # self (bind=True)
            frame_data,
            session_id="123",
            user_id=1,
            frame_format="jpeg",
            timestamp=123456.0
        )

        assert result["success"] is True
        assert "face_detected" in result

    def test_send_notification_task(self):
        """Test notification task"""
        result = tasks.send_notification_task(
            user_id=1,
            message="Test message",
            notification_type="info"
        )

        assert result["success"] is True
        assert result["user_id"] == 1
        assert result["message"] == "Test message"

    def test_cleanup_temp_files_task(self):
        """Test cleanup temporary files task"""
        result = tasks.cleanup_temp_files_task()

        assert "active_sessions" in result

    def test_process_pending_evaluations_task(self):
        """Test process pending evaluations task"""
        result = tasks.process_pending_evaluations_task()

        assert "processed_count" in result
        assert "timestamp" in result


class TestCeleryIntegration:
    """Test Celery integration with FastAPI"""

    @pytest.mark.skip(reason="Requires Redis server running")
    def test_task_submission_and_result(self):
        """Test end-to-end task submission and result retrieval"""
        # This test requires:
        # 1. Redis server running
        # 2. Celery worker running
        # 3. FastAPI app running

        # Submit task
        audio_data = base64.b64encode(b"test audio").decode()
        task_id = task_manager.submit_audio_task(
            audio_data_b64=audio_data,
            session_id="123",
            user_id=1
        )

        # Wait for task to complete
        import time
        time.sleep(2)

        # Check status
        status = task_manager.get_task_status(task_id)
        assert status in ["PENDING", "STARTED", "SUCCESS", "FAILURE"]

        # Get result if ready
        if task_manager.is_task_ready(task_id):
            result = task_manager.get_task_result_value(task_id)
            assert result is not None
