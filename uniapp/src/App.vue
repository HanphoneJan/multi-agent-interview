<script>
import { useUserStore } from '@/stores/user';
import { ENDPOINTS } from '@/stores/api.js';
export default {
  data() {
    return {
      _refreshTimer: null,
      userStore: useUserStore(),
      isRefreshing: false,
      // 添加刷新冷却期，避免短时间内重复刷新
      refreshCooldown: 60000 // 1分钟冷却期
    }
  },
  onLaunch() {
    console.log('App Launch');
    this.initAuthSystem();
    this.detectPlatform();
    if (this.userStore.isH5 && window.innerWidth>768) {
      document.documentElement.style.setProperty('--navbar-height', '60px');
      console.log('PC端，设置导航栏高度为60px');
    }
  },
  onShow() {
    console.log('App Show');
    this.checkTokenStatus();
  },
  onHide() {
    clearTimeout(this._refreshTimer);
  },
  methods: {
    async initAuthSystem() {
      this.setupInterceptors();
      
      if (this.userStore.isLoggedIn) {
        this.setupTokenRefresh(); // 这里不需要await，避免阻塞初始化
      }
    },
    
    setupInterceptors() {
      const whiteList = [
        '/users/register',
        '/users/login',
        '/users/refresh',
        '/users/login-unified',
        '/users/wechat/login'
      ];
      
      uni.addInterceptor('request', {
        invoke: (args) => {
          const isWhiteListed = whiteList.some(url => args.url.includes(url));
          
          // FIX: 直接从 localStorage 读取 token，避免 Pinia 状态同步问题
          const token = uni.getStorageSync('access_token');
          if (token && !isWhiteListed) {
            args.header = args.header || {};
            args.header.Authorization = `Bearer ${token}`;
          }
          return args;
        },
        fail: (err) => {
          return Promise.reject(err);
        }
      });
      
      // Note: 401 handling is done in request.js to avoid duplicate redirects
      // This prevents multiple login page redirects when token expires
    },
    
    setupTokenRefresh() {
      // 清除现有定时器，防止重复设置
      clearTimeout(this._refreshTimer);
      
      // 如果未登录或正在刷新，不设置定时器
      if (!this.userStore.isLoggedIn || this.isRefreshing) {
        return;
      }
      
      // 计算剩余有效时间（提前10分钟刷新）
      const remainingTime = this.userStore.tokenExpire - Date.now() - 600000;
      // 确保时间不小于0，且至少有冷却期的时间
      const delay = Math.max(remainingTime, this.refreshCooldown);
      
      console.log(`设置下一次Token刷新，延迟 ${delay/1000} 秒`);
      
      // 设置定时刷新
      this._refreshTimer = setTimeout(async () => {
        try {
          const refreshSuccess = await this.refreshToken();
          // 只有刷新成功后才设置下一次刷新
          if (refreshSuccess) {
            this.setupTokenRefresh();
          }
        } catch (error) {
          console.error('定时刷新Token失败:', error);
        }
      }, delay);
    },
    
    async refreshToken() {
      if (this.isRefreshing) {
        return new Promise(resolve => {
          const checkRefresh = setInterval(() => {
            if (!this.isRefreshing) {
              clearInterval(checkRefresh);
              resolve(this.userStore.access ? true : false);
            }
          }, 100);
        });
      }
      
      if (!this.userStore.refresh) {
        console.error('刷新Token失败: refresh令牌缺失');
        return false;
      }
      
      try {
        this.isRefreshing = true;
        
        const res = await uni.request({
          url: ENDPOINTS.user.refresh,
          method: 'POST',
          data: { refresh: this.userStore.refresh }
        });
        
        const [responseErr, responseData] = Array.isArray(res) ? res : [null, res];
        if (responseErr) {
          throw new Error(responseErr.errMsg || '网络请求失败');
        }
        
        console.log('Token获取成功');
        const data = responseData.data;
        // FastAPI returns { access_token, refresh_token }, Django returns { access, refresh }
        const access = data.access_token || data.access;
        const refresh = data.refresh_token || data.refresh || this.userStore.refresh;

        // 更新store，设置新的过期时间
        // 修复：移除 ...this.userStore 展开，使用与后端一致的 token 过期时间（30分钟）
        const ACCESS_TOKEN_EXPIRE_MINUTES = 30;
        const tokenExpire = Date.now() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000);

        this.userStore.setUser({
          access: access,
          refresh: refresh,
          tokenExpire: tokenExpire,
          isLoggedIn: true,
          isH5: this.userStore.isH5,
          platform: this.userStore.platform
        });

        // 同步更新本地存储
        uni.setStorageSync('token_expire', tokenExpire);
        
        console.log('Token刷新成功，新的过期时间:', new Date(this.userStore.tokenExpire).toLocaleString());
        return true;
      } catch (error) {
        console.error('刷新Token失败:', error);
        this.logout();
        return false;
      } finally {
        this.isRefreshing = false;
      }
    },
    
    handleTokenExpired() {
      clearTimeout(this._refreshTimer);
      
      if (this.isRefreshing) return;
      
      this.refreshToken().then(success => {
        if (success) {
          // 刷新成功后设置下一次刷新
          this.setupTokenRefresh();
        } else {
          this.logout();
          uni.showToast({ title: '登录已过期', icon: 'none' });
          uni.navigateTo({ url: '/pages/login/login' });
        }
      });
    },
    
    logout() {
      this.userStore = useUserStore();
      this.userStore.clearUser();
      clearTimeout(this._refreshTimer);
      this.isRefreshing = false;
    },
    
    checkTokenStatus() {
      this.userStore = useUserStore();
      if (this.userStore.isLoggedIn && this.userStore.tokenExpire < Date.now()) {
        this.handleTokenExpired();
      }
    },
    
    detectPlatform() {
      try {
        const systemInfo = uni.getSystemInfoSync();
        const platform = systemInfo.platform;
        this.userStore.platform = platform;
        console.log('检测到平台:', platform);
        
        if (process.env.VUE_APP_PLATFORM === 'h5') {
          console.log('H5环境，窗口宽度:', window.innerWidth);
          this.userStore.isH5 = true;
          return;
        } else {
          const isH5 = ['windows', 'mac', 'linux', 'web', 'h5'].includes(platform)
          this.userStore.isH5 = isH5;
        }
      } catch (error) {
        console.error('检测平台失败:', error);
      }
    }
  }
}  
</script>

