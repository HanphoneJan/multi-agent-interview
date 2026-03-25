"""Tests for audio/video processing services"""
import pytest
import base64
from app.services.audio_service import audio_service, AudioProcessingService
from app.services.video_service import video_service, video_analytics_service, VideoProcessingService, VideoAnalyticsService
from app.services.webrtc_service import webrtc_service, WebRTCService


class TestAudioService:
    """Test audio processing service"""

    @pytest.fixture
    def audio_service_instance(self):
        """Create audio service instance"""
        return AudioProcessingService()

    def test_decode_valid_audio(self, audio_service_instance):
        """Test decoding valid base64 audio"""
        test_data = base64.b64encode(b"test audio data").decode()
        result = audio_service_instance._decode_audio(test_data)
        assert result == b"test audio data"

    def test_decode_audio_with_data_url(self, audio_service_instance):
        """Test decoding audio with data URL prefix"""
        test_data = "data:audio/wav;base64," + base64.b64encode(b"test audio").decode()
        result = audio_service_instance._decode_audio(test_data)
        assert result == b"test audio"

    def test_decode_invalid_audio(self, audio_service_instance):
        """Test decoding invalid base64 audio"""
        with pytest.raises(ValueError):
            audio_service_instance._decode_audio("invalid base64!")

    def test_estimate_duration(self, audio_service_instance):
        """Test audio duration estimation"""
        test_bytes = b"x" * 32000  # ~1 second at 16kHz 16-bit
        duration = audio_service_instance._estimate_duration(test_bytes, "wav")
        assert duration > 0

    @pytest.mark.asyncio
    async def test_process_audio_success(self, audio_service_instance):
        """Test successful audio processing"""
        audio_data = base64.b64encode(b"test audio").decode()
        result = await audio_service_instance.process_audio(
            audio_data=audio_data,
            audio_format="wav",
            session_id="test_session",
            user_id=1
        )
        assert result["success"] is True
        assert "transcript" in result
        assert "duration" in result

    @pytest.mark.asyncio
    async def test_process_audio_failure(self, audio_service_instance):
        """Test audio processing with invalid data"""
        result = await audio_service_instance.process_audio(
            audio_data="invalid",
            audio_format="wav"
        )
        assert result["success"] is False
        assert result["error"] is not None


class TestVideoService:
    """Test video processing service"""

    @pytest.fixture
    def video_service_instance(self):
        """Create video service instance"""
        return VideoProcessingService()

    @pytest.fixture
    def analytics_service_instance(self):
        """Create video analytics service instance"""
        return VideoAnalyticsService()

    def test_decode_valid_frame(self, video_service_instance):
        """Test decoding valid base64 frame"""
        test_data = base64.b64encode(b"test frame data").decode()
        result = video_service_instance._decode_frame(test_data)
        assert result == b"test frame data"

    def test_decode_frame_with_data_url(self, video_service_instance):
        """Test decoding frame with data URL prefix"""
        test_data = "data:image/jpeg;base64," + base64.b64encode(b"test frame").decode()
        result = video_service_instance._decode_frame(test_data)
        assert result == b"test frame"

    def test_decode_invalid_frame(self, video_service_instance):
        """Test decoding invalid base64 frame"""
        with pytest.raises(ValueError):
            video_service_instance._decode_frame("invalid base64!")

    @pytest.mark.asyncio
    async def test_process_video_frame_success(self, video_service_instance):
        """Test successful video frame processing"""
        frame_data = base64.b64encode(b"test frame").decode()
        result = await video_service_instance.process_video_frame(
            frame_data=frame_data,
            frame_format="jpeg",
            timestamp=1234567890.0,
            session_id="test_session",
            user_id=1
        )
        assert result["success"] is True
        assert "face_detected" in result
        assert "emotion" in result
        assert "attention_score" in result

    @pytest.mark.asyncio
    async def test_process_video_frame_failure(self, video_service_instance):
        """Test video frame processing with invalid data"""
        result = await video_service_instance.process_video_frame(
            frame_data="invalid",
            frame_format="jpeg"
        )
        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_save_frame(self, video_service_instance):
        """Test saving frame to file"""
        frame_data = base64.b64encode(b"test frame").decode()
        result = await video_service_instance.save_frame(
            frame_data=frame_data,
            frame_format="jpeg",
            session_id="test_session",
            user_id=1,
            timestamp=1234567890.0
        )
        assert result is not None
        assert result.exists()

    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, video_service_instance):
        """Test cleanup of temporary files"""
        frame_data = base64.b64encode(b"test frame").decode()
        saved_path = await video_service_instance.save_frame(
            frame_data=frame_data,
            frame_format="jpeg",
            session_id="test_cleanup_session",
            user_id=1,
            timestamp=1234567890.0
        )
        assert saved_path.exists()

        await video_service_instance.cleanup_temp_files("test_cleanup_session")
        # Files should be cleaned up

    def test_record_frame_result(self, analytics_service_instance):
        """Test recording frame result"""
        frame_result = {
            "success": True,
            "face_detected": True,
            "emotion": {"happy": 0.5, "neutral": 0.5},
            "attention_score": 0.8,
            "timestamp": 1234567890.0
        }
        analytics_service_instance.record_frame_result(
            "test_session", 1, frame_result
        )
        assert "test_session" in analytics_service_instance.frame_history
        assert 1 in analytics_service_instance.frame_history["test_session"]

    def test_get_session_analytics_empty(self, analytics_service_instance):
        """Test getting analytics for empty session"""
        result = analytics_service_instance.get_session_analytics(
            "nonexistent_session", 1
        )
        assert result["total_frames"] == 0
        assert result["frames_with_face"] == 0

    def test_get_session_analytics_with_data(self, analytics_service_instance):
        """Test getting analytics with data"""
        for i in range(10):
            frame_result = {
                "success": True,
                "face_detected": i % 2 == 0,
                "emotion": {"happy": 0.5, "neutral": 0.5},
                "attention_score": 0.8,
                "timestamp": 1234567890.0 + i
            }
            analytics_service_instance.record_frame_result(
                "test_session", 1, frame_result
            )

        result = analytics_service_instance.get_session_analytics("test_session", 1)
        assert result["total_frames"] == 10
        assert result["frames_with_face"] == 5
        assert result["face_detection_rate"] == 0.5

    def test_clear_session_history(self, analytics_service_instance):
        """Test clearing session history"""
        frame_result = {
            "success": True,
            "face_detected": True,
            "emotion": {"happy": 0.5},
            "attention_score": 0.8,
            "timestamp": 1234567890.0
        }
        analytics_service_instance.record_frame_result("test_session", 1, frame_result)
        assert "test_session" in analytics_service_instance.frame_history

        analytics_service_instance.clear_session_history("test_session")
        assert "test_session" not in analytics_service_instance.frame_history


