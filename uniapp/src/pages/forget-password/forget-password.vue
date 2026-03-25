<template>
  <view class="container">
    <view class="reset-container">
      <view class="logo-area">
        <image class="logo" src="https://hanphone.top/ai-interview/logo.png" mode="aspectFit" />
        <text class="app-name">AI面试助手</text>
        <text class="app-desc">找回您的密码</text>
      </view>

      <view class="form-area">
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.email" 
            placeholder="请输入注册邮箱" 
            placeholder-class="placeholder"
            type="text"
          />
        </view>
        
        <view class="input-group with-code">
          <input 
            class="input-field" 
            v-model="formData.verification_code" 
            placeholder="请输入验证码" 
            placeholder-class="placeholder"
            type="number"
          />
          <button 
            class="code-btn" 
            :disabled="codeCountdown > 0"
            @tap="sendVerificationCode"
          >
            {{ codeCountdown > 0 ? `${codeCountdown}s后重试` : '获取验证码' }}
          </button>
        </view>
        
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.new_password" 
            placeholder="请输入新密码(至少8位)" 
            placeholder-class="placeholder"
            type="password"
            password
          />
        </view>
        
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.confirm_password" 
            placeholder="请确认新密码" 
            placeholder-class="placeholder"
            type="password"
            password
          />
        </view>

        <button 
          class="reset-btn" 
          :loading="loading" 
          :disabled="!canReset"
          @tap="onResetPassword"
        >
          重置密码
        </button>

        <view v-if="errorMsg" class="error-msg">
          <text>{{ errorMsg }}</text>
        </view>
      </view>

      <view class="footer">
        <text class="footer-text">记得密码?</text>
        <text class="login-link" @tap="onLogin">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ENDPOINTS } from '@/stores/api.js';
const formData = ref({
  email: '',
  verification_code: '',
  new_password: '',
  confirm_password: ''
});

const codeCountdown = ref(0);
const loading = ref(false);
const errorMsg = ref('');

const canReset = computed(() => {
  return (
    formData.value.email &&
    formData.value.verification_code &&
    formData.value.new_password &&
    formData.value.confirm_password
  );
});

// 表单验证
const validateForm = () => {
  if (!formData.value.email.trim()) {
    errorMsg.value = '请输入邮箱';
    return false;
  }
  
  if (!/^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/.test(formData.value.email)) {
    errorMsg.value = '邮箱格式不正确';
    return false;
  }
  
  if (!formData.value.verification_code) {
    errorMsg.value = '请输入验证码';
    return false;
  }
  
  if (formData.value.new_password.length < 8) {
    errorMsg.value = '新密码长度不能少于8位';
    return false;
  }
  
  if (formData.value.new_password !== formData.value.confirm_password) {
    errorMsg.value = '两次输入的密码不一致';
    return false;
  }
  
  errorMsg.value = '';
  return true;
};

function sendVerificationCode() {
  if (!formData.value.email) {
    errorMsg.value = '请输入邮箱';
    return;
  }
  
  uni.request({
    url: ENDPOINTS.user.resetPasswordRequest,
    method: 'POST',
    data: {
      email: formData.value.email,

    },
    success: (res) => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        codeCountdown.value = 60;
        const timer = setInterval(() => {
          codeCountdown.value--;
          if (codeCountdown.value <= 0) {
            clearInterval(timer);
          }
        }, 1000);
        uni.showToast({
          title: '发送成功',
          icon: 'success'
        });
      } else {
        errorMsg.value = res.data?.detail || res.data?.message || '验证码发送失败';
      }
    },
    fail: (err) => {
      errorMsg.value = '网络错误，请稍后重试';
      console.error('发送验证码失败:', err);
    }
  });
}

async function onResetPassword() {
  if (!validateForm()) return;
  
  loading.value = true;
  errorMsg.value = '';
  
  try {
    // 准备重置密码数据
    const resetData = {
      email: formData.value.email,
      code: formData.value.verification_code,
      new_password: formData.value.new_password,
      confirm_password: formData.value.confirm_password
    };
    
    // 发送重置密码请求
    const res = await uni.request({
      url: ENDPOINTS.user.resetPassword, 
      method: 'POST',
      data: resetData,
      header: {
        'Content-Type': 'application/json'
      }
    });
    
    if (res.statusCode === 200) {
      uni.showToast({ 
        title: '密码重置成功', 
        icon: 'success',
        duration: 3000 // 显示3秒
      });
      await new Promise(resolve => setTimeout(resolve, 3000));
      // 重置成功后跳转到登录页
      onLogin();
    } else {
      errorMsg.value = res.data?.detail || res.data?.message || '密码重置失败，请稍后重试';
    }
  } catch (error) {
    console.error('重置密码错误:', error);
    errorMsg.value = '网络错误，请稍后重试';
  } finally {
    loading.value = false;
  }
}

