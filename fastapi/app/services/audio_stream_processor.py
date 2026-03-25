"""音频流处理器

处理候选人的实时音频输入:
1. 音频缓冲和切片
2. VAD (语音活动检测)
3. 智能分段 (按句子/停顿分割)
"""

import asyncio
import collections
import math
from dataclasses import dataclass
from typing import Optional, Callable, List
import struct

import numpy as np

from app.utils.log_helper import get_logger

logger = get_logger("services.audio_stream")


@dataclass
class VADConfig:
    """VAD 配置"""
    sample_rate: int = 16000
    frame_duration_ms: int = 30  # 每帧30ms
    threshold: int = 500  # 语音能量阈值
    silence_duration_ms: int = 800  # 静音超过800ms认为语音结束
    min_speech_duration_ms: int = 500  # 最小语音长度500ms
    max_speech_duration_ms: int = 30000  # 最大语音长度30秒
    pre_speech_buffer_ms: int = 200  # 前置缓冲200ms

    @property
    def frame_bytes(self) -> int:
        """每帧字节数 (16-bit PCM)"""
        return int(self.sample_rate * 2 * self.frame_duration_ms / 1000)

    @property
    def silence_frames(self) -> int:
        """静音帧数"""
        return self.silence_duration_ms // self.frame_duration_ms

    @property
    def min_bytes(self) -> int:
        """最小语音字节数"""
        return int(self.sample_rate * 2 * self.min_speech_duration_ms / 1000)

    @property
    def max_bytes(self) -> int:
        """最大语音字节数"""
        return int(self.sample_rate * 2 * self.max_speech_duration_ms / 1000)


class VADProcessor:
    """简单的能量基 VAD 处理器

    可以替换为更复杂的算法如 WebRTC VAD 或 Silero VAD
    """

    def __init__(self, config: VADConfig = None):
        self.config = config or VADConfig()
        self._energy_history = collections.deque(maxlen=30)  # 约900ms历史
        self._dynamic_threshold = self.config.threshold

    def detect(self, pcm_data: bytes) -> bool:
        """检测是否为语音

        Args:
            pcm_data: 16-bit PCM 数据

        Returns:
            True 如果是语音，False 如果是静音
        """
        try:
            # 将 bytes 转换为 numpy array
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)

            # 计算 RMS 能量
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

            # 更新动态阈值 (使用移动平均)
            self._energy_history.append(rms)
            if len(self._energy_history) >= 10:
                # 使用历史能量中的较低值作为噪声基线
                noise_floor = np.percentile(list(self._energy_history), 10)
                self._dynamic_threshold = max(self.config.threshold, noise_floor * 2)

            is_speech = rms > self._dynamic_threshold

            return is_speech

        except Exception as e:
            logger.warning(f"VAD检测出错: {e}")
            return False

    def reset(self):
        """重置状态"""
        self._energy_history.clear()
        self._dynamic_threshold = self.config.threshold


