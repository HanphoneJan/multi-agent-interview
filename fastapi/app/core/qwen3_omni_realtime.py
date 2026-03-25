"""Qwen3-Omni Realtime API 客户端

提供端到端的实时音视频对话能力。
文档: https://help.aliyun.com/zh/model-studio/user-guide/qwen-omni
"""

import asyncio
import base64
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Callable, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from app.config import get_settings
from app.utils.log_helper import get_logger

logger = get_logger("core.qwen3_omni")


class ConversationState(Enum):
    """对话状态"""
    IDLE = "idle"
    CONNECTING = "connecting"
    LISTENING = "listening"      # 听取用户输入
    THINKING = "thinking"        # 模型思考中
    SPEAKING = "speaking"        # AI 播报中
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class RealtimeConfig:
    """Realtime 配置"""
    model: str = "qwen3-omni-30b-a3b-instruct"
    voice: str = "Chelsie"  # Ethan(男), Chelsie(女), Aiden(男)
    enable_audio: bool = True
    enable_thinking: bool = False  # 是否启用思考模式
    input_sample_rate: int = 16000  # 输入音频采样率
    output_sample_rate: int = 24000  # 输出音频采样率


@dataclass
class AudioSegment:
    """音频片段"""
    pcm_data: bytes
    timestamp: float
    is_speech: bool = True


