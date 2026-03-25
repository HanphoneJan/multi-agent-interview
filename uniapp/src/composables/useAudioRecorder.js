/**
 * 音频录制组合式函数 (Qwen3-Omni 实时音视频面试)
 *
 * 支持实时音频流输出 (PCM 16kHz 16-bit)
 * 兼容 H5 和微信小程序
 */
import { ref, onUnmounted } from 'vue'

const DEFAULT_SAMPLE_RATE = 16000
const DEFAULT_FRAME_DURATION = 100 // 每100ms发送一帧

/**
 * 音频录制器
 * @param {Object} options - 配置选项
 * @param {number} options.sampleRate - 采样率 (默认 16000)
 * @param {number} options.frameDuration - 帧时长 ms (默认 100)
 * @param {Function} options.onFrame - 音频帧回调 (base64)
 * @param {Function} options.onError - 错误回调
 */
export function useAudioRecorder(options = {}) {
  const {
    sampleRate = DEFAULT_SAMPLE_RATE,
    frameDuration = DEFAULT_FRAME_DURATION,
    onFrame = null,
    onError = null
  } = options

  // 状态
  const isRecording = ref(false)
  const hasPermission = ref(false)
  const volume = ref(0) // 当前音量 (0-100)
  const isSpeaking = ref(false) // 是否检测到说话

  // 内部状态
  let recorderManager = null
  let audioContext = null
  let mediaStream = null
  let processor = null
  let source = null
  let recordingTimer = null
  let vadBuffer = [] // VAD 缓冲区
  let _onFrameCallback = onFrame

  // VAD 配置
  const VAD_THRESHOLD = 500
  const VAD_HISTORY_SIZE = 10
  let energyHistory = []

  /**
   * 计算 RMS 能量
   */
  const calculateRMS = (floatArray) => {
    let sum = 0
    for (let i = 0; i < floatArray.length; i++) {
      sum += floatArray[i] * floatArray[i]
    }
    return Math.sqrt(sum / floatArray.length)
  }

  /**
   * Float32 转 Int16
   */
  const floatTo16BitPCM = (input) => {
    const output = new Int16Array(input.length)
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]))
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }
    return output
  }

  /**
   * VAD 检测
   */
  const detectSpeech = (rms) => {
    energyHistory.push(rms)
    if (energyHistory.length > VAD_HISTORY_SIZE) {
      energyHistory.shift()
    }

    // 使用历史能量计算动态阈值
    const noiseFloor = Math.min(...energyHistory)
    const dynamicThreshold = Math.max(VAD_THRESHOLD / 32768, noiseFloor * 2)

    const isSpeech = rms > dynamicThreshold

    // 更新说话状态
    if (isSpeech !== isSpeaking.value) {
      isSpeaking.value = isSpeech
    }

    return isSpeech
  }

  /**
   * 初始化 H5 Web Audio
   */
  const initWebAudio = async () => {
    // #ifdef H5
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })

      audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: sampleRate
      })

      source = audioContext.createMediaStreamSource(mediaStream)
      processor = audioContext.createScriptProcessor(4096, 1, 1)

      processor.onaudioprocess = (e) => {
        if (!isRecording.value) return

        const inputData = e.inputBuffer.getChannelData(0)

        // 计算音量
        const rms = calculateRMS(inputData)
        volume.value = Math.min(100, rms * 100 * 2)

        // VAD 检测
        detectSpeech(rms)

        // 转换为 16-bit PCM
        const pcmData = floatTo16BitPCM(inputData)

        // 转为 base64 并回调
        if (_onFrameCallback) {
          const base64 = arrayBufferToBase64(pcmData.buffer)
          _onFrameCallback(base64, {
            timestamp: Date.now(),
            volume: volume.value,
            isSpeaking: isSpeaking.value,
            sampleRate: sampleRate
          })
        }
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      hasPermission.value = true
      return true
    } catch (err) {
      console.error('获取麦克风权限失败', err)
      hasPermission.value = false
      if (onError) onError(err)
      return false
    }
    // #endif
    return false
  }

  /**
   * 初始化小程序录音
   */
  const initMiniProgramRecorder = () => {
    // #ifdef MP-WEIXIN
    recorderManager = uni.getRecorderManager()

    recorderManager.onStart(() => {
      console.log('录音开始')
      isRecording.value = true
    })

    recorderManager.onStop((res) => {
      console.log('录音结束', res)
      isRecording.value = false
    })

    recorderManager.onError((err) => {
      console.error('录音错误', err)
      isRecording.value = false
      if (onError) onError(err)
    })

    // 小程序不支持实时音频流，需要分段录制
    // 这里使用定时录制小段音频的方式
    return true
    // #endif
    return false
  }

  /**
   * 检查并请求权限
   */
  const checkPermission = async () => {
    // #ifdef MP-WEIXIN
    try {
      const setting = await uni.getSetting()
      if (setting.authSetting['scope.record']) {
        hasPermission.value = true
        return true
      }

      await uni.authorize({ scope: 'scope.record' })
      hasPermission.value = true
      return true
    } catch (err) {
      console.error('麦克风权限被拒绝', err)
      hasPermission.value = false
      return false
    }
    // #endif

    // #ifdef H5
    const result = await initWebAudio()
    return result
    // #endif

    return false
  }

  /**
   * ArrayBuffer 转 Base64
   */
  const arrayBufferToBase64 = (buffer) => {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  /**
   * 开始录音
   * @param {Function} onFrameCallback - 音频帧回调 (替代构造函数中的 onFrame)
   */
  const startRecording = async (onFrameCallback = null) => {
    if (onFrameCallback) {
      _onFrameCallback = onFrameCallback
    }

    if (!_onFrameCallback) {
      console.warn('未设置音频帧回调函数')
    }

    const hasPerm = await checkPermission()
    if (!hasPerm) {
      return false
    }

    // #ifdef H5
    // H5 已经在 initWebAudio 中开始处理
    isRecording.value = true
    // #endif

    // #ifdef MP-WEIXIN
    // 小程序使用分段录制
    startMiniProgramRecording()
    // #endif

    return true
  }

  /**
   * 小程序分段录制
   */
  const startMiniProgramRecording = () => {
    // #ifdef MP-WEIXIN
    const recordSegment = () => {
      if (!isRecording.value) return

      recorderManager.start({
        duration: frameDuration,
        sampleRate: sampleRate,
        numberOfChannels: 1,
        encodeBitRate: 16000,
        format: 'pcm',
      })

      // 定时停止并发送
      setTimeout(() => {
        if (isRecording.value) {
          recorderManager.stop()
        }
      }, frameDuration)
    }

    recorderManager.onStop((res) => {
      if (!isRecording.value) return

      // 读取录音文件
      uni.getFileSystemManager().readFile({
        filePath: res.tempFilePath,
        encoding: 'base64',
        success: (fileRes) => {
          if (_onFrameCallback) {
            _onFrameCallback(fileRes.data, {
              timestamp: Date.now(),
              sampleRate: sampleRate
            })
          }
          // 继续下一段
          recordSegment()
        },
        fail: (err) => {
          console.error('读取录音文件失败', err)
          if (isRecording.value) {
            recordSegment() // 失败重试
          }
        }
      })
    })

    isRecording.value = true
    recordSegment()
    // #endif
  }

  /**
   * 停止录音
   */
  const stopRecording = () => {
    isRecording.value = false
    isSpeaking.value = false
    volume.value = 0
    energyHistory = []

    // #ifdef H5
    if (processor) {
      processor.disconnect()
      processor = null
    }
    if (source) {
      source.disconnect()
      source = null
    }
    if (audioContext) {
      audioContext.close()
      audioContext = null
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
      mediaStream = null
    }
    // #endif

    // #ifdef MP-WEIXIN
    if (recorderManager) {
      recorderManager.stop()
    }
    // #endif

    if (recordingTimer) {
      clearInterval(recordingTimer)
      recordingTimer = null
    }

    console.log('录音已停止')
  }

  /**
   * 获取当前音量级别 (0-100)
   */
  const getVolumeLevel = () => {
    return volume.value
  }

  /**
   * 是否检测到说话
   */
  const isUserSpeaking = () => {
    return isSpeaking.value
  }

  // 清理
  onUnmounted(() => {
    stopRecording()
  })

  return {
    // 状态
    isRecording,
    hasPermission,
    volume,
    isSpeaking,

    // 方法
    startRecording,
    stopRecording,
    checkPermission,
    getVolumeLevel,
    isUserSpeaking,

    // 设置回调
    setOnFrame: (callback) => { _onFrameCallback = callback },
    setOnError: (callback) => { onError = callback },
  }
}

export default useAudioRecorder
