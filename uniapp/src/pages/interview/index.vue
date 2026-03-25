<template>
  <view class="interview-entry">
    <view class="loading-container">
      <text class="loading-text">正在进入面试...</text>
      <view class="loading-spinner"></view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 面试入口页面
 * 根据 scenario.is_realtime 自动跳转到对应面试页面
 */
import { onLoad } from '@dcloudio/uni-app';
import { useInterviewBase } from '@/composables/interview/useInterviewBase';

const { showError } = useInterviewBase();

onLoad((options) => {
  const sessionId = options?.id;

  if (!sessionId) {
    showError('缺少会话ID');
    setTimeout(() => uni.navigateBack(), 1500);
    return;
  }

  // 获取 session 详情，判断面试类型
  loadSessionAndRedirect(parseInt(sessionId));
});

/**
 * 获取会话信息并跳转
 */
const loadSessionAndRedirect = async (sessionId: number) => {
  try {
    const token = uni.getStorageSync('access_token');
    if (!token) {
      showError('请先登录');
      uni.redirectTo({ url: '/pages/login/login' });
      return;
    }

    // 获取 session 详情
    const res = await uni.request({
      url: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/interviews/sessions/${sessionId}`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
    }) as any;

    if (res.statusCode !== 200 || !res.data) {
      throw new Error('获取会话信息失败');
    }

    const session = res.data;
    const isRealtime = session.scenario?.is_realtime ?? true;

    // 根据类型跳转
    if (isRealtime) {
      console.log('[InterviewEntry] 实时面试，跳转到 realtime 页面');
      uni.redirectTo({
        url: `/pages/interview/realtime/realtime?id=${sessionId}`
      });
    } else {
      console.log('[InterviewEntry] 传统面试，跳转到 classic 页面');
      uni.redirectTo({
        url: `/pages/interview/classic/classic?id=${sessionId}`
      });
    }

  } catch (err) {
    console.error('加载会话失败:', err);
    showError('加载面试信息失败');
    setTimeout(() => uni.navigateBack(), 1500);
  }
};
</script>

<style>
.interview-entry {
  min-height: 100vh;
  background: var(--bg-color, #f5f5f5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
}

.loading-text {
  font-size: 32rpx;
  color: var(--text-secondary, #666);
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #e0e0e0;
  border-top-color: var(--primary-color, #3964fe);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
