<template>
  <WebNavbar>
    <view class="report-page">
      <!-- 页面头部 -->
      <view class="page-header">
        <view class="header-content">
          <text class="page-title">面试反馈</text>
          <text class="page-subtitle">历史记录 · 能力评估 · 提升建议</text>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <view class="loader"></view>
        <text class="loading-text">正在加载数据...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="interviews.length === 0" class="empty-state">
        <text class="fa-solid fa-clipboard-list empty-icon"></text>
        <text class="empty-title">暂无面试记录</text>
        <text class="empty-desc">开始您的第一次面试，获取专业反馈</text>
        <button class="start-btn" @click="goToInterview">开始面试</button>
      </view>

      <!-- 主要内容 -->
      <view v-else class="content-wrapper">
        <!-- 统计卡片区域 -->
        <view class="stats-section">
          <view class="stats-row">
            <view class="stat-card">
              <text class="stat-value">{{ userStats.total_interviews || interviews.length }}</text>
              <text class="stat-label">总面试</text>
            </view>
            <view class="stat-card">
              <text class="stat-value">{{ completedCount }}</text>
              <text class="stat-label">已完成</text>
            </view>
            <view class="stat-card">
              <text class="stat-value">{{ formatScore(userStats.average_score) }}</text>
              <text class="stat-label">平均分</text>
            </view>
          </view>
        </view>

        <!-- 面试历史列表 -->
        <view class="history-section">
          <view class="section-header">
            <text class="section-title">面试历史</text>
            <view class="filter-tabs">
              <view
                v-for="tab in tabs"
                :key="tab.value"
                class="tab"
                :class="{ active: currentTab === tab.value }"
                @click="currentTab = tab.value"
              >
                {{ tab.label }}
              </view>
            </view>
          </view>

          <scroll-view scroll-y class="session-list" @scrolltolower="loadMore">
            <view
              v-for="session in filteredSessions"
              :key="session.id"
              class="session-item"
              :class="{ active: selectedSession?.id === session.id }"
              @click="selectSession(session)"
            >
              <view class="session-main">
                <view class="session-info">
                  <text class="scenario-name">{{ session.scenario_name || '未知场景' }}</text>
                  <view class="session-meta">
                    <text class="meta-item">
                      <text class="fa-solid fa-calendar meta-icon"></text>
                      {{ formatDate(session.start_time) }}
                    </text>
                    <text class="meta-item" v-if="session.overall_score">
                      <text class="fa-solid fa-star meta-icon score-icon"></text>
                      {{ session.overall_score }}分
                    </text>
                  </view>
                </view>
                <view class="status-badge" :class="session.status">
                  {{ statusText[session.status] }}
                </view>
              </view>
              <view class="session-action" v-if="selectedSession?.id === session.id">
                <text class="fa-solid fa-chevron-right action-icon"></text>
              </view>
            </view>

            <!-- 加载更多 -->
            <view v-if="loadingMore" class="loading-more">
              <text class="fa-solid fa-spinner fa-spin"></text>
              <text>加载中...</text>
            </view>
          </scroll-view>
        </view>

        <!-- 详细报告区域（选中某个面试后显示） -->
        <view v-if="selectedSession && selectedSession.has_evaluation" class="detail-section">
          <!-- 能力雷达图 -->
          <view class="detail-card">
            <view class="card-header">
              <text class="fa-solid fa-chart-radar card-icon"></text>
              <text class="card-title">能力评估</text>
            </view>
            <view class="chart-wrapper">
              <qiun-data-charts
                type="radar"
                :opts="radarOpts"
                :chartData="radarData"
              />
            </view>
          </view>

          <!-- 综合评估 -->
          <view class="detail-card">
            <view class="card-header">
              <text class="fa-solid fa-clipboard-check card-icon"></text>
              <text class="card-title">综合评估</text>
            </view>
            <view class="evaluation-content">
              <text class="evaluation-text">{{ selectedSession.evaluation?.overall_evaluation || '暂无综合评估' }}</text>
            </view>
          </view>

          <!-- 各项得分 -->
          <view class="detail-card" v-if="selectedSession.evaluation">
            <view class="card-header">
              <text class="fa-solid fa-list-check card-icon"></text>
              <text class="card-title">详细得分</text>
            </view>
            <view class="score-grid">
              <view class="score-item">
                <text class="score-name">专业知识</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.professional_knowledge) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">技能匹配</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.skill_match) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">语言表达</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.language_expression) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">逻辑思维</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.logical_thinking) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">压力应对</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.stress_response) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">性格</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.personality) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">动机</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.motivation) }}</text>
              </view>
              <view class="score-item">
                <text class="score-name">价值观</text>
                <text class="score-value">{{ formatScore(selectedSession.evaluation.value) }}</text>
              </view>
            </view>
          </view>

          <!-- 提升建议 -->
          <view class="detail-card">
            <view class="card-header">
              <text class="fa-solid fa-lightbulb card-icon"></text>
              <text class="card-title">提升建议</text>
            </view>
            <view class="suggestion-content">
              <text class="suggestion-text">{{ selectedSession.evaluation?.help || '暂无提升建议' }}</text>
            </view>
            <view class="learning-link" @click="goToLearning" v-if="selectedSession.evaluation?.help">
              <text class="link-text">根据建议，前往个性化学习</text>
              <text class="fa-solid fa-arrow-right link-icon"></text>
            </view>
          </view>

          <!-- 智能推荐 -->
          <view class="detail-card" v-if="ragRecommendations.length > 0">
            <view class="card-header">
              <text class="fa-solid fa-wand-magic-sparkles card-icon"></text>
              <text class="card-title">智能推荐</text>
              <text v-if="ragWeakAreas.length > 0" class="weak-areas">针对：{{ ragWeakAreas.join('、') }}</text>
            </view>
            <view class="recommend-list">
              <view
                v-for="(item, index) in ragRecommendations"
                :key="index"
                class="recommend-item"
                @click="goToResource(item)"
              >
                <view class="rec-header">
                  <text class="rec-name">{{ item.name }}</text>
                  <view class="rec-tags">
                    <text class="rec-tag" v-for="(tag, i) in item.tags.slice(0, 2)" :key="i">{{ tag }}</text>
                  </view>
                </view>
                <text class="rec-reason">{{ item.reason }}</text>
                <view class="rec-meta">
                  <text class="rec-type">{{ item.resource_type }}</text>
                  <text class="rec-difficulty" :class="'difficulty-' + item.difficulty">{{ item.difficulty }}</text>
                </view>
              </view>
            </view>
            <view class="overall-advice" v-if="ragOverallAdvice">
              <text class="advice-title">整体建议</text>
              <text class="advice-content">{{ ragOverallAdvice }}</text>
            </view>
          </view>
        </view>

        <!-- 未完成的面试提示 -->
        <view v-else-if="selectedSession && !selectedSession.has_evaluation" class="no-evaluation">
          <text class="fa-solid fa-clock no-eval-icon"></text>
          <text class="no-eval-title">评估报告生成中</text>
          <text class="no-eval-desc">面试结束后系统正在分析您的表现，请稍后再来查看</text>
        </view>
      </view>
    </view>
  </WebNavbar>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import WebNavbar from '@/components/WebNavbar.vue'
