<template>
  <view class="realtime-interview">
    <view class="nav-bar">
      <view class="nav-left">
        <text class="nav-title">瀹炴椂闈㈣瘯</text>
        <text class="nav-subtitle">鐩存帴鍙ｅご浣滅瓟锛岀郴缁熶細鍗虫椂缁х画杩介棶</text>
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
          <text>{{ isConnecting ? '杩炴帴涓? : '寮€濮嬮潰璇? }}</text>
        </button>
        <button v-else class="action-btn danger" @click="handleEnd">
          <text class="fa-solid fa-stop" />
          <text>缁撴潫闈㈣瘯</text>
        </button>
      </view>
    </view>

    <view class="stage-card">
      <view class="video-stage">
        <live-pusher
          v-if="mediaState.hasCamera"
          ref="livePusherRef"
          class="live-pusher"
          mode="RTC"
          :autopush="true"
          :muted="mediaState.isMuted"
          :enable-camera="mediaState.videoEnabled"
          @statechange="onPusherStateChange"
        />
        <view v-else class="video-placeholder">
          <text class="fa-solid fa-video-slash" />
          <text>鎽勫儚澶存湭寮€鍚?/text>
        </view>

        <view class="stage-overlay">
          <text class="stage-chip strong" :class="interviewState.status">{{ statusText }}</text>
          <text class="stage-chip">宸插洖绛?{{ answeredCount }}</text>
          <text class="stage-chip">{{ props.userInfo.name || props.userInfo.username || '鍊欓€変汉' }}</text>
          <text class="stage-chip" :class="{ muted: !mediaState.hasMicrophone || mediaState.isMuted }">
            {{ !mediaState.hasMicrophone || mediaState.isMuted ? '楹﹀厠椋庡叧闂? : '楹﹀厠椋庡紑鍚? }}
          </text>
        </view>
      </view>
    </view>

    <view class="conversation-card">
      <view class="section-header">
        <view>
          <text class="section-title">瀹炴椂瀵硅瘽</text>
          <text class="section-subtitle">鎸変綇璇磋瘽锛屾澗寮€鍚庣珛鍗冲彂閫佽闊冲洖绛?/text>
        </view>
      </view>

      <scroll-view class="chat-container" scroll-y :scroll-top="scrollTop">
        <view v-if="messages.length === 0 && !currentMessage" class="empty-state">
          <text class="fa-solid fa-comments" />
          <text class="empty-title">鍑嗗寮€濮嬪疄鏃堕潰璇?/text>
          <text class="empty-text">杩炴帴鎴愬姛鍚庯紝灏卞儚鐪熷疄闈㈣瘯涓€鏍风洿鎺ュ紑鍙ｅ嵆鍙€?/text>
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
            @click="toggleCamera"
          >
            <text class="fa-solid" :class="mediaState.videoEnabled ? 'fa-video' : 'fa-video-slash'" />
          </button>
          <button
            class="icon-btn"
            :class="{ active: mediaState.hasMicrophone && !mediaState.isMuted }"
            @click="toggleMute"
          >
            <text class="fa-solid" :class="!mediaState.hasMicrophone || mediaState.isMuted ? 'fa-microphone-slash' : 'fa-microphone'" />
          </button>
        </view>

        <text class="dock-tip">
          {{ isConnected ? '瀹炴椂妯″紡浠ヨ闊充负涓伙紝涓嶅啀鎶婂ぇ鏂囨湰妗嗕綔涓轰富浣滅瓟鍏ュ彛銆? : '杩炴帴鍚庡嵆鍙紑濮嬭闊充綔绛斻€? }}
        </text>
      </view>

      <button
        class="record-btn"
        :class="{ recording: isRecording }"
        :disabled="!isConnected || !mediaState.hasMicrophone"
        @touchstart="startVoiceRecord"
        @touchend="stopVoiceRecord"
      >
        <text class="fa-solid" :class="isRecording ? 'fa-stop' : 'fa-microphone'" />
        <text>{{ isRecording ? '鏉惧紑鍙戦€? : '鎸変綇璇磋瘽' }}</text>
      </button>
    </view>

    <view v-if="errorMessage" class="error-toast">
      <text class="fa-solid fa-exclamation-circle" />
      <text>{{ errorMessage }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useUniWebSocket } from './useUniWebSocket'
import { useUniMedia } from './useUniMedia'
import InterviewStatus from '../components/InterviewStatus.vue'
import MessageBubble from '../components/MessageBubble.vue'

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

// 闈㈣瘯鐘舵€?
const interviewState = ref({
  status: 'idle' as const,
  duration: 0,
  currentQuestion: 0
})

// 娑堟伅鐩稿叧
const messages = ref<Message[]>([])
const currentMessage = ref<Message | null>(null)
const scrollTop = ref(0)
const errorMessage = ref('')

// 褰曢煶鐘舵€?
const isRecording = ref(false)
let recordStartTime = 0

// live-pusher 寮曠敤
const livePusherRef = ref<any>(null)

// 浣跨敤 composables
const {
  state: mediaState,
  requestPermissions,
  startRecording,
  stopRecording,
  readAudioFile,
  playAudio,
  toggleMute,
  toggleVideo,
  stopAll
} = useUniMedia()

// WebSocket
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1'
const wsUrl = computed(() => {
  return `${WS_BASE_URL}/ws/interview/realtime/${props.sessionId}?token=${props.token}`
})

const { status: wsStatus, connect, disconnect, send } = useUniWebSocket({
  url: () => wsUrl.value,
  onMessage: handleWebSocketMessage,
  onConnect: () => {
    interviewState.value.status = 'connected'
    startTimer()
    send({
      type: 'start_interview',
      timestamp: Date.now(),
      session_id: props.sessionId
    })
  },
  onDisconnect: () => {
    interviewState.value.status = 'idle'
    stopTimer()
  },
  onError: (err) => {
    showError('WebSocket 杩炴帴閿欒')
    console.error('[WebSocket] 閿欒:', err)
  }
})

// 璁＄畻灞炴€?
const isConnected = computed(() => wsStatus.value === 'connected')
const isConnecting = computed(() => wsStatus.value === 'connecting')

const statusText = computed(() => {
  const statusMap: Record<string, string> = {
    idle: '鏈紑濮?,
    connecting: '杩炴帴涓?..',
    connected: '杩涜涓?,
    error: '杩炴帴寮傚父',
    ended: '宸茬粨鏉?
  }
  return statusMap[interviewState.value.status] || '鏈煡'
})

const answeredCount = computed(() => {
  return messages.value.filter(m => m.role === 'user').length
})

// 璁℃椂鍣?
let timerInterval: number | null = null

const startTimer = () => {
  stopTimer()
  timerInterval = setInterval(() => {
    interviewState.value.duration++
  }, 1000) as unknown as number
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// 鍒濆鍖?
onMounted(async () => {
  // 璇锋眰鏉冮檺
  await requestPermissions({ audio: true, video: true })
})

onUnmounted(() => {
  stopTimer()
  stopAll()
  disconnect()
})

// 寮€濮嬮潰璇?
const startInterview = () => {
  if (!props.sessionId || !props.token) {
    showError('缂哄皯蹇呰鐨勪細璇濅俊鎭?)
    return
  }
  interviewState.value.status = 'connecting'
  connect()
}

// 缁撴潫闈㈣瘯
const handleEnd = () => {
  uni.showModal({
    title: '纭缁撴潫',
    content: '纭畾瑕佺粨鏉熷綋鍓嶉潰璇曞悧锛熺粨鏉熷悗灏嗙敓鎴愯瘎浼版姤鍛娿€?,
    success: (res) => {
      if (res.confirm) {
        send({ type: 'end_interview' })
        disconnect()
        interviewState.value.status = 'ended'
      }
    }
  })
}

// 鍙戦€佹枃鏈洖绛?
// 鍒囨崲鎽勫儚澶?
const toggleCamera = () => {
  toggleVideo()
  // live-pusher 浼氳嚜鍔ㄥ搷搴?enable-camera 灞炴€у彉鍖?
}

// 寮€濮嬪綍闊筹紙鎸変綇璇磋瘽锛?
const startVoiceRecord = async () => {
  if (!isConnected.value) return

  isRecording.value = true
  recordStartTime = Date.now()

  const ok = await startRecording()
  if (!ok) {
    isRecording.value = false
    showError('褰曢煶鍚姩澶辫触')
  }
}

// 鍋滄褰曢煶
const stopVoiceRecord = async () => {
  if (!isRecording.value) return

  isRecording.value = false
  const duration = Date.now() - recordStartTime

  // 褰曢煶澶煭锛屽彇娑?
  if (duration < 500) {
    stopRecording()
    return
  }

  const filePath = await stopRecording()
  if (filePath) {
    // 璇诲彇鏂囦欢骞跺彂閫?
    const base64 = await readAudioFile(filePath)
    if (base64) {
      send({
        type: 'audio',
        audio: base64
      })

      messages.value.push({
        role: 'user',
        content: '[璇煶娑堟伅]',
        type: 'audio',
        timestamp: Date.now()
      })

      scrollToBottom()
    }
  }
}

// live-pusher 鐘舵€佸彉鍖?
const onPusherStateChange = (e: any) => {
  console.log('[LivePusher] 鐘舵€佸彉鍖?', e)
}

// 婊氬姩鍒板簳閮?
const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = messages.value.length * 200 + 1000
  })
}

// 澶勭悊 WebSocket 娑堟伅
function handleWebSocketMessage(msg: any) {
  console.log('[WebSocket] 鏀跺埌娑堟伅:', msg)

  switch (msg.type) {
    case 'question':
      if (currentMessage.value) {
        messages.value.push({
          ...currentMessage.value,
          isStreaming: false
        })
      }
      currentMessage.value = {
        role: 'ai',
        content: msg.question,
        type: 'markdown',
        timestamp: Date.now()
      }
      scrollToBottom()
      break

    case 'stream_start':
      if (currentMessage.value) {
        messages.value.push({
          ...currentMessage.value,
          isStreaming: false
        })
      }
      currentMessage.value = {
        role: 'ai',
        content: '',
        type: 'markdown',
        timestamp: Date.now(),
        isStreaming: true
      }
      scrollToBottom()
      break

    case 'stream_chunk':
      if (currentMessage.value && msg.chunk) {
        currentMessage.value.content += msg.chunk
        scrollToBottom()
      }
      break

    case 'stream_end':
      if (currentMessage.value) {
        currentMessage.value.isStreaming = false
      }
      break

    case 'audio_result':
    case 'user_message':
      const content = msg.answer || msg.transcript || msg.content
      if (content) {
        messages.value.push({
          role: 'user',
          content,
          type: 'text',
          timestamp: Date.now()
        })
        scrollToBottom()
      }
      break

    case 'end':
      disconnect()
      interviewState.value.status = 'ended'
      uni.showModal({
        title: '闈㈣瘯缁撴潫',
        content: msg.summary?.overall_evaluation || '闈㈣瘯宸插畬鎴?,
        showCancel: false,
        success: () => {
          uni.redirectTo({
            url: `/pages/report/report?sessionId=${props.sessionId}`
          })
        }
      })
      break

    case 'error':
      showError(msg.error || '鏈嶅姟鍣ㄩ敊璇?)
      break
  }
}

// 鏄剧ず閿欒
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
  padding: 20rpx;
  gap: 20rpx;
  box-sizing: border-box;
  overflow: hidden;
}

.nav-bar,
.stage-card,
.conversation-card,
.control-dock {
  width: 100%;
  box-sizing: border-box;
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20rpx;
  padding: 28rpx 32rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16rpx 40rpx rgba(16, 24, 40, 0.08);
}

.nav-left {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.nav-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #1f2a44;
}

.nav-subtitle {
  font-size: 24rpx;
  color: #667085;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  min-height: 76rpx;
  padding: 0 28rpx;
  border: none;
  border-radius: 999rpx;
  font-size: 26rpx;
  color: #fff;
}

.action-btn.primary {
  background: linear-gradient(135deg, #3964fe, #5177ff);
}

.action-btn.danger {
  background: #ef4444;
}

.stage-card {
  border-radius: 28rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16rpx 40rpx rgba(16, 24, 40, 0.08);
}

.video-stage {
  position: relative;
  aspect-ratio: 16 / 9;
  background: #111827;
}

.live-pusher {
  width: 100%;
  height: 100%;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  color: rgba(255, 255, 255, 0.78);
}

.video-placeholder .fa-solid {
  font-size: 60rpx;
}

.stage-overlay {
  position: absolute;
  left: 20rpx;
  right: 20rpx;
  bottom: 20rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 56rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: rgba(15, 23, 42, 0.55);
  color: #fff;
  font-size: 22rpx;
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

.conversation-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 28rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 16rpx 40rpx rgba(16, 24, 40, 0.08);
}

.section-header {
  padding: 26rpx 28rpx;
  border-bottom: 1rpx solid #e7ecf3;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: #1f2a44;
}

.section-subtitle {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #667085;
}

.chat-container {
  flex: 1;
  min-height: 420rpx;
  padding: 24rpx;
  box-sizing: border-box;
}

.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  text-align: center;
  color: #667085;
}

.empty-state .fa-solid {
  font-size: 68rpx;
  opacity: 0.3;
}

.empty-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #344054;
}

