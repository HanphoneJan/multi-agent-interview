<template>
  <view class="history-container">
    <!-- 顶部导航 -->
    <view class="header">
      <view class="header-top">
        <text class="title">面试历史</text>
        <text class="subtitle">共 {{ total }} 场面试</text>
      </view>

      <!-- 统计卡片 -->
      <view class="stats-row">
        <view class="stat-card">
          <text class="stat-value">{{ userStats.total_interviews || total }}</text>
          <text class="stat-label">总面试</text>
        </view>
        <view class="stat-card">
          <text class="stat-value">{{ userStats.completed_interviews || completedCount }}</text>
          <text class="stat-label">已完成</text>
        </view>
        <view class="stat-card">
          <text class="stat-value">{{ userStats.average_score ? userStats.average_score.toFixed(1) : '-' }}</text>
          <text class="stat-label">平均分</text>
        </view>
      </view>
    </view>

    <!-- 筛选标签 -->
    <view class="filter-tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        class="tab"
        :class="{ active: currentTab === tab.value }"
        @click="currentTab = tab.value"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <!-- 面试列表 -->
    <scroll-view class="session-list" scroll-y @scrolltolower="loadMore" @refresherrefresh="onRefresh" refresher-enabled refresher-triggered="{{isRefreshing}}">
      <view
        v-for="session in filteredSessions"
        :key="session.id"
        class="session-card"
        @click="viewDetail(session)"
      >
        <view class="card-header">
          <view class="scenario-info">
            <text class="scenario-name">{{ session.scenario_name || '未知场景' }}</text>
            <text class="tech-field">{{ session.technology_field || '通用' }}</text>
          </view>
          <view class="status-badge" :class="session.status">
            {{ statusText[session.status] }}
          </view>
        </view>

        <view class="card-body">
          <view class="info-row">
            <uni-icons type="calendar" size="14" color="var(--text-secondary)"></uni-icons>
            <text class="info-text">{{ formatDate(session.start_time) }}</text>
          </view>
          <view class="info-row">
            <uni-icons type="clock" size="14" color="var(--text-secondary)"></uni-icons>
            <text class="info-text">{{ formatDuration(session.start_time, session.end_time) }}</text>
          </view>
          <view v-if="session.overall_score" class="info-row score-row">
            <uni-icons type="star" size="14" color="var(--color-warning)"></uni-icons>
            <text class="info-text score-text">{{ session.overall_score }}分</text>
          </view>
        </view>

        <view class="card-footer">
          <button
            v-if="session.is_finished && session.has_report"
            class="action-btn small primary"
            @click.stop="viewReport(session)"
          >
            查看报告
          </button>
          <button
            v-else-if="session.status === 'active' || session.status === 'paused'"
            class="action-btn small warning"
            @click.stop="resumeSession(session)"
          >
            继续面试
          </button>
          <button
            v-else-if="session.status === 'completed' && !session.has_report"
            class="action-btn small"
            @click.stop="checkReport(session)"
          >
            检查报告
          </button>
          <text v-else class="no-report">暂无报告</text>
        </view>
      </view>

      <!-- 加载更多 -->
      <view v-if="loading" class="loading-more">
        <uni-icons type="spinner" size="16" color="var(--text-secondary)"></uni-icons>
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && filteredSessions.length === 0" class="empty-state">
        <uni-icons type="list" size="48" color="var(--text-tertiary)"></uni-icons>
        <text class="empty-title">暂无面试记录</text>
        <text class="empty-desc">开始您的第一次面试吧</text>
        <button class="action-btn primary" @click="startNewInterview">开始面试</button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '@/stores/request.js'
import { ENDPOINTS } from '@/stores/api.js'

// 标签页
const tabs = [
  { label: '全部', value: 'all' },
  { label: '已完成', value: 'completed' },
  { label: '进行中', value: 'active' },
]
const currentTab = ref('all')

// 状态文本
const statusText = {
  'active': '进行中',
  'paused': '已暂停',
  'completed': '已完成',
  'cancelled': '已取消',
  'pending': '待开始'
}

// 数据
const sessions = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = 10
const isRefreshing = ref(false)

// 用户统计数据
const userStats = ref({
  total_interviews: 0,
  completed_interviews: 0,
  average_score: null,
  total_duration: 0
})

// 计算属性：筛选后的会话
const filteredSessions = computed(() => {
  if (currentTab.value === 'all') return sessions.value
  if (currentTab.value === 'completed') {
    return sessions.value.filter(s => s.is_finished)
  }
  if (currentTab.value === 'active') {
    return sessions.value.filter(s => s.status === 'in_progress' || s.status === 'paused')
  }
  return sessions.value
})