import { useUserStore } from '@/stores/user.js'
import { useTokenRefresh } from '@/stores/useTokenRefresh'
import { ENDPOINTS } from '@/stores/api.js'
import { http } from '@/stores/request.js'
import { onShow } from '@dcloudio/uni-app'

const userStore = useUserStore()
const { refreshToken } = useTokenRefresh()

// 加载状态
const loading = ref(true)
const loadingMore = ref(false)

// 统计数据
const userStats = ref({
  total_interviews: 0,
  completed_interviews: 0,
  average_score: null
})

// 面试列表数据
const interviews = ref([])
const selectedSession = ref(null)
const page = ref(1)
const pageSize = 10
const hasMore = ref(true)

// 筛选标签
const tabs = [
  { label: '全部', value: 'all' },
  { label: '已完成', value: 'completed' },
  { label: '进行中', value: 'active' }
]
const currentTab = ref('all')

// 状态文本映射
const statusText = {
  'active': '进行中',
  'paused': '已暂停',
  'completed': '已完成',
  'cancelled': '已取消',
  'pending': '待开始',
  'in_progress': '进行中'
}

// RAG 推荐
const ragRecommendations = ref([])
const ragWeakAreas = ref([])
const ragOverallAdvice = ref('')

// 计算属性：筛选后的会话
const filteredSessions = computed(() => {
  if (currentTab.value === 'all') return interviews.value
  if (currentTab.value === 'completed') {
    return interviews.value.filter(s => s.is_finished || s.status === 'completed')
  }
  if (currentTab.value === 'active') {
    return interviews.value.filter(s => s.status === 'in_progress' || s.status === 'paused' || s.status === 'active')
  }
  return interviews.value
})

