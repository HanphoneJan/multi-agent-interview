<template>
  <WebNavbar>
    <!-- 骨架屏 -->
    <HomeSkeleton v-if="loading" />

    <!-- 主内容 -->
    <template v-else>
      <!-- 主容器 -->
      <view class="main-container">

        <!-- 主要内容区 -->
        <view class="content-wrapper">

          <!-- 欢迎语区域 -->
          <WelcomeSection
            :last-interview-type="lastInterviewType"
            @continue="goToInterview"
            @start="goToInterview"
            @login="goToLogin"
          />

          <!-- 数据看板（仅登录用户显示） -->
          <StatsCard
            v-if="userStore.isLoggedIn"
            :total-interviews="totalInterviews"
            :average-score="averageScore"
            :score-trend="scoreTrend"
            :completion-rate="completionRate"
          />

          <!-- 推荐区域 -->
          <view v-if="userStore.major" class="recommend-section">
            <text class="recommend-title">
              根据你的专业【{{ userStore.major }}】，为你推荐：
            </text>
            <view class="recommend-tags">
              <view
                v-for="(rec, index) in recommendedJobs"
                :key="index"
                class="recommend-tag"
                @click="goToTagInterview(rec)"
              >
                {{ rec }}
              </view>
            </view>
          </view>

          <!-- 四大核心功能模块 -->
          <view class="features-section">
            <text class="section-title">核心功能</text>

            <!-- 主功能卡片：智能面试 -->
            <view class="feature-card main" @click="handleCardClick(goToInterview)">
              <view class="card-badge hot">HOT</view>
              <view class="card-icon large">
                <text class="fa-solid fa-microphone-lines fa-icon"></text>
              </view>
              <view class="card-content">
                <text class="card-title">智能面试</text>
              </view>
              <text class="fa-solid fa-chevron-right card-arrow main-arrow"></text>
            </view>

            <!-- 次要功能卡片网格 -->
            <view class="feature-grid">
              <view class="feature-card secondary" @click="handleCardClick(goToQuestionBank)">
                <view class="card-icon">
                  <text class="fa-solid fa-book-open fa-icon"></text>
                </view>
                <text class="card-title">面试题库</text>
              </view>

              <view class="feature-card secondary" @click="handleCardClick(goToFeedback)">
                <view class="card-icon">
                  <text class="fa-solid fa-clipboard-check fa-icon"></text>
                </view>
                <text class="card-title">面试反馈</text>
              </view>
            </view>

            <!-- 底部功能卡片：简历优化 -->
            <view class="feature-card bottom" @click="handleCardClick(goToResume)">
              <view class="card-icon">
                <text class="fa-solid fa-file-lines fa-icon"></text>
              </view>
              <view class="card-content">
                <text class="card-title">简历优化</text>
                <text class="card-desc">AI 智能简历诊断与优化建议</text>
              </view>
              <text class="fa-solid fa-chevron-right card-arrow bottom-arrow"></text>
            </view>
          </view>

          <!-- 左右滑动功能卡片（移动端） -->
          <swiper
            v-if="!isPC"
            class="feature-swiper"
            indicator-dots
            circular
            autoplay
            interval="5000"
          >
            <swiper-item v-for="(feature, index) in swiperFeatures" :key="index">
              <view class="swiper-card" @click="handleCardClick(feature.action)">
                <text :class="['fa-solid', feature.iconClass, 'swiper-icon']"></text>
                <text class="swiper-title">{{ feature.title }}</text>
                <text class="swiper-desc">{{ feature.desc }}</text>
              </view>
            </swiper-item>
          </swiper>
        </view>
      </view>

    </template>

    <!-- 首次引导浮层 -->
    <FirstTimeGuide @close="onGuideClose" />
  </WebNavbar>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import WebNavbar from '@/components/WebNavbar.vue'
import HomeSkeleton from '@/components/HomeSkeleton.vue'
import StatsCard from '@/components/StatsCard.vue'
import WelcomeSection from '@/components/WelcomeSection.vue'
import FirstTimeGuide from '@/components/FirstTimeGuide.vue'
import { ENDPOINTS } from '@/stores/api.js'
import { http } from '@/stores/request.js'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user.js'

const userStore = useUserStore()

// 响应式数据
const loading = ref(true)

// 用户数据
const totalInterviews = ref(0)
const averageScore = ref(0)
const scoreTrend = ref(0)
const completionRate = ref(0)
const lastInterviewType = ref('')

