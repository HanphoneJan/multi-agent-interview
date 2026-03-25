import { ref, onMounted } from 'vue'

/**
 * 获取小程序顶部导航栏高度
 * 用于适配小程序胶囊按钮和 H5 环境的差异
 * @returns {Object} { navHeight, statusBarHeight, topDistance, isWechat }
 */
export function useNavbarHeight() {
  const navHeight = ref(0)
  const statusBarHeight = ref(0)
  const topDistance = ref(0)
  const isWechat = ref(false)

  onMounted(() => {
    // #ifdef MP-WEIXIN
    isWechat.value = true
    calculateHeight()
    // #endif

    // #ifdef H5
    isWechat.value = false
    // H5 不需要额外间距
    navHeight.value = 0
    statusBarHeight.value = 0
    topDistance.value = 0
    // #endif
  })

  const calculateHeight = () => {
    try {
      const systemInfo = uni.getSystemInfoSync()
      const menuButtonInfo = uni.getMenuButtonBoundingClientRect()

      statusBarHeight.value = systemInfo.statusBarHeight || 0

      // 计算导航栏高度
      const menuButtonHeight = menuButtonInfo.height || 32
      const menuButtonTop = menuButtonInfo.top || 0
      navHeight.value = menuButtonHeight + (menuButtonTop - statusBarHeight.value) * 2

      // 总距离 = 状态栏高度 + 导航栏高度
      topDistance.value = statusBarHeight.value + navHeight.value
    } catch (err) {
      console.error('获取导航栏高度失败:', err)
      // 使用默认值兜底
      statusBarHeight.value = 20
      navHeight.value = 44
      topDistance.value = 64
    }
  }

  return {
    navHeight,
    statusBarHeight,
    topDistance,
    isWechat
  }
}