function onLogin() {
  uni.navigateTo({
    url: '/pages/login/login'
  });
}
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

.reset-container {
  width: 100%;
  max-width: 800rpx;
  background-color: var(--bg-card);
  border-radius: 16rpx;
  border: 1rpx solid var(--border-default); /* 更柔和的边框颜色 */
  padding: 60rpx 40rpx;
  box-shadow: 
    0 1rpx 6rpx rgba(33, 150, 243, 0.1), /* 基础阴影 */
    0 2rpx 10rpx rgba(33, 150, 243, 0.08); /* 扩散阴影 */
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease; /* 添加过渡效果 */
}

.login-container:active {
  transform: translateY(1rpx);
  box-shadow: 
    0 1rpx 3rpx rgba(33, 150, 243, 0.1),
    0 1rpx 5rpx rgba(33, 150, 243, 0.08);
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
  box-shadow: 0 2rpx 6rpx rgba(33, 150, 243, 0.6);
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
}

.input-group {
  margin-bottom: 24rpx;
  position: relative;
  width: 100%;
}

.input-group.with-code {
  display: flex;
  align-items: center;
  width: 100%;
}

.input-field {
  width: 100%;
  height: 80rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid var(--border-default);
  border-radius: 12rpx;
  background-color: var(--bg-page);
  transition: all 0.2s;
  box-sizing: border-box;
}

.input-field:focus {
  border-color: var(--color-primary);
  background-color: var(--bg-card);
  box-shadow: 0 0 0 2rpx rgba(42, 123, 246, 0.2);
}

.code-btn {
  width: 200rpx;
  height: 80rpx;
  line-height: 80rpx;
  font-size: 26rpx;
  color: var(--color-primary);
  background-color: var(--bg-page);
  border-radius: 12rpx;
  margin-left: 20rpx;
  flex-shrink: 0;
  border: none;
  box-sizing: border-box;
  text-align: center;
}

.code-btn:disabled {
  color: var(--text-disabled);
  background-color: var(--bg-disabled);
}

.reset-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--text-inverse);
  font-size: 32rpx;
  border-radius: 12rpx;
  margin: 30rpx 0;
  border: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.reset-btn:active {
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
}

.reset-btn:disabled {
  background: var(--bg-disabled);
  color: var(--text-disabled);
  opacity: 0.7;
}

.reset-btn::after {
  border: none;
}

.error-msg {
  color: var(--color-error);
  font-size: var(--text-sm);
  text-align: center;
  margin-bottom: 20rpx;
  background-color: var(--color-error-bg);
  padding: 16rpx;
  border-radius: 8rpx;
  box-sizing: border-box;
}

.footer {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20rpx;
}

.footer-text {
  font-size: 26rpx;
  color: var(--text-secondary);
}

.login-link {
  font-size: 28rpx;
  color: var(--color-primary);
  margin-left: 12rpx;
  font-weight: 600;
  text-decoration: underline;
}

/* PC适配 */
@media (min-width: 768px) {
  .reset-container {
    padding: 60rpx 80rpx;
    max-width: 500px;
  }
  
  .logo {
    width: 150rpx;
    height: 150rpx;
    border-radius: 30rpx;
  }
  
  .app-name {
    font-size: 40rpx;
  }
  
  .app-desc {
    font-size: 28rpx;
  }
  
  .input-field {
    height: 90rpx;
    font-size: 30rpx;
  }
  
  .code-btn {
    height: 90rpx;
    line-height: 90rpx;
    font-size: 28rpx;
  }
  
  .reset-btn {
    height: 100rpx;
    line-height: 100rpx;
    font-size: 36rpx;
  }
  
  .footer-text,
  .login-link {
    font-size: 28rpx;
  }
}
</style>
