"""Qwen3-Omni HTTP API Service for non-realtime interviews

This service provides HTTP-based interaction with Qwen3-Omni model,
supporting text input and text+audio output for non-realtime interviews.
"""
import os
import base64
import asyncio
from typing import List, Dict, AsyncGenerator, Optional, Callable
from dataclasses import dataclass

from openai import OpenAI, AsyncOpenAI
from app.config import get_settings
import structlog

logger = structlog.get_logger()


@dataclass
class ChatChunk:
    """Chat response chunk"""
    type: str  # "text" | "audio" | "usage"
    content: Optional[str] = None  # text content
    audio_data: Optional[str] = None  # base64 encoded audio
    usage: Optional[Dict] = None  # usage info


class Qwen3OmniHTTPService:
    """Qwen3-Omni HTTP API Service"""

    # Available voices for audio output
    VOICES = ["Cherry", "Serena", "Ethan", "Chelsie"]

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.DASHSCOPE_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = getattr(settings, "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = "qwen3-omni-flash-2025-12-01"

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        logger.info(
            "Qwen3OmniHTTPService initialized",
            model=self.model,
            base_url=self.base_url,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        voice: str = "Cherry",
        stream: bool = True,
        on_text: Optional[Callable[[str], None]] = None,
        on_audio: Optional[Callable[[str], None]] = None,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Send chat request to Qwen3-Omni HTTP API

        Args:
            messages: List of messages with role and content
            voice: Voice for audio output (Cherry, Serena, Ethan, Chelsie)
            stream: Whether to stream the response
            on_text: Callback for text chunks
            on_audio: Callback for audio chunks

        Yields:
            ChatChunk: Response chunks (text or audio)
        """
        if voice not in self.VOICES:
            voice = "Cherry"
            logger.warning(f"Invalid voice, using default: {voice}")

        try:
            logger.info(
                "Sending chat request to Qwen3-Omni",
                message_count=len(messages),
                voice=voice,
                stream=stream,
            )

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                modalities=["text", "audio"],
                audio={"voice": voice, "format": "wav"},
                stream=stream,
                stream_options={"include_usage": True} if stream else None,
            )

            if stream:
                async for chunk in self._process_stream(
                    completion, on_text=on_text, on_audio=on_audio
                ):
                    yield chunk
            else:
                # Non-streaming response
                result = await completion
                if result.choices and result.choices[0].message:
                    message = result.choices[0].message
                    if message.content:
                        yield ChatChunk(type="text", content=message.content)
                    if hasattr(message, 'audio') and message.audio:
                        yield ChatChunk(type="audio", audio_data=message.audio.data)

        except Exception as e:
            logger.error("Error in Qwen3-Omni chat", error=str(e))
            raise

    async def _process_stream(
        self,
        completion,
        on_text: Optional[Callable[[str], None]] = None,
        on_audio: Optional[Callable[[str], None]] = None,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Process streaming response"""

        async for chunk in completion:
            if not chunk.choices:
                # Handle usage info at the end
                if hasattr(chunk, 'usage') and chunk.usage:
                    yield ChatChunk(type="usage", usage={
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    })
                continue

            delta = chunk.choices[0].delta

            # Handle text content
            if delta.content:
                text = delta.content
                if on_text:
                    try:
                        on_text(text)
                    except Exception as e:
                        logger.error("Error in text callback", error=str(e))
                yield ChatChunk(type="text", content=text)

            # Handle audio content
            if hasattr(delta, 'audio') and delta.audio:
                audio_data = delta.audio.data if hasattr(delta.audio, 'data') else None
                if audio_data:
                    if on_audio:
                        try:
                            on_audio(audio_data)
                        except Exception as e:
                            logger.error("Error in audio callback", error=str(e))
                    yield ChatChunk(type="audio", audio_data=audio_data)

    async def chat_with_history(
        self,
        session_id: str,
        user_message: str,
        system_prompt: Optional[str] = None,
        voice: str = "Cherry",
        history: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Chat with conversation history

        Args:
            session_id: Interview session ID
            user_message: User's message
            system_prompt: System prompt for the interview
            voice: Voice for audio output
            history: Previous conversation history

        Yields:
            ChatChunk: Response chunks
        """
        messages = []

        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add history
        if history:
            messages.extend(history)

        # Add user message
        messages.append({"role": "user", "content": user_message})

        logger.info(
            "Chat with history",
            session_id=session_id,
            history_length=len(history) if history else 0,
        )

        async for chunk in self.chat(messages, voice=voice):
            yield chunk

    def build_interview_system_prompt(
        self,
        scenario_name: str,
        scenario_description: str,
        is_technical: bool = True,
    ) -> str:
        """Build system prompt for interview scenario

        Args:
            scenario_name: Name of the interview scenario
            scenario_description: Description of the scenario
            is_technical: Whether this is a technical interview

        Returns:
            System prompt string
        """
        prompt = f"""你是一位专业的{scenario_name}面试官。

面试场景描述：{scenario_description}

{'这是技术面试，请重点考察候选人的：1) 专业知识掌握程度 2) 问题解决能力 3) 代码质量意识' if is_technical else '这是综合面试，请重点考察候选人的：1) 沟通表达能力 2) 逻辑思维 3) 职业素养'}

面试规则：
1. 每次只问一个问题，等待候选人回答
2. 问题应该循序渐进，从基础到深入
3. 注意倾听候选人的回答，可以追问细节
4. 保持专业、友善的面试氛围
5. 控制面试节奏，确保覆盖关键考察点

请用中文进行面试，语气专业但不失亲和力。"""

        return prompt


# Singleton instance
_qwen3_omni_http_service: Optional[Qwen3OmniHTTPService] = None


def get_qwen3_omni_http_service() -> Qwen3OmniHTTPService:
    """Get singleton instance of Qwen3OmniHTTPService"""
    global _qwen3_omni_http_service
    if _qwen3_omni_http_service is None:
        _qwen3_omni_http_service = Qwen3OmniHTTPService()
    return _qwen3_omni_http_service