class AudioStreamProcessor:
    """音频流处理器

    使用示例:
    processor = AudioStreamProcessor(on_speech_segment=handle_segment)
    await processor.start()

    # 持续输入音频
    await processor.feed_audio(pcm_chunk)

    # 结束时
    await processor.stop()
    """

    def __init__(
        self,
        on_speech_segment: Callable[[bytes], None],
        config: Optional[VADConfig] = None
    ):
        self.config = config or VADConfig()
        self.on_speech_segment = on_speech_segment
        self.vad = VADProcessor(self.config)

        # 缓冲区
        self._input_buffer = collections.deque()
        self._speech_buffer = bytearray()
        self._pre_speech_buffer = collections.deque(maxlen=int(
            self.config.sample_rate * 2 * self.config.pre_speech_buffer_ms / 1000
        ))

        # 状态
        self._is_speaking = False
        self._silence_frames = 0
        self._total_speech_bytes = 0

        # 运行状态
        self._running = False
        self._process_task: Optional[asyncio.Task] = None

        # 统计
        self._segments_count = 0

    async def start(self):
        """启动处理器"""
        self._running = True
        self._process_task = asyncio.create_task(self._process_loop())
        logger.info(f"音频流处理器已启动 (sample_rate={self.config.sample_rate})")

    async def stop(self):
        """停止处理器"""
        self._running = False

        # 处理剩余缓冲区
        if len(self._speech_buffer) > 0 and len(self._speech_buffer) >= self.config.min_bytes:
            segment = bytes(self._speech_buffer)
            logger.debug(f"停止时刷新缓冲区, 长度: {len(segment)} bytes")
            await asyncio.get_event_loop().run_in_executor(
                None, self.on_speech_segment, segment
            )
            self._segments_count += 1

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass

        logger.info(f"音频流处理器已停止, 共处理 {self._segments_count} 个语音片段")

    async def feed_audio(self, pcm_data: bytes):
        """输入音频数据

        Args:
            pcm_data: 16-bit 小端 PCM 数据
        """
        if not self._running:
            return

        self._input_buffer.append(pcm_data)

    def force_segment(self) -> Optional[bytes]:
        """强制分割当前语音片段

        用于手动触发（如点击发送按钮时）

        Returns:
            如果有语音数据则返回，否则返回 None
        """
        if len(self._speech_buffer) >= self.config.min_bytes:
            segment = bytes(self._speech_buffer)
            self._speech_buffer = bytearray()
            self._is_speaking = False
            self._silence_frames = 0
            self._segments_count += 1
            return segment
        return None

    async def _process_loop(self):
        """处理循环"""
        frame_bytes = self.config.frame_bytes

        while self._running:
            # 收集足够的数据
            buffer_data = self._collect_buffer()
            while len(buffer_data) < frame_bytes and self._running:
                await asyncio.sleep(0.005)  # 5ms 轮询
                buffer_data = self._collect_buffer()

            if not self._running:
                break

            # 提取一帧
            data = buffer_data[:frame_bytes]
            self._consume_buffer(frame_bytes)

            # VAD 检测
            is_speech = self.vad.detect(data)

            if is_speech:
                if not self._is_speaking:
                    # 语音开始
                    self._is_speaking = True
                    self._silence_frames = 0

                    # 添加前置缓冲
                    self._speech_buffer.extend(b"".join(self._pre_speech_buffer))
                    self._pre_speech_buffer.clear()

                    logger.debug("检测到语音开始")

                self._speech_buffer.extend(data)
                self._total_speech_bytes += len(data)

                # 检查是否超过最大长度
                if len(self._speech_buffer) >= self.config.max_bytes:
                    logger.debug("语音超过最大长度，强制分割")
                    segment = bytes(self._speech_buffer)
                    self._speech_buffer = bytearray()
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.on_speech_segment, segment
                    )
                    self._segments_count += 1
                    self._is_speaking = False

            else:
                # 保存到前置缓冲
                if not self._is_speaking:
                    self._pre_speech_buffer.append(data)
                else:
                    self._silence_frames += 1
                    self._speech_buffer.extend(data)

                    # 检查静音时长
                    if self._silence_frames >= self.config.silence_frames:
                        # 语音结束
                        self._is_speaking = False

                        # 去掉尾部的静音
                        segment_bytes = bytes(self._speech_buffer)
                        speech_end = len(segment_bytes) - (self._silence_frames * frame_bytes)
                        if speech_end < self.config.min_bytes:
                            speech_end = len(segment_bytes)
                        segment = segment_bytes[:speech_end]

                        if len(segment) >= self.config.min_bytes:
                            logger.debug(f"检测到语音结束, 长度: {len(segment)} bytes, "
                                       f"静音帧: {self._silence_frames}")
                            await asyncio.get_event_loop().run_in_executor(
                                None, self.on_speech_segment, segment
                            )
                            self._segments_count += 1

                        self._speech_buffer = bytearray()
                        self._silence_frames = 0

    def _collect_buffer(self) -> bytes:
        """收集缓冲区数据"""
        return b"".join(self._input_buffer)

    def _consume_buffer(self, n: int):
        """消耗缓冲区数据"""
        remaining = n
        while remaining > 0 and self._input_buffer:
            chunk = self._input_buffer[0]
            if len(chunk) <= remaining:
                remaining -= len(chunk)
                self._input_buffer.popleft()
            else:
                self._input_buffer[0] = chunk[remaining:]
                remaining = 0

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "segments_count": self._segments_count,
            "total_speech_bytes": self._total_speech_bytes,
            "is_speaking": self._is_speaking,
            "buffer_size": len(self._speech_buffer),
        }


