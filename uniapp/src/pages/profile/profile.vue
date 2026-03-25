<template>
  <WebNavbar>
    <view class="container">
    <!-- 加载状态 -->
    <view v-if="loading" class="loading-container">
      <view class="loader"></view>
      <text class="loading-text">正在加载数据...</text>
    </view>
    
    <!-- 错误状态 -->
    <view v-else-if="error" class="error-container">
      <image class="error-icon" src="/static/icons/error.png"></image>
      <text class="error-text">数据加载失败，请稍后重试</text>
      <button class="retry-btn" @click="fetchUserInfo">重试</button>
    </view>
    
    <!-- 内容区域 -->
    <view v-else class="content">
      <!-- 顶部头像区域 -->
      <view class="header">
        <view class="avatar-container">
          <image class="avatar" :src="userInfo.avatarUrl || userInfo.avatar_url || 'https://hanphone.top/images/zhuxun.jpg'" mode="aspectFill"></image>
        </view>
        <text class="username">{{ userInfo.name || userInfo.username }}</text>
      </view>

      <!-- 信息卡片 -->
      <view class="card info-card">
        <view class="card-title">
          <text>个人信息</text>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/email.png"></image>
          <view class="info-content">
            <text class="info-label">邮箱</text>
            <text class="info-value">{{ userInfo.email }}</text>
          </view>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/phone.png"></image>
          <view class="info-content">
            <text class="info-label">电话</text>
            <text class="info-value">{{ userInfo.phone || '未填写' }}</text>
          </view>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/gender.png"></image>
          <view class="info-content">
            <text class="info-label">性别</text>
            <text class="info-value">{{ genderMap[userInfo.gender] || '未填写' }}</text>
          </view>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/ethnicity.png"></image>
          <view class="info-content">
            <text class="info-label">民族</text>
            <text class="info-value">{{ userInfo.ethnicity || '未填写' }}</text>
          </view>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/address.png"></image>
          <view class="info-content">
            <text class="info-label">城市</text>
            <text class="info-value">{{ userInfo.city || '未填写' }}</text>
          </view>
        </view>
      </view>

      <!-- 教育信息卡片 -->
      <view class="card info-card">
        <view class="card-title">
          <text>教育信息</text>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/university.png"></image>
          <view class="info-content">
            <text class="info-label">学校</text>
            <text class="info-value">{{ userInfo.university || '未填写' }}</text>
          </view>
        </view>
        
        <view class="info-item">
          <image class="info-icon" src="/static/profile/major.png"></image>
          <view class="info-content">
            <text class="info-label">专业</text>
            <text class="info-value">{{ userInfo.major || '未填写' }}</text>
          </view>
        </view>

         <view class="info-item">
          <image class="info-icon" src="/static/profile/stage.png"></image>
          <view class="info-content">
            <text class="info-label">学习阶段</text>
            <text class="info-value">{{  learningStageMap[userInfo.learningStage]  || '未填写' }}</text>
          </view>
        </view>
      </view>


      <!-- 操作按钮 -->
      <view class="action-buttons">
        <button class="edit-btn" @click="handleEdit">编辑资料</button>
      </view>
      <view class="action-buttons">
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </view>
    </view>
  </view>
  </WebNavbar>
</template>

<script setup>
import { ref} from 'vue'
import WebNavbar from '@/components/WebNavbar.vue'
import { useUserStore } from '@/stores/user.js'
import { useTokenRefresh } from '@/stores/useTokenRefresh'
const userStore = useUserStore();
import { onShow } from '@dcloudio/uni-app';
const { refreshToken } = useTokenRefresh()
import { ENDPOINTS } from '@/stores/api.js';
// 定义响应式数据
const userInfo = ref({})
const genderMap = {
  M: "男",
  F: "女",
  O: "其他"
}
const loading = ref(true)
const error = ref(false)
// 定义学习阶段映射关系
const learningStageMap = {
  'FRESHMAN_1': '大一上',
  'FRESHMAN_2': '大一下',
  'SOPHOMORE_1': '大二上',
  'SOPHOMORE_2': '大二下',
  'JUNIOR_1': '大三上',
  'JUNIOR_2': '大三下',
  'SENIOR_1': '大四上',
  'SENIOR_2': '大四下',
  'GRADUATE_STUDENT': '研究生',
  'JOB_SEEKER': '应届生',
  'EMPLOYED': '社会人士',
  'OTHER': '其他'
}

