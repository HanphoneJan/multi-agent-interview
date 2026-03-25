<template>
  <view class="realtime-interview">
    <view class="nav-bar">
      <view class="nav-left">
        <text class="nav-title">实时面试</text>
        <text class="nav-subtitle">直接说话，系统会根据你的表达即时追问</text>
      </view>
      <view class="nav-right">
        <InterviewStatus :status="interviewState.status" :duration="interviewState.duration" />
        <button
          v-if="!isConnected"
          class="action-btn primary"
          :disabled="isConnecting"
          @click="startInterview"
        >
          <text class="fa-solid" :class="isConnecting ? 'fa-spinner fa-spin' : 'fa-play'" />
          <text>{{ isConnecting ? '连接中' : '开始面试' }}</text>
        </button>
        <button v-else class="action-btn danger" @click="handleEnd">
          <text class="fa-solid fa-stop" />
          <text>结束面试</text>
        </button>
      </view>
    </view>

    <view class="stage-card">
      <view class="video-stage">
        <video
          v-if="mediaState.hasCamera"
          ref="videoRef"
          class="video-player"
          autoplay
          playsinline
          muted
        />
        <view v-else class="video-placeholder">
          <text class="fa-solid fa-video-slash" />
          <text>摄像头未开启</text>
        </view>

        <view class="stage-overlay">
          <text class="stage-chip strong" :class="interviewState.status">{{ statusText }}</text>
          <text class="stage-chip">已回答 {{ answeredCount }}</text>
          <text class="stage-chip">{{ props.userInfo.name || props.userInfo.username || '候选人' }}</text>
          <text class="stage-chip" :class="{ muted: !mediaState.hasMicrophone || mediaState.isMuted }">
            {{ !mediaState.hasMicrophone || mediaState.isMuted ? '麦克风关闭' : '麦克风开启' }}
          </text>
        </view>
      </view>

      <view class="stage-note" v-if="permissionStatus?.error || !mediaState.hasMicrophone">
        <text class="fa-solid fa-circle-info" />
        <text>{{ permissionStatus?.error || '麦克风不可用时，实时面试体验会受影响。' }}</text>
      </view>
    </view>

    <view class="conversation-card">
      <view class="section-header">
        <view>
          <text class="section-title">实时对话</text>
          <text class="section-subtitle">按住下方按钮说话，松开后 AI 会继续回应</text>
        </view>
      </view>

      <scroll-view class="chat-container" scroll-y :scroll-top="scrollTop">
        <view v-if="messages.length === 0 && !currentMessage" class="empty-state">
          <text class="fa-solid fa-comments" />
          <text class="empty-title">准备开始实时面试</text>
          <text class="empty-text">连接后，你可以像真实面试一样直接开口回答。</text>
        </view>

        <view v-for="(msg, index) in messages" :key="index" class="message-wrapper">
          <MessageBubble
            :role="msg.role"
            :content="msg.content"
            :type="msg.type"
            :timestamp="msg.timestamp"
            :show-time="true"
          />
        </view>

        <view v-if="currentMessage" class="message-wrapper">
          <MessageBubble
            :role="currentMessage.role"
            :content="currentMessage.content"
            :type="currentMessage.type"
            :is-streaming="currentMessage.isStreaming"
          />
          <text v-if="currentMessage.isStreaming" class="streaming-cursor">|</text>
        </view>
      </scroll-view>
    </view>

    <view class="control-dock">
      <view class="dock-top">
        <view class="device-controls">
          <button
            class="icon-btn"
            :class="{ active: mediaState.videoEnabled }"
            :disabled="!mediaState.hasCamera"
            @click="toggleCamera"
          >
            <text class="fa-solid" :class="mediaState.videoEnabled ? 'fa-video' : 'fa-video-slash'" />
          </button>
          <button
            class="icon-btn"
            :class="{ active: mediaState.hasMicrophone && !mediaState.isMuted }"
            :disabled="!mediaState.hasMicrophone"
            @click="toggleMic"
          >
            <text class="fa-solid" :class="!mediaState.hasMicrophone || mediaState.isMuted ? 'fa-microphone-slash' : 'fa-microphone'" />
          </button>
        </view>

        <text class="dock-tip">
          {{ isConnected ? '实时模式建议直接口头作答，不需要先整理成文字。' : '连接后即可开始语音作答。' }}
        </text>
      </view>

      <button
        class="record-btn"
        :class="{ recording: isRecording }"
        :disabled="!isConnected || !mediaState.hasMicrophone"
        @mousedown="startRecording"
        @mouseup="stopRecording"
        @mouseleave="cancelRecording"
        @touchstart.prevent="startRecording"
        @touchend.prevent="stopRecording"
      >
        <text class="fa-solid" :class="isRecording ? 'fa-stop' : 'fa-microphone'" />
        <text>{{ isRecording ? '松开结束' : '按住说话' }}</text>
      </button>
    </view>

    <RecordingIndicator
      v-if="isRecording"
      :is-recording="isRecording"
      :audio-level="mediaState.audioLevel"
      :duration="recordingDuration"
    />

    <view v-if="errorMessage" class="error-toast">
      <text class="fa-solid fa-exclamation-circle" />
      <text>{{ errorMessage }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useBrowserWebSocket } from './useBrowserWebSocket'
