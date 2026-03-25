/**
 * H5 浏览器媒体 API 封装
 * 用于实时面试的音频/视频录制和播放
 */

import { ref, onUnmounted } from 'vue'

export interface AudioChunk {
  data: string      // Base64 PCM 数据
  timestamp: number
  duration: number
}

export interface MediaState {
  hasMicrophone: boolean
  hasCamera: boolean
  isRecording: boolean
  isMuted: boolean
  videoEnabled: boolean
  audioLevel: number
  error: string | null
}

export interface PermissionResult {
  success: boolean
  microphone: boolean
  camera: boolean
  error?: string
}

export function useBrowserMedia() {
  const mediaStream = ref<MediaStream | null>(null)
  const mediaRecorder = ref<MediaRecorder | null>(null)
  const audioContext = ref<AudioContext | null>(null)
  const analyser = ref<AnalyserNode | null>(null)
  const recordedChunks = ref<Blob[]>([])

  const state = ref<MediaState>({
    hasMicrophone: false,
    hasCamera: false,
    isRecording: false,
    isMuted: false,
    videoEnabled: true,
    audioLevel: 0,
    error: null
  })

  let audioLevelInterval: number | null = null

  /**
   * 请求媒体权限
   */
  const requestPermissions = async (options: {
    audio?: boolean
    video?: boolean
  } = {}): Promise<PermissionResult> => {
    const result: PermissionResult = {
      success: false,
      microphone: false,
      camera: false
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: options.audio ?? true,
        video: options.video ?? false
      })

      mediaStream.value = stream
      state.value.hasMicrophone = options.audio ?? false
      state.value.hasCamera = options.video ?? false
      state.value.error = null

      // 初始化音频分析器（用于音量检测）
      if (options.audio) {
        initAudioAnalyser(stream)
      }

      result.success = true
      result.microphone = options.audio ?? false
      result.camera = options.video ?? false
      return result
    } catch (err: any) {
      console.error('[Media] 获取媒体权限失败:', err)

      // 根据错误类型提供友好的错误信息
      let errorMsg = '无法访问媒体设备'
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMsg = '用户拒绝了媒体权限，您可以使用文本模式继续面试'
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMsg = '未找到摄像头或麦克风设备，您可以使用文本模式继续面试'
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMsg = '设备被其他应用占用，请关闭其他使用摄像头的应用后重试'
      } else if (err.name === 'OverconstrainedError') {
        errorMsg = '设备不支持 requested 的配置，将使用默认配置'
      } else if (err.name === 'SecurityError') {
        errorMsg = '安全限制：请在 HTTPS 或 localhost 环境下使用'
      }

      state.value.error = errorMsg
      result.error = errorMsg
      return result
    }
  }

  /**
   * 初始化音频分析器
   */
  const initAudioAnalyser = (stream: MediaStream) => {
    audioContext.value = new (window.AudioContext || (window as any).webkitAudioContext)()
    analyser.value = audioContext.value.createAnalyser()
    analyser.value.fftSize = 256

    const source = audioContext.value.createMediaStreamSource(stream)
    source.connect(analyser.value)

    // 开始监测音量
    startAudioLevelMonitoring()
  }

  /**
   * 监测音频音量
   */
  const startAudioLevelMonitoring = () => {
    if (!analyser.value) return

    const dataArray = new Uint8Array(analyser.value.frequencyBinCount)

    audioLevelInterval = window.setInterval(() => {
      analyser.value!.getByteFrequencyData(dataArray)
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length
      state.value.audioLevel = average / 255
    }, 100)
  }

  /**
   * 开始录音（完整录音模式 - 用于传统面试）
   */
  const startRecording = async (): Promise<boolean> => {
    if (!mediaStream.value) {
      const result = await requestPermissions({ audio: true })
      if (!result.success) return false
    }

    try {
      recordedChunks.value = []
      const recorder = new MediaRecorder(mediaStream.value!, {
        mimeType: 'audio/webm;codecs=opus'
      })

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.value.push(event.data)
        }
      }

      recorder.start()
      mediaRecorder.value = recorder
      state.value.isRecording = true

      return true
    } catch (err) {
      console.error('[Media] 开始录音失败:', err)
      return false
    }
  }

  /**
   * 停止录音并返回音频 Blob
   */
  const stopRecording = async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorder.value || !state.value.isRecording) {
        resolve(null)
        return
      }

      mediaRecorder.value.onstop = () => {
        const blob = new Blob(recordedChunks.value, { type: 'audio/webm' })
        recordedChunks.value = []
        resolve(blob)
      }

      mediaRecorder.value.stop()
      state.value.isRecording = false
    })
  }

  /**
   * 开始实时音频流录制
   */
  const startRealtimeRecording = async (
    onChunk: (chunk: AudioChunk) => void,
    options: { sampleRate?: number; frameSize?: number } = {}
  ): Promise<boolean> => {
    if (!mediaStream.value) {
      const result = await requestPermissions({ audio: true })
      if (!result.success) return false
    }

    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: options.sampleRate || 16000
      })

      const source = audioCtx.createMediaStreamSource(mediaStream.value!)
      const processor = audioCtx.createScriptProcessor(options.frameSize || 320, 1, 1)

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0)
        // 转换为 16-bit PCM
        const pcmData = floatTo16BitPCM(inputData)
        const base64 = arrayBufferToBase64(pcmData.buffer)

        onChunk({
          data: base64,
          timestamp: Date.now(),
          duration: 20 // 20ms 每帧
        })
      }

      source.connect(processor)
      processor.connect(audioCtx.destination)

      state.value.isRecording = true

      return true
    } catch (err) {
      console.error('[Media] 开始实时录音失败:', err)
      return false
    }
  }

  /**
   * Float32 转 16-bit PCM
   */
  const floatTo16BitPCM = (input: Float32Array): Int16Array => {
    const output = new Int16Array(input.length)
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]))
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }
    return output
  }

  /**
   * ArrayBuffer 转 Base64
   */
  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  /**
   * 停止实时录音
   */
  const stopRealtimeRecording = () => {
    state.value.isRecording = false
    if (audioContext.value) {
      audioContext.value.close()
      audioContext.value = null
    }
  }

  /**
   * 播放 Base64 音频
   */
  const playAudio = async (base64Data: string, mimeType: string = 'audio/wav'): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        const byteCharacters = atob(base64Data)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], { type: mimeType })
        const url = URL.createObjectURL(blob)

        const audio = new Audio(url)
        audio.onended = () => {
          URL.revokeObjectURL(url)
          resolve()
        }
        audio.onerror = (err) => {
          URL.revokeObjectURL(url)
          reject(err)
        }
        audio.play()
      } catch (err) {
        reject(err)
      }
    })
  }

  /**
   * 静音/取消静音
   */
  const toggleMute = (): boolean => {
    if (!mediaStream.value) return false

    const audioTracks = mediaStream.value.getAudioTracks()
    state.value.isMuted = !state.value.isMuted
    audioTracks.forEach(track => {
      track.enabled = !state.value.isMuted
    })

    return state.value.isMuted
  }

  /**
   * 切换摄像头开关
   */
  const toggleVideo = (): boolean => {
    if (!mediaStream.value) return false

    const videoTracks = mediaStream.value.getVideoTracks()
    state.value.videoEnabled = !state.value.videoEnabled
    videoTracks.forEach(track => {
      track.enabled = state.value.videoEnabled
    })

    return state.value.videoEnabled
  }

  /**
   * 停止所有媒体流
   */
  const stopAll = () => {
    if (audioLevelInterval) {
      clearInterval(audioLevelInterval)
      audioLevelInterval = null
    }

    if (mediaRecorder.value && state.value.isRecording) {
      mediaRecorder.value.stop()
    }

    if (mediaStream.value) {
      mediaStream.value.getTracks().forEach(track => track.stop())
      mediaStream.value = null
    }

    if (audioContext.value) {
      audioContext.value.close()
      audioContext.value = null
    }

    state.value = {
      hasMicrophone: false,
      hasCamera: false,
      isRecording: false,
      isMuted: false,
      videoEnabled: true,
      audioLevel: 0,
      error: null
    }
  }

  onUnmounted(() => {
    stopAll()
  })

  return {
    state,
    mediaStream,
    requestPermissions,
    startRecording,
    stopRecording,
    startRealtimeRecording,
    stopRealtimeRecording,
    playAudio,
    toggleMute,
    toggleVideo,
    stopAll
  }
}