<style>
/* 引入主题变量 */
@import './styles/theme.css';

/* Font Awesome CDN */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');

/* 全局CSS变量 */
:root {
  --safe-area-inset-bottom: env(safe-area-inset-bottom);
  --navbar-height: 0px;
}

/* 基础样式重置 */
page {
  background-color: var(--bg-page);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               'Helvetica Neue', Arial, sans-serif;
  box-sizing: border-box;
}

/* 跨平台适配方案 */
/* 移动端样式 */
@media screen and (max-width: 768px) {
  .web-navbar {
    display: none !important;
  }
  
  .page-container {
    padding-bottom: calc(50px + var(--safe-area-inset-bottom));
  }
}

/* 网页端样式 */
@media screen and (min-width: 769px) {
  uni-tabbar {
    display: none !important;
  }
  
  .uni-app--web {
    padding-top: 0;
  }
  
  .web-navbar {
    display: flex !important;
  }
  
  .page-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
}

/* 安全区域适配 */
.safe-area-inset-bottom {
  padding-bottom: var(--safe-area-inset-bottom);
}

/* 全局工具类 */
.text-primary {
  color: var(--color-primary);
}

.bg-primary {
  background-color: var(--color-primary);
}

.flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 解决uniapp按钮默认样式问题 */
button::after {
  border: none;
}

button {
  background-color: transparent;
  padding: 0;
  margin: 0;
  line-height: inherit;
  border-radius: 0;
}

/* 解决iOS滚动回弹效果 */
::-webkit-scrollbar {
  display: none;
  width: 0 !important;
  height: 0 !important;
  -webkit-appearance: none;
  background: transparent;
}
</style>
    