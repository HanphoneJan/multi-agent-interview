<template>
  <view class="home-container">
    <!-- 背景装饰 -->
    <view class="bg-decoration">
      <view class="gradient-orb orb-1"></view>
      <view class="gradient-orb orb-2"></view>
      <view class="grid-lines"></view>
    </view>

    <!-- 顶部导航 -->
    <view class="header">
      <view class="logo-wrap">
        <view class="logo-icon">
          <view class="logo-pulse"></view>
          <text class="logo-text-inner">AI</text>
        </view>
        <text class="logo-text">面试助手</text>
      </view>
    </view>

    <!-- 主内容区 -->
    <view class="main-content">
      <!-- 核心标题区 -->
      <view class="hero-section">
        <view class="tag">
          <view class="tag-dot"></view>
          <text class="tag-text">智能面试系统</text>
        </view>

        <text class="main-title">
          <text class="title-highlight">AI</text> 模拟面试
        </text>

        <text class="subtitle">基于大语言模型的智能面试官</text>

        <view class="feature-list">
          <view class="feature-item">
            <view class="feature-icon">
              <view class="icon-check"></view>
            </view>
            <text class="feature-text">实时语音交互</text>
          </view>
          <view class="feature-item">
            <view class="feature-icon">
              <view class="icon-check"></view>
            </view>
            <text class="feature-text">多维度评估</text>
          </view>
          <view class="feature-item">
            <view class="feature-icon">
              <view class="icon-check"></view>
            </view>
            <text class="feature-text">个性化学习资源</text>
          </view>
        </view>
      </view>

      <!-- 面试场景预览 -->
      <view class="scenes-section">
        <text class="section-label">SUPPORTED SCENARIOS</text>
        <view class="scenes-list">
          <view class="scene-tag">Java开发</view>
          <view class="scene-tag">Python</view>
          <view class="scene-tag">算法工程师</view>
          <view class="scene-tag">产品经理</view>
          <view class="scene-tag">前端开发</view>
          <view class="scene-tag">数据分析</view>
        </view>
      </view>
    </view>

    <!-- 底部行动区 -->
    <view class="action-bar">
      <button class="primary-btn" @click="goToExperience">
        <text class="btn-text">开始面试</text>
        <view class="btn-arrow">
          <view class="arrow-line"></view>
          <view class="arrow-head"></view>
        </view>
      </button>
      <text class="hint-text">开启你的个性化面试体验</text>
    </view>
  </view>
</template>

<script setup>
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();

const navigateToTarget = () => {
  const targetUrl = '/pages/home/home';

  if (userStore.isLoggedIn) {
    uni.switchTab({ url: targetUrl });
  } else {
    uni.navigateTo({ url: '/pages/login/login' });
  }
};

const goToLogin = navigateToTarget;
const goToExperience = navigateToTarget;
</script>

<style lang="css" scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(180deg, var(--bg-page) 0%, #f0f7ff 40%, #f8fafc 100%);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 背景装饰 */
.bg-decoration {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(21, 101, 192, 0.25) 0%, transparent 70%);
  top: -100px;
  right: -50px;
}

.orb-2 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(33, 150, 243, 0.2) 0%, transparent 70%);
  bottom: 20%;
  left: -80px;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(21, 101, 192, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(21, 101, 192, 0.06) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* 顶部导航 */
.header {
  position: relative;
  z-index: 10;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.logo-pulse {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border-radius: 10px;
  animation: pulse 2s ease-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.6;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.logo-text-inner {
  color: var(--text-inverse);
  font-size: 14px;
  font-weight: 700;
  position: relative;
  z-index: 1;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 1px;
}

.header-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.header-btn:active {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

/* 主内容区 */
.main-content {
  flex: 1;
  position: relative;
  z-index: 10;
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* Hero区域 */
.hero-section {
  margin-bottom: 48px;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(57, 100, 254, 0.1);
  border: 1px solid rgba(57, 100, 254, 0.2);
  padding: 6px 14px;
  border-radius: 20px;
  margin-bottom: 24px;
}

.tag-dot {
  width: 6px;
  height: 6px;
  background: var(--color-primary);
  border-radius: 50%;
  animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.tag-text {
  font-size: 12px;
  color: var(--color-primary);
  letter-spacing: 1px;
  font-weight: 500;
}

.main-title {
  font-size: 42px;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
  margin-bottom: 12px;
  letter-spacing: -1px;
}

.title-highlight {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 50%, var(--color-primary-lighter) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 32px;
}

/* 特性列表 */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feature-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-check {
  width: 16px;
  height: 10px;
  border-left: 2px solid var(--color-primary);
  border-bottom: 2px solid var(--color-primary);
  transform: rotate(-45deg) translate(1px, -1px);
}

.feature-text {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 场景区域 */
.scenes-section {
  margin-top: auto;
}

.section-label {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 2px;
  margin-bottom: 12px;
  display: block;
}

.scenes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-tag {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(57, 100, 254, 0.15);
  border-radius: 16px;
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
}

/* 底部行动区 */
.action-bar {
  position: relative;
  z-index: 10;
  padding: 24px;
  background: linear-gradient(to top, var(--bg-page) 0%, rgba(248, 250, 252, 0.9) 60%, transparent 100%);
}

.primary-btn {
  width: 100%;
  height: 52px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border: none;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
  position: relative;
  overflow: hidden;
}

.primary-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  50%, 100% { left: 100%; }
}

.btn-text {
  color: var(--text-inverse);
  font-size: 16px;
  font-weight: 600;
}

.btn-arrow {
  display: flex;
  align-items: center;
}

.arrow-line {
  width: 12px;
  height: 2px;
  background: var(--text-inverse);
}

.arrow-head {
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 6px solid var(--text-inverse);
  margin-left: -2px;
}

.hint-text {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  display: block;
}

/* PC 适配 */
@media (min-width: 768px) {
  .header {
    padding: 24px 40px;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }

  .logo-text {
    font-size: 20px;
  }

  .main-content {
    padding: 60px 40px;
    max-width: 1200px;
    margin: 0 auto;
    flex-direction: row;
    align-items: center;
    gap: 60px;
  }

  .hero-section {
    flex: 1;
    margin-bottom: 0;
  }

  .tag {
    margin-bottom: 32px;
  }

  .main-title {
    font-size: 56px;
    margin-bottom: 16px;
  }

  .subtitle {
    font-size: 18px;
    margin-bottom: 40px;
  }

  .feature-list {
    flex-direction: row;
    gap: 24px;
  }

  .scenes-section {
    flex: 0 0 320px;
    margin-top: 0;
  }

  .scenes-list {
    gap: 10px;
  }

  .scene-tag {
    padding: 8px 16px;
    font-size: 13px;
  }

  .action-bar {
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    align-items: center;
    background: linear-gradient(to top, var(--bg-page) 0%, rgba(248, 250, 252, 0.95) 70%, transparent 100%);
  }

  .primary-btn {
    width: auto;
    min-width: 240px;
    height: 56px;
    border-radius: 28px;
  }

  .btn-text {
    font-size: 17px;
  }
}

/* 大屏适配 */
@media (min-width: 1024px) {
  .main-content {
    gap: 80px;
  }

  .main-title {
    font-size: 64px;
  }

  .scenes-section {
    flex: 0 0 380px;
  }
}

/* 超大屏适配 */
@media (min-width: 1400px) {
  .header {
    max-width: 1400px;
    padding: 28px 60px;
  }

  .main-content {
    max-width: 1400px;
    padding: 80px 60px;
  }

  .main-title {
    font-size: 72px;
  }
}
</style>
