<template>
  <view class="container">
    <web-view
      v-if="!showErrorPage"
      ref="webViewRef"
      :src="webViewSrc"
      @message="handleWebViewMessage"
    ></web-view>

    <!-- 错误页面 -->
    <view v-if="showErrorPage && !userStore.isH5" class="error-container">
      <view class="error-content animate-fade-in">
        <view class="error-icon">
          <view class="icon warning-icon"></view>
        </view>
        <text class="error-title">网页加载失败</text>
        <text class="error-desc">无法连接到服务器，请手动复制链接自行打开</text>
        <text class="error-url">{{ webViewSrc }}</text>
        <view class="error-actions">
          <button class="copy-btn" @click="copyUrl">
            <view class="btn-icon copy-icon"></view>
            <text>复制链接</text>
          </button>
          <button class="retry-btn" @click="retryLoad">
            <view class="btn-icon refresh-icon"></view>
            <text>重新加载</text>
          </button>
        </view>
      </view>
    </view>

    <!-- 底部浮动操作栏 -->
    <view v-if="!showErrorPage && resourceId" class="float-action-bar">
      <view class="action-item" @click="handleView">
        <uni-icons type="eye" size="20" color="var(--text-secondary)"></uni-icons>
        <text class="action-count">{{ viewCount || 0 }}</text>
      </view>
      <view class="action-divider"></view>
      <view class="action-item" :class="{ active: isFavorited }" @click="handleFavorite">
        <uni-icons :type="isFavorited ? 'star-filled' : 'star'" size="20"
          :color="isFavorited ? 'var(--color-warning)' : 'var(--text-secondary)'"
        ></uni-icons>
        <text class="action-label" :class="{ active: isFavorited }">收藏</text>
      </view>
      <view class="action-divider"></view>
      <view class="action-item" :class="{ active: isLiked }" @click="handleLike">
        <uni-icons :type="isLiked ? 'heart-filled' : 'heart'" size="20"
          :color="isLiked ? 'var(--color-error)' : 'var(--text-secondary)'"
        ></uni-icons>
        <text class="action-label" :class="{ active: isLiked }">点赞</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onLoad, onUnload } from '@dcloudio/uni-app';
import { ref } from 'vue';
import { useUserStore } from '@/stores/user.js'
import { ENDPOINTS } from '@/stores/api.js'
import http from '@/stores/request.js'

const userStore = useUserStore();
const webViewSrc = ref('');
const showErrorPage = ref(false);
const loadCheckTimer = ref(null);
const isPageLoaded = ref(false);

// 资源交互相关
const resourceId = ref(null)
const isFavorited = ref(false)
const isLiked = ref(false)
const viewCount = ref(0)

onLoad((options) => {
  if (options.url) {
    webViewSrc.value = decodeURIComponent(options.url);
    startLoadCheck();
  }
  // 从 URL 参数或 storage 获取资源 ID
  if (options.id) {
    resourceId.value = parseInt(options.id)
    // 进入页面时自动调用 view API
    recordView()
    // 获取资源详情（包含收藏/点赞状态）
    fetchResourceDetail()
  }
});

// 获取资源详情
const fetchResourceDetail = async () => {
  if (!resourceId.value) return
  try {
    const response = await http.get(ENDPOINTS.learning.resourceDetail(resourceId.value))
    if (response) {
      viewCount.value = response.view_count || 0
      // 如果后端返回收藏/点赞状态，可以在这里设置
      // isFavorited.value = response.is_favorited || false
      // isLiked.value = response.is_liked || false
    }
  } catch (error) {
    console.error('获取资源详情失败:', error)
  }
}

// 记录浏览
const recordView = async () => {
  if (!resourceId.value) return
  try {
    const response = await http.post(ENDPOINTS.learning.resourceView(resourceId.value))
    if (response && response.view_count !== undefined) {
      viewCount.value = response.view_count
    }
  } catch (error) {
    console.error('记录浏览失败:', error)
  }
}

// 处理查看（刷新计数）
const handleView = async () => {
  await recordView()
  uni.showToast({
    title: `浏览数: ${viewCount.value}`,
    icon: 'none'
  })
}

