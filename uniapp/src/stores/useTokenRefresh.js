import { useUserStore } from '@/stores/user'
import { ENDPOINTS } from '@/stores/api.js';

// Token 过期时间配置（与后端保持一致）
const ACCESS_TOKEN_EXPIRE_MINUTES = 30;
const REFRESH_TOKEN_EXPIRE_DAYS = 7;

export function useTokenRefresh() {
  const userStore = useUserStore()

  const refreshToken = async () => {
    // 检查refresh令牌是否存在
    if (!userStore.refresh) {
      console.error('刷新Token失败: refresh令牌缺失')
      return false
    }

    try {
      // 发起请求到FastAPI端点
      const res = await uni.request({
        url: ENDPOINTS.user.refresh,
        method: 'POST',
        data: { refresh: userStore.refresh }
      })

      // 处理响应格式
      const [responseErr, responseData] = Array.isArray(res) ? res : [null, res]

      if (responseErr) {
        throw new Error(responseErr.errMsg || '网络请求失败')
      }

      if (responseData.statusCode !== 200) {
        throw new Error(responseData.data?.detail || 'Token刷新失败')
      }

      console.log('Token获取成功')
      const data = responseData.data
      // FastAPI returns { access_token, refresh_token, token_type }
      const access = data.access_token || data.access
      const refresh = data.refresh_token || data.refresh || userStore.refresh

      // 计算新的过期时间（与后端 JWT_ACCESS_TOKEN_EXPIRE_MINUTES 保持一致）
      const tokenExpire = Date.now() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000)

      // 更新存储 - 修复：不使用展开运算符，避免循环引用和存储冗余数据
      // 注意：保留 isH5 和 platform 等现有值
      userStore.setUser({
        access,
        refresh,
        tokenExpire,
        isLoggedIn: true,
        isH5: userStore.isH5,
        platform: userStore.platform
      })

      // 同步更新本地存储
      uni.setStorageSync('access_token', access)
      uni.setStorageSync('refresh_token', refresh)
      uni.setStorageSync('token_expire', tokenExpire)

      console.log('Token刷新成功，新过期时间:', new Date(tokenExpire).toLocaleString())
      return true

    } catch (error) {
      console.error('刷新Token失败:', error)
      // 修复：调用 clearUser() 而不是不存在的 logout()
      userStore.clearUser()
      // 清除本地存储
      uni.removeStorageSync('access_token')
      uni.removeStorageSync('refresh_token')
      uni.removeStorageSync('token_expire')
      return false
    }
  }

  /**
   * 检查token是否需要刷新
   * @returns {boolean} 是否需要刷新
   */
  const shouldRefreshToken = () => {
    if (!userStore.tokenExpire) return false

    // 如果token将在5分钟内过期，则需要刷新
    const fiveMinutes = 5 * 60 * 1000
    return userStore.tokenExpire - Date.now() < fiveMinutes
  }

  /**
   * 清除token并重定向到登录页
   */
  const handleAuthError = () => {
    userStore.clearUser()
    uni.removeStorageSync('access_token')
    uni.removeStorageSync('refresh_token')
    uni.removeStorageSync('token_expire')

    uni.showToast({
      title: '登录已过期，请重新登录',
      icon: 'none',
    })

    setTimeout(() => {
      uni.reLaunch({ url: '/pages/login/login' })
    }, 1500)
  }

  return {
    refreshToken,
    shouldRefreshToken,
    handleAuthError,
    // 导出配置供其他模块使用
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
  }
}
