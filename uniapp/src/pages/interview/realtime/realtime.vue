<template>
  <!-- H5 环境 -->
  <!-- #ifdef H5 -->
  <RealtimeInterviewH5
    v-if="sessionId && token"
    :session-id="sessionId"
    :token="token"
    :user-info="userInfo"
  />
  <view v-else class="loading-container">
    <text class="loading-text">加载中...</text>
  </view>
  <!-- #endif -->

  <!-- 小程序环境 -->
  <!-- #ifdef MP -->
  <RealtimeInterviewMP
    v-if="sessionId && token"
    :session-id="sessionId"
    :token="token"
    :user-info="userInfo"
  />
  <view v-else class="loading-container">
    <text class="loading-text">加载中...</text>
  </view>
  <!-- #endif -->
</template>

<script setup lang="ts">
/**
 * 实时面试入口页面
 * 根据平台（H5/小程序）加载对应的实现
 */
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import RealtimeInterviewH5 from '../realtime-h5/RealtimeInterview.vue'
import RealtimeInterviewMP from '../realtime-mp/RealtimeInterview.vue'

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

// 会话信息
const sessionId = ref('')
const token = ref('')
const userInfo = ref<UserInfo>({})

// 页面加载
onLoad((options) => {
  const id = options?.id
  if (!id) {
    uni.showToast({ title: '缺少会话ID', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 1500)
    return
  }

  sessionId.value = id
  token.value = uni.getStorageSync('access_token')

  if (!token.value) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    uni.redirectTo({ url: '/pages/login/login' })
    return
  }

  // 加载用户信息
  loadUserInfo()
})

// 加载用户信息
const loadUserInfo = () => {
  const userStore = uni.getStorageSync('userInfo')
  if (userStore) {
    try {
      const parsed = JSON.parse(userStore)
      userInfo.value = {
        name: parsed.name || parsed.username,
        username: parsed.username,
        university: parsed.university,
        major: parsed.major,
        gender: parsed.gender,
        learningStage: parsed.learning_stage || parsed.learningStage,
        access: token.value,
        sessionId: sessionId.value
      }
    } catch (e) {
      console.error('解析用户信息失败:', e)
    }
  }
}
</script>

<style scoped>
.loading-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 32rpx;
  color: #666;
}
</style>
