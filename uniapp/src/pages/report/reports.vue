<template>
  <view class="reports-container">
    <view class="header">
      <text class="title">评估报告</text>
      <text class="subtitle">共 {{ total }} 份报告</text>
    </view>

    <scroll-view class="report-list" scroll-y @scrolltolower="loadMore">
      <view
        v-for="report in reports"
        :key="report.id"
        class="report-card"
        @click="viewDetail(report)"
      >
        <view class="score-section">
          <view class="score-circle" :class="getScoreClass(report.overall_score)">
            <text class="score-value">{{ report.overall_score || '-' }}</text>
            <text class="score-label">总分</text>
          </view>
        </view>

        <view class="info-section">
          <text class="report-title">面试评估报告</text>
          <text class="report-date">{{ formatDate(report.created_at) }}</text>

          <view class="dimension-scores">
            <view class="dimension">
              <text class="dim-label">专业能力</text>
              <text class="dim-value">{{ report.technical_score || '-' }}</text>
            </view>
            <view class="dimension">
              <text class="dim-label">沟通能力</text>
              <text class="dim-value">{{ report.communication_score || '-' }}</text>
            </view>
            <view class="dimension">
              <text class="dim-label">逻辑思维</text>
              <text class="dim-value">{{ report.logical_score || '-' }}</text>
            </view>
          </view>
        </view>

        <uni-icons type="right" size="16" color="var(--text-tertiary)"></uni-icons>
      </view>

      <view v-if="loading" class="loading">加载中...</view>
      <view v-if="!loading && reports.length === 0" class="empty">
        <uni-icons type="list" size="48" color="var(--text-tertiary)"></uni-icons>
        <text>暂无评估报告</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import http from '@/stores/request.js'
import { ENDPOINTS } from '@/stores/api.js'

const reports = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)

async function fetchReports(reset = false) {
  if (loading.value) return
  if (reset) {
    page.value = 1
    reports.value = []
  }

  loading.value = true
  try {
    const response = await http.get(ENDPOINTS.evaluation.reports, {
      params: { skip: (page.value - 1) * 10, limit: 10 }
    })
    reports.value.push(...response.items)
    total.value = response.total
  } catch (error) {
    uni.showToast({ title: '获取失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function getScoreClass(score) {
  if (!score) return ''
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 60) return 'pass'
  return 'fail'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function viewDetail(report) {
  uni.navigateTo({
    url: `/pages/report/report?sessionId=${report.session_id || report.id}`
  })
}

function loadMore() {
  if (reports.value.length < total.value) {
    page.value++
    fetchReports()
  }
}

onMounted(() => fetchReports(true))
</script>

<style scoped>
.reports-container {
  min-height: 100vh;
  background: var(--bg-primary);
}

.header {
  padding: 20px;
  background: var(--bg-secondary);
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

.report-list {
  padding: 16px;
  height: calc(100vh - 100px);
}

.report-card {
  display: flex;
  align-items: center;
  padding: 16px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
  border-radius: 12px;
}

.score-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  margin-right: 16px;
}

.score-circle.excellent { background: var(--color-success-bg); color: var(--color-success); }
.score-circle.good { background: var(--color-primary-bg); color: var(--color-primary); }
.score-circle.pass { background: var(--color-warning-bg); color: var(--color-warning); }
.score-circle.fail { background: var(--color-error-bg); color: var(--color-error); }

.score-value {
  font-size: 20px;
  font-weight: 600;
}

.score-label {
  font-size: 10px;
}

.info-section {
  flex: 1;
}

.report-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.report-date {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  display: block;
}

.dimension-scores {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.dimension {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.dim-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.dim-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.loading, .empty {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
</style>
