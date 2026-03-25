<template>
  <view v-if="visible" class="guide-overlay" @click="handleSkip">
    <!-- 高亮区域（通过绝对定位覆盖在目标元素上） -->
    <view class="highlight-area" :style="highlightStyle" @click.stop>
      <view class="pulse-ring"></view>
    </view>

    <!-- 引导内容 -->
    <view class="guide-content" :style="contentStyle" @click.stop>
      <view class="guide-card">
        <text class="guide-title">{{ currentStep.title }}</text>
        <text class="guide-desc">{{ currentStep.description }}</text>
        <view class="guide-actions">
          <text class="skip-text" @click="handleSkip">跳过引导</text>
          <button class="next-btn" @click="handleNext">
            {{ isLastStep ? '开始使用' : '下一步' }}
          </button>
        </view>
        <view class="step-dots">
          <view
            v-for="(step, index) in steps"
            :key="index"
            class="dot"
            :class="{ active: currentStepIndex === index }"
          />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  showGuide: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['close']);

const visible = ref(false);
const currentStepIndex = ref(0);

const steps = [
  {
    title: '欢迎来到 AI 面试助手',
    description: '这里是你提升面试能力的一站式平台，让 AI 帮你模拟真实面试场景。',
    highlight: { top: '100rpx', left: '20rpx', right: '20rpx', height: '300rpx' },
    position: 'bottom'
  },
  {
    title: '智能面试',
    description: '选择你想要的岗位，AI 面试官会根据你的简历和岗位需求进行个性化提问。',
    highlight: { top: '400rpx', left: '20rpx', width: '45%', height: '200rpx' },
    position: 'bottom'
  },
  {
    title: '面试资料',
    description: '海量面试题库和精选资料，帮你系统性地准备面试。',
    highlight: { top: '400rpx', right: '20rpx', width: '45%', height: '200rpx' },
    position: 'bottom'
  },
  {
    title: '能力提升',
    description: '通过数据分析了解自己的能力短板，针对性提升面试表现。',
    highlight: { top: '620rpx', left: '20rpx', right: '20rpx', height: '150rpx' },
    position: 'top'
  }
];

const currentStep = computed(() => steps[currentStepIndex.value]);
const isLastStep = computed(() => currentStepIndex.value === steps.length - 1);

// 高亮区域样式
const highlightStyle = computed(() => {
  const h = currentStep.value.highlight;
  return {
    top: h.top,
    left: h.left,
    right: h.right,
    width: h.width,
    height: h.height
  };
});

// 内容区域样式
const contentStyle = computed(() => {
  const position = currentStep.value.position;
  if (position === 'top') {
    return { bottom: '200rpx' };
  }
  return { top: '650rpx' };
});

const handleNext = () => {
  if (isLastStep.value) {
    handleSkip();
  } else {
    currentStepIndex.value++;
  }
};

const handleSkip = () => {
  visible.value = false;
  uni.setStorageSync('hasSeenGuide', true);
  emit('close');
};

onMounted(() => {
  // 检查是否是首次访问
  const hasSeenGuide = uni.getStorageSync('hasSeenGuide');
  if (!hasSeenGuide && props.showGuide) {
    setTimeout(() => {
      visible.value = true;
    }, 500);
  }
});
</script>

<style scoped>
.guide-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 9999;
}

.highlight-area {
  position: absolute;
  border-radius: 16rpx;
  box-shadow: 0 0 0 9999rpx rgba(0, 0, 0, 0.7);
  pointer-events: none;
}

.pulse-ring {
  position: absolute;
  top: -10rpx;
  left: -10rpx;
  right: -10rpx;
  bottom: -10rpx;
  border: 4rpx solid var(--color-primary);
  border-radius: 20rpx;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.1);
    opacity: 0;
  }
}

.guide-content {
  position: absolute;
  left: 40rpx;
  right: 40rpx;
}

.guide-card {
  background: var(--bg-card);
  border-radius: 16rpx;
  padding: 40rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.3);
}

.guide-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 16rpx;
}

.guide-desc {
  display: block;
  font-size: 26rpx;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 30rpx;
}

.guide-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skip-text {
  font-size: 26rpx;
  color: var(--text-tertiary);
  padding: 10rpx 20rpx;
}

.next-btn {
  padding: 16rpx 40rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary));
  color: white;
  border-radius: 32rpx;
  font-size: 28rpx;
  border: none;
  line-height: 1.5;
}

.step-dots {
  display: flex;
  justify-content: center;
  gap: 16rpx;
  margin-top: 30rpx;
}

.dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: var(--border-default);
  transition: all 0.3s;
}

.dot.active {
  width: 32rpx;
  background: var(--color-primary);
  border-radius: 6rpx;
}
</style>