import { useBrowserMedia, type PermissionResult } from './useBrowserMedia'
import { useSpeechSynthesis } from './useSpeechSynthesis'
import InterviewStatus from '../components/InterviewStatus.vue'
import MessageBubble from '../components/MessageBubble.vue'
import RecordingIndicator from '../components/RecordingIndicator.vue'

interface Message {
  id?: string
  role: 'user' | 'ai' | 'system'
  content: string
  type: 'text' | 'markdown' | 'audio'
  timestamp: number
  isStreaming?: boolean
}

interface UserInfo {
  name?: string
  username?: string
  university?: string
  major?: string
  gender?: string
  learningStage?: string
  access?: string
  sessionId?: string
}

const props = defineProps<{
  sessionId: string
  token: string
  userInfo: UserInfo
}>()

// 面试状态
const interviewState = ref({
  status: 'idle' as const,
  duration: 0,
  currentQuestion: 0
})

// 消息相关
const messages = ref<Message[]>([])
const currentMessage = ref<Message | null>(null)
const scrollTop = ref(0)
const errorMessage = ref('')

// 录音状态
const isRecording = ref(false)
const recordingDuration = ref(0)
let recordingTimer: number | null = null

// 视频引用
const videoRef = ref<HTMLVideoElement>()

// 权限提示
const permissionStatus = ref<PermissionResult | null>(null)

// 使用 composables
const {
  state: mediaState,
  mediaStream,
  requestPermissions,
  startRealtimeRecording,
  stopRealtimeRecording,
  playAudio,
  toggleMute,
  toggleVideo,
  stopAll
} = useBrowserMedia()

const { speak, stop: stopTTS } = useSpeechSynthesis()

// WebSocket
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1'
const wsUrl = computed(() => {
  return `${WS_BASE_URL}/ws/interview/realtime/${props.sessionId}?token=${props.token}`
})

const { status: wsStatus, connect, disconnect, send } = useBrowserWebSocket({
  url: () => {
    console.log('[WebSocket] 连接 URL:', wsUrl.value)
    return wsUrl.value
  },
  onMessage: (msg) => {
    console.log('[WebSocket] 收到消息:', msg)
    handleWebSocketMessage(msg)
  },
  onConnect: () => {
    console.log('[WebSocket] 连接成功，发送 start 消息')
    interviewState.value.status = 'connected'
    startTimer()
    // 发送开始面试消息
    const sent = send({
      type: 'start',
      timestamp: Date.now(),
      session_id: props.sessionId
    })
    console.log('[WebSocket] start 消息发送结果:', sent)
  },
  onDisconnect: () => {
    interviewState.value.status = 'idle'
    stopTimer()
  },
  onError: (err) => {
    showError('WebSocket 连接错误')
    console.error('[WebSocket] 错误:', err)
  }
})

