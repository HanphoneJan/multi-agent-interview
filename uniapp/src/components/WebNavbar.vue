<template>
  <view class="web-navbar" v-if="isPC">
    <div class="logo">AI面试助手</div>
    <div class="nav-items">
      <div
        class="nav-item"
        :class="{ active: currentRoute === '/pages/home/home' }"
        @click="navigateTo('/pages/home/home')"
      >主页</div>
          <div
        class="nav-item"
        :class="{ active: currentRoute === '/pages/learn/ready' }"
        @click="navigateTo('/pages/learn/ready')"
      >面试准备</div>
      <div
        class="nav-item"
        :class="{ active: currentRoute === '/pages/report/report' }"
        @click="navigateTo('/pages/report/report')"
      >面试反馈</div>
      <div
        class="nav-item"
        :class="{ active: currentRoute === '/pages/profile/profile' }"
        @click="navigateTo('/pages/profile/profile')"
      >个人中心</div>
    </div>
    <div class="user-actions">
      <div class="user-avatar" @click="navigateTo('/pages/profile/profile')">
        <image src="https://hanphone.top/images/zhuxun.jpg" mode="aspectFit" />
      </div>
      <!-- 根据登录状态显示不同按钮 -->
      <button
        v-if="userStore.isLoggedIn"
        class="logout-btn"
        @click="logout"
      >退出登录</button>
      <button
        v-else
        class="login-btn"
        @click="navigateTo('/pages/login/login')"
      >登录</button>
    </div>
  </view>
  <!-- 为固定导航栏预留空间 (仅在PC端显示导航栏时占位) -->
  <view v-if="isPC" class="navbar-spacer"></view>
  <!-- 页面内容插槽 -->
  <slot></slot>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'; // 引入 Pinia 用户状态管理

const userStore = useUserStore(); // 获取用户状态存储实例
const { isH5 } = storeToRefs(userStore); // 获取响应式引用

// 当前路由 - 使用 ref 以便动态更新
const currentRoute = ref('')

// 窗口宽度 - 响应式
const windowWidth = ref(0)

// 获取当前路由（修复：确保返回带 / 的路径）
const updateCurrentRoute = () => {
  const pages = getCurrentPages()
  const route = pages[pages.length - 1]?.route || ''
  // 修复：确保路径以 / 开头，与模板中的比较一致
  currentRoute.value = route.startsWith('/') ? route : '/' + route
}

// 检测是否为移动设备（通过 user agent）
const isMobileDevice = () => {
  const userAgent = navigator.userAgent.toLowerCase()
  return /mobile|android|iphone|ipad|ipod|windows phone/i.test(userAgent)
}

// 更新窗口宽度
const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}

// PC端判断：H5环境 + 宽度大于668px + 不是移动设备
const isPC = computed(() => {
  const result = isH5.value && (windowWidth.value > 668) && !isMobileDevice()
  console.log('[WebNavbar] isPC computed:', { isH5: isH5.value, windowWidth: windowWidth.value, isPC: result })
  return result
})

// 定义tabBar页面路径数组
const tabBarPages = [
  '/pages/home/home',
  '/pages/learn/ready',
  '/pages/report/report',
  '/pages/profile/profile'
]

// 智能导航方法
const navigateTo = (path) => {
  if (tabBarPages.includes(path)) {
    // 如果是tabBar页面，使用switchTab
    uni.switchTab({ url: path })
  } else {
    // 普通页面使用navigateTo
    uni.navigateTo({ url: path })
  }
}

// 退出登录方法
const logout = () => {
  uni.showModal({
    title: '确认退出',
    content: '您确定要退出当前账号吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.clearUser() // 清除用户状态
        navigateTo('/pages/home/home') // 跳转到首页
        uni.showToast({
          title: '已退出登录',
          icon: 'success'
        })
      }
    }
  })
}

// resize 事件防抖
let resizeTimer = null
const handleResize = () => {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    updateWindowWidth()
  }, 100)
}

// 生命周期
onMounted(() => {
  // 初始化窗口宽度
  updateWindowWidth()
  // 初始化当前路由
  updateCurrentRoute()
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)

  // 调试日志
  console.log('[WebNavbar] Mounted:', {
    isH5: isH5.value,
    windowWidth: windowWidth.value,
    isPC: isPC.value,
    currentRoute: currentRoute.value
  })
})

onUnmounted(() => {
  // 移除监听
  window.removeEventListener('resize', handleResize)
  clearTimeout(resizeTimer)
})

// 页面显示时更新路由（处理页面切换后导航栏高亮不更新问题）
onShow(() => {
  updateCurrentRoute()
})
</script>

<style scoped>
.web-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 40px;
  background-color: var(--bg-card);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

.logo {
  font-size: 20px;
  font-weight: bold;
  color: var(--color-primary);
  width:120px
}

.nav-items {
  display: flex;
  gap: 60px;
  cursor: pointer;
  color: var(--text-primary);
  border-radius: 4px;
  transition: all 0.3s;
  font-size: large;
  font-weight: 700;
}

.nav-item:hover {
  background-color: var(--bg-page);
  color: var(--color-primary);
}

.nav-item.active {
  color: var(--color-primary);
  font-weight: bold;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
}

.user-avatar image {
  width: 100%;
  height: 100%;
}

/* 登录/退出按钮样式 */
.login-btn, .logout-btn {
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  outline: none;
  transition: all 0.3s;
}

.login-btn {
  background-color: var(--color-primary);
  color: white;
}

.login-btn:hover {
  background-color: var(--color-primary);
}

.logout-btn {
  background-color: var(--bg-page);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.logout-btn:hover {
  background-color: var(--border-default);
}

/* 导航栏占位元素，为固定定位的导航栏预留空间 */
.navbar-spacer {
  height: 60px;
}
</style>