// 已完成数量
const completedCount = computed(() => {
  return interviews.value.filter(s => s.is_finished || s.status === 'completed').length
})

// 雷达图配置
const radarOpts = ref({
  color: ['#1877F2'],
  padding: [5, 5, 5, 5],
  dataLabel: false,
  enableScroll: false,
  legend: { show: false },
  extra: {
    radar: {
      gridType: 'radar',
      gridColor: '#E1E5EA',
      gridCount: 5,
      opacity: 0.2,
      max: 100,
      labelShow: true,
      border: true,
      background: '#F5F6F7'
    }
  }
})

// 雷达图数据
const radarData = computed(() => {
  if (!selectedSession.value?.evaluation) return {}
  const eva = selectedSession.value.evaluation
  return {
    categories: ['专业知识', '技能匹配', '语言表达', '逻辑思维', '压力应对', '性格', '动机', '价值观'],
    series: [{
      name: '能力评估',
      data: [
        toScore(eva.professional_knowledge),
        toScore(eva.skill_match),
        toScore(eva.language_expression),
        toScore(eva.logical_thinking),
        toScore(eva.stress_response),
        toScore(eva.personality),
        toScore(eva.motivation),
        toScore(eva.value)
      ]
    }]
  }
})

// 转换为百分制分数
function toScore(value) {
  if (!value) return 0
  const num = parseFloat(value)
  if (num <= 10) return num * 10
  return num
}

