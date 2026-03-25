<template>
  <view class="stats-container">
    <!-- 完成率 -->
    <view class="stat-card">
      <view class="progress-ring">
        <view class="progress-circle" :style="{ background: progressGradient }">
          <text class="progress-text">{{ completionRate }}%</text>
        </view>
      </view>
      <text class="stat-label">完成率</text>
    </view>

    <!-- 平均得分 -->
    <view class="stat-card">
      <view class="score-display">
        <text class="score-number" :class="scoreClass">{{ averageScore || '--' }}</text>
        <view class="score-trend" v-if="averageScore">
          <text class="trend-icon">{{ scoreTrend >= 0 ? '↑' : '↓' }}</text>
          <text class="trend-value">{{ Math.abs(scoreTrend) }}%</text>
        </view>
      </view>
      <text class="stat-label">平均得分</text>
    </view>

    <!-- 总面试次数 -->
    <view class="stat-card">
      <view class="count-display">
        <text class="count-number">{{ totalInterviews || 0 }}</text>
        <text class="count-unit">次</text>
      </view>
      <text class="stat-label">累计面试</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  totalInterviews: {
    type: Number,
    default: 0
  },
  averageScore: {
    type: Number,
    default: 0
  },
  scoreTrend: {
    type: Number,
    default: 0
  },
  completionRate: {
    type: Number,
    default: 0
  }
});

// 进度环渐变
const progressGradient = computed(() => {
  const percentage = Math.min(props.completionRate, 100);
  return `conic-gradient(var(--color-primary) ${percentage}%, var(--bg-page) ${percentage}%)`;
});

// 分数等级
const scoreClass = computed(() => {
  if (!props.averageScore) return '';
  if (props.averageScore >= 90) return 'excellent';
  if (props.averageScore >= 80) return 'good';
  if (props.averageScore >= 60) return 'pass';
  return 'fail';
});
</script>

<style scoped>
.stats-container {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.stat-card {
  flex: 1;
  background: var(--bg-card);
  border-radius: 16rpx;
  padding: 24rpx 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

/* 统一的内容显示区域 */
.progress-ring,
.score-display,
.count-display {
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
}

/* 进度环 */
.progress-ring {
  width: 100rpx;
}

.progress-circle {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.progress-circle::before {
  content: '';
  width: 80%;
  height: 80%;
  background: var(--bg-card);
  border-radius: 50%;
  position: absolute;
}

.progress-text {
  font-size: 24rpx;
  font-weight: bold;
  color: var(--color-primary);
  z-index: 1;
}

/* 分数显示 */
.score-display {
  flex-direction: column;
}

.score-number {
  font-size: 44rpx;
  font-weight: bold;
  color: var(--text-primary);
  line-height: 1;
}

.score-number.excellent {
  color: var(--color-success);
}

.score-number.good {
  color: var(--color-primary);
}

.score-number.pass {
  color: var(--color-warning);
}

.score-number.fail {
  color: var(--color-error);
}

.score-trend {
  display: flex;
  align-items: center;
  gap: 4rpx;
  font-size: 22rpx;
  margin-top: 4rpx;
}

.trend-icon {
  color: var(--color-success);
}

.trend-value {
  color: var(--color-success);
}

/* 计数显示 */
.count-display {
  align-items: center;
}

.count-number {
  font-size: 44rpx;
  font-weight: bold;
  color: var(--color-primary);
  line-height: 1;
}

.count-unit {
  font-size: 24rpx;
  color: var(--text-tertiary);
  margin-left: 4rpx;
}

.stat-label {
  font-size: 24rpx;
  color: var(--text-secondary);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .stats-container {
    gap: 12rpx;
  }

  .stat-card {
    padding: 20rpx 12rpx;
  }

  .progress-ring,
  .score-display,
  .count-display {
    height: 80rpx;
    margin-bottom: 12rpx;
  }

  .progress-ring {
    width: 80rpx;
  }

  .progress-text {
    font-size: 20rpx;
  }

  .score-number,
  .count-number {
    font-size: 36rpx;
  }

  .score-trend {
    font-size: 20rpx;
  }

  .count-unit {
    font-size: 20rpx;
  }

  .stat-label {
    font-size: 22rpx;
  }
}
</style>