// 计算属性
const isConnected = computed(() => wsStatus.value === 'connected')
const isConnecting = computed(() => wsStatus.value === 'connecting')

const statusText = computed(() => {
  const statusMap: Record<string, string> = {
    idle: '未开始',
    connecting: '连接中...',
    connected: '进行中',
    error: '连接异常',
    ended: '已结束'
  }
  return statusMap[interviewState.value.status] || '未知'
})

const answeredCount = computed(() => {
  return messages.value.filter(m => m.role === 'user').length
})

// 计时器
let timerInterval: number | null = null

const startTimer = () => {
  stopTimer()
  timerInterval = window.setInterval(() => {
    interviewState.value.duration++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// 初始化
onMounted(async () => {
  // 请求权限并启动摄像头
  const result = await requestPermissions({ audio: true, video: true })
  permissionStatus.value = result

  if (result.success && videoRef.value && mediaStream.value) {
    videoRef.value.srcObject = mediaStream.value
  } else if (!result.success && result.error) {
    // 显示权限错误提示，但允许用户继续使用文本模式
    showError(result.error)
  }
})

onUnmounted(() => {
  stopTimer()
  stopAll()
  disconnect()
})

// 开始面试
const startInterview = () => {
  if (!props.sessionId || !props.token) {
    showError('缺少必要的会话信息')
    return
  }
  interviewState.value.status = 'connecting'
  connect()
}

// 结束面试
const handleEnd = () => {
  uni.showModal({
    title: '确认结束',
    content: '确定要结束当前面试吗？结束后将生成评估报告。',
    success: (res) => {
      if (res.confirm) {
        // 先发送结束消息，等待服务器确认后再断开
        const sent = send({ type: 'end' })
        if (sent) {
          // 消息已发送，等待服务器响应（通过 onDisconnect 回调处理）
          interviewState.value.status = 'ended'
          // 3秒后强制断开（防止服务器无响应）
          setTimeout(() => {
            if (isConnected.value) {
              disconnect()
            }
          }, 3000)
        } else {
          // 发送失败，直接断开
          disconnect()
          interviewState.value.status = 'ended'
        }
      }
    }
  })
}

// 录音相关
let isRecordingActive = false

// 开始录音
const startRecording = async () => {
  if (!isConnected.value || !mediaState.value.hasMicrophone) return

  isRecordingActive = true
  isRecording.value = true
  recordingDuration.value = 0

  // 开始计时
  recordingTimer = window.setInterval(() => {
    recordingDuration.value++
  }, 1000)

  // 开始实时录音并发送音频数据
  await startRealtimeRecording(
    (chunk) => {
      if (isRecordingActive && isConnected.value) {
        send({
          type: 'audio',
          data: chunk.data,
          timestamp: chunk.timestamp
        })
      }
    },
    { sampleRate: 16000, frameSize: 320 }
  )
}

// 停止录音
const stopRecording = () => {
  if (!isRecordingActive) return

  isRecordingActive = false
  isRecording.value = false

  // 停止计时
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }

  // 停止实时录音
  stopRealtimeRecording()

  // 发送录音结束标记
  if (isConnected.value) {
    send({ type: 'audio_end' })
  }

  // 添加用户消息标记（实际内容由后端识别后添加）
  messages.value.push({
    role: 'user',
    content: '[语音回答]',
    type: 'text',
    timestamp: Date.now()
  })
  scrollToBottom()
}

// 取消录音（鼠标移出按钮时）
const cancelRecording = () => {
  if (!isRecordingActive) return

  isRecordingActive = false
  isRecording.value = false

  // 停止计时
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }

  // 停止实时录音但不发送
  stopRealtimeRecording()
}

// 切换摄像头
const toggleCamera = () => {
  const enabled = toggleVideo()
  if (videoRef.value && mediaStream.value) {
    videoRef.value.srcObject = enabled ? mediaStream.value : null
  }
}

// 切换麦克风
const toggleMic = () => {
  toggleMute()
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = messages.value.length * 200 + 1000
  })
}