// 生命周期钩子替代onLoad
onShow(() => {
  if (!userStore.access && !userStore.refresh) {
    uni.showToast({
      title: '请先登录',
      icon: 'none',
      duration: 2000
    })
    uni.navigateTo({
      url: '/pages/login/login'
    })
  }

  refreshToken()
  fetchUserInfo()
})

// 定义方法
const fetchUserInfo = () => {
  loading.value = true
  error.value = false
  
  uni.request({
    url: ENDPOINTS.user.profile,
    method: 'GET',
    success: (res) => {      
      if (res.statusCode === 200) {
        userInfo.value = res.data
        
        if (!userInfo.value.username) {
          console.warn('用户数据缺少必要字段')
        }

        // 更新userStore
        userStore.username = userInfo.value.username || userStore.username
        userStore.userId = userInfo.value.userId || userStore.userId
        userStore.avatarUrl = userInfo.value.avatarUrl || userInfo.value.avatar_url || userStore.avatarUrl
        userStore.name = userInfo.value.name || userStore.name
        userStore.email = userInfo.value.email || userStore.email
        userStore.phone = userInfo.value.phone || userStore.phone
        userStore.age = userInfo.value.age || userStore.age
        userStore.gender = userInfo.value.gender || userStore.gender
        userStore.major = userInfo.value.major || userStore.major
        userStore.university = userInfo.value.university || userStore.university
        userStore.city = userInfo.value.city || userStore.city
        userStore.province = userInfo.value.province || userStore.province
        userStore.district = userInfo.value.district || userStore.district
        userStore.address = userInfo.value.address || userStore.address
        userStore.ethnicity = userInfo.value.ethnicity || userStore.ethnicity
        userStore.learningStage = userInfo.value.learningStage || userInfo.value.learning_stage || userStore.learningStage
        userStore.access = userInfo.value.access || userStore.access
        userStore.refresh = userInfo.value.refresh || userStore.refresh
        userStore.isLoggedIn = userInfo.value.isLoggedIn || userStore.isLoggedIn
        userStore.tokenExpire = userInfo.value.tokenExpire || userStore.tokenExpire
        userStore.isH5 = userInfo.value.isH5 || userStore.isH5
        userStore.platform = userInfo.value.platform || userStore.platform
        userStore.sessionId = userInfo.value.sessionId || userInfo.value.session_id || userStore.sessionId
        
      } else {
        console.error('获取用户信息失败:', res.errMsg || '未知错误')
        error.value = true
        // 从userStore获取信息
        userInfo.value = {
          username: userStore.username,
          userId: userStore.userId,
          name: userStore.name,
          email: userStore.email,
          phone: userStore.phone,
          age: userStore.age,
          gender: userStore.gender,
          major: userStore.major,
          university: userStore.university,
          address: userStore.address,
          ethnicity: userStore.ethnicity,
          learningStage: userStore.learningStage,
          avatarUrl: userStore.avatarUrl,
          access: userStore.access,
          refresh: userStore.refresh,
          isLoggedIn: userStore.isLoggedIn,
          tokenExpire: userStore.tokenExpire,
          isH5: userStore.isH5,
          platform: userStore.platform,
          sessionId: userStore.sessionId
        }
      }
    },
    fail: (err) => {
      console.error('请求失败:', err)
      error.value = true
      // 从userStore获取信息
      userInfo.value = {
        username: userStore.username,
        userId: userStore.userId,
        name: userStore.name,
        email: userStore.email,
        phone: userStore.phone,
        age: userStore.age,
        gender: userStore.gender,
        major: userStore.major,
        university: userStore.university,
        address: userStore.address,
        ethnicity: userStore.ethnicity,
        learningStage: userStore.learningStage,
        access: userStore.access,
        refresh: userStore.refresh,
        isLoggedIn: userStore.isLoggedIn,
        tokenExpire: userStore.tokenExpire,
        isH5: userStore.isH5,
        platform: userStore.platform,
        sessionId: userStore.sessionId
      }
    },
    complete: () => {
      loading.value = false
    }
  })
}