class SlidingWindowBuffer:
    """滑动窗口缓冲区

    用于累积音频数据，确保句子完整性
    """

    def __init__(self, window_ms: int = 3000, sample_rate: int = 16000):
        self.window_ms = window_ms
        self.sample_rate = sample_rate
        self.max_bytes = int(sample_rate * 2 * window_ms / 1000)
        self._buffer = bytearray()

    def append(self, pcm_data: bytes) -> Optional[bytes]:
        """添加数据，如果缓冲区满则返回数据并清空

        Args:
            pcm_data: PCM 音频数据

        Returns:
            如果缓冲区满则返回累积的数据，否则返回 None
        """
        self._buffer.extend(pcm_data)

        if len(self._buffer) >= self.max_bytes:
            return self.flush()
        return None

    def flush(self) -> bytes:
        """刷新缓冲区，返回数据并清空"""
        data = bytes(self._buffer)
        self._buffer = bytearray()
        return data

    def peek(self) -> bytes:
        """查看当前数据但不清空"""
        return bytes(self._buffer)

    def clear(self):
        """清空缓冲区"""
        self._buffer = bytearray()

    def __len__(self) -> int:
        """返回当前缓冲区大小"""
        return len(self._buffer)


class AudioResampler:
    """音频重采样器

    用于将不同采样率的音频转换为统一采样率
    """

    def __init__(self, input_rate: int, output_rate: int):
        self.input_rate = input_rate
        self.output_rate = output_rate
        self._ratio = output_rate / input_rate

    def resample(self, pcm_data: bytes) -> bytes:
        """重采样音频

        Args:
            pcm_data: 16-bit PCM 数据

        Returns:
            重采样后的 16-bit PCM 数据
        """
        if self.input_rate == self.output_rate:
            return pcm_data

        try:
            # 转换为 numpy array
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)

            # 使用线性插值重采样
            input_length = len(audio_array)
            output_length = int(input_length * self._ratio)

            indices = np.linspace(0, input_length - 1, output_length)
            indices_floor = np.floor(indices).astype(np.int32)
            indices_ceil = np.minimum(indices_floor + 1, input_length - 1)
            fractions = indices - indices_floor

            resampled = (audio_array[indices_floor] * (1 - fractions) +
                        audio_array[indices_ceil] * fractions)

            return resampled.astype(np.int16).tobytes()

        except Exception as e:
            logger.error(f"重采样失败: {e}")
            return pcm_data  # 失败时返回原始数据


def convert_pcm_to_float32(pcm_data: bytes) -> np.ndarray:
    """将 16-bit PCM 转换为 float32 (-1.0 ~ 1.0)

    Args:
        pcm_data: 16-bit PCM 数据

    Returns:
        float32 numpy array
    """
    audio_array = np.frombuffer(pcm_data, dtype=np.int16)
    return audio_array.astype(np.float32) / 32768.0


def convert_float32_to_pcm(float_data: np.ndarray) -> bytes:
    """将 float32 (-1.0 ~ 1.0) 转换为 16-bit PCM

    Args:
        float_data: float32 numpy array

    Returns:
        16-bit PCM bytes
    """
    clipped = np.clip(float_data, -1.0, 1.0)
    pcm_array = (clipped * 32767).astype(np.int16)
    return pcm_array.tobytes()