// 处理 WebSocket 消息
function handleWebSocketMessage(msg: any) {
  console.log('[WebSocket] 收到消息:', msg)

  switch (msg.type) {
    case 'connected':
      // 连接成功，面试已开始
      console.log('[WebSocket] 连接成功:', msg.message)
      break

    case 'info':
      // 提示信息
      console.log('[WebSocket] 信息:', msg.message)
      break

    case 'status':
      // 状态更新
      console.log('[WebSocket] 状态:', msg.state)
      break

    case 'question':
      // response.done 事件 - AI 回复完成
      // 如果有流式消息，先保存它
      if (currentMessage.value && currentMessage.value.role === 'ai') {
        messages.value.push({
          ...currentMessage.value,
          isStreaming: false
        })
        currentMessage.value = null
      }
      // 如果 question 事件携带了文本且与当前不同，添加为新消息
      const questionText = msg.text || msg.question
      if (questionText) {
        // 检查最后一条消息是否与此相同（避免重复）
        const lastMsg = messages.value[messages.value.length - 1]
        if (!lastMsg || lastMsg.role !== 'ai' || lastMsg.content !== questionText) {
          messages.value.push({
            role: 'ai',
            content: questionText,
            type: 'markdown',
            timestamp: Date.now(),
            isStreaming: false
          })
        }
      }
      scrollToBottom()
      break

    case 'text_delta':
      // 流式文本增量 - 追加到当前AI消息
      if (!currentMessage.value) {
        currentMessage.value = {
          role: 'ai',
          content: '',
          type: 'markdown',
          timestamp: Date.now(),
          isStreaming: true
        }
      }
      if (msg.text && currentMessage.value.role === 'ai') {
        currentMessage.value.content += msg.text
        scrollToBottom()
      }
      break

    case 'audio':
      // AI 语音输出（PCM格式）
      if (msg.data) {
        playPCMAudio(msg.data, msg.sample_rate || 24000)
      }
      break

    case 'speech_started':
      // 检测到用户说话
      console.log('[WebSocket] 检测到用户说话')
      break

    case 'speech_stopped':
      // 用户说话结束 - 只记录状态，不处理消息保存
      // 消息保存由 question 事件处理
      console.log('[WebSocket] 用户说话结束')
      break

    case 'end':
      // 面试结束
      disconnect()
      interviewState.value.status = 'ended'
      uni.showModal({
        title: '面试结束',
        content: msg.summary?.overall_evaluation || '面试已完成',
        showCancel: false,
        success: () => {
          // 使用 switchTab 跳转到 tabbar 页面（不支持 URL 参数）
          uni.switchTab({
            url: '/pages/report/report'
          })
        }
      })
      break

    case 'error':
      showError(msg.error || '服务器错误')
      break
  }
}

// 播放 base64 MP3 音频
const playBase64Audio = (base64Data: string) => {
  try {
    const audio = new Audio(`data:audio/mp3;base64,${base64Data}`)
    audio.play().catch(err => {
      console.error('[Audio] 播放失败:', err)
    })
  } catch (err) {
    console.error('[Audio] 创建音频失败:', err)
  }
}

// 播放 PCM 音频 (实时面试使用)
const playPCMAudio = (base64Data: string, sampleRate: number = 24000) => {
  try {
    // 解码 base64
    const binaryString = atob(base64Data)
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }

    // 创建 AudioContext
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()

    // 创建音频缓冲区 (16-bit PCM)
    const buffer = audioCtx.createBuffer(1, bytes.length / 2, sampleRate)
    const channelData = buffer.getChannelData(0)

    // 将 16-bit PCM 转换为 Float32
    const dataView = new DataView(bytes.buffer)
    for (let i = 0; i < channelData.length; i++) {
      const int16 = dataView.getInt16(i * 2, true) // little-endian
      channelData[i] = int16 / 32768.0 // 转换为 -1.0 ~ 1.0
    }

    // 创建音频源并播放
    const source = audioCtx.createBufferSource()
    source.buffer = buffer
    source.connect(audioCtx.destination)
    source.start()
  } catch (err) {
    console.error('[Audio] PCM 播放失败:', err)
  }
}