const handleEdit = () => {
  uni.navigateTo({
    url: '/pages/profile/edit'
  })
}


// 退出登录方法
const handleLogout = () => {
  uni.showModal({
    title: '确认退出',
    content: '您确定要退出当前账号吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.clearUser() // 清除用户状态
          uni.navigateTo({
          url: '/pages/index/index'
        })
        uni.showToast({
          title: '已退出登录',
          icon: 'success'
        })
      }
    }
  })
}
</script>

<style lang="css" scoped>
/* 通用样式 */
.container {
  padding: 20px;
  background-color: var(--bg-page);
  min-height: 100vh;
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

 .loader {
  width: 80rpx;
  height: 80rpx;
  border: 8rpx solid var(--color-neutral-200);
  border-top: 8rpx solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 30rpx;
}

.loading-text {
  font-size: 32rpx;
  color: var(--text-secondary);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误状态样式 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.error-icon {
  width: 160rpx;
  height: 160rpx;
  margin-bottom: 30rpx;
}

.error-text {
  font-size: 32rpx;
  color: var(--text-tertiary);
  margin-bottom: 40rpx;
}

.retry-btn {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--text-inverse);
  border: none;
  border-radius: 50rpx;
  height: 90rpx;
  line-height: 90rpx;
  font-size: 32rpx;
  width: 300rpx;
}

/* 内容区域样式 */
.content {
  min-height: 100vh;
}

/* 头部样式 */
.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: 0 0 20rpx 20rpx;
  margin-bottom: 20rpx;
  color: var(--text-inverse);
}

.avatar-container {
  width: 150rpx;
  height: 150rpx;
  border-radius: 50%;
  background-color: var(--bg-card);
  padding: 5rpx;
  margin-bottom: 20rpx;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.username {
  font-size: 40rpx;
  font-weight: bold;
  margin-bottom: 2rpx;
}


/* 卡片样式 */
.card {
  background-color: var(--bg-card);
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: var(--shadow-md);
}

.card-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 30rpx;
  color: var(--text-primary);
  position: relative;
  padding-left: 20rpx;
}

 .card-title::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 8rpx;
  height: 32rpx;
  background: linear-gradient(to bottom, var(--color-primary), var(--color-primary-light));
  border-radius: 4rpx;
}

/* 信息项样式 */
.info-item {
  display: flex;
  align-items: center;
  padding: 25rpx 0;
  border-bottom: 1rpx solid var(--border-default);
}

.info-item:last-child {
  border-bottom: none;
}

.info-icon {
  width: 40rpx;
  height: 40rpx;
  margin-right: 20rpx;
}

.info-content {
  flex: 1;
}

.info-label {
  font-size: 28rpx;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: 8rpx;
}

.info-value {
  font-size: 32rpx;
  color: var(--text-primary);
}


/* 按钮样式 */
.action-buttons {
  padding: 0 30rpx;
  margin-top: 40rpx;
}

.edit-btn {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--text-inverse);
  border: none;
  border-radius: 50rpx;
  height: 90rpx;
  line-height: 90rpx;
  font-size: 32rpx;
}

/* PC适配 */
@media (min-width: 768px) {
  .container {
    max-width: 600px;
    margin: 0 auto;
    padding: 40rpx;
  }

  .avatar-container {
    width: 180rpx;
    height: 180rpx;
  }
}

/* #ifdef MP-WEIXIN */
@media(max-width: 768px) {
  .container {
    margin-top:40px;
  }
}
/* #endif */
</style>
