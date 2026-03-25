/**
 * 视频采集组合式函数 (Qwen3-Omni 实时音视频面试)
 *
 * 支持实时视频帧捕获和发送
 * 兼容 H5 和微信小程序
 */
import { ref, onUnmounted } from 'vue'

const DEFAULT_FRAME_INTERVAL = 2000 // 默认每2秒发送一帧
const DEFAULT_QUALITY = 0.8 // 图片质量 0-1

/**
 * 视频采集器
 * @param {Object} options - 配置选项
 * @param {number} options.frameInterval - 帧间隔 ms (默认 2000)
 * @param {number} options.quality - 图片质量 (默认 0.8)
 * @param {Function} options.onFrame - 视频帧回调 (base64)
 */
export function useVideoCapture(options = {}) {
  const {
    frameInterval = DEFAULT_FRAME_INTERVAL,
    quality = DEFAULT_QUALITY,
    onFrame = null
  } = options

  // 状态
  const isCapturing = ref(false)
  const hasPermission = ref(false)
  const lastFrameTime = ref(0)

  // 内部状态
  let captureTimer = null
  let mediaStream = null
  let videoElement = null
  let canvas = null
  let _onFrameCallback = onFrame

  /**
   * 初始化 H5 视频
   */
  const initWebVideo = async () => {
    // #ifdef H5
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      })

      // 创建视频元素
      videoElement = document.createElement('video')
      videoElement.srcObject = mediaStream
      videoElement.muted = true
      videoElement.playsInline = true

      await videoElement.play()

      // 创建 canvas
      canvas = document.createElement('canvas')
      canvas.width = 640
      canvas.height = 480

      hasPermission.value = true
      return true
    } catch (err) {
      console.error('获取摄像头权限失败', err)
      hasPermission.value = false
      return false
    }
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
      if (setting.authSetting['scope.camera']) {
        hasPermission.value = true
        return true
      }

      await uni.authorize({ scope: 'scope.camera' })
      hasPermission.value = true
      return true
    } catch (err) {
      console.error('摄像头权限被拒绝', err)
      hasPermission.value = false
      return false
    }
    // #endif

    // #ifdef H5
    return await initWebVideo()
    // #endif

    return false
  }

  /**
   * 捕获一帧 (H5)
   */
  const captureFrameWeb = () => {
    // #ifdef H5
    if (!videoElement || !canvas) return null

    const ctx = canvas.getContext('2d')
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height)

    // 转为 base64 (JPEG)
    const base64 = canvas.toDataURL('image/jpeg', quality)
    return base64.split(',')[1] // 去掉 data:image/jpeg;base64, 前缀
    // #endif
    return null
  }

  /**
   * 捕获一帧 (小程序)
   */
  const captureFrameMiniProgram = () => {
    return new Promise((resolve, reject) => {
      // #ifdef MP-WEIXIN
      const cameraCtx = uni.createCameraContext()
      cameraCtx.takePhoto({
        quality: 'normal',
        success: (res) => {
          // 读取图片文件
          uni.getFileSystemManager().readFile({
            filePath: res.tempImagePath,
            encoding: 'base64',
            success: (fileRes) => {
              resolve(fileRes.data)
            },
            fail: reject
          })
        },
        fail: reject
      })
      // #endif

      // #ifndef MP-WEIXIN
      resolve(null)
      // #endif
    })
  }

  /**
   * 开始捕获
   * @param {Function} onFrameCallback - 帧回调 (替代构造函数中的 onFrame)
   */
  const startCapture = async (onFrameCallback = null) => {
    if (onFrameCallback) {
      _onFrameCallback = onFrameCallback
    }

    const hasPerm = await checkPermission()
    if (!hasPerm) {
      return false
    }

    isCapturing.value = true

    // 立即捕获一帧
    await captureAndSend()

    // 定时捕获
    captureTimer = setInterval(async () => {
      if (isCapturing.value) {
        await captureAndSend()
      }
    }, frameInterval)

    return true
  }

  /**
   * 捕获并发送一帧
   */
  const captureAndSend = async () => {
    if (!_onFrameCallback) return

    try {
      let base64 = null

      // #ifdef H5
      base64 = captureFrameWeb()
      // #endif

      // #ifdef MP-WEIXIN
      base64 = await captureFrameMiniProgram()
      // #endif

      if (base64) {
        lastFrameTime.value = Date.now()
        _onFrameCallback(base64, {
          timestamp: lastFrameTime.value,
          width: 640,
          height: 480,
          format: 'jpeg'
        })
      }
    } catch (err) {
      console.error('捕获视频帧失败', err)
    }
  }

  /**
   * 停止捕获
   */
  const stopCapture = () => {
    isCapturing.value = false

    if (captureTimer) {
      clearInterval(captureTimer)
      captureTimer = null
    }

    // #ifdef H5
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop())
      mediaStream = null
    }
    if (videoElement) {
      videoElement.pause()
      videoElement.srcObject = null
      videoElement = null
    }
    canvas = null
    // #endif

    console.log('视频捕获已停止')
  }

  /**
   * 手动捕获一帧
   */
  const captureOnce = async () => {
    if (!hasPermission.value) {
      const hasPerm = await checkPermission()
      if (!hasPerm) return null
    }

    await captureAndSend()
    return lastFrameTime.value
  }

  // 清理
  onUnmounted(() => {
    stopCapture()
  })

  return {
    // 状态
    isCapturing,
    hasPermission,
    lastFrameTime,

    // 方法
    startCapture,
    stopCapture,
    captureOnce,
    checkPermission,

    // 设置回调
    setOnFrame: (callback) => { _onFrameCallback = callback },
  }
}

export default useVideoCapture
