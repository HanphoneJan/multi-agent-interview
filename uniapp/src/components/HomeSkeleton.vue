<template>
  <view class="skeleton-container">
    <!-- 横幅骨架 -->
    <view class="skeleton-banner"></view>

    <!-- 步骤指示器骨架 -->
    <view class="skeleton-steps">
      <view class="skeleton-step" v-for="i in 3" :key="i">
        <view class="skeleton-circle"></view>
        <view class="skeleton-line-short"></view>
      </view>
    </view>

    <!-- 快捷入口骨架 -->
    <view class="skeleton-quick-access">
      <view class="skeleton-tag" v-for="i in 4" :key="i"></view>
    </view>

    <!-- 欢迎语骨架 -->
    <view class="skeleton-welcome">
      <view class="skeleton-line-long"></view>
      <view class="skeleton-line-medium"></view>
    </view>

    <!-- 数据看板骨架 -->
    <view class="skeleton-stats">
      <view class="skeleton-stat-card" v-for="i in 3" :key="i">
        <view class="skeleton-circle-large"></view>
        <view class="skeleton-line-short"></view>
      </view>
    </view>

    <!-- 功能卡片骨架 -->
    <view class="skeleton-cards">
      <view class="skeleton-card" v-for="i in 4" :key="i">
        <view class="skeleton-icon"></view>
        <view class="skeleton-line-medium"></view>
        <view class="skeleton-line-long"></view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.skeleton-container {
  padding: 20rpx;
  background-color: var(--bg-page);
  min-height: 100vh;
}

/* 基础动画 */
.skeleton-banner,
.skeleton-circle,
.skeleton-line-short,
.skeleton-line-medium,
.skeleton-line-long,
.skeleton-tag,
.skeleton-stat-card,
.skeleton-card,
.skeleton-icon,
.skeleton-circle-large {
  background: linear-gradient(90deg, var(--border-default) 25%, var(--bg-page) 50%, var(--border-default) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 8rpx;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 横幅骨架 */
.skeleton-banner {
  width: 100%;
  height: 300rpx;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
}

/* 步骤指示器骨架 */
.skeleton-steps {
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-bottom: 30rpx;
  padding: 20rpx;
  background: var(--bg-card);
  border-radius: 16rpx;
}

.skeleton-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.skeleton-circle {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
}

.skeleton-line-short {
  width: 100rpx;
  height: 20rpx;
}

/* 快捷入口骨架 */
.skeleton-quick-access {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
  padding: 20rpx;
  overflow-x: auto;
}

.skeleton-tag {
  width: 150rpx;
  height: 60rpx;
  border-radius: 30rpx;
  flex-shrink: 0;
}

/* 欢迎语骨架 */
.skeleton-welcome {
  padding: 30rpx;
  background: var(--bg-card);
  border-radius: 16rpx;
  margin-bottom: 30rpx;
}

.skeleton-line-long {
  width: 100%;
  height: 36rpx;
  margin-bottom: 16rpx;
}

.skeleton-line-medium {
  width: 60%;
  height: 28rpx;
}

/* 数据看板骨架 */
.skeleton-stats {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.skeleton-stat-card {
  flex: 1;
  background: var(--bg-card);
  border-radius: 16rpx;
  padding: 30rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.skeleton-circle-large {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
}

/* 功能卡片骨架 */
.skeleton-cards {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.skeleton-card {
  background: var(--bg-card);
  border-radius: 16rpx;
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.skeleton-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
}
</style>
