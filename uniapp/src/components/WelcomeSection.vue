<template>
  <view class="welcome-section">
    <!-- 已登录状态 -->
    <template v-if="userStore.isLoggedIn">
      <view class="welcome-header">
        <image
          class="user-avatar"
          :src="userStore.avatarUrl || '/static/default-avatar.png'"
          mode="aspectFill"
        />
        <view class="welcome-text">
          <text class="greeting">欢迎回来，{{ userStore.name || '用户' }}！</text>
          <text v-if="lastInterviewType" class="sub-text">
            继续完成上次的 {{ lastInterviewType }} 面试？
          </text>
          <text v-else class="sub-text">开始你的第一次 AI 面试之旅吧</text>
        </view>
      </view>
      <button
        v-if="lastInterviewType"
        class="continue-btn"
        @click="handleContinue"
      >
        继续面试
      </button>
      <button
        v-else
        class="continue-btn primary"
        @click="handleStart"
      >
        开始面试
      </button>
    </template>

    <!-- 未登录状态 -->
    <template v-else>
      <view class="welcome-header">
        <view class="welcome-text center">
          <text class="greeting">开启你的 AI 面试之旅</text>
          <text class="sub-text">已有 10,000+ 用户通过面试拿到 Offer</text>
        </view>
      </view>
      <button class="continue-btn primary" @click="handleLogin">
        立即登录
      </button>
    </template>
  </view>
</template>

<script setup>
import { useUserStore } from '@/stores/user.js';

const props = defineProps({
  lastInterviewType: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['continue', 'start', 'login']);

const userStore = useUserStore();

const handleContinue = () => {
  emit('continue');
};

const handleStart = () => {
  emit('start');
};

const handleLogin = () => {
  emit('login');
};
</script>

<style scoped>
.welcome-section {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary) 100%);
  border-radius: 16rpx;
  padding: 40rpx 30rpx;
  margin-bottom: 30rpx;
  color: white;
  box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.3);
}

.welcome-header {
  display: flex;
  align-items: center;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.user-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.welcome-text {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.welcome-text.center {
  align-items: center;
  text-align: center;
}

.greeting {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
}

.sub-text {
  font-size: 24rpx;
  opacity: 0.9;
}

.continue-btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2rpx solid rgba(255, 255, 255, 0.5);
  border-radius: 40rpx;
  font-size: 28rpx;
  font-weight: 600;
  transition: all 0.3s ease;
}

.continue-btn.primary {
  background: white;
  color: var(--color-primary);
  border: none;
}

.continue-btn:active {
  transform: scale(0.98);
  opacity: 0.9;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .welcome-section {
    padding: 30rpx 24rpx;
  }

  .user-avatar {
    width: 64rpx;
    height: 64rpx;
  }

  .greeting {
    font-size: 28rpx;
  }

  .sub-text {
    font-size: 22rpx;
  }

  .continue-btn {
    height: 72rpx;
    line-height: 72rpx;
    font-size: 26rpx;
  }
}
</style>
