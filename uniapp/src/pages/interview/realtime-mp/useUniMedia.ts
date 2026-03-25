/**
 * 小程序媒体 API 封装
 * 用于实时面试的音频录制和播放
 */

import { ref, onUnmounted } from 'vue'

export interface MediaState {
  hasMicrophone: boolean
  hasCamera: boolean
  isRecording: boolean
  isMuted: boolean
  videoEnabled: boolean
  audioLevel: number
}

export function useUniMedia() {
  const recorderManager = ref<UniApp.RecorderManager | null>(null)
  const innerAudioContext = ref<UniApp.InnerAudioContext | null>(null)

  const state = ref<MediaState>({
    hasMicrophone: false,
    hasCamera: false,
    isRecording: false,
    isMuted: false,
    videoEnabled: true,
    audioLevel: 0
  })

  // 初始化录音管理器
  const initRecorder = () => {
    if (!recorderManager.value) {
      recorderManager.value = uni.getRecorderManager()
    }
    return recorderManager.value
  }

  /**
   * 请求麦克风权限
   */
  const requestMicrophonePermission = async (): Promise<boolean> => {
    return new Promise((resolve) => {
      uni.authorize({
        scope: 'scope.record',
        success: () => {
          state.value.hasMicrophone = true
          resolve(true)
        },
        fail: () => {
          uni.showModal({
            title: '需要麦克风权限',
            content: '面试需要使用麦克风进行语音交流',
            success: (res) => {
              if (res.confirm) {
                uni.openSetting()
              }
            }
          })
          resolve(false)
        }
      })
    })
  }

  /**
   * 请求摄像头权限
   */
  const requestCameraPermission = async (): Promise<boolean> => {
    return new Promise((resolve) => {
      uni.authorize({
        scope: 'scope.camera',
        success: () => {
          state.value.hasCamera = true
          resolve(true)
        },
        fail: () => {
          uni.showModal({
            title: '需要摄像头权限',
            content: '面试需要使用摄像头进行视频交流',
            success: (res) => {
              if (res.confirm) {
                uni.openSetting()
              }
            }
          })
          resolve(false)
        }
      })
    })
  }

  /**
   * 请求所有权限
   */
  const requestPermissions = async (options: {
    audio?: boolean
    video?: boolean
  } = {}): Promise<boolean> => {
    if (options.audio) {
      const micOk = await requestMicrophonePermission()
      if (!micOk) return false
    }

    if (options.video) {
      const camOk = await requestCameraPermission()
      if (!camOk) return false
    }

    return true
  }

  /**
   * 开始录音（完整录音模式）
   * 小程序不支持实时流，只能录完后再发送
   */
  const startRecording = async (
    onComplete?: (filePath: string) => void
  ): Promise<boolean> => {
    const recorder = initRecorder()
    if (!recorder) {
      console.error('[Media] 录音管理器不可用')
      return false
    }

    // 检查权限
    if (!state.value.hasMicrophone) {
      const ok = await requestMicrophonePermission()
      if (!ok) return false
    }

    return new Promise((resolve) => {
      // 监听录音停止
      recorder.onStop((res) => {
        state.value.isRecording = false
        onComplete?.(res.tempFilePath)
      })

      recorder.onError((err) => {
        console.error('[Media] 录音错误:', err)
        state.value.isRecording = false
        resolve(false)
      })

      // 开始录音
      recorder.start({
        duration: 60000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 96000,
        format: 'wav'
      })

      state.value.isRecording = true
      resolve(true)
    })
  }

  /**
   * 停止录音
   */
  const stopRecording = () => {
    const recorder = initRecorder()
    if (recorder && state.value.isRecording) {
      recorder.stop()
    }
  }

  /**
   * 读取录音文件为 base64
   */
  const readAudioFile = async (filePath: string): Promise<string | null> => {
    return new Promise((resolve) => {
      uni.getFileSystemManager().readFile({
        filePath,
        encoding: 'base64',
        success: (res) => {
          resolve(res.data as string)
        },
        fail: (err) => {
          console.error('[Media] 读取音频文件失败:', err)
          resolve(null)
        }
      })
    })
  }

  /**
   * 播放音频（支持 base64 或 URL）
   */
  const playAudio = async (audioData: string, isBase64: boolean = true): Promise<void> => {
    return new Promise((resolve, reject) => {
      // 停止之前的播放
      stopAudio()

      let src: string
      if (isBase64) {
        // base64 数据需要写入临时文件
        const fs = uni.getFileSystemManager()
        const filePath = `${uni.env.USER_DATA_PATH}/temp_audio_${Date.now()}.wav`

        try {
          fs.writeFileSync(filePath, audioData, 'base64')
          src = filePath
        } catch (err) {
          console.error('[Media] 写入音频文件失败:', err)
          reject(err)
          return
        }
      } else {
        src = audioData
      }

      innerAudioContext.value = uni.createInnerAudioContext()
      innerAudioContext.value.src = src

      innerAudioContext.value.onPlay(() => {
        state.value.isMuted = false
      })

      innerAudioContext.value.onEnded(() => {
        resolve()
      })

      innerAudioContext.value.onError((err) => {
        console.error('[Media] 播放错误:', err)
        reject(err)
      })

      innerAudioContext.value.play()
    })
  }

  /**
   * 停止播放
   */
  const stopAudio = () => {
    if (innerAudioContext.value) {
      innerAudioContext.value.stop()
      innerAudioContext.value.destroy()
      innerAudioContext.value = null
    }
  }

  /**
   * 静音/取消静音（仅标记状态，小程序没有直接的静音 API）
   */
  const toggleMute = (): boolean => {
    state.value.isMuted = !state.value.isMuted
    if (state.value.isMuted) {
      stopAudio()
    }
    return state.value.isMuted
  }

  /**
   * 切换视频（标记状态，实际由 live-pusher 组件控制）
   */
  const toggleVideo = (): boolean => {
    state.value.videoEnabled = !state.value.videoEnabled
    return state.value.videoEnabled
  }

  /**
   * 停止所有媒体
   */
  const stopAll = () => {
    stopRecording()
    stopAudio()
    state.value.isRecording = false
    state.value.isMuted = false
  }

  onUnmounted(() => {
    stopAll()
  })

  return {
    state,
    recorderManager,
    requestPermissions,
    startRecording,
    stopRecording,
    readAudioFile,
    playAudio,
    stopAudio,
    toggleMute,
    toggleVideo,
    stopAll
  }
}
