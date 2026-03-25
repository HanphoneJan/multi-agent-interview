"""Audio processing service for interview sessions"""
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import os

from app.utils.log_helper import get_logger

logger = get_logger("services.audio")

class AudioProcessingService:
    """Service for processing audio during interviews"""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "interview_audio"
        self.temp_dir.mkdir(exist_ok=True)
        self._asr_engine = None  # ASR engine placeholder
        self._noise_suppression_enabled = True

    async def save_audio_only(
        self,
        audio_data: str,
        audio_format: str = "wav",
        session_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save audio data without ASR processing.
        ASR has been moved to frontend for better performance.

        Args:
            audio_data: Base64 encoded audio data
            audio_format: Audio format (wav, mp3, etc.)
            session_id: Interview session ID
            user_id: User ID

        Returns:
            Dict containing:
                - success: bool
                - audio_path: str (path to saved file)
                - duration: float (estimated duration in seconds)
                - error: str (if failed)
        """
        try:
            # Decode base64 audio data
            audio_bytes = self._decode_audio(audio_data)

            # Calculate audio duration (simplified)
            duration = self._estimate_duration(audio_bytes, audio_format)

            # Save audio to temporary file
            audio_path = None
            if session_id and user_id:
                audio_path = await self._save_audio(
                    audio_bytes,
                    audio_format,
                    session_id,
                    user_id
                )

            logger.info(
                f"Audio saved for session {session_id}, user {user_id}, "
                f"duration: {duration:.2f}s, path: {audio_path}"
            )

            return {
                "success": True,
                "audio_path": str(audio_path) if audio_path else None,
                "duration": duration,
                "error": None
            }

        except Exception as e:
            logger.error(f"Audio save error: {e}")
            return {
                "success": False,
                "audio_path": None,
                "duration": 0.0,
                "error": str(e)
            }

    async def process_audio(
        self,
        audio_data: str,
        audio_format: str = "wav",
        session_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Audio processing with ASR has been moved to frontend.
        Use save_audio_only() for archiving purposes.

        Returns an error message directing frontend to use client-side ASR.
        """
        logger.warning(
            "process_audio() is deprecated. "
            "ASR has been moved to frontend. "
            "Use Web Speech API or send text directly."
        )

        return {
            "success": False,
            "transcript": None,
            "duration": 0.0,
            "confidence": 0.0,
            "audio_path": None,
            "error": "ASR has been moved to frontend. Please use client-side speech recognition."
        }

    def _decode_audio(self, audio_data: str) -> bytes:
        """Decode base64 audio data"""
        try:
            # Remove data URL prefix if present
            if audio_data.startswith("data:"):
                audio_data = audio_data.split(",", 1)[1]
            return base64.b64decode(audio_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 audio data: {e}")

    def _estimate_duration(self, audio_bytes: bytes, audio_format: str) -> float:
        """
        Estimate audio duration from bytes
        This is a simplified estimation. For production, use libraries like wave or pydub
        """
        # Rough estimation: 16kbps for voice
        # This should be replaced with actual audio library in production
        return len(audio_bytes) / (16000 * 2)  # Assume 16kHz, 16-bit mono

    async def _apply_noise_suppression(
        self,
        audio_bytes: bytes,
        audio_format: str
    ) -> bytes:
        """
        Apply noise suppression to audio
        This is a placeholder. Implement actual noise suppression in production
        """
        # TODO: Implement noise suppression using libraries like noisereduce
        return audio_bytes

    async def _speech_to_text(
        self,
        audio_bytes: bytes,
        audio_format: str,
        session_id: Optional[str],
        user_id: Optional[int]
    ) -> tuple[str, float]:
        """
        Convert speech to text using ASR engine
        This is a stub implementation. Replace with actual ASR in production
        """
        # TODO: Integrate actual ASR engine (e.g., Whisper, Google STT, Azure STT)
        # For now, return a placeholder transcript

        logger.info(
            f"ASR processing for session {session_id}, user {user_id}, "
            f"format: {audio_format}, size: {len(audio_bytes)} bytes"
        )

        # Stub: Return empty transcript with high confidence
        return "", 1.0

    async def _save_audio(
        self,
        audio_bytes: bytes,
        audio_format: str,
        session_id: str,
        user_id: int
    ) -> Optional[Path]:
        """Save audio to temporary file"""
        try:
            filename = f"{session_id}_{user_id}_{hash(audio_bytes)}.{audio_format}"
            audio_path = self.temp_dir / filename

            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"Saved audio to {audio_path}")
            return audio_path

        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return None

    async def cleanup_temp_files(self, session_id: str):
        """Clean up temporary audio files for a session"""
        try:
            pattern = f"{session_id}_*"
            for file in self.temp_dir.glob(pattern):
                file.unlink()
                logger.info(f"Cleaned up temporary file: {file}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

    def set_asr_engine(self, engine):
        """Set the ASR engine"""
        self._asr_engine = engine
        logger.info("ASR engine updated")

    def enable_noise_suppression(self, enabled: bool = True):
        """Enable or disable noise suppression"""
        self._noise_suppression_enabled = enabled
        logger.info(f"Noise suppression {'enabled' if enabled else 'disabled'}")


# Global audio processing service instance
audio_service = AudioProcessingService()