// 推荐岗位（从后端API获取）
const recommendedJobs = ref([])

// 获取推荐岗位
const fetchRecommendedJobs = async () => {
  if (!userStore.isLoggedIn) {
    recommendedJobs.value = ['产品经理', '运营专员', '市场营销']
    return
  }
  try {
    const data = await http.get(ENDPOINTS.recommendation.jobs)
    recommendedJobs.value = data.jobs || []
  } catch (error) {
    console.error('获取推荐岗位失败:', error)
    // 降级到默认推荐
    recommendedJobs.value = ['产品经理', '运营专员', '市场营销']
  }
}

// PC 端判断
const isPC = computed(() => {
  // #ifdef H5
  return window.innerWidth > 768
  // #endif
  return false
})

// 触觉反馈 + 导航
const handleCardClick = (navigateFn) => {
  // 触觉反馈
  // #ifdef APP-PLUS
  uni.vibrateShort({ type: 'light' })
  // #endif
  navigateFn()
}

// 导航方法
const goToInterview = () => {
  uni.navigateTo({ url: '/pages/interview/select' })
}

const goToQuestionBank = () => {
  uni.navigateTo({ url: '/pages/learn/resources' })
}

const goToFeedback = () => {
  uni.switchTab({ url: '/pages/report/report' })
}

const goToResume = () => {
  uni.navigateTo({ url: '/pages/resume/resume' })
}

const goToTagInterview = (tag) => {
  uni.navigateTo({ url: `/pages/interview/select?tag=${encodeURIComponent(tag)}` })
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}

// 轮播功能列表（必须在导航函数之后定义）
const swiperFeatures = [
  { iconClass: 'fa-microphone-lines', title: '智能面试', desc: 'AI 模拟真实面试', action: () => goToInterview() },
  { iconClass: 'fa-book-open', title: '面试题库', desc: '2000+ 真题练习', action: () => goToQuestionBank() },
  { iconClass: 'fa-clipboard-check', title: '面试反馈', desc: '查看历史与分析', action: () => goToFeedback() },
  { iconClass: 'fa-file-lines', title: '简历优化', desc: 'AI 智能诊断', action: () => goToResume() }
]

const onGuideClose = () => {
  console.log('引导已完成')
}

// 获取用户信息
const fetchUserInfo = async () => {
  if (!userStore.isLoggedIn) {
    loading.value = false
    return
  }

  try {
    const data = await http.get(ENDPOINTS.user.profile)

    // 更新用户存储
    userStore.username = data.username || userStore.username
    userStore.name = data.name || userStore.name
    userStore.avatarUrl = data.avatar_url || userStore.avatarUrl
    userStore.major = data.major || userStore.major

    // 从后端获取统计数据
    totalInterviews.value = data.total_interviews || 0
    averageScore.value = data.average_score || 0
    scoreTrend.value = data.score_trend || 0
    completionRate.value = data.completion_rate || 0
    lastInterviewType.value = data.last_interview_type || ''

  } catch (error) {
    console.error('获取用户信息失败:', error)
  } finally {
    loading.value = false
  }

  // 获取推荐岗位
  await fetchRecommendedJobs()
}

// 生命周期
onShow(() => {
  fetchUserInfo()
})

onMounted(() => {
  // 模拟加载延迟，展示骨架屏效果
  setTimeout(() => {
    if (!userStore.isLoggedIn) {
      loading.value = false
    }
  }, 800)
})
</script>

<style lang="css" scoped>
.main-container {
  padding: 20px;
  min-height: 100vh;
  background-color: var(--bg-page);
  position: relative;
  overflow-x: hidden;
  z-index: 1;
}

/* 推荐区域 */
.recommend-section {
  background: var(--bg-card);
  border-radius: 16rpx;
  padding: 28rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.recommend-title {
  display: block;
  font-size: 26rpx;
  color: var(--text-secondary);
  margin-bottom: 20rpx;
  line-height: 1.4;
}

.recommend-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.recommend-tag {
  padding: 12rpx 24rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary));
  color: var(--bg-card);
  border-radius: 32rpx;
  font-size: 24rpx;
  transition: all 0.3s;
}

.recommend-tag:active {
  transform: scale(0.95);
  opacity: 0.9;
}

/* 功能模块区域 */
.features-section {
  margin-bottom: 30rpx;
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 20rpx;
  padding-left: 4rpx;
}

