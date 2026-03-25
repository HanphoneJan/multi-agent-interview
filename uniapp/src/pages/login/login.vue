<template>
  <view class="container">
    <view class="login-container">
      <view class="logo-area">
        <image class="logo" src="https://hanphone.top/ai-interview/logo.png" mode="aspectFit" />
        <text class="app-name">AI面试助手</text>
        <text class="app-desc">智能面试 · 专业评估</text>
      </view>

      <view class="form-area">
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="loginIdentifier" 
            placeholder="请输入手机号/邮箱" 
            placeholder-class="placeholder"
            type="text"
          />
        </view>
        <view class="input-group">
          <view class="password-input-wrapper">
            <input
              class="input-field password-field"
              v-model="password"
              placeholder="请输入密码"
              placeholder-class="placeholder"
              :type="showPassword ? 'text' : 'password'"
            />
            <view class="password-toggle-btn" @tap="togglePasswordVisibility">
              <text :class="showPassword ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash'" class="fa-icon"></text>
            </view>
          </view>
        </view>

        <view class="action-row">
          <label class="remember-me">
            <checkbox-group @change="toggleRememberMe">
              <checkbox 
              value="true" :checked="rememberMe"
              color="var(--color-primary)" 
              style="transform:scale(0.8)" 
            />
          </checkbox-group>
            <text class="remember-text">记住我</text>
          </label>
          <text class="forget-password" @tap="onForgetPassword">忘记密码?</text>
        </view>

        <button 
          class="login-btn" 
          :loading="loading" 
          :disabled="!canLogin"
          @tap="onLogin"
        >
          登 录
        </button>

        <view v-if="errorMsg" class="error-msg">
          <text>{{ errorMsg }}</text>
        </view>

        <view class="divider">
          <view class="divider-line"></view>
          <text class="divider-text">其他登录方式</text>
          <view class="divider-line"></view>
        </view>

        <view class="third-party" v-if="!userStore.isH5">
          <button class="wechat-btn" open-type="getPhoneNumber" @tap="onWechatLogin">
            <image class="icon" src="/static/wechat.png" mode="aspectFit" />
          </button>
        </view>
      </view>

      <view class="footer">
        <text class="footer-text">还没有账号?</text>
        <text class="register-link" @tap="onRegister">立即注册</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useUserStore } from '@/stores/user';
import { ENDPOINTS } from '@/stores/api.js';
import { http } from '@/stores/request.js';
import { onShow } from '@dcloudio/uni-app';
const userStore = useUserStore();

const loginIdentifier = ref(''); // 统一存储手机号或邮箱
const password = ref('');
const rememberMe = ref(false);
const loading = ref(false);
const errorMsg = ref('');
const showPassword = ref(false);

const canLogin = computed(() => {
  return loginIdentifier.value.length > 0 && password.value.length >= 6;
});

const toggleRememberMe = (e) => {
  rememberMe.value = e.detail.value[0]; // 通过 .value 修改 ref
};

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};

// 表单验证
const validateForm = () => {
  if (!loginIdentifier.value.trim()) {
    errorMsg.value = '请输入账号';
    return false;
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码长度不能少于6位';
    return false;
  }
  errorMsg.value = '';
  return true;
};

// 判断输入的是手机号还是邮箱
const getLoginData = () => {
  const value = loginIdentifier.value.trim();
  
  // 简单判断是否为手机号格式（11位数字）
  const isPhone = /^\d{11}$/.test(value);
  
  if (isPhone) {
    return { phone: value, password: password.value };
  } else {
    // 否则默认为邮箱格式
    return { email: value, password: password.value };
  }
};