// 统计数量
const completedCount = computed(() => sessions.value.filter(s => s.is_finished).length)
const inProgressCount = computed(() => sessions.value.filter(s => s.status === 'in_progress' || s.status === 'paused').length)

// 获取用户统计数据
async function fetchUserStats() {
  try {
    const response = await http.get(ENDPOINTS.interview.userData)
    if (response) {
      userStats.value = response
    }
  } catch (error) {
    console.error('获取用户统计数据失败:', error)
  }
}

// 下拉刷新
async function onRefresh() {
  isRefreshing.value = true
  await Promise.all([
    fetchSessions(true),
    fetchUserStats()
  ])
  isRefreshing.value = false
}

// 获取面试历史
async function fetchSessions(reset = false) {
  if (loading.value) return

  if (reset) {
    page.value = 1
    sessions.value = []
  }

  loading.value = true
  try {
    const response = await http.get(ENDPOINTS.interview.sessions, {
      params: {
        skip: (page.value - 1) * pageSize,
        limit: pageSize
      }
    })

    const data = response
    const newSessions = data.items || []

    // 检查每个会话是否有报告
    for (const session of newSessions) {
      if (session.is_finished) {
        checkHasReport(session)
      }
    }

    sessions.value.push(...newSessions)
    total.value = data.total || 0
  } catch (error) {
    console.error('获取面试历史失败:', error)
    uni.showToast({ title: '获取失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 检查是否有报告
async function checkHasReport(session) {
  try {
    await http.get(ENDPOINTS.evaluation.reportDetail(session.id))
    session.has_report = true
  } catch {
    session.has_report = false
  }
}

// 检查报告（用于手动触发检查）
async function checkReport(session) {
  uni.showLoading({ title: '检查中...' })
  await checkHasReport(session)
  uni.hideLoading()

  if (session.has_report) {
    uni.showToast({ title: '报告已生成', icon: 'success' })
  } else {
    uni.showToast({ title: '报告生成中，请稍后', icon: 'none' })
  }
}

// 加载更多
function loadMore() {
  if (sessions.value.length < total.value) {
    page.value++
    fetchSessions()
  }
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

// 格式化时长
function formatDuration(start, end) {
  if (!start) return '-'
  const startTime = new Date(start)
  const endTime = end ? new Date(end) : new Date()
  const diff = Math.floor((endTime - startTime) / 1000 / 60) // minutes

  if (diff < 1) return '不到1分钟'
  if (diff < 60) return `${diff}分钟`
  const hours = Math.floor(diff / 60)
  const mins = diff % 60
  return `${hours}小时${mins > 0 ? mins + '分钟' : ''}`
}

// 查看详情
function viewDetail(session) {
  uni.navigateTo({
    url: `/pages/history/detail?id=${session.id}`
  })
}

// 查看报告
function viewReport(session) {
  uni.navigateTo({
    url: `/pages/report/report?sessionId=${session.id}`
  })
}

// 继续面试 (使用新的 Qwen3-Omni Realtime 方案)
function resumeSession(session) {
  uni.navigateTo({
    url: `/pages/interview/interview-realtime?sessionId=${session.id}&resume=true`
  })
}

// 开始新面试
function startNewInterview() {
  uni.switchTab({
    url: '/pages/home/home'
  })
}

onMounted(() => {
  fetchSessions(true)
  fetchUserStats()
})
</script>

<style scoped>
.history-container {
  min-height: 100vh;
  background: var(--bg-primary);
}

.header {
  padding: 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.header-top {
  margin-bottom: 16px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  display: block;
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.stats-row {
  display: flex;
  gap: 12px;
}

.stat-card {
  flex: 1;
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-primary);
  display: block;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.filter-tabs {
  display: flex;
  padding: 12px 20px;
  gap: 12px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.tab {
  padding: 6px 16px;
  border-radius: 16px;
  background: var(--bg-tertiary);
  transition: all 0.2s;
}

.tab.active {
  background: var(--color-primary);
}

.tab text {
  font-size: 14px;
  color: var(--text-secondary);
}

.tab.active text {
  color: var(--text-inverse);
}

.session-list {
  padding: 16px;
  height: calc(100vh - 220px);
}

.session-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.scenario-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  display: block;
}

.tech-field {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
  display: block;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.completed {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.status-badge.paused {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-badge.cancelled {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.card-body {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.info-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.score-row {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
}

.score-text {
  color: var(--color-warning);
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.action-btn.small {
  padding: 6px 12px;
  font-size: 13px;
}

.action-btn.primary {
  background: var(--color-primary);
  color: var(--text-inverse);
}

.action-btn.warning {
  background: var(--color-warning);
  color: var(--text-inverse);
}

.no-report {
  font-size: 13px;
  color: var(--text-tertiary);
}

.loading-more,
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-top: 16px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
  margin-bottom: 24px;
}
</style>
