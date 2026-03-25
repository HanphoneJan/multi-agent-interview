<template>
  <view class="interview-realtime-container">
    <!-- 顶部状态栏 -->
    <view class="status-bar">
      <view class="status-item">
        <uni-icons :type="wsConnected ? 'link' : 'unlink'" size="16" :color="wsConnected ? '#10b981' : '#ef4444'"></uni-icons>
        <text :class="wsConnected ? 'connected' : 'disconnected'">{{ wsConnected ? '已连接' : '未连接' }}</text>
      </view>
      <view class="status-item">
        <uni-icons type="clock" size="16" color="#666"></uni-icons>
        <text>{{ formattedTime }}</text>
      </view>
      <view class="status-item" v-if="aiState">
        <text class="ai-state">AI: {{ aiStateText }}</text>
      </view>
    </view>

    <!-- 视频预览区 -->
    <view class="video-section">
      <view class="camera-container" v-if="isCameraOn">
        <!-- #ifdef MP-WEIXIN -->
        <camera device-position="front" flash="off" class="camera"></camera>
        <!-- #endif -->
        <!-- #ifdef H5 -->
        <video v-if="videoUrl" :src="videoUrl" autoplay muted class="camera"></video>
        <!-- #endif -->
      </view>
      <view class="camera-placeholder" v-else @click="toggleCamera">
        <uni-icons type="videocam" size="48" color="#999"></uni-icons>
        <text>点击开启摄像头</text>
      </view>

      <!-- 音量指示器 -->
      <view class="volume-indicator" v-if="isRecording">
        <view class="volume-bar" :style="{ width: volume + '%' }"></view>
        <text class="volume-text">{{ isSpeaking ? '说话中...' : '聆听中...' }}</text>
      </view>
    </view>

    <!-- 对话区域 -->
    <scroll-view class="chat-section" scroll-y :scroll-top="chatScrollTop">
      <view class="chat-list">
        <view v-for="(msg, index) in messages" :key="index" :class="['chat-item', msg.role]">
          <view class="avatar">
            <uni-icons :type="msg.role === 'assistant' ? 'staff' : 'person'" size="24" color="#fff"></uni-icons>
          </view>
          <view class="content">
            <text class="text">{{ msg.content }}</text>
            <text class="time">{{ formatTime(msg.timestamp) }}</text>
          </view>
        </view>

        <!-- AI 思考中 -->
        <view class="chat-item assistant thinking" v-if="aiState === 'thinking'">
          <view class="avatar">
            <uni-icons type="staff" size="24" color="#fff"></uni-icons>
          </view>
          <view class="content">
            <view class="thinking-dots">
              <text>思考中</text>
              <text class="dot">.</text>
              <text class="dot">.</text>
              <text class="dot">.</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 控制按钮区 -->
    <view class="control-section">
      <button
        class="control-btn"
        :class="isRecording ? 'recording' : ''"
        @touchstart="startSpeaking"
        @touchend="stopSpeaking"
        @mousedown="startSpeaking"
        @mouseup="stopSpeaking"
        @mouseleave="stopSpeaking"
      >
        <uni-icons :type="isRecording ? 'mic-filled' : 'mic'" size="32" color="#fff"></uni-icons>
        <text>{{ isRecording ? '松开结束' : '按住说话' }}</text>
      </button>

      <view class="action-buttons">
        <button class="action-btn" @click="toggleCamera">
          <uni-icons :type="isCameraOn ? 'videocam' : 'videocam-slash'" size="20"></uni-icons>
          <text>{{ isCameraOn ? '关闭' : '开启' }}</text>
        </button>

        <button class="action-btn" @click="togglePause">
          <uni-icons :type="isPaused ? 'play' : 'pause'" size="20"></uni-icons>
          <text>{{ isPaused ? '继续' : '暂停' }}</text>
        </button>

        <button class="action-btn danger" @click="confirmEnd">
          <uni-icons type="close" size="20" color="#fff"></uni-icons>
          <text>结束</text>
        </button>
      </view>
    </view>

    <!-- 连接按钮 (未连接时显示) -->
    <view class="connect-overlay" v-if="!wsConnected">
      <button class="connect-btn" @click="connectWebSocket" :loading="isConnecting">
        <uni-icons type="refresh" size="24" color="#fff"></uni-icons>
        <text>开始面试</text>
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user.js'
import { WS_URL } from '@/config/index.js'

// 引入 composables
import { useAudioRecorder } from '@/composables/useAudioRecorder.js'
import { useAudioPlayer } from '@/composables/useAudioPlayer.js'
import { useVideoCapture } from '@/composables/useVideoCapture.js'

const userStore = useUserStore()

// ===== 状态 =====
const wsConnected = ref(false)
const isConnecting = ref(false)
const ws = ref(null)

const sessionId = computed(() => userStore.sessionId || '')
const token = computed(() => userStore.access || '')

const messages = ref([])
const chatScrollTop = ref(0)

const interviewTimer = ref(0)
const timerInterval = ref(null)

const aiState = ref('') // listening, thinking, speaking
const isPaused = ref(false)
const isCameraOn = ref(false)

// ===== Composables =====
const { isRecording, volume, isSpeaking, startRecording, stopRecording } = useAudioRecorder({
  onFrame: handleAudioFrame,
  onError: handleAudioError
})

const { isPlaying, interrupt, queueAudio } = useAudioPlayer({
  onPlayStart: () => console.log('AI 开始说话'),
  onPlayEnd: () => console.log('AI 说话结束')
})

const { startCapture, stopCapture, setOnFrame: setVideoFrameCallback } = useVideoCapture({
  frameInterval: 2000,
  onFrame: handleVideoFrame
})

// ===== 计算属性 =====
const formattedTime = computed(() => {
  const mins = Math.floor(interviewTimer.value / 60)
  const secs = interviewTimer.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

const aiStateText = computed(() => {
  const map = {
    'listening': '聆听中',
    'thinking': '思考中',
    'speaking': '说话中'
  }
  return map[aiState.value] || ''
})

// ===== WebSocket =====
const connectWebSocket = async () => {
  if (wsConnected.value || isConnecting.value) return

  isConnecting.value = true

  const wsUrl = `${WS_URL}/realtime/${sessionId.value}?token=${encodeURIComponent(token.value)}`

  try {
    ws.value = uni.connectSocket({
      url: wsUrl,
      success: () => console.log('WebSocket 连接中...'),
      fail: (err) => {
        console.error('WebSocket 连接失败', err)
        isConnecting.value = false
        uni.showToast({ title: '连接失败', icon: 'none' })
      }
    })

    ws.value.onOpen(() => {
      console.log('WebSocket 连接成功')
      wsConnected.value = true
      isConnecting.value = false
      startTimer()

      // 发送开始消息
      sendMessage({
        type: 'start',
        timestamp: Date.now()
      })
    })

    ws.value.onMessage((res) => {
      handleWebSocketMessage(JSON.parse(res.data))
    })

    ws.value.onError((err) => {
      console.error('WebSocket 错误', err)
      wsConnected.value = false
      isConnecting.value = false
    })

    ws.value.onClose(() => {
      console.log('WebSocket 关闭')
      wsConnected.value = false
      stopTimer()
      stopRecording()
      stopCapture()
    })

  } catch (err) {
    console.error('创建 WebSocket 失败', err)
    isConnecting.value = false
  }
}

const sendMessage = (data) => {
  if (ws.value && wsConnected.value) {
    ws.value.send({ data: JSON.stringify(data) })
  }
}

const handleWebSocketMessage = (data) => {
  console.log('收到消息', data)

  switch (data.type) {
    case 'connected':
      uni.showToast({ title: '已连接', icon: 'success' })
      break

    case 'audio':
      // AI 语音输出
      if (!isRecording.value) { // 用户没在说话时播放
        queueAudio(data.data, data.sample_rate || 24000)
      }
      break

    case 'text_delta':
      // 实时文本 (可选显示)
      break

    case 'question':
      // AI 完整问题
      messages.value.push({
        role: 'assistant',
        content: data.text,
        timestamp: Date.now()
      })
      scrollToBottom()
      break

    case 'speech_started':
      // 用户开始说话，打断 AI
      interrupt()
      break

    case 'status':
      aiState.value = data.state
      break

    case 'info':
      uni.showToast({ title: data.message, icon: 'none' })
      break

    case 'end':
      uni.showModal({
        title: '面试结束',
        content: data.summary?.overall_evaluation || '面试已完成',
        showCancel: false,
        success: () => {
          uni.switchTab({ url: '/pages/report/report' })
        }
      })
      break

    case 'error':
      uni.showToast({ title: data.error, icon: 'none' })
      break

    case 'pong':
      // 心跳响应
      break
  }
}

// ===== 音频处理 =====
function handleAudioFrame(base64Data, info) {
  if (!wsConnected.value || isPaused.value) return

  sendMessage({
    type: 'audio',
    data: base64Data,
    timestamp: info.timestamp,
    volume: info.volume
  })
}

function handleAudioError(err) {
  console.error('音频错误', err)
  uni.showToast({ title: '麦克风错误', icon: 'none' })
}

// ===== 视频处理 =====
function handleVideoFrame(base64Data, info) {
  if (!wsConnected.value || isPaused.value) return

  sendMessage({
    type: 'video',
    data: base64Data,
    timestamp: info.timestamp
  })
}

// ===== 用户交互 =====
const startSpeaking = () => {
  if (!wsConnected.value || isPaused.value) return

  startRecording()
}

const stopSpeaking = () => {
  stopRecording()
}

const toggleCamera = async () => {
  if (isCameraOn.value) {
    stopCapture()
    isCameraOn.value = false
  } else {
    const success = await startCapture()
    if (success) {
      isCameraOn.value = true
    }
  }
}

const togglePause = () => {
  isPaused.value = !isPaused.value
  sendMessage({ type: isPaused.value ? 'pause' : 'resume' })
}

const confirmEnd = () => {
  uni.showModal({
    title: '结束面试',
    content: '确定要结束本次面试吗？',
    success: (res) => {
      if (res.confirm) {
        endInterview()
      }
    }
  })
}

const endInterview = () => {
  sendMessage({ type: 'end' })

  if (ws.value) {
    ws.value.close()
  }
}

// ===== 工具方法 =====
const startTimer = () => {
  if (timerInterval.value) clearInterval(timerInterval.value)
  timerInterval.value = setInterval(() => {
    interviewTimer.value++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

const scrollToBottom = () => {
  setTimeout(() => {
    chatScrollTop.value = messages.value.length * 1000
  }, 100)
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
}

// ===== 生命周期 =====
onShow(() => {
  // 页面显示时
})

onHide(() => {
  // 页面隐藏时
  if (ws.value && wsConnected.value) {
    ws.value.close()
  }
})

onUnmounted(() => {
  stopTimer()
  stopRecording()
  stopCapture()
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style lang="scss" scoped>
.interview-realtime-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

// 状态栏
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 24rpx;
  background: #fff;
  border-bottom: 1rpx solid #e5e5e5;

  .status-item {
    display: flex;
    align-items: center;
    gap: 8rpx;

    text {
      font-size: 24rpx;
      color: #666;

      &.connected {
        color: #10b981;
      }

      &.disconnected {
        color: #ef4444;
      }
    }

    .ai-state {
      color: #3964fe;
      font-weight: 500;
    }
  }
}

// 视频区
.video-section {
  position: relative;
  height: 400rpx;
  background: #000;

  .camera-container,
  .camera-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .camera-placeholder {
    flex-direction: column;
    gap: 16rpx;
    color: #999;

    text {
      font-size: 28rpx;
    }
  }

  .camera {
    width: 100%;
    height: 100%;
  }

  .volume-indicator {
    position: absolute;
    bottom: 20rpx;
    left: 20rpx;
    right: 20rpx;
    height: 40rpx;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 20rpx;
    overflow: hidden;
    display: flex;
    align-items: center;

    .volume-bar {
      height: 100%;
      background: linear-gradient(90deg, #10b981, #34d399);
      transition: width 0.1s;
    }

    .volume-text {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      color: #fff;
      font-size: 22rpx;
    }
  }
}

// 对话区
.chat-section {
  flex: 1;
  padding: 20rpx;
  overflow-y: auto;

  .chat-list {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
  }

  .chat-item {
    display: flex;
    gap: 16rpx;
    max-width: 80%;

    &.user {
      align-self: flex-end;
      flex-direction: row-reverse;

      .content {
        background: #3964fe;
        color: #fff;
      }
    }

    &.assistant {
      align-self: flex-start;

      .content {
        background: #fff;
      }
    }

    &.thinking {
      .content {
        background: #f0f0f0;
      }
    }

    .avatar {
      width: 72rpx;
      height: 72rpx;
      border-radius: 36rpx;
      background: #3964fe;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .content {
      padding: 20rpx 24rpx;
      border-radius: 16rpx;
      font-size: 28rpx;
      line-height: 1.6;
      color: #333;

      .time {
        display: block;
        margin-top: 8rpx;
        font-size: 20rpx;
        color: #999;
      }
    }

    .thinking-dots {
      display: flex;
      align-items: center;
      gap: 4rpx;

      .dot {
        animation: blink 1.4s infinite;

        &:nth-child(2) {
          animation-delay: 0.2s;
        }

        &:nth-child(3) {
          animation-delay: 0.4s;
        }
      }
    }
  }
}

@keyframes blink {
  0%, 60%, 100% {
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
}

// 控制区
.control-section {
  padding: 24rpx;
  background: #fff;
  border-top: 1rpx solid #e5e5e5;

  .control-btn {
    width: 200rpx;
    height: 200rpx;
    border-radius: 100rpx;
    background: #3964fe;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12rpx;
    margin: 0 auto 24rpx;

    &.recording {
      background: #ef4444;
      animation: pulse 1s infinite;
    }

    text {
      color: #fff;
      font-size: 24rpx;
    }
  }

  .action-buttons {
    display: flex;
    justify-content: center;
    gap: 32rpx;

    .action-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8rpx;
      padding: 16rpx 32rpx;
      background: #f5f5f5;
      border-radius: 12rpx;

      &.danger {
        background: #ef4444;

        text {
          color: #fff;
        }
      }

      text {
        font-size: 22rpx;
        color: #666;
      }
    }
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

// 连接遮罩
.connect-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  .connect-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16rpx;
    padding: 48rpx 64rpx;
    background: #3964fe;
    border-radius: 24rpx;

    text {
      color: #fff;
      font-size: 32rpx;
      font-weight: 500;
    }
  }
}
</style>
