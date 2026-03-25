<template>
  <view class="recording-indicator" :class="{ active: isRecording }">
    <view class="wave-container">
      <view
        v-for="i in 5"
        :key="i"
        class="wave-bar"
        :style="{ height: getBarHeight(i) }"
      ></view>
    </view>
    <text class="recording-text">{{ isRecording ? '正在聆听...' : '点击开始说话' }}</text>
    <text v-if="duration > 0" class="duration">{{ formattedDuration }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'

interface Props {
  isRecording: boolean
  audioLevel?: number // 0 - 1
  duration?: number // 秒数
}

const props = withDefaults(defineProps<Props>(), {
  audioLevel: 0,
  duration: 0
})

const localAudioLevel = ref(0)
let animationFrame: number | null = null

// 平滑音频级别
const smoothAudioLevel = () => {
  const target = props.audioLevel
  const current = localAudioLevel.value
  const diff = target - current
  localAudioLevel.value = current + diff * 0.1
  animationFrame = requestAnimationFrame(smoothAudioLevel)
}

onMounted(() => {
  smoothAudioLevel()
})

onUnmounted(() => {
  if (animationFrame) {
    cancelAnimationFrame(animationFrame)
  }
})

const getBarHeight = (index: number) => {
  if (!props.isRecording) return '20%'

  const baseHeight = 20 + (index % 2) * 20
  const levelBoost = localAudioLevel.value * 60
  const randomBoost = Math.sin(Date.now() / 200 + index) * 10

  return `${Math.min(100, Math.max(20, baseHeight + levelBoost + randomBoost))}%`
}

const formattedDuration = computed(() => {
  const mins = Math.floor(props.duration / 60)
  const secs = props.duration % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})
</script>

<style scoped>
.recording-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
  padding: 40rpx;
  background: #f5f5f5;
  border-radius: 20rpx;
  transition: all 0.3s ease;
}

.recording-indicator.active {
  background: rgba(57, 100, 254, 0.1);
}

.wave-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  height: 100rpx;
}

.wave-bar {
  width: 12rpx;
  background: var(--primary-color, #3964fe);
  border-radius: 6rpx;
  transition: height 0.1s ease;
  opacity: 0.5;
}

.recording-indicator.active .wave-bar {
  opacity: 1;
  animation: wave 0.5s ease-in-out infinite alternate;
}

.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }
.wave-bar:nth-child(4) { animation-delay: 0.3s; }
.wave-bar:nth-child(5) { animation-delay: 0.4s; }

@keyframes wave {
  from { transform: scaleY(0.8); }
  to { transform: scaleY(1.2); }
}

.recording-text {
  font-size: 28rpx;
  color: #666;
}

.recording-indicator.active .recording-text {
  color: var(--primary-color, #3964fe);
}

.duration {
  font-size: 24rpx;
  color: #999;
  font-family: monospace;
}
</style>
