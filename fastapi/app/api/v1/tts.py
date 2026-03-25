"""TTS API endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.services.tts_service import tts_service, TTSProvider

router = APIRouter(prefix="/tts", tags=["TTS"])


class TTSSynthesizeRequest(BaseModel):
    """TTS Synthesis Request"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice type (e.g., xiaoyan, xiaofeng)")
    speed: Optional[int] = Field(None, ge=0, le=100, description="Speech speed (0-100)")
    volume: Optional[int] = Field(None, ge=0, le=100, description="Volume (0-100)")
    pitch: Optional[int] = Field(None, ge=0, le=100, description="Pitch (0-100)")


class TTSSynthesizeResponse(BaseModel):
    """TTS Synthesis Response"""
    success: bool
    audio_base64: Optional[str] = None
    audio_format: str = "mp3"
    duration: float = 0.0
    provider: str
    error_message: Optional[str] = None


class TTSProviderInfo(BaseModel):
    """TTS Provider Information"""
    provider: str
    available_providers: list[str]
    voices: dict[str, list[str]]


# Available voices for each provider
VOICE_OPTIONS = {
    "xfyun": [
        "xiaoyan",    # 小燕 - 女声
        "xiaofeng",   # 小峰 - 男声
        "xiaomei",    # 小美 - 女声
        "xiaoyu",     # 小宇 - 男声
        "xiaoxin",    # 小新 - 童声
    ],
    "aliyun": [
        "xiaoyun",    # 小云
        "xiaogang",   # 小刚
    ],
    "qwen": [
        "longxiaochun",  # 龙小淳
        "longxiaoxia",   # 龙小夏
        "longxiaocheng", # 龙小诚
        "longxiaobai",   # 龙小白
    ],
}


@router.get("/provider", response_model=TTSProviderInfo)
async def get_tts_provider(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current TTS provider information

    Returns information about the currently configured TTS provider
    and available voice options.
    """
    provider = tts_service.get_provider()

    return TTSProviderInfo(
        provider=provider.value,
        available_providers=[p.value for p in TTSProvider],
        voices=VOICE_OPTIONS,
    )


@router.post("/synthesize", response_model=TTSSynthesizeResponse)
async def synthesize_speech(
    request: TTSSynthesizeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Synthesize text to speech

    Converts text to speech using the configured TTS provider.
    Returns base64-encoded audio data.

    - **text**: Text to synthesize (1-5000 characters)
    - **voice**: Voice type (provider-specific)
    - **speed**: Speech speed 0-100 (optional)
    - **volume**: Volume 0-100 (optional)
    - **pitch**: Pitch 0-100 (optional)
    """
    import base64

    try:
        result = await tts_service.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            volume=request.volume,
            pitch=request.pitch,
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error_message or "TTS synthesis failed"
            )

        # Encode audio data to base64
        audio_base64 = base64.b64encode(result.audio_data).decode() if result.audio_data else None

        return TTSSynthesizeResponse(
            success=True,
            audio_base64=audio_base64,
            audio_format=result.audio_format,
            duration=result.duration,
            provider=tts_service.get_provider().value,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS error: {str(e)}"
        )


@router.post("/synthesize/stream")
async def synthesize_speech_stream(
    request: TTSSynthesizeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Stream synthesize text to speech

    Streams audio data chunks as they are generated.
    Useful for real-time applications.

    Returns: StreamingResponse with audio/mpeg content type
    """
    from fastapi.responses import StreamingResponse
    import io

    async def audio_stream():
        async for chunk in tts_service.synthesize_stream(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            volume=request.volume,
            pitch=request.pitch,
        ):
            yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "attachment; filename=tts_output.mp3"
        }
    )


@router.get("/voices/{provider}")
async def get_voices(
    provider: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get available voices for a specific provider

    - **provider**: TTS provider name (xfyun, aliyun, qwen, mock)
    """
    if provider not in VOICE_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}. Available: {list(VOICE_OPTIONS.keys())}"
        )

    return {
        "provider": provider,
        "voices": VOICE_OPTIONS[provider]
    }


@router.post("/test")
async def test_tts(
    current_user: dict = Depends(get_current_user),
):
    """
    Test TTS service with a sample text

    Returns test result and provider information.
    """
    import base64

    test_text = "你好，这是一个TTS测试。Hello, this is a TTS test."

    try:
        result = await tts_service.synthesize(test_text)

        return {
            "success": result.success,
            "provider": tts_service.get_provider().value,
            "audio_format": result.audio_format,
            "duration": result.duration,
            "audio_size": len(result.audio_data) if result.audio_data else 0,
            "test_text": test_text,
            "error_message": result.error_message,
        }

    except Exception as e:
        return {
            "success": False,
            "provider": tts_service.get_provider().value,
            "error_message": str(e),
        }
