"""Text-to-Speech (TTS) Service with multiple provider support"""
import abc
import asyncio
import base64
import hashlib
import hmac
import json
import time
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass

import httpx
import websockets

from app.config import get_settings
from app.utils.log_helper import get_logger

logger = get_logger("services.tts")


class TTSProvider(Enum):
    """TTS Provider Types"""
    XFYUN = "xfyun"          # 讯飞星火
    ALIYUN = "aliyun"        # 阿里云
    QWEN = "qwen"            # 通义千问
    MOCK = "mock"            # Mock (for testing)


@dataclass
class TTSConfig:
    """TTS Configuration"""
    provider: TTSProvider = TTSProvider.MOCK
    # XFYun settings
    xfyun_app_id: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""
    xfyun_voice: str = "xiaoyan"  # xiaoyan, xiaofeng, xiaomei, xiaoyu, xiaoxin
    # Aliyun settings
    aliyun_app_key: str = ""
    aliyun_token: str = ""
    # Qwen settings
    qwen_api_key: str = ""
    qwen_voice: str = "longxiaochun"
    # Common settings
    sample_rate: int = 16000
    speed: int = 50          # 0-100
    volume: int = 50         # 0-100
    pitch: int = 50          # 0-100


@dataclass
class TTSResult:
    """TTS Synthesis Result"""
    success: bool
    audio_data: Optional[bytes] = None
    audio_format: str = "mp3"
    duration: float = 0.0
    error_message: Optional[str] = None