class TestWebRTCService:
    """Test WebRTC signaling service"""

    @pytest.fixture
    def webrtc_service_instance(self):
        """Create WebRTC service instance"""
        return WebRTCService()

    def test_create_connection(self, webrtc_service_instance):
        """Test creating a new WebRTC connection"""
        result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )
        assert result["success"] is True
        assert "connection_id" in result
        assert result["session_id"] == "test_session"
        assert result["host_user_id"] == 1

    def test_get_existing_connection(self, webrtc_service_instance):
        """Test getting existing connection for session"""
        webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )

        result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )
        assert result["success"] is True
        assert webrtc_service_instance.get_connection_by_session("test_session") is not None

    def test_set_host_offer(self, webrtc_service_instance):
        """Test setting host SDP offer"""
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )

        result = webrtc_service_instance.set_host_offer(
            conn_result["connection_id"],
            {"sdp": "test_sdp", "type": "offer"}
        )
        assert result["success"] is True

        conn = webrtc_service_instance.get_connection(conn_result["connection_id"])
        assert conn.host_offer is not None

    def test_set_guest_offer(self, webrtc_service_instance):
        """Test setting guest SDP offer"""
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1,
            guest_user_id=2
        )

        result = webrtc_service_instance.set_guest_offer(
            conn_result["connection_id"],
            {"sdp": "test_sdp", "type": "offer"}
        )
        assert result["success"] is True

        conn = webrtc_service_instance.get_connection(conn_result["connection_id"])
        assert conn.guest_offer is not None

    def test_add_host_ice_candidate(self, webrtc_service_instance):
        """Test adding host ICE candidate"""
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )

        result = webrtc_service_instance.add_host_ice_candidate(
            conn_result["connection_id"],
            {
                "candidate": "test_candidate",
                "sdp_mid": "0",
                "sdp_mline_index": 0
            }
        )
        assert result["success"] is True

        candidates = webrtc_service_instance.get_host_ice_candidates(
            conn_result["connection_id"]
        )
        assert len(candidates) == 1

    def test_add_guest_ice_candidate(self, webrtc_service_instance):
        """Test adding guest ICE candidate"""
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1,
            guest_user_id=2
        )

        result = webrtc_service_instance.add_guest_ice_candidate(
            conn_result["connection_id"],
            {
                "candidate": "test_candidate",
                "sdp_mid": "0",
                "sdp_mline_index": 0
            }
        )
        assert result["success"] is True

        candidates = webrtc_service_instance.get_guest_ice_candidates(
            conn_result["connection_id"]
        )
        assert len(candidates) == 1

    def test_close_connection(self, webrtc_service_instance):
        """Test closing a connection"""
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )

        result = webrtc_service_instance.close_connection(
            conn_result["connection_id"]
        )
        assert result["success"] is True
        assert result["status"] == "disconnected"

        conn = webrtc_service_instance.get_connection(conn_result["connection_id"])
        assert conn.status == "disconnected"

    def test_get_connection_info(self, webrtc_service_instance):
        """Test getting connection info"""
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )

        info = webrtc_service_instance.get_connection_info(
            conn_result["connection_id"]
        )
        assert info is not None
        assert info["connection_id"] == conn_result["connection_id"]
        assert info["session_id"] == "test_session"
        assert info["status"] == "pending"

    def test_cleanup_old_connections(self, webrtc_service_instance):
        """Test cleanup of old connections"""
        from datetime import datetime, timedelta

        # Create connection
        conn_result = webrtc_service_instance.create_connection(
            session_id="test_session",
            host_user_id=1
        )

        # Close it
        webrtc_service_instance.close_connection(conn_result["connection_id"])

        # Set created_at to old time
        conn = webrtc_service_instance.get_connection(conn_result["connection_id"])
        conn.created_at = datetime.now() - timedelta(hours=25)

        # Cleanup
        webrtc_service_instance.cleanup_old_connections(max_age_hours=24)

        # Connection should be removed
        assert webrtc_service_instance.get_connection(
            conn_result["connection_id"]
        ) is None
