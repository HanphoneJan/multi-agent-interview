"""Video processing service for interview sessions"""
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile
import json
from datetime import datetime

from app.utils.log_helper import get_logger

logger = get_logger("services.video")

class VideoProcessingService:
    """Service for processing video during interviews"""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "interview_video"
        self.temp_dir.mkdir(exist_ok=True)
        self._face_detector = None  # Face detection engine placeholder
        self._emotion_detector = None  # Emotion detection engine placeholder
        self._attention_tracker = None  # Attention tracking placeholder

    async def process_video_frame(
        self,
        frame_data: str,
        frame_format: str = "jpeg",
        timestamp: Optional[float] = None,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a single video frame

        Args:
            frame_data: Base64 encoded frame data
            frame_format: Image format (jpeg, png, etc.)
            timestamp: Frame timestamp (seconds since epoch)
            session_id: Interview session ID
            user_id: User ID

        Returns:
            Dict containing:
                - success: bool
                - face_detected: bool
                - emotion: Dict (emotion scores)
                - attention_score: float
                - landmarks: List (face landmarks)
                - error: str (if failed)
        """
        try:
            # Decode base64 frame data
            frame_bytes = self._decode_frame(frame_data)

            # Face detection
            face_detected, landmarks = await self._detect_faces(frame_bytes)

            # Emotion detection
            emotion = await self._detect_emotion(frame_bytes, face_detected)

            # Attention tracking
            attention_score = await self._track_attention(
                frame_bytes,
                face_detected,
                landmarks
            )

            return {
                "success": True,
                "face_detected": face_detected,
                "emotion": emotion,
                "attention_score": attention_score,
                "landmarks": landmarks,
                "timestamp": timestamp,
                "error": None
            }

        except Exception as e:
            logger.error(f"Video frame processing error: {e}")
            return {
                "success": False,
                "face_detected": False,
                "emotion": None,
                "attention_score": 0.0,
                "landmarks": None,
                "timestamp": timestamp,
                "error": str(e)
            }

    def _decode_frame(self, frame_data: str) -> bytes:
        """Decode base64 frame data"""
        try:
            # Remove data URL prefix if present
            if frame_data.startswith("data:"):
                frame_data = frame_data.split(",", 1)[1]
            return base64.b64decode(frame_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 frame data: {e}")

    async def _detect_faces(
        self,
        frame_bytes: bytes
    ) -> tuple[bool, Optional[List]]:
        """
        Detect faces in the frame
        This is a stub. Implement actual face detection in production
        """
        # TODO: Implement face detection using libraries like face_recognition
        # or MediaPipe
        logger.debug("Face detection processing")
        return False, None

    async def _detect_emotion(
        self,
        frame_bytes: bytes,
        face_detected: bool
    ) -> Dict[str, float]:
        """
        Detect emotions from the frame
        This is a stub. Implement actual emotion detection in production
        """
        if not face_detected:
            return {
                "happy": 0.0,
                "sad": 0.0,
                "angry": 0.0,
                "surprise": 0.0,
                "neutral": 0.0,
                "fear": 0.0,
                "disgust": 0.0
            }

        # TODO: Implement emotion detection using libraries like DeepFace
        logger.debug("Emotion detection processing")

        # Stub: Return neutral emotion
        return {
            "happy": 0.0,
            "sad": 0.0,
            "angry": 0.0,
            "surprise": 0.0,
            "neutral": 1.0,
            "fear": 0.0,
            "disgust": 0.0
        }

    async def _track_attention(
        self,
        frame_bytes: bytes,
        face_detected: bool,
        landmarks: Optional[List]
    ) -> float:
        """
        Track user's attention level (0.0 to 1.0)
        This is a stub. Implement actual attention tracking in production
        """
        if not face_detected:
            return 0.0

        # TODO: Implement attention tracking using gaze detection
        logger.debug("Attention tracking processing")

        # Stub: Return medium attention
        return 0.75

    async def save_frame(
        self,
        frame_data: str,
        frame_format: str,
        session_id: str,
        user_id: int,
        timestamp: float
    ) -> Optional[Path]:
        """Save a video frame to temporary file"""
        try:
            frame_bytes = self._decode_frame(frame_data)
            timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{session_id}_{user_id}_{timestamp_str}.{frame_format}"
            frame_path = self.temp_dir / filename

            with open(frame_path, "wb") as f:
                f.write(frame_bytes)

            logger.debug(f"Saved frame to {frame_path}")
            return frame_path

        except Exception as e:
            logger.error(f"Error saving frame: {e}")
            return None

    async def cleanup_temp_files(self, session_id: str):
        """Clean up temporary video files for a session"""
        try:
            pattern = f"{session_id}_*"
            for file in self.temp_dir.glob(pattern):
                file.unlink()
                logger.info(f"Cleaned up temporary file: {file}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    def set_face_detector(self, detector):
        """Set the face detection engine"""
        self._face_detector = detector
        logger.info("Face detector updated")

    def set_emotion_detector(self, detector):
        """Set the emotion detection engine"""
        self._emotion_detector = detector
        logger.info("Emotion detector updated")

    def set_attention_tracker(self, tracker):
        """Set the attention tracking engine"""
        self._attention_tracker = tracker
        logger.info("Attention tracker updated")


class VideoAnalyticsService:
    """Service for aggregating and analyzing video data across an interview"""

    def __init__(self):
        self.frame_history: Dict[str, Dict[int, List[Dict]]] = {}

    def record_frame_result(
        self,
        session_id: str,
        user_id: int,
        frame_result: Dict
    ):
        """Record a frame processing result"""
        if session_id not in self.frame_history:
            self.frame_history[session_id] = {}
        if user_id not in self.frame_history[session_id]:
            self.frame_history[session_id][user_id] = []

        self.frame_history[session_id][user_id].append(frame_result)

    def get_session_analytics(
        self,
        session_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Get aggregated analytics for a session"""
        if session_id not in self.frame_history:
            return {
                "total_frames": 0,
                "frames_with_face": 0,
                "face_detection_rate": 0.0,
                "avg_attention": 0.0,
                "emotion_distribution": {},
                "attention_timeline": []
            }

        frames = self.frame_history[session_id].get(user_id, [])
        if not frames:
            return {
                "total_frames": 0,
                "frames_with_face": 0,
                "face_detection_rate": 0.0,
                "avg_attention": 0.0,
                "emotion_distribution": {},
                "attention_timeline": []
            }

        frames_with_face = [f for f in frames if f.get("face_detected", False)]
        face_detection_rate = len(frames_with_face) / len(frames) if frames else 0.0

        # Average attention
        attention_scores = [
            f.get("attention_score", 0.0) for f in frames_with_face
            if f.get("success")
        ]
        avg_attention = (
            sum(attention_scores) / len(attention_scores)
            if attention_scores else 0.0
        )

        # Emotion distribution
        emotion_distribution = {
            "happy": 0.0,
            "sad": 0.0,
            "angry": 0.0,
            "surprise": 0.0,
            "neutral": 0.0,
            "fear": 0.0,
            "disgust": 0.0
        }
        for frame in frames_with_face:
            emotion = frame.get("emotion", {})
            for key in emotion_distribution:
                emotion_distribution[key] += emotion.get(key, 0.0)

        total_frames_with_face = len(frames_with_face)
        if total_frames_with_face > 0:
            for key in emotion_distribution:
                emotion_distribution[key] /= total_frames_with_face

        # Attention timeline
        attention_timeline = [
            {
                "timestamp": f.get("timestamp"),
                "attention_score": f.get("attention_score", 0.0)
            }
            for f in frames_with_face
            if f.get("success")
        ]

        return {
            "total_frames": len(frames),
            "frames_with_face": len(frames_with_face),
            "face_detection_rate": face_detection_rate,
            "avg_attention": avg_attention,
            "emotion_distribution": emotion_distribution,
            "attention_timeline": attention_timeline
        }

    def clear_session_history(self, session_id: str):
        """Clear history for a session"""
        if session_id in self.frame_history:
            del self.frame_history[session_id]
            logger.info(f"Cleared video history for session {session_id}")


# Global video processing service instances
video_service = VideoProcessingService()
video_analytics_service = VideoAnalyticsService()
