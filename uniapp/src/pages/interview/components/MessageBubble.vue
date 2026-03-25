<template>
  <view class="message-bubble" :class="role">
    <view class="content-wrapper">
      <view class="bubble" :class="{ 'is-markdown': isMarkdown }" @longpress="copyContent">
        <!-- 纯文本 -->
        <text v-if="!isMarkdown && !isAudio" class="text">{{ content }}</text>

        <!-- Markdown 内容 -->
        <rich-text v-else-if="isMarkdown" :nodes="renderedMarkdown"></rich-text>

        <!-- 音频 -->
        <view v-else-if="isAudio" class="audio-message" @click="onPlayAudio">
          <text class="fa-solid" :class="isPlaying ? 'fa-volume-high' : 'fa-play'"></text>
          <text class="audio-text">语音消息</text>
          <text class="audio-duration">{{ duration }}"</text>
        </view>
      </view>
      <view class="message-footer">
        <text v-if="showTime" class="time">{{ formattedTime }}</text>
        <text class="copy-hint" @click="copyContent">
          <text class="fa-solid fa-copy" />
          <text>复制</text>
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  role: 'user' | 'ai' | 'system'
  content: string
  type?: 'text' | 'markdown' | 'audio'
  audioUrl?: string
  duration?: number
  timestamp?: number
  showTime?: boolean
  isPlaying?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  duration: 0,
  showTime: false,
  isPlaying: false
})

const emit = defineEmits<{
  playAudio: [url: string]
}>()

const isMarkdown = computed(() => props.type === 'markdown')
const isAudio = computed(() => props.type === 'audio')

const formattedTime = computed(() => {
  if (!props.timestamp) return ''
  const date = new Date(props.timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
})

// 简单的 Markdown 渲染（只处理基本格式）
const renderedMarkdown = computed(() => {
  let html = props.content
    // 代码块
    .replace(/```([\s\S]*?)```/g, '<pre style="background:#f5f5f5;padding:10px;border-radius:8px;overflow-x:auto;font-size:14px;line-height:1.4;"><code>$1</code></pre>')
    // 行内代码
    .replace(/`([^`]+)`/g, '<code style="background:#f5f5f5;padding:2px 6px;border-radius:4px;font-size:14px;">$1</code>')
    // 粗体
    .replace(/\*\*(.*?)\*\*/g, '<strong style="font-weight:600;">$1</strong>')
    // 斜体
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // 换行
    .replace(/\n/g, '<br>')

  return html
})

const onPlayAudio = () => {
  if (props.audioUrl) {
    emit('playAudio', props.audioUrl)
  }
}

const copyContent = () => {
  uni.setClipboardData({
    data: props.content,
    success: () => {
      uni.showToast({
        title: '已复制',
        icon: 'none',
        duration: 1500
      })
    },
    fail: () => {
      uni.showToast({
        title: '复制失败',
        icon: 'none',
        duration: 1500
      })
    }
  })
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  max-width: 85%;
  margin-bottom: 16px;
}

.message-bubble.user {
  align-self: flex-end;
  margin-left: auto;
}

.message-bubble.ai {
  align-self: flex-start;
  margin-right: auto;
}

.message-bubble.system {
  align-self: center;
  max-width: 90%;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble.user .content-wrapper {
  align-items: flex-end;
}

.message-bubble.ai .content-wrapper {
  align-items: flex-start;
}

.message-bubble.system .content-wrapper {
  align-items: center;
}

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  max-width: calc(100vw - 120px);
  word-break: break-word;
}

.message-bubble.user .bubble {
  background: var(--primary-color, #3964fe);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.ai .bubble {
  background: #fff;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-bubble.system .bubble {
  background: #fff3e0;
  color: #666;
  font-size: 14px;
}

.bubble.is-markdown {
  font-size: 15px;
  line-height: 1.6;
}

.message-bubble.user .bubble.is-markdown {
  color: #fff;
}

.text {
  font-size: 15px;
  line-height: 1.5;
}

.message-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.message-bubble.user .message-footer {
  flex-direction: row-reverse;
}

.time {
  font-size: 12px;
  color: #999;
}

.copy-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}

.copy-hint:active {
  background: rgba(0, 0, 0, 0.05);
  color: var(--primary-color, #3964fe);
}

.copy-hint .fa-solid {
  font-size: 12px;
}

/* 音频消息 */
.audio-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  min-width: 160px;
}

.audio-message .fa-solid {
  font-size: 20px;
  color: var(--primary-color, #3964fe);
}

.audio-text {
  flex: 1;
  font-size: 15px;
}

.audio-duration {
  font-size: 13px;
  color: #999;
}
</style>