.empty-text {
  font-size: 24rpx;
}

.message-wrapper {
  margin-bottom: 18rpx;
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 26rpx;
  background: #3964fe;
  margin-left: 4rpx;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.control-dock {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 28rpx 32rpx 36rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 16rpx 40rpx rgba(16, 24, 40, 0.08);
}

.dock-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  flex-wrap: wrap;
}

.dock-tip {
  font-size: 24rpx;
  color: #667085;
}

.device-controls {
  display: flex;
  gap: 12rpx;
}

.icon-btn {
  width: 76rpx;
  height: 76rpx;
  border-radius: 50%;
  border: 1rpx solid #dbe4ee;
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
  width: 240rpx;
  height: 240rpx;
  margin: 0 auto;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #3964fe, #4f7bff);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  box-shadow: 0 18rpx 34rpx rgba(57, 100, 254, 0.28);
}

.record-btn .fa-solid {
  font-size: 44rpx;
}

.record-btn text:last-child {
  font-size: 28rpx;
}

.record-btn.recording {
  background: linear-gradient(135deg, #ef4444, #fb7185);
  box-shadow: 0 18rpx 34rpx rgba(239, 68, 68, 0.28);
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}

.error-toast {
  position: fixed;
  bottom: 30rpx;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(239, 68, 68, 0.95);
  color: #fff;
  padding: 18rpx 24rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  font-size: 24rpx;
  box-shadow: 0 10rpx 24rpx rgba(239, 68, 68, 0.25);
  z-index: 1000;
}
</style>
