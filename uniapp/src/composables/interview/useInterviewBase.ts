/**
 * 面试基础功能 Composable
 * 提供共享的音频初始化、权限申请、错误处理等功能
 */

import { ref } from 'vue';

export type InterviewMode = 'realtime' | 'classic';

export interface InterviewConfig {
  sessionId: string;
  token: string;
  mode: InterviewMode;
}

export function useInterviewBase() {
  const isInitializing = ref(false);
  const error = ref<string>('');
  const permissions = ref({
    microphone: false,
    camera: false
  });

  /**
   * 申请麦克风权限
   */
  const requestMicrophonePermission = async (): Promise<boolean> => {
    return new Promise((resolve) => {
      uni.authorize({
        scope: 'scope.record',
        success: () => {
          permissions.value.microphone = true;
          resolve(true);
        },
        fail: () => {
          uni.showModal({
            title: '需要麦克风权限',
            content: '面试需要使用麦克风进行语音交流',
            success: (res) => {
              if (res.confirm) {
                uni.openSetting();
              }
            }
          });
          resolve(false);
        }
      });
    });
  };

  /**
   * 申请摄像头权限
   */
  const requestCameraPermission = async (): Promise<boolean> => {
    return new Promise((resolve) => {
      uni.authorize({
        scope: 'scope.camera',
        success: () => {
          permissions.value.camera = true;
          resolve(true);
        },
        fail: () => {
          uni.showModal({
            title: '需要摄像头权限',
            content: '面试需要使用摄像头进行视频交流',
            success: (res) => {
              if (res.confirm) {
                uni.openSetting();
              }
            }
          });
          resolve(false);
        }
      });
    });
  };

  /**
   * 初始化所有权限
   */
  const initPermissions = async (needCamera = true): Promise<boolean> => {
    isInitializing.value = true;
    error.value = '';

    try {
      const micOk = await requestMicrophonePermission();
      if (!micOk) {
        error.value = '麦克风权限被拒绝';
        return false;
      }

      if (needCamera) {
        const camOk = await requestCameraPermission();
        if (!camOk) {
          error.value = '摄像头权限被拒绝';
          return false;
        }
      }

      return true;
    } catch (err) {
      error.value = '权限申请失败';
      return false;
    } finally {
      isInitializing.value = false;
    }
  };

  /**
   * 获取 WebSocket 基础 URL
   */
  const getWebSocketUrl = (config: InterviewConfig): string => {
    const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1';
    const endpoint = config.mode === 'realtime'
      ? `/ws/interview/realtime/${config.sessionId}`
      : `/ws/interview/${config.sessionId}`;
    return `${baseUrl}${endpoint}?token=${config.token}`;
  };

  /**
   * 显示错误信息
   */
  const showError = (msg: string) => {
    error.value = msg;
    uni.showToast({
      title: msg,
      icon: 'none',
      duration: 3000
    });
  };

  return {
    isInitializing,
    error,
    permissions,
    requestMicrophonePermission,
    requestCameraPermission,
    initPermissions,
    getWebSocketUrl,
    showError
  };
}
