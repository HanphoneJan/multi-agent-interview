/**
 * TTS Service - 语音合成服务
 */
import http from './request.js'
import { ENDPOINTS } from './api.js'

class TTSService {
  constructor() {
    this.audioContext = null
    this.currentAudio = null
    this.provider = null
    this.voices = {}
  }

  /**
   * 初始化 TTS 服务
   */
  async init() {
    try {
      const response = await http.get(ENDPOINTS.tts.provider)
      this.provider = response.provider
      this.voices = response.voices
      return response
    } catch (error) {
      console.error('TTS 初始化失败:', error)
      throw error
    }
  }

  /**
   * 获取可用音色列表
   */
  async getVoices(providerName) {
    try {
      const response = await http.get(ENDPOINTS.tts.voices(providerName || this.provider))
      return response.voices
    } catch (error) {
      console.error('获取音色失败:', error)
      return []
    }
  }

  /**
   * 合成语音
   */
  async synthesize(text, options = {}) {
    try {
      const response = await http.post(ENDPOINTS.tts.synthesize, {
        text,
        voice: options.voice || 'xiaoyan',
        speed: options.speed || 50,
        volume: options.volume || 50,
        pitch: options.pitch || 50
      })

      if (!response.success) {
        throw new Error(response.error_message || '语音合成失败')
      }

      return response.audio_base64
    } catch (error) {
      console.error('语音合成失败:', error)
      throw error
    }
  }

  /**
   * 播放文本
   */
  async speak(text, options = {}) {
    try {
      const audioBase64 = await this.synthesize(text, options)
      await this.playAudio(audioBase64)
    } catch (error) {
      console.error('播放失败:', error)
      this.fallbackSpeak(text)
    }
  }

  /**
   * 播放 base64 音频
   */
  playAudio(base64Data) {
    return new Promise((resolve, reject) => {
      // #ifdef H5
      const audio = new Audio(`data:audio/mp3;base64,${base64Data}`)
      audio.onended = resolve
      audio.onerror = reject
      audio.play()
      this.currentAudio = audio
      // #endif

      // #ifndef H5
      const innerAudioContext = uni.createInnerAudioContext()
      innerAudioContext.src = `data:audio/mp3;base64,${base64Data}`
      innerAudioContext.onPlay(() => {
        console.log('开始播放')
      })
      innerAudioContext.onEnded(() => {
        resolve()
        innerAudioContext.destroy()
      })
      innerAudioContext.onError((err) => {
        reject(err)
        innerAudioContext.destroy()
      })
      innerAudioContext.play()
      this.currentAudio = innerAudioContext
      // #endif
    })
  }

  /**
   * 停止播放
   */
  stop() {
    if (this.currentAudio) {
      // #ifdef H5
      this.currentAudio.pause()
      // #endif
      // #ifndef H5
      this.currentAudio.stop()
      this.currentAudio.destroy()
      // #endif
      this.currentAudio = null
    }
  }

  /**
   * 浏览器 TTS 回退
   */
  fallbackSpeak(text) {
    // #ifdef H5
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'zh-CN'
      speechSynthesis.speak(utterance)
    }
    // #endif
  }
}

export const ttsService = new TTSService()
export default ttsService