// 格式化分数显示
function formatScore(score) {
  if (!score) return '-'
  const num = parseFloat(score)
  if (num > 10) return num.toFixed(1)
  return num.toFixed(1)
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return `今天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 获取统计数据
async function fetchStats() {
  try {
    const response = await http.get(ENDPOINTS.interview.userData)
    if (response) {
      userStats.value = response
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取面试列表
async function fetchInterviews(reset = false) {
  if (reset) {
    page.value = 1
    interviews.value = []
    hasMore.value = true
  }

  if (!hasMore.value && !reset) return

  try {
    const response = await http.get(ENDPOINTS.interview.sessions, {
      params: {
        skip: (page.value - 1) * pageSize,
        limit: pageSize
      }
    })

    const items = response.items || []

    // 处理每个会话，检查是否有评估数据
    for (const item of items) {
      if (item.is_finished || item.status === 'completed') {
        await fetchEvaluation(item)
      }
    }

    interviews.value.push(...items)
    hasMore.value = items.length === pageSize
  } catch (error) {
    console.error('获取面试列表失败:', error)
  }
}

// 获取单个面试的评估数据
async function fetchEvaluation(session) {
  try {
    const response = await http.get(ENDPOINTS.evaluation.reportDetail(session.id))
    if (response) {
      session.evaluation = response
      session.has_evaluation = true
      session.overall_score = response.overall_score
    }
  } catch (error) {
    session.has_evaluation = false
  }
}

// 加载更多
async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  await fetchInterviews()
  loadingMore.value = false
}

// 选择会话
async function selectSession(session) {
  selectedSession.value = session

  // 如果有评估数据但未加载，先加载评估
  if ((session.is_finished || session.status === 'completed') && !session.has_evaluation) {
    uni.showLoading({ title: '加载中...' })
    await fetchEvaluation(session)
    uni.hideLoading()
  }

  // 加载 RAG 推荐
  if (session.has_evaluation) {
    await loadRAGRecommendations(session.id)
  }
}

// 加载 RAG 推荐
async function loadRAGRecommendations(sessionId) {
  try {
    const data = await http.get(ENDPOINTS.recommendation.report(sessionId))
    if (data) {
      ragRecommendations.value = data.recommendations || []
      ragWeakAreas.value = data.weak_areas || []
      ragOverallAdvice.value = data.overall_advice || ''
    }
  } catch (error) {
    console.error('获取推荐失败:', error)
    ragRecommendations.value = []
    ragWeakAreas.value = []
    ragOverallAdvice.value = ''
  }
}

// 跳转到资源
function goToResource(item) {
  if (item.url) {
    uni.navigateTo({
      url: `/pages/learn/single-resource?url=${encodeURIComponent(item.url)}`
    })
  } else {
    uni.showToast({ title: '暂无资源链接', icon: 'none' })
  }
}

// 跳转到学习页面
function goToLearning() {
  if (selectedSession.value?.evaluation) {
    uni.setStorageSync('selectedInterview', {
      overall_evaluation: selectedSession.value.evaluation
    })
    uni.navigateTo({
      url: '/pages/learn/personalized'
    })
  }
}

// 跳转到面试页面
function goToInterview() {
  uni.switchTab({
    url: '/pages/home/home'
  })
}

// 初始化
async function init() {
  loading.value = true
  await Promise.all([
    fetchStats(),
    fetchInterviews(true)
  ])

  // 如果有面试记录，默认选中第一个已完成的
  const completed = interviews.value.find(s => s.is_finished || s.status === 'completed')
  if (completed) {
    await selectSession(completed)
  } else if (interviews.value.length > 0) {
    selectedSession.value = interviews.value[0]
  }

  loading.value = false
}

// 页面显示
onShow(() => {
  if (!userStore.access && !userStore.refresh) {
    uni.showToast({ title: '请先登录', icon: 'none', duration: 2000 })
    uni.navigateTo({ url: '/pages/login/login' })
    return
  }
  refreshToken()
  init()
})
</script>

<style scoped>
.report-page {
  min-height: 100vh;
  background: var(--bg-page);
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  padding: 40rpx 30rpx 60rpx;
  position: relative;
}

.page-header::after {
  content: '';
  position: absolute;
  bottom: -20rpx;
  left: 0;
  right: 0;
  height: 40rpx;
  background: var(--bg-page);
  border-radius: 20rpx 20rpx 0 0;
}

.header-content {
  position: relative;
  z-index: 1;
}

.page-title {
  font-size: 40rpx;
  font-weight: 600;
  color: white;
  display: block;
  margin-bottom: 12rpx;
}

.page-subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.85);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 40rpx;
}

.loader {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid var(--color-neutral-200);
  border-top: 4rpx solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20rpx;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 28rpx;
  color: var(--text-secondary);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 40rpx;
}

.empty-icon {
  font-size: 100rpx;
  color: var(--color-neutral-300);
  margin-bottom: 30rpx;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16rpx;
}

.empty-desc {
  font-size: 26rpx;
  color: var(--text-secondary);
  margin-bottom: 40rpx;
}

.start-btn {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: white;
  border: none;
  border-radius: 40rpx;
  padding: 24rpx 60rpx;
  font-size: 30rpx;
  font-weight: 500;
}

/* 内容区 */
.content-wrapper {
  padding: 20rpx;
}

/* 统计区域 */
.stats-section {
  margin-bottom: 30rpx;
}

.stats-row {
  display: flex;
  gap: 20rpx;
}

.stat-card {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 30rpx 20rpx;
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.stat-value {
  font-size: 44rpx;
  font-weight: 700;
  color: var(--color-primary);
  display: block;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 24rpx;
  color: var(--text-secondary);
}

/* 历史区域 */
.history-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: 30rpx;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.section-header {
  padding: 30rpx;
  border-bottom: 1rpx solid var(--border-divider);
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  display: block;
  margin-bottom: 20rpx;
}

.filter-tabs {
  display: flex;
  gap: 16rpx;
}

.tab {
  padding: 12rpx 24rpx;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: var(--text-secondary);
  background: var(--bg-page);
  transition: all 0.2s;
}

.tab.active {
  background: var(--color-primary);
  color: white;
}

/* 会话列表 */
.session-list {
  max-height: 600rpx;
  padding: 20rpx;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: var(--bg-page);
  border-radius: var(--radius-md);
  border: 2rpx solid transparent;
  transition: all 0.2s;
}

.session-item:active {
  transform: scale(0.98);
}

.session-item.active {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, rgba(24, 119, 242, 0.05), rgba(59, 130, 246, 0.05));
}

.session-main {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.scenario-name {
  font-size: 30rpx;
  font-weight: 500;
  color: var(--text-primary);
  display: block;
  margin-bottom: 12rpx;
}

.session-meta {
  display: flex;
  gap: 20rpx;
}

.meta-item {
  font-size: 24rpx;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.meta-icon {
  font-size: 22rpx;
}

.score-icon {
  color: var(--color-warning);
}

.status-badge {
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  font-weight: 500;
}

.status-badge.completed {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-success);
}

.status-badge.active,
.status-badge.in_progress {
  background: rgba(24, 119, 242, 0.1);
  color: var(--color-primary);
}

.status-badge.paused {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
}

.session-action {
  margin-left: 20rpx;
}

.action-icon {
  font-size: 28rpx;
  color: var(--color-primary);
}

.loading-more {
  text-align: center;
  padding: 30rpx;
  font-size: 26rpx;
  color: var(--text-secondary);
}

/* 详情区域 */
.detail-section {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20rpx); }
  to { opacity: 1; transform: translateY(0); }
}

.detail-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: 30rpx;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 30rpx;
  border-bottom: 1rpx solid var(--border-divider);
}

.card-icon {
  font-size: 32rpx;
  color: var(--color-primary);
}

.card-title {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.weak-areas {
  font-size: 24rpx;
  color: var(--text-secondary);
}

/* 图表 */
.chart-wrapper {
  height: 400rpx;
  padding: 20rpx;
}

/* 评估内容 */
.evaluation-content,
.suggestion-content {
  padding: 30rpx;
}

.evaluation-text,
.suggestion-text {
  font-size: 28rpx;
  line-height: 1.6;
  color: var(--text-secondary);
}

/* 得分网格 */
.score-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20rpx;
  padding: 30rpx;
}

.score-item {
  text-align: center;
  padding: 20rpx 10rpx;
  background: var(--bg-page);
  border-radius: var(--radius-md);
}

.score-name {
  font-size: 22rpx;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 8rpx;
}

.score-value {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--color-primary);
}

/* 学习链接 */
.learning-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 24rpx 30rpx;
  border-top: 1rpx solid var(--border-divider);
  background: rgba(24, 119, 242, 0.03);
}

.link-text {
  font-size: 26rpx;
  color: var(--color-primary);
  font-weight: 500;
}

.link-icon {
  font-size: 24rpx;
  color: var(--color-primary);
}

/* 推荐列表 */
.recommend-list {
  padding: 20rpx;
}

.recommend-item {
  padding: 24rpx;
  margin-bottom: 16rpx;
  background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%);
  border-radius: var(--radius-md);
  border-left: 4rpx solid var(--color-primary);
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12rpx;
}

.rec-name {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.rec-tags {
  display: flex;
  gap: 8rpx;
}

.rec-tag {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  background: rgba(24, 119, 242, 0.1);
  color: var(--color-primary);
  border-radius: 10rpx;
}

.rec-reason {
  font-size: 26rpx;
  color: var(--text-secondary);
  line-height: 1.5;
  display: block;
  margin-bottom: 16rpx;
}

.rec-meta {
  display: flex;
  gap: 16rpx;
}

.rec-type {
  font-size: 22rpx;
  color: var(--text-tertiary);
}

.rec-difficulty {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-weight: 500;
}

.difficulty-easy {
  background: #d4edda;
  color: #155724;
}

.difficulty-medium {
  background: #fff3cd;
  color: #856404;
}

.difficulty-hard {
  background: #f8d7da;
  color: #721c24;
}

/* 整体建议 */
.overall-advice {
  margin: 20rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, #e8f4fd 0%, #d1e7f7 100%);
  border-radius: var(--radius-md);
  border: 1rpx solid rgba(24, 119, 242, 0.2);
}

.advice-title {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--color-primary);
  display: block;
  margin-bottom: 12rpx;
}

.advice-content {
  font-size: 26rpx;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* 无评估提示 */
.no-evaluation {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 40rpx;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.no-eval-icon {
  font-size: 80rpx;
  color: var(--color-warning);
  margin-bottom: 24rpx;
}

.no-eval-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12rpx;
}

.no-eval-desc {
  font-size: 26rpx;
  color: var(--text-secondary);
  text-align: center;
}

/* 响应式适配 */
@media (min-width: 768px) {
  .content-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }

  .score-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    gap: 16rpx;
  }

  .stat-card {
    padding: 24rpx 16rpx;
  }

  .stat-value {
    font-size: 36rpx;
  }

  .score-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .page-title {
    font-size: 36rpx;
  }
}
</style>