const onLogin = async () => {
  if (!validateForm()) return;

  loading.value = true;
  errorMsg.value = '';

  const loginData = getLoginData();

  try {
    // Use unified login endpoint for phone/email compatibility
    const data = await http.post(ENDPOINTS.user.loginUnified, {
      phone: loginData.phone,
      email: loginData.email,
      password: loginData.password,
    });

    const { access_token, refresh_token } = data;

    if (!access_token || !refresh_token) {
      throw new Error('服务器返回数据不完整');
    }

    console.log('登录成功:', rememberMe.value);

    // 先保存token到storage，这样获取用户资料的请求才能使用token
    uni.setStorageSync('access_token', access_token);
    uni.setStorageSync('refresh_token', refresh_token);

    // Fetch user profile
    const userProfile = await http.get(ENDPOINTS.user.profile);

    // 保存登录状态到Pinia
    // 修复：移除 ...userStore 展开，避免循环引用和存储冗余数据
    // 修复：使用与后端一致的 token 过期时间（30分钟）
    const ACCESS_TOKEN_EXPIRE_MINUTES = 30;
    const tokenExpire = Date.now() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000);

    userStore.setUser({
      username: userProfile.username || loginIdentifier.value,
      userId: userProfile.id,
      name: userProfile.name || '未设置',
      email: userProfile.email || '未设置',
      phone: userProfile.phone || '未设置',
      gender: userProfile.gender || '未设置',
      major: userProfile.major || '未设置',
      university: userProfile.university || '未设置',
      address: userProfile.address || '未设置',
      ethnicity: userProfile.ethnicity || '未设置',
      age: userProfile.age,
      learningStage: userProfile.learning_stage || '未设置',
      avatarUrl: userProfile.avatar_url || 'https://hanphone.top/images/zhuxun.jpg',
      access: access_token,
      refresh: refresh_token,
      isLoggedIn: true,
      tokenExpire: tokenExpire,
      isH5: userStore.isH5,
      platform: userStore.platform
    });

    // 同步保存 token 过期时间到本地存储
    uni.setStorageSync('token_expire', tokenExpire);

    // 如果需要记住我，保存到本地存储
    if (rememberMe.value) {
      uni.setStorageSync('rememberedUser', {
        username: loginIdentifier.value,
        rememberMe: true
      });
    } else {
      uni.removeStorageSync('rememberedUser');
    }

    uni.showToast({
      title: '登录成功',
      icon: 'success',
      success: () => {
        uni.reLaunch({
          url: '/pages/home/home'
        });
      }
    });
  } catch (error) {
    console.error('登录错误:', error);
    errorMsg.value = error.message || '网络错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

function onRegister() {
  console.log('跳转到注册页面');
  uni.navigateTo({
    url: '/pages/register/register'
  });
}

function onForgetPassword() {
  uni.navigateTo({
    url: '/pages/forget-password/forget-password'
  });
}

// 封装uni.login为Promise
const getWechatLoginCode = () => {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: resolve,
      fail: reject
    });
  });
};


function onWechatLogin(e) {
  console.log('微信登录事件:', e);
  
  loading.value = true;
  errorMsg.value = '';

  // 只获取登录code
  getWechatLoginCode()
    .then(loginRes => {
      console.log('登录凭证:', loginRes);
      if (!loginRes.code) {
        throw new Error('获取登录凭证失败');
      }

      // 构造登录参数（不包含用户信息）
      const loginParams = {
        code: loginRes.code
      };
      console.log('登录参数:', loginParams);
      // 调用后端登录接口
      return new Promise((resolve, reject) => {
        uni.request({
          url: ENDPOINTS.user.wechatLogin,
          method: 'POST',
          data: loginParams,
          header: {
            'Content-Type': 'application/json'
          },
          success: resolve,
          fail: reject
        });
      });
    })
    .then(res => {
      const [responseErr, responseData] = Array.isArray(res) ? res : [null, res];
      
      if (responseErr) {
        throw new Error(responseErr.errMsg || '微信登录请求失败');
      }

      if (responseData.statusCode !== 200) {
        throw new Error(responseData.data?.message || '微信登录失败，请重试');
      }

      const { access, refresh, user_id, profile } = responseData.data;
      
      if (!access || !refresh || !user_id) {
        throw new Error('微信登录信息不完整');
      }

      // 保存登录状态（使用后端返回的用户信息）
      // 修复：移除 ...userStore 展开，使用与后端一致的 token 过期时间（30分钟）
      const ACCESS_TOKEN_EXPIRE_MINUTES = 30;
      const tokenExpire = Date.now() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000);

      userStore.setUser({
        username: profile?.username || '微信用户',
        userId: user_id,
        name: profile?.name|| '微信用户',
        avatar_url: profile?.avatar_url || 'https://hanphone.top/images/zhuxun.jpg',
        access: access,
        refresh: refresh,
        isLoggedIn: true,
        tokenExpire: tokenExpire,
        isH5: userStore.isH5,
        platform: userStore.platform
      });

      // 同步保存 token 过期时间到本地存储
      uni.setStorageSync('token_expire', tokenExpire);

      // 登录成功处理
      uni.showToast({
        title: '微信登录成功',
        icon: 'success',
        success: () => {
          uni.reLaunch({
            url: '/pages/home/home'
          });
        }
      });
    })
    .catch(err => {
      console.error('登录流程出错:', err);
      errorMsg.value = err.message || '登录失败，请重试';
    })
    .finally(() => {
      loading.value = false;
    });
}


onShow(() => {
  console.log('登录页面显示');
  // 检查是否有记住的账号
  const rememberedUser = uni.getStorageSync('rememberedUser');
  if (rememberedUser && rememberedUser.rememberMe) {
    console.log('自动填充记住的用户:', rememberedUser);
    loginIdentifier.value = rememberedUser.username;
    rememberMe.value = true;
  }
});

</script>

<style lang="css" scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--bg-page);
  padding: 40rpx;
  box-sizing: border-box;
}

