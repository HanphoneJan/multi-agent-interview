<template>
  <view class="interview-status" :class="status">
    <view class="status-dot"></view>
    <text class="status-text">{{ statusText }}</text>
    <text v-if="duration" class="duration">{{ formattedDuration }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type InterviewStatus = 'idle' | 'connecting' | 'connected' | 'error' | 'ended' | 'paused'

interface Props {
  status: InterviewStatus
  duration?: number // 秒数
}

const props = withDefaults(defineProps<Props>(), {
  duration: 0
})

const statusText = computed(() => {
  switch (props.status) {
    case 'idle': return '准备中'
    case 'connecting': return '连接中...'
    case 'connected': return '面试中'
    case 'paused': return '已暂停'
    case 'error': return '连接异常'
    case 'ended': return '已结束'
    default: return '未知状态'
  }
})

const formattedDuration = computed(() => {
  const mins = Math.floor(props.duration / 60)
  const secs = props.duration % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})
</script>

<style scoped>
.interview-status {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 12rpx 24rpx;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 30rpx;
}

.status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #999;
}

.status-text {
  font-size: 26rpx;
  color: #666;
}

.duration {
  font-size: 24rpx;
  color: #999;
  padding-left: 12rpx;
  border-left: 2rpx solid #ddd;
}

/* 状态样式 */
.interview-status.connected .status-dot {
  background: #4caf50;
  animation: pulse 1.5s ease-in-out infinite;
}

.interview-status.connected .status-text {
  color: #4caf50;
}

.interview-status.connecting .status-dot {
  background: #ff9800;
  animation: blink 1s ease-in-out infinite;
}

.interview-status.connecting .status-text {
  color: #ff9800;
}

.interview-status.error .status-dot {
  background: #f44336;
}

.interview-status.error .status-text {
  color: #f44336;
}

.interview-status.paused .status-dot {
  background: #ff9800;
}

.interview-status.paused .status-text {
  color: #ff9800;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