class Qwen3OmniRealtimeClient:
    """Qwen3-Omni Realtime 客户端

    使用说明:
    1. 创建实例: client = Qwen3OmniRealtimeClient()
    2. 连接: await client.connect(system_prompt="...")
    3. 发送音频: await client.send_audio(pcm_data)
    4. 接收回复: async for event in client.receive_events():
    5. 断开: await client.disconnect()
    """

    # 使用新版 DashScope Realtime WebSocket API
    DASHSCOPE_REALTIME_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"

    def __init__(self, config: Optional[RealtimeConfig] = None):
        self.config = config or RealtimeConfig()
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.state = ConversationState.IDLE
        self.session_id: Optional[str] = None
        self._callbacks: dict[str, Callable] = {}
        self._audio_buffer: bytes = b""
        self._connected = False

    async def connect(self, system_prompt: str = "") -> bool:
        """建立与 Qwen3-Omni Realtime API 的连接

        Args:
            system_prompt: 系统提示词，定义AI面试官的行为

        Returns:
            是否连接成功
        """
        settings = get_settings()
        # 优先使用 DASHSCOPE_API_KEY，其次使用 QWEN_API_KEY
        api_key = getattr(settings, 'DASHSCOPE_API_KEY', None) or settings.QWEN_API_KEY

        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 或 QWEN_API_KEY 未配置")

        self.state = ConversationState.CONNECTING

        # 构建连接 URL - 使用新版 API 格式
        url = f"{self.DASHSCOPE_REALTIME_URL}?model=qwen3-omni-flash-realtime"

        # 构建请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "X-DashScope-DataInspection": "enable",
        }

        try:
            logger.info(f"正在连接 Qwen3-Omni Realtime API: {self.config.model}")
            self.ws = await websockets.connect(url, additional_headers=headers)

            # 发送初始化消息 (session.update) - 符合百炼文档格式
            # 注意：禁用 server_vad，改为手动控制 response.create
            # 这样可以更好支持文本+音频混合输入模式
            init_message = {
                "event_id": f"event_init_{int(time.time() * 1000)}",
                "type": "session.update",
                "session": {
                    "instructions": system_prompt or self._default_system_prompt(),
                    "voice": self.config.voice,
                    "output_audio_format": "pcm24",  # Flash 模型使用 pcm24
                    "input_audio_format": "pcm16",   # 输入仅支持 pcm16
                    "modalities": ["text", "audio"],  # 输出文本和音频
                    "turn_detection": None,  # 明确设置为 null，由客户端手动控制回复时机
                }
            }
            await self.ws.send(json.dumps(init_message))

            # 等待确认
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            data = json.loads(response)

            if data.get("type") == "session.created":
                self.session_id = data.get("session", {}).get("id")
                self.state = ConversationState.LISTENING
                self._connected = True
                logger.info(f"Qwen3-Omni 连接成功, session_id={self.session_id}")
                return True
            else:
                logger.error(f"连接初始化失败: {data}")
                self.state = ConversationState.ERROR
                return False

        except Exception as e:
            logger.error(f"连接 Qwen3-Omni 失败: {e}")
            self.state = ConversationState.ERROR
            return False

    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        return """你是一位专业的技术面试官，正在进行语音面试。

职责:
1. 评估候选人的技术能力和沟通表达能力
2. 通过候选人的语音语调判断其自信程度和情绪状态
3. 提出专业、有深度的技术问题
4. 根据回答追问，挖掘候选人真实水平

面试流程:
1. 开场自我介绍
2. 技术基础问答 (3-5题)
3. 项目经验深挖 (2-3题)
4. 场景设计与问题解决 (1-2题)
5. 候选人提问环节

注意:
- 一次只问一个问题，等待候选人完整回答
- 注意候选人语气中的犹豫和自信变化
- 对于紧张候选人给予适当鼓励
- 保持专业但友好的态度"""

    async def send_audio(self, pcm_data: bytes, sample_rate: int = None):
        """发送音频数据到模型

        Args:
            pcm_data: 16-bit PCM 音频数据 (小端序)
            sample_rate: 采样率，默认使用配置值
        """
        if not self.ws or self.state == ConversationState.ERROR:
            raise RuntimeError("WebSocket 未连接")

        # 将 PCM 转换为 base64
        audio_b64 = base64.b64encode(pcm_data).decode()

        message = {
            "event_id": f"event_audio_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }

        await self.ws.send(json.dumps(message))
        self.state = ConversationState.LISTENING

    async def send_video_frame(self, image_base64: str, timestamp: Optional[int] = None):
        """发送视频帧到模型

        Args:
            image_base64: base64 编码的图片 (JPEG/PNG)
            timestamp: 时间戳 (毫秒)
        """
        if not self.ws or self.state == ConversationState.ERROR:
            raise RuntimeError("WebSocket 未连接")

        message = {
            "event_id": f"event_video_{int(time.time() * 1000)}",
            "type": "input_image_buffer.append",
            "image": image_base64,
        }
        if timestamp is not None:
            message["timestamp"] = timestamp

        await self.ws.send(json.dumps(message))

    async def commit_audio(self):
        """提交音频缓冲区，通知模型可以开始处理

        通常在检测到语音结束时调用 (VAD)
        """
        if not self.ws:
            return

        message = {
            "event_id": f"event_commit_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.commit"
        }
        await self.ws.send(json.dumps(message))
        self.state = ConversationState.THINKING
        logger.debug("音频缓冲区已提交")

    async def create_response(self, modalities: Optional[list] = None):
        """显式请求模型生成回复

        Args:
            modalities: 输出模态 ["text", "audio"]，默认两者都输出
        """
        if not self.ws:
            return

        if modalities is None:
            modalities = ["text", "audio"] if self.config.enable_audio else ["text"]

        message = {
            "event_id": f"event_response_{int(time.time() * 1000)}",
            "type": "response.create",
            "response": {
                "modalities": modalities
            }
        }
        await self.ws.send(json.dumps(message))
        logger.debug(f"请求生成回复: modalities={modalities}")

    async def cancel_response(self):
        """取消当前正在生成的回复 (用于打断)"""
        if not self.ws:
            return

        message = {
            "event_id": f"event_cancel_{int(time.time() * 1000)}",
            "type": "response.cancel"
        }
        await self.ws.send(json.dumps(message))
        logger.debug("已取消当前回复")

    async def receive_events(self) -> AsyncGenerator[dict, None]:
        """接收模型事件流

        Yields:
            事件字典，包含以下类型:
            - input_audio_buffer.speech_started: 检测到语音开始
            - input_audio_buffer.speech_stopped: 检测到语音结束
            - response.created: 回复创建
            - response.text.delta: 文本片段
            - response.text.done: 文本完成
            - response.audio.delta: 音频片段 (base64)
            - response.audio.done: 音频完成
            - response.done: 整个回复完成
        """
        if not self.ws:
            raise RuntimeError("WebSocket 未连接")

        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    event_type = data.get("type", "")

                    # 更新状态
                    if event_type == "response.audio.delta":
                        self.state = ConversationState.SPEAKING
                    elif event_type == "response.done":
                        self.state = ConversationState.LISTENING

                    yield data

                except json.JSONDecodeError:
                    logger.warning(f"收到无法解析的消息: {message[:100]}")
                    continue

        except ConnectionClosed:
            logger.info("Qwen3-Omni 连接已关闭")
            self.state = ConversationState.IDLE
            self._connected = False

    async def disconnect(self):
        """断开连接"""
        self._connected = False
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.warning(f"关闭连接时出错: {e}")
            self.ws = None
        self.state = ConversationState.IDLE
        self.session_id = None
        logger.info("Qwen3-Omni 连接已断开")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected and self.ws is not None


# 全局客户端实例管理
_clients: dict[str, Qwen3OmniRealtimeClient] = {}


async def get_or_create_client(
    session_id: str,
    system_prompt: str = "",
    config: Optional[RealtimeConfig] = None
) -> Qwen3OmniRealtimeClient:
    """获取或创建客户端实例

    每个面试会话对应一个独立的客户端实例
    """
    if session_id not in _clients or not _clients[session_id].is_connected():
        client = Qwen3OmniRealtimeClient(config)
        success = await client.connect(system_prompt)
        if success:
            _clients[session_id] = client
        else:
            raise RuntimeError(f"无法为会话 {session_id} 创建 Qwen3-Omni 连接")

    return _clients[session_id]


async def close_client(session_id: str):
    """关闭指定会话的客户端"""
    if session_id in _clients:
        await _clients[session_id].disconnect()
        del _clients[session_id]
        logger.info(f"会话 {session_id} 的客户端已关闭")


async def close_all_clients():
    """关闭所有客户端连接"""
    session_ids = list(_clients.keys())
    for session_id in session_ids:
        await close_client(session_id)
    logger.info("所有 Qwen3-Omni 客户端已关闭")
