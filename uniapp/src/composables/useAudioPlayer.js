/**
 * 音频播放器组合式函数 (Qwen3-Omni 实时音视频面试)
 *
 * 支持 PCM 音频流实时播放
 * 兼容 H5 和微信小程序
 */
import { ref } from 'vue'

const DEFAULT_SAMPLE_RATE = 24000  // Qwen3-Omni 输出 24kHz

/**
 * 音频播放器
 * @param {Object} options - 配置选项
 * @param {number} options.sampleRate - 采样率 (默认 24000)
 * @param {Function} options.onPlayStart - 播放开始回调
 * @param {Function} options.onPlayEnd - 播放结束回调
 */
export function useAudioPlayer(options = {}) {
  const {
    sampleRate = DEFAULT_SAMPLE_RATE,
    onPlayStart = null,
    onPlayEnd = null
  } = options

  // 状态
  const isPlaying = ref(false)
  const isLoading = ref(false)
  const currentDuration = ref(0)
  const playbackQueue = ref([])

  // 内部状态
  let audioContext = null
  let currentSource = null
  let isProcessing = false
  let queue = []

  /**
   * 初始化 Web Audio Context
   */
  const initAudioContext = () => {
    // #ifdef H5
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: sampleRate
      })
    }
    return audioContext
    // #endif
    return null
  }

  /**
   * Base64 转 ArrayBuffer
   */
  const base64ToArrayBuffer = (base64) => {
    const binary = atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return bytes.buffer
  }

  /**
   * 播放单个 PCM 数据
   * @param {string} base64Data - base64 编码的 PCM 数据
   * @param {number} playSampleRate - 播放采样率
   */
  const playPCM = async (base64Data, playSampleRate = sampleRate) => {
    // #ifdef H5
    if (!base64Data) return

    try {
      const ctx = initAudioContext()
      if (!ctx) return

      // Base64 -> ArrayBuffer -> Int16Array
      const arrayBuffer = base64ToArrayBuffer(base64Data)
      const int16Array = new Int16Array(arrayBuffer)

      // 转换为 Float32Array
      const float32Array = new Float32Array(int16Array.length)
      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768.0
      }

      // 创建 AudioBuffer
      const audioBuffer = ctx.createBuffer(1, float32Array.length, playSampleRate)
      audioBuffer.copyToChannel(float32Array, 0)

      // 创建播放节点
      const source = ctx.createBufferSource()
      source.buffer = audioBuffer
      source.connect(ctx.destination)

      // 播放
      source.start(0)
      isPlaying.value = true
      currentDuration.value = audioBuffer.duration

      if (onPlayStart) onPlayStart()

      source.onended = () => {
        isPlaying.value = false
        if (onPlayEnd) onPlayEnd()
        processQueue()
      }

      currentSource = source

    } catch (err) {
      console.error('播放 PCM 音频失败', err)
      isPlaying.value = false
    }
    // #endif

    // #ifdef MP-WEIXIN
    // 小程序使用 InnerAudioContext
    playPCMInMiniProgram(base64Data)
    // #endif
  }

  /**
   * 小程序播放 PCM
   * 需要将 PCM 转换为 mp3 或其他格式，或者使用插件
   */
  const playPCMInMiniProgram = (base64Data) => {
    // #ifdef MP-WEIXIN
    // 小程序不直接支持 PCM 播放，需要转换为音频文件
    // 这里简化处理，实际项目中可能需要使用音频转换插件
    console.log('小程序播放 PCM 需要音频转换，暂不支持')
    // #endif
  }

  /**
   * 添加到播放队列 (用于流式音频)
   * @param {string} base64Data - base64 编码的音频数据
   * @param {number} dataSampleRate - 音频采样率
   */
  const queueAudio = (base64Data, dataSampleRate = sampleRate) => {
    queue.push({ data: base64Data, sampleRate: dataSampleRate })
    playbackQueue.value = [...queue]

    if (!isProcessing && !isPlaying.value) {
      processQueue()
    }
  }

  /**
   * 处理播放队列
   */
  const processQueue = async () => {
    if (queue.length === 0) {
      isProcessing = false
      return
    }

    isProcessing = true
    const item = queue.shift()
    playbackQueue.value = [...queue]

    await playPCM(item.data, item.sampleRate)
  }

  /**
   * 停止播放
   */
  const stop = () => {
    // #ifdef H5
    if (currentSource) {
      try {
        currentSource.stop()
        currentSource.disconnect()
      } catch (e) {
        // 可能已停止
      }
      currentSource = null
    }
    // #endif

    queue = []
    playbackQueue.value = []
    isPlaying.value = false
    isProcessing = false
    currentDuration.value = 0
  }

  /**
   * 打断播放 (候选人开始说话时)
   */
  const interrupt = () => {
    console.log('音频播放被用户打断')
    stop()
    if (onPlayEnd) onPlayEnd({ interrupted: true })
  }

  /**
   * 清空队列
   */
  const clearQueue = () => {
    queue = []
    playbackQueue.value = []
  }

  /**
   * 获取队列长度
   */
  const getQueueLength = () => {
    return queue.length
  }

  return {
    // 状态
    isPlaying,
    isLoading,
    currentDuration,
    playbackQueue,

    // 方法
    playPCM,
    queueAudio,
    stop,
    interrupt,
    clearQueue,
    getQueueLength,
  }
}

export default useAudioPlayer