/* 功能卡片通用样式 */
.feature-card {
  background: var(--bg-card);
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.feature-card:active {
  transform: scale(0.98);
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.feature-card.main {
  display: flex;
  align-items: center;
  gap: 28rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary));
  color: var(--bg-card);
  min-height: 180rpx;
}

.feature-card.main .card-title,
.feature-card.main .card-desc {
  color: var(--bg-card);
}

.feature-card.main .card-icon {
  background: rgba(255, 255, 255, 0.2);
}

.feature-card.main .fa-icon {
  color: var(--bg-card);
}

.card-badge {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.card-badge.hot {
  background: var(--color-error);
  color: var(--bg-card);
}

.card-badge.new {
  background: var(--color-success);
  color: var(--bg-card);
}

.card-badge.limited {
  background: var(--color-warning);
  color: var(--text-inverse);
}

.card-icon {
  width: 100rpx;
  height: 100rpx;
  background: var(--bg-card);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
}

.fa-icon {
  font-size: 48rpx;
  color: var(--color-primary);
}

.card-icon.large .fa-icon {
  font-size: 56rpx;
}

.card-icon.large {
  width: 120rpx;
  height: 120rpx;
}


.card-content {
  flex: 1;
}

.card-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 12rpx;
}

.card-desc {
  display: block;
  font-size: 26rpx;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 箭头图标样式 */
.card-arrow {
  font-size: 28rpx;
  opacity: 0.9;
}

/* 主卡片箭头 - 白色（蓝色背景） */
.main-arrow {
  color: var(--bg-card);
}

/* 底部卡片箭头 - 主色调（浅色背景） */
.bottom-arrow {
  color: var(--color-primary);
}

/* 功能网格 */
.feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.feature-card.secondary {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32rpx 24rpx;
  min-height: 220rpx;
  justify-content: center;
}

.feature-card.secondary .card-icon {
  margin-bottom: 20rpx;
}

.feature-card.secondary .card-title {
  font-size: 28rpx;
}

.feature-card.secondary .card-desc {
  font-size: 22rpx;
}

.feature-card.bottom {
  display: flex;
  align-items: center;
  gap: 28rpx;
  background: linear-gradient(135deg, rgba(57, 100, 254, 0.06), rgba(103, 158, 254, 0.1));
  border: 2rpx solid rgba(57, 100, 254, 0.15);
  min-height: 140rpx;
}

.feature-card.bottom .card-title {
  color: var(--color-primary);
}

.feature-card.bottom .card-desc {
  color: var(--text-secondary);
}

/* 轮播卡片（移动端） */
.feature-swiper {
  height: 300rpx;
  margin-bottom: 40rpx;
}

.swiper-card {
  height: 100%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary));
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 20rpx;
}

.swiper-icon {
  font-size: 64rpx;
  color: var(--bg-card);
  margin-bottom: 16rpx;
}

.swiper-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
}

.swiper-desc {
  font-size: 24rpx;
  opacity: 0.9;
}

/* 响应式适配 */
@media (min-width: 768px) {
  .main-container {
    max-width: 800px;
    margin: 0 auto;
  }

  .feature-swiper {
    display: none;
  }
}

@media (max-width: 768px) {
  .recommend-section {
    padding: 24rpx;
  }

  .feature-grid {
    gap: 12rpx;
  }

  .feature-card {
    padding: 24rpx;
    margin-bottom: 16rpx;
  }

  .feature-card.main {
    min-height: 160rpx;
    gap: 20rpx;
  }

  .feature-card.secondary {
    min-height: 180rpx;
    padding: 24rpx 16rpx;
  }

  .feature-card.bottom {
    min-height: 120rpx;
    gap: 20rpx;
  }

  .card-icon {
    width: 72rpx;
    height: 72rpx;
  }

  .card-icon.large {
    width: 96rpx;
    height: 96rpx;
  }

  .fa-icon {
    font-size: 40rpx;
  }

  .card-icon.large .fa-icon {
    font-size: 48rpx;
  }

  .card-title {
    font-size: 28rpx;
    margin-bottom: 8rpx;
  }

  .card-desc {
    font-size: 22rpx;
  }

  .section-title {
    font-size: 30rpx;
    margin-bottom: 16rpx;
  }
}

/* 深色模式适配 */
@media (prefers-color-scheme: dark) {
  .main-container {
    background-color: #263238;
  }

  .feature-card,
  .recommend-section {
    background: #37474F;
  }

  .section-title,
  .card-title {
    color: #fff;
  }

  .card-desc,
  .recommend-title {
    color: #B0BEC5;
  }
}
</style>