class BaseTTSEngine(abc.ABC):
    """Base TTS Engine Interface"""

    @abc.abstractmethod
    async def synthesize(self, text: str, **kwargs) -> TTSResult:
        """
        Synthesize text to speech

        Args:
            text: Text to synthesize
            **kwargs: Additional parameters (voice, speed, etc.)

        Returns:
            TTSResult with audio data
        """
        pass

    @abc.abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesize text to speech

        Args:
            text: Text to synthesize
            **kwargs: Additional parameters

        Yields:
            Audio data chunks
        """
        pass

    async def close(self):
        """Close the engine and cleanup resources"""
        pass


class XFYunTTSEngine(BaseTTSEngine):
    """Xunfei (iFlytek) Spark TTS Engine"""

    WEBSOCKET_URL = "wss://tts-api.xfyun.cn/v2/tts"

    def __init__(self, config: TTSConfig):
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Validate configuration"""
        if not all([
            self.config.xfyun_app_id,
            self.config.xfyun_api_key,
            self.config.xfyun_api_secret
        ]):
            raise ValueError("XFYun TTS requires app_id, api_key, and api_secret")

    def _generate_auth_url(self) -> str:
        """Generate authenticated WebSocket URL"""
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        signature_origin = (
            f"host: tts-api.xfyun.cn\n"
            f"date: {date}\n"
            f"GET /v2/tts HTTP/1.1"
        )

        signature_sha = hmac.new(
            self.config.xfyun_api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode()

        authorization_origin = (
            f'api_key="{self.config.xfyun_api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode()).decode()

        return (
            f"{self.WEBSOCKET_URL}?"
            f"authorization={authorization}&"
            f"date={date.replace(' ', '%20')}&"
            f"host=tts-api.xfyun.cn"
        )

    def _build_request(self, text: str, **kwargs) -> dict:
        """Build TTS request payload"""
        voice = kwargs.get('voice', self.config.xfyun_voice)
        speed = kwargs.get('speed', self.config.speed)
        volume = kwargs.get('volume', self.config.volume)
        pitch = kwargs.get('pitch', self.config.pitch)

        return {
            "common": {
                "app_id": self.config.xfyun_app_id
            },
            "business": {
                "aue": "lame",           # MP3 format
                "sfl": 1,                # Stream
                "auf": f"audio/L16;rate={self.config.sample_rate}",
                "vcn": voice,
                "speed": speed,
                "volume": volume,
                "pitch": pitch,
                "bgs": 0,
                "tte": "UTF8"
            },
            "data": {
                "status": 2,
                "text": base64.b64encode(text.encode('utf-8')).decode()
            }
        }

    async def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Synthesize text to speech"""
        try:
            url = self._generate_auth_url()
            request_data = self._build_request(text, **kwargs)

            audio_chunks = []

            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(request_data))

                while True:
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=30)
                        result = json.loads(response)

                        code = result.get("code")
                        if code != 0:
                            message = result.get("message", "Unknown error")
                            logger.error(f"XFYun TTS error: {code} - {message}")
                            return TTSResult(
                                success=False,
                                error_message=f"TTS error: {message}"
                            )

                        data = result.get("data", {})
                        audio_base64 = data.get("audio", "")

                        if audio_base64:
                            audio_data = base64.b64decode(audio_base64)
                            audio_chunks.append(audio_data)

                        if data.get("status") == 2:
                            break

                    except asyncio.TimeoutError:
                        logger.error("XFYun TTS timeout")
                        return TTSResult(
                            success=False,
                            error_message="TTS timeout"
                        )

            if audio_chunks:
                combined_audio = b"".join(audio_chunks)
                duration = len(combined_audio) / (self.config.sample_rate * 2)

                return TTSResult(
                    success=True,
                    audio_data=combined_audio,
                    audio_format="mp3",
                    duration=duration
                )
            else:
                return TTSResult(
                    success=False,
                    error_message="No audio data received"
                )

        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"XFYun WebSocket error: {e.status_code}")
            return TTSResult(
                success=False,
                error_message=f"Connection failed: {e.status_code}"
            )
        except Exception as e:
            logger.error(f"XFYun TTS error: {e}")
            return TTSResult(
                success=False,
                error_message=str(e)
            )

    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesize text to speech"""
        try:
            url = self._generate_auth_url()
            request_data = self._build_request(text, **kwargs)

            async with websockets.connect(url, ping_interval=None) as ws:
                await ws.send(json.dumps(request_data))

                while True:
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=30)
                        result = json.loads(response)

                        code = result.get("code")
                        if code != 0:
                            message = result.get("message", "Unknown error")
                            logger.error(f"XFYun TTS stream error: {code} - {message}")
                            break

                        data = result.get("data", {})
                        audio_base64 = data.get("audio", "")

                        if audio_base64:
                            audio_data = base64.b64decode(audio_base64)
                            yield audio_data

                        if data.get("status") == 2:
                            break

                    except asyncio.TimeoutError:
                        logger.error("XFYun TTS stream timeout")
                        break

        except Exception as e:
            logger.error(f"XFYun TTS stream error: {e}")


class AliyunTTSEngine(BaseTTSEngine):
    """Aliyun TTS Engine (placeholder)"""

    def __init__(self, config: TTSConfig):
        self.config = config

    def _build_auth_header(self) -> dict:
        """Build Aliyun authorization header"""
        import datetime
        import uuid

        date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        nonce = str(uuid.uuid4())

        return {
            "X-NLS-Token": self.config.aliyun_token,
            "Content-Type": "application/octet-stream",
            "X-NLS-Date": date,
            "X-NLS-Nonce": nonce,
        }

    async def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Synthesize text using Aliyun TTS"""
        if not all([self.config.aliyun_app_key, self.config.aliyun_token]):
            return TTSResult(
                success=False,
                error_message="Aliyun TTS not configured. Missing app_key or token."
            )

        try:
            voice = kwargs.get("voice", "xiaoyun")
            speed = kwargs.get("speed", self.config.speed)
            volume = kwargs.get("volume", self.config.volume)
            pitch = kwargs.get("pitch", self.config.pitch)

            url = f"https://nls-gateway.aliyuncs.com/stream/v1/tts"
            headers = self._build_auth_header()

            payload = {
                "appkey": self.config.aliyun_app_key,
                "text": text,
                "format": "mp3",
                "sample_rate": self.config.sample_rate,
                "voice": voice,
                "speech_rate": int((speed - 50) * 10),  # Convert to -500~500
                "volume": int(volume * 2),  # Convert to 0-200
                "pitch_rate": int((pitch - 50) * 10),  # Convert to -500~500
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    audio_data = response.content
                    duration = len(audio_data) / 16000  # Rough estimate

                    return TTSResult(
                        success=True,
                        audio_data=audio_data,
                        audio_format="mp3",
                        duration=duration
                    )
                else:
                    error_msg = f"Aliyun TTS error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return TTSResult(success=False, error_message=error_msg)

        except Exception as e:
            logger.error(f"Aliyun TTS error: {e}")
            return TTSResult(success=False, error_message=str(e))

    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesize text using Aliyun TTS (non-streaming fallback)"""
        result = await self.synthesize(text, **kwargs)
        if result.success and result.audio_data:
            chunk_size = 1024
            for i in range(0, len(result.audio_data), chunk_size):
                yield result.audio_data[i:i + chunk_size]


class QwenTTSEngine(BaseTTSEngine):
    """Qwen (DashScope) TTS Engine"""

    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/speech"

    def __init__(self, config: TTSConfig):
        self.config = config

    async def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Synthesize text using Qwen (DashScope) TTS"""
        if not self.config.qwen_api_key:
            return TTSResult(
                success=False,
                error_message="Qwen TTS not configured. Missing API key."
            )

        try:
            voice = kwargs.get("voice", self.config.qwen_voice)
            speed = kwargs.get("speed", self.config.speed)

            # Map speed 0-100 to valid range for Qwen
            speech_rate = int(0.5 + (speed - 50) * 0.01)  # -0.5 ~ 1.5

            headers = {
                "Authorization": f"Bearer {self.config.qwen_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "speech-turbo",
                "input": {"text": text},
                "parameters": {
                    "voice": voice,
                    "speed_ratio": max(0.5, min(2.0, 1.0 + speech_rate)),
                    "format": "mp3",
                    "sample_rate": self.config.sample_rate,
                },
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.API_URL, headers=headers, json=payload)

                if response.status_code == 200:
                    audio_data = response.content
                    duration = len(text) * 0.25  # Rough estimate: 0.25s per char

                    return TTSResult(
                        success=True,
                        audio_data=audio_data,
                        audio_format="mp3",
                        duration=duration
                    )
                else:
                    error_msg = f"Qwen TTS error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return TTSResult(success=False, error_message=error_msg)

        except Exception as e:
            logger.error(f"Qwen TTS error: {e}")
            return TTSResult(success=False, error_message=str(e))

    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """Stream synthesize text using Qwen TTS (non-streaming fallback)"""
        result = await self.synthesize(text, **kwargs)
        if result.success and result.audio_data:
            chunk_size = 1024
            for i in range(0, len(result.audio_data), chunk_size):
                yield result.audio_data[i:i + chunk_size]


class NoConfigTTSEngine(BaseTTSEngine):
    """TTS Engine that returns error when no configuration is available"""

    def __init__(self, config: TTSConfig):
        self.config = config

    async def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Return error - no TTS provider configured"""
        logger.error("TTS synthesis failed: no TTS provider configured")

        return TTSResult(
            success=False,
            audio_data=None,
            audio_format="mp3",
            duration=0.0,
            error_message="TTS service not configured. Please configure XFYun, Aliyun, or Qwen TTS provider."
        )

    async def synthesize_stream(
        self,
        text: str,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """Return error - no TTS provider configured"""
        logger.error("TTS streaming failed: no TTS provider configured")
        # Immediately stop the generator
        return


class TTSService:
    """Text-to-Speech Service"""

    _instance: Optional['TTSService'] = None
    _engine: Optional[BaseTTSEngine] = None
    _config: Optional[TTSConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: Optional[TTSConfig] = None):
        """Initialize TTS service with configuration"""
        if config is None:
            config = self._create_config_from_settings()

        self._config = config
        self._engine = self._create_engine(config)
        logger.info(f"TTS Service initialized with provider: {config.provider.value}")

    def _create_config_from_settings(self) -> TTSConfig:
        """Create TTS config from application settings"""
        settings = get_settings()

        # Determine provider based on settings
        provider_map = {
            "xfyun": TTSProvider.XFYUN,
            "aliyun": TTSProvider.ALIYUN,
            "qwen": TTSProvider.QWEN,
            "mock": TTSProvider.MOCK,
            "auto": None,  # Will be determined automatically
        }

        provider = provider_map.get(settings.TTS_PROVIDER.lower(), TTSProvider.MOCK)

        # Auto-detect provider if set to auto (priority: XFYun > Aliyun > Qwen)
        if provider is None:
            if settings.XFYUN_APP_ID and settings.XFYUN_APP_KEY and settings.XFYUN_APP_SECRET:
                provider = TTSProvider.XFYUN
                logger.info("Auto-selected TTS provider: XFYun (讯飞)")
            elif settings.ALIYUN_TTS_APPKEY and settings.ALIYUN_TTS_TOKEN:
                provider = TTSProvider.ALIYUN
                logger.info("Auto-selected TTS provider: Aliyun")
            elif settings.QWEN_API_KEY:
                provider = TTSProvider.QWEN
                logger.info("Auto-selected TTS provider: Qwen")
            else:
                provider = TTSProvider.MOCK
                logger.warning("No TTS provider configured, using error fallback")

        return TTSConfig(
            provider=provider,
            xfyun_app_id=settings.XFYUN_APP_ID or "",
            xfyun_api_key=settings.XFYUN_APP_KEY or "",
            xfyun_api_secret=settings.XFYUN_APP_SECRET or "",
            xfyun_voice=settings.XFYUN_VOICE or "xiaoyan",
            qwen_api_key=settings.QWEN_API_KEY or "",
            aliyun_app_key=settings.ALIYUN_TTS_APPKEY or "",
            speed=settings.XFYUN_SPEED,
            volume=settings.XFYUN_VOLUME,
            pitch=settings.XFYUN_PITCH,
        )

    def _create_engine(self, config: TTSConfig) -> BaseTTSEngine:
        """Create TTS engine based on configuration"""
        engines = {
            TTSProvider.XFYUN: XFYunTTSEngine,
            TTSProvider.ALIYUN: AliyunTTSEngine,
            TTSProvider.QWEN: QwenTTSEngine,
            TTSProvider.MOCK: NoConfigTTSEngine,
        }

        engine_class = engines.get(config.provider, NoConfigTTSEngine)
        return engine_class(config)

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[int] = None,
        **kwargs
    ) -> TTSResult:
        """
        Synthesize text to speech

        Args:
            text: Text to synthesize
            voice: Voice type (overrides config)
            speed: Speech speed 0-100 (overrides config)
            **kwargs: Additional parameters

        Returns:
            TTSResult with audio data
        """
        if self._engine is None:
            self.initialize()

        kwargs_override = {}
        if voice:
            kwargs_override['voice'] = voice
        if speed is not None:
            kwargs_override['speed'] = speed

        kwargs.update(kwargs_override)

        return await self._engine.synthesize(text, **kwargs)

    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesize text to speech

        Args:
            text: Text to synthesize
            voice: Voice type (overrides config)
            speed: Speech speed 0-100 (overrides config)
            **kwargs: Additional parameters

        Yields:
            Audio data chunks
        """
        if self._engine is None:
            self.initialize()

        kwargs_override = {}
        if voice:
            kwargs_override['voice'] = voice
        if speed is not None:
            kwargs_override['speed'] = speed

        kwargs.update(kwargs_override)

        async for chunk in self._engine.synthesize_stream(text, **kwargs):
            yield chunk

    async def save_audio(
        self,
        result: TTSResult,
        output_path: Path,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save synthesized audio to file

        Args:
            result: TTS result with audio data
            output_path: Directory to save file
            filename: Optional filename (default: auto-generated)

        Returns:
            Path to saved file
        """
        if not result.success or result.audio_data is None:
            raise ValueError("Cannot save failed TTS result")

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = int(time.time())
            filename = f"tts_{timestamp}.{result.audio_format}"

        file_path = output_path / filename

        with open(file_path, "wb") as f:
            f.write(result.audio_data)

        logger.info(f"Saved TTS audio to {file_path}")
        return file_path

    def get_provider(self) -> TTSProvider:
        """Get current TTS provider"""
        if self._config is None:
            self.initialize()
        return self._config.provider

    async def close(self):
        """Close TTS service and cleanup"""
        if self._engine:
            await self._engine.close()
            self._engine = None
            logger.info("TTS Service closed")


# Global TTS service instance
tts_service = TTSService()