.login-container {
  width: 100%;
  max-width: 800px;
  background-color: var(--bg-card);
  border-radius: 16rpx;
  border: 1rpx solid var(--border-default);
  padding: 60rpx 40rpx;
  box-shadow: var(--shadow-md), var(--shadow-sm);
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;
}

.logo {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 24rpx;
  border-radius: 24rpx;
  box-shadow: var(--shadow-lg);
}

.app-name {
  font-size: 38rpx;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 8rpx;
  letter-spacing: 1rpx;
}

.app-desc {
  font-size: 26rpx;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-area {
  width: 100%;
  box-sizing: border-box;
}

.input-group {
  margin-bottom: 40rpx;
  width: 100%;
  box-sizing: border-box;
}

.input-field {
  width: 100%;
  height: 96rpx;
  padding: 0 32rpx;
  font-size: 30rpx;
  border: 2rpx solid var(--border-default);
  border-radius: 12rpx;
  background-color: var(--bg-page);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
  color: var(--text-primary);
}

.input-field:focus {
  border-color: var(--color-primary);
  background-color: var(--bg-card);
  box-shadow: 0 0 0 4rpx rgba(57, 100, 254, 0.12);
  outline: none;
}

.password-input-wrapper {
  position: relative;
  width: 100%;
}

.password-field {
  padding-right: 80rpx;
}

.password-toggle-btn {
  position: absolute;
  right: 20rpx;
  top: 50%;
  transform: translateY(-50%);
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: transform 0.2s ease;
}

.password-toggle-btn:active {
  transform: translateY(-50%) scale(0.9);
}

/* Font Awesome 眼睛图标 */
.fa-icon {
  font-size: 32rpx;
  color: var(--text-tertiary);
}

.password-toggle-btn:active .fa-icon {
  color: var(--color-primary);
}

.placeholder {
  color: var(--text-placeholder);
  font-size: var(--text-base);
}

.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
  width: 100%;
}

.remember-me {
  display: flex;
  align-items: center;
}

.remember-text {
  font-size: 28rpx;
  color: var(--text-secondary);
  margin-left: 8rpx;
}

.forget-password {
  font-size: 28rpx;
  color: var(--color-primary);
  font-weight: 500;
}

.login-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--text-inverse);
  font-size: 34rpx;
  font-weight: 600;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-btn);
  text-transform: uppercase;
  letter-spacing: 2rpx;
}

.login-btn:active {
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  box-shadow: var(--shadow-btn-active);
  transform: translateY(2rpx);
}

.login-btn:disabled {
  background: var(--bg-disabled);
  box-shadow: none;
  color: var(--text-disabled);
}

.login-btn::after {
  border: none;
}

.error-msg {
  color: var(--color-error);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  text-align: center;
  margin-bottom: 24rpx;
  background-color: var(--color-error-bg);
  padding: 20rpx;
  border-radius: var(--radius-sm);
  width: 100%;
  box-sizing: border-box;
  border-left: 4rpx solid var(--color-error);
}

.divider {
  display: flex;
  align-items: center;
  margin: 48rpx 0;
  width: 100%;
}

.divider-line {
  flex: 1;
  height: 2rpx;
  background-color: var(--border-default);
}

.divider-text {
  padding: 0 24rpx;
  font-size: 26rpx;
  color: #81858c;
  font-weight: 500;
}

.third-party {
  display: flex;
  justify-content: center;
  margin-bottom: 40rpx;
  width: 100%;
}

.wechat-btn {
  width: 88rpx;
  height: 88rpx;
  padding: 0;
  background: none;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: transform 0.3s;
}

.wechat-btn:active {
  transform: scale(0.95);
}

.wechat-btn::after {
  border: none;
}

.icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  box-shadow: 0 4rpx 4rpx rgba(0, 0, 0, 0.1);
}

.footer {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30rpx;
  width: 100%;
}

.footer-text {
  font-size: 28rpx;
  color: var(--text-secondary);
}

.register-link {
  font-size: 28rpx;
  color: var(--color-primary);
  margin-left: 12rpx;
  font-weight: 600;
}

/* PC适配 */
@media (min-width: 768px) {
  .login-container {
    padding: 80rpx 60rpx;
    max-width: 500px;
    border-radius: 20rpx;
  }
  
  .logo {
    width: 160rpx;
    height: 160rpx;
    border-radius: 30rpx;
  }
  
  .app-name {
    font-size: 44rpx;
  }
  
  .app-desc {
    font-size: 30rpx;
  }
  
  .input-field {
    height: 110rpx;
    font-size: 34rpx;
    border-radius: 14rpx;
  }
  
  .login-btn {
    height: 110rpx;
    line-height: 110rpx;
    font-size: 38rpx;
    border-radius: 14rpx;
  }
  
  .error-msg {
    font-size: 28rpx;
    padding: 24rpx;
  }
}
</style>