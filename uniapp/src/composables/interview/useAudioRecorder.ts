/**
 * 音频录制 Composable
 * 支持实时音频流录制（用于实时面试）和完整录音（用于传统面试）
 */

import { ref } from 'vue';

export type RecorderStatus = 'idle' | 'recording' | 'paused';

export interface AudioChunk {
  data: string;      // Base64 PCM 数据
  timestamp: number; // 时间戳
  duration: number;  // 时长(ms)
}

export function useAudioRecorder() {
  const status = ref<RecorderStatus>('idle');
  const recorderManager = uni.getRecorderManager?.();
  const isRecording = ref(false);

  /**
   * 检查录音功能是否可用
   */
  const isAvailable = (): boolean => {
    if (!recorderManager) {
      console.error('[AudioRecorder] 录音管理器不可用，请检查环境');
      return false;
    }
    return true;
  };

  // 录制配置
  const recordOptions: UniApp.RecorderManagerStartOption = {
    duration: 60000,           // 最大录制时长 60s
    sampleRate: 16000,         // 采样率 16kHz
    numberOfChannels: 1,       // 单声道
    encodeBitRate: 96000,      // 编码码率
    format: 'pcm',             // PCM 格式
    frameSize: 320             // 每帧大小（20ms @ 16kHz）
  };

  /**
   * 开始录音（传统模式：按住说话）
   */
  const startRecording = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (!isAvailable()) {
        reject(new Error('录音功能不可用'));
        return;
      }

      if (status.value === 'recording') {
        resolve();
        return;
      }

      recorderManager!.onStart(() => {
        status.value = 'recording';
        isRecording.value = true;
        resolve();
      });

      recorderManager!.onError((err) => {
        console.error('录音错误:', err);
        reject(err);
      });

      recorderManager!.start(recordOptions);
    });
  };

  /**
   * 停止录音
   */
  const stopRecording = (): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!isAvailable()) {
        reject(new Error('录音功能不可用'));
        return;
      }

      recorderManager!.onStop((res) => {
        status.value = 'idle';
        isRecording.value = false;
        // 读取文件并转为 base64
        uni.getFileSystemManager().readFile({
          filePath: res.tempFilePath,
          encoding: 'base64',
          success: (readRes) => {
            resolve(readRes.data as string);
          },
          fail: reject
        });
      });

      recorderManager!.stop();
    });
  };

  /**
   * 实时音频流录制（实时面试模式）
   * @param onChunk 每帧音频数据的回调
   */
  const startRealtimeRecording = (
    onChunk: (chunk: AudioChunk) => void
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (!isAvailable()) {
        reject(new Error('录音功能不可用，H5 环境可能需要使用微信小程序或 App'));
        return;
      }

      // 检查 onFrameRecorded 方法是否存在（H5 可能不支持）
      if (!recorderManager!.onFrameRecorded) {
        reject(new Error('实时音频流录制不支持当前环境'));
        return;
      }

      // 监听实时帧
      recorderManager!.onFrameRecorded((res) => {
        if (res.isLastFrame) return;

        // 将 ArrayBuffer 转为 base64
        const base64 = uni.arrayBufferToBase64(res.frameBuffer);

        onChunk({
          data: base64,
          timestamp: Date.now(),
          duration: 20 // 每帧 20ms
        });
      });

      recorderManager!.onStart(() => {
        status.value = 'recording';
        isRecording.value = true;
        resolve();
      });

      recorderManager!.onError((err) => {
        console.error('实时录音错误:', err);
        reject(err);
      });

      // 开始录制，设置较短的帧大小以获取实时数据
      recorderManager!.start({
        ...recordOptions,
        duration: 600000, // 10分钟，实时模式下需要持续录制
        frameSize: 320    // 20ms 帧
      });
    });
  };

  /**
   * 停止实时录制
   */
  const stopRealtimeRecording = (): void => {
    if (!recorderManager) return;
    try {
      recorderManager.stop();
    } catch (err) {
      console.warn('[AudioRecorder] 停止录音失败:', err);
    }
    status.value = 'idle';
    isRecording.value = false;
  };

  /**
   * 暂停录制
   */
  const pauseRecording = (): void => {
    if (!recorderManager) return;
    try {
      recorderManager.pause?.();
    } catch (err) {
      console.warn('[AudioRecorder] 暂停录音失败:', err);
    }
    status.value = 'paused';
  };

  /**
   * 恢复录制
   */
  const resumeRecording = (): void => {
    if (!recorderManager) return;
    try {
      recorderManager.resume?.();
      status.value = 'recording';
    } catch (err) {
      console.warn('[AudioRecorder] 恢复录音失败:', err);
    }
  };

  return {
    status,
    isRecording,
    isAvailable,
    startRecording,
    stopRecording,
    startRealtimeRecording,
    stopRealtimeRecording,
    pauseRecording,
    resumeRecording
  };
}
