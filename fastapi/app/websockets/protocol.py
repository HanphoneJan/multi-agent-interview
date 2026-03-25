"""WebSocket message protocol definitions"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """WebSocket message types"""

    # Client -> Server
    CONNECT = "connect"
    START_INTERVIEW = "start_interview"
    PAUSE_INTERVIEW = "pause_interview"
    RESUME_INTERVIEW = "resume_interview"
    END_INTERVIEW = "end_interview"
    AUDIO = "audio"
    VIDEO_FRAME = "video_frame"
    TEXT = "text"

    # Server -> Client
    QUESTION = "question"
    AUDIO_REPLY = "audio_reply"
    PROGRESS = "progress"
    ERROR = "error"
    EVALUATION = "evaluation"
    CONNECTED = "connected"

    # Streaming
    STREAM_START = "stream_start"
    STREAM_CHUNK = "stream_chunk"
    STREAM_END = "stream_end"
    USER_MESSAGE = "user_message"


class BaseMessage(BaseModel):
    """Base WebSocket message"""
    type: MessageType


class ConnectMessage(BaseMessage):
    """Connection message"""
    session_id: str
    user_id: int


class StartInterviewMessage(BaseMessage):
    """Start interview message"""
    session_id: str
    scenario_id: int


class AudioMessage(BaseMessage):
    """Audio data message"""
    audio_data: str  # Base64 encoded
    duration: float


class VideoFrameMessage(BaseMessage):
    """Video frame message"""
    frame_data: str  # Base64 encoded
    timestamp: float


class TextMessage(BaseMessage):
    """Text message"""
    text: str


class QuestionMessage(BaseMessage):
    """Question message (Server -> Client)"""
    question: str
    question_id: int
    order: int


class ProgressMessage(BaseMessage):
    """Progress message (Server -> Client)"""
    stage: str
    progress: float = Field(..., ge=0.0, le=1.0)
    message: str

    @field_validator('progress')
    def progress_percentage(cls, v):
        return round(v, 2)


class ErrorMessage(BaseMessage):
    """Error message (Server -> Client)"""
    error: str
    error_code: Optional[str] = None
    suggestion: Optional[str] = None


def parse_message(data: str | dict) -> BaseMessage:
    """Parse incoming message"""
    if isinstance(data, str):
        data_dict = json.loads(data)
    else:
        data_dict = data

    msg_type = data_dict.get("type")

    if msg_type == MessageType.CONNECT:
        return ConnectMessage(**data_dict)
    elif msg_type == MessageType.START_INTERVIEW:
        return StartInterviewMessage(**data_dict)
    elif msg_type == MessageType.AUDIO:
        return AudioMessage(**data_dict)
    elif msg_type == MessageType.VIDEO_FRAME:
        return VideoFrameMessage(**data_dict)
    elif msg_type == MessageType.TEXT:
        return TextMessage(**data_dict)
    else:
        return BaseMessage(**data_dict)