// 处理收藏
const handleFavorite = async () => {
  if (!resourceId.value) {
    uni.showToast({ title: '资源ID缺失', icon: 'none' })
    return
  }
  try {
    const action = isFavorited.value ? 'unfavorite' : 'favorite'
    const response = await http.post(ENDPOINTS.learning.resourceInteract(resourceId.value), {
      action: action
    })
    isFavorited.value = !isFavorited.value
    uni.showToast({
      title: isFavorited.value ? '已收藏' : '已取消收藏',
      icon: 'success'
    })
  } catch (error) {
    console.error('收藏操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

// 处理点赞
const handleLike = async () => {
  if (!resourceId.value) {
    uni.showToast({ title: '资源ID缺失', icon: 'none' })
    return
  }
  try {
    const action = isLiked.value ? 'unlike' : 'like'
    const response = await http.post(ENDPOINTS.learning.resourceInteract(resourceId.value), {
      action: action
    })
    isLiked.value = !isLiked.value
    uni.showToast({
      title: isLiked.value ? '已点赞' : '已取消点赞',
      icon: 'success'
    })
  } catch (error) {
    console.error('点赞操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const startLoadCheck = () => {
  clearTimeout(loadCheckTimer.value);
  isPageLoaded.value = false;
  showErrorPage.value = false;

  // 3秒后检查页面是否加载成功
  loadCheckTimer.value = setTimeout(() => {
    if (!isPageLoaded.value && !userStore.isH5) {
      console.log('页面加载超时，显示自定义错误页');
      showErrorPage.value = true;
    }
  }, 3000); // 3秒超时
};

const handleWebViewMessage = (e) => {
  console.log('收到web-view消息:', e);
  isPageLoaded.value = true;
  clearTimeout(loadCheckTimer.value);
};

const copyUrl = async () => {
  try {
    await uni.setClipboardData({
      data: webViewSrc.value
    });
    uni.showToast({ title: '链接已复制', icon: 'none' });
  } catch (err) {
    uni.showToast({ title: '复制失败', icon: 'none' });
  }
};

const retryLoad = () => {
  startLoadCheck();
};

onUnload(() => {
  clearTimeout(loadCheckTimer.value);
});
</script>

<style>
.container {
  flex: 1;
  height: 100%;
  position: relative;
}

/* 底部浮动操作栏 */
.float-action-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  background: var(--bg-secondary);
  border-radius: 50px;
  padding: 8px 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.action-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 20px;
}

.action-item:active {
  transform: scale(0.95);
}

.action-item.active {
  background: var(--bg-primary);
}

.action-count {
  font-size: 14px;
  color: var(--text-secondary);
  min-width: 20px;
  text-align: center;
}

.action-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.action-label.active {
  font-weight: 500;
}

.action-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
  margin: 0 4px;
}

/* 错误页面样式 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  padding: 40rpx;
  padding-top: 150px;
  background-color: var(--bg-page);
}

.error-content {
  width: 100%;
  max-width: 600rpx;
  background-color: var(--bg-card);
  border-radius: 16rpx;
  padding: 60rpx 40rpx;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.08);
  text-align: center;
  border-top: 6rpx solid var(--color-error);
}

.error-icon {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background-color: var(--bg-page);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 30rpx;
}

.error-icon .icon {
  width: 60rpx;
  height: 60rpx;
  position: relative;
}

/* 警告图标 - 使用 CSS 绘制三角形 */
.warning-icon {
  background: linear-gradient(135deg, #FFA726, #FF7043);
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
}

.warning-icon::before {
  content: '!';
  position: absolute;
  top: 55%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 28rpx;
  font-weight: bold;
}

/* 按钮图标样式 */
.btn-icon {
  width: 28rpx;
  height: 28rpx;
  position: relative;
  display: inline-block;
  margin-right: 8rpx;
}

/* 复制图标 */
.copy-icon {
  border: 2rpx solid currentColor;
  border-radius: 4rpx;
  background: transparent;
}

.copy-icon::before {
  content: '';
  position: absolute;
  width: 60%;
  height: 60%;
  border: 2rpx solid currentColor;
  border-radius: 2rpx;
  top: -6rpx;
  right: -6rpx;
  background: inherit;
}

/* 刷新图标 */
.refresh-icon {
  border: 3rpx solid currentColor;
  border-radius: 50%;
  border-left-color: transparent;
  animation: none;
}

.refresh-icon::before {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-left: 8rpx solid currentColor;
  border-top: 5rpx solid transparent;
  border-bottom: 5rpx solid transparent;
  top: -4rpx;
  right: 2rpx;
  transform: rotate(-30deg);
}

.error-title {
  font-size: 38rpx;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: 20rpx;
  display: block;
}

.error-desc {
  font-size: 28rpx;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 30rpx;
  display: block;
}

.error-url {
  font-size: 24rpx;
  color: var(--text-tertiary);
  word-break: break-all;
  background-color: var(--bg-page);
  padding: 20rpx;
  border-radius: 8rpx;
  margin: 30rpx 0;
  display: block;
  max-height: 120rpx;
  overflow: auto;
}

.error-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 20rpx;
}

.copy-btn,
.retry-btn {
  flex: 1;
  padding: 24rpx 0;
  border-radius: 8rpx;
  font-size: 28rpx;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.copy-btn {
  background-color: var(--bg-page);
  color: var(--text-secondary);
}

.copy-btn:active {
  background-color: var(--border-default);
}

.retry-btn {
  background-color: var(--color-error);
  color: var(--bg-card);
}

.retry-btn:active {
  background-color: var(--color-error);
}

.btn-icon {
  font-size: 28rpx;
}

/* 动画效果 */
.animate-fade-in {
  animation: fadeIn 0.5s ease forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
