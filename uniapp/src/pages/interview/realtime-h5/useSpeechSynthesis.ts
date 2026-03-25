/**
 * H5 浏览器语音合成 (TTS) 封装
 * 用于 AI 回复的语音播报
 */

import { ref, onUnmounted } from 'vue'

export type SpeechStatus = 'idle' | 'speaking' | 'paused'

export interface SpeechOptions {
  rate?: number      // 语速 0.1 - 10
  pitch?: number     // 音调 0 - 2
  volume?: number    // 音量 0 - 1
  lang?: string      // 语言
}

export function useSpeechSynthesis() {
  const status = ref<SpeechStatus>('idle')
  const isSupported = ref<boolean>(false)
  const voices = ref<SpeechSynthesisVoice[]>([])

  // 检查浏览器支持
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    isSupported.value = true
  }

  /**
   * 获取可用语音列表
   */
  const loadVoices = (): SpeechSynthesisVoice[] => {
    if (!isSupported.value) return []

    const availableVoices = window.speechSynthesis.getVoices()
    voices.value = availableVoices
    return availableVoices
  }

  // 延迟加载语音列表
  if (isSupported.value) {
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices
    }
    // 立即尝试加载
    setTimeout(loadVoices, 100)
  }

  /**
   * 播放文本
   */
  const speak = (
    text: string,
    options: SpeechOptions = {},
    onEnd?: () => void
  ): boolean => {
    if (!isSupported.value) {
      console.warn('[TTS] 浏览器不支持语音合成')
      return false
    }

    // 取消之前的播放
    stop()

    const utterance = new SpeechSynthesisUtterance(text)

    // 设置选项
    utterance.rate = options.rate ?? 1
    utterance.pitch = options.pitch ?? 1
    utterance.volume = options.volume ?? 1
    utterance.lang = options.lang ?? 'zh-CN'

    // 选择中文语音
    const zhVoice = voices.value.find(v => v.lang.includes('zh') || v.lang.includes('CN'))
    if (zhVoice) {
      utterance.voice = zhVoice
    }

    utterance.onstart = () => {
      status.value = 'speaking'
    }

    utterance.onend = () => {
      status.value = 'idle'
      onEnd?.()
    }

    utterance.onerror = (err) => {
      console.error('[TTS] 播放错误:', err)
      status.value = 'idle'
    }

    window.speechSynthesis.speak(utterance)
    return true
  }

  /**
   * 停止播放
   */
  const stop = () => {
    if (!isSupported.value) return

    window.speechSynthesis.cancel()
    status.value = 'idle'
  }

  /**
   * 暂停播放
   */
  const pause = () => {
    if (!isSupported.value) return

    window.speechSynthesis.pause()
    status.value = 'paused'
  }

  /**
   * 恢复播放
   */
  const resume = () => {
    if (!isSupported.value) return

    window.speechSynthesis.resume()
    status.value = 'speaking'
  }

  onUnmounted(() => {
    stop()
  })

  return {
    status,
    isSupported,
    voices,
    speak,
    stop,
    pause,
    resume
  }
}