// 显示错误
const showError = (message: string) => {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 5000)
}
</script>

<style scoped>
.realtime-interview {
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(57, 100, 254, 0.14), transparent 24%),
    linear-gradient(180deg, #eef3fb 0%, #f6f8fc 100%);
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 16px;
  box-sizing: border-box;
  overflow: hidden;
}

.nav-bar,
.stage-card,
.conversation-card,
.control-dock {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  box-sizing: border-box;
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16px 40px rgba(16, 24, 40, 0.08);
}

.nav-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2a44;
}

.nav-subtitle {
  font-size: 13px;
  color: #667085;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  font-size: 14px;
  color: #fff;
}

.action-btn.primary {
  background: linear-gradient(135deg, #3964fe, #5177ff);
}

.action-btn.danger {
  background: #ef4444;
}

.stage-card {
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16px 40px rgba(16, 24, 40, 0.08);
}

.video-stage {
  position: relative;
  aspect-ratio: 16 / 7;
  background: #111827;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.78);
}

.video-placeholder .fa-solid {
  font-size: 34px;
}

.stage-overlay {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 13px;
}

.stage-chip.strong.connected {
  background: rgba(6, 118, 71, 0.86);
}

.stage-chip.strong.connecting {
  background: rgba(181, 71, 8, 0.88);
}

.stage-chip.strong.idle,
.stage-chip.strong.ended {
  background: rgba(71, 84, 103, 0.86);
}

.stage-chip.muted {
  background: rgba(190, 24, 93, 0.84);
}

.stage-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 14px 16px;
  background: #fff6e8;
  color: #b54708;
  font-size: 13px;
  line-height: 1.6;
}

.conversation-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16px 40px rgba(16, 24, 40, 0.08);
}

.section-header {
  padding: 18px 20px;
  border-bottom: 1px solid #e7ecf3;
}

.section-title {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #1f2a44;
}

.section-subtitle {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  color: #667085;
}

.chat-container {
  flex: 1;
  min-height: 320px;
  padding: 20px;
  box-sizing: border-box;
}

.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  color: #667085;
}

.empty-state .fa-solid {
  font-size: 42px;
  opacity: 0.3;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #344054;
}

.empty-text {
  font-size: 13px;
}

.message-wrapper {
  display: flex;
  width: 100%;
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 18px;
  background: #3964fe;
  margin-left: 4px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.control-dock {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 24px 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16px 40px rgba(16, 24, 40, 0.08);
}

.dock-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.dock-tip {
  font-size: 13px;
  color: #667085;
}

.device-controls {
  display: flex;
  gap: 10px;
}

.icon-btn {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 1px solid #dbe4ee;
  background: #f8fafc;
  color: #475467;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn.active {
  border-color: #3964fe;
  background: #eef4ff;
  color: #3964fe;
}

.record-btn {
  width: 180px;
  height: 180px;
  margin: 0 auto;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #3964fe, #4f7bff);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 18px 34px rgba(57, 100, 254, 0.28);
}

.record-btn .fa-solid {
  font-size: 34px;
}

.record-btn text:last-child {
  font-size: 15px;
}

.record-btn.recording {
  background: linear-gradient(135deg, #ef4444, #fb7185);
  box-shadow: 0 18px 34px rgba(239, 68, 68, 0.28);
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}

.error-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(239, 68, 68, 0.95);
  color: #fff;
  padding: 12px 18px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  box-shadow: 0 10px 24px rgba(239, 68, 68, 0.25);
  z-index: 1000;
}

@media (max-width: 768px) {
  .realtime-interview {
    padding: 14px;
  }

  .nav-bar,
  .control-dock {
    padding: 16px;
  }

  .nav-bar,
  .dock-top {
    flex-direction: column;
    align-items: stretch;
  }

  .nav-right {
    justify-content: space-between;
  }

  .video-stage {
    aspect-ratio: 4 / 3;
  }

  .record-btn {
    width: 152px;
    height: 152px;
  }
}
</style>