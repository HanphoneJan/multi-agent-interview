<template>
  <view class="container">
    <view class="register-container">
      <view class="logo-area">
        <image class="logo" src="https://hanphone.top/ai-interview/logo.png" mode="aspectFit" />
        <text class="app-name">AI面试助手</text>
        <text class="app-desc">智能面试 · 专业评估</text>
      </view>

      <view class="form-area">
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.name" 
            placeholder="请输入姓名" 
            placeholder-class="placeholder"
            type="text"
          />
        </view>
                
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.username" 
            placeholder="请输入用户名(至少两个字符)" 
            placeholder-class="placeholder"
            type="text"
          />
        </view>
        
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.password" 
            placeholder="请输入密码(至少8位)" 
            placeholder-class="placeholder"
            type="password"
            password
          />
        </view>
        
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.confirm_password" 
            placeholder="请确认密码" 
            placeholder-class="placeholder"
            type="password"
            password
          />
        </view>
        
        <view class="input-group">
          <input 
            class="input-field" 
            v-model="formData.email" 
            placeholder="请输入邮箱" 
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
            v-model="formData.phone"
            placeholder="请输入手机号"
            placeholder-class="placeholder"
            type="number"
          />
        </view>

        <button 
          class="register-btn" 
          :loading="loading" 
          :disabled="!canRegister"
          @tap="onRegister"
        >
          注 册
        </button>

        <view v-if="errorMsg" class="error-msg">
          <text>{{ errorMsg }}</text>
        </view>

        <view class="agreement">
          <label class="agreement-label">
            
          <checkbox-group @change="handleAgreementChange">
              <checkbox 
              value="true" :checked="agreed"
              color="var(--color-primary)" 
              style="transform:scale(0.8)" 
            />
          </checkbox-group>

            <text class="agreement-text">我已阅读并同意</text>
          </label>
          <text class="agreement-link" @tap="onViewAgreement">《用户协议》</text>
          <text class="agreement-text">和</text>
          <text class="agreement-link" @tap="onViewPrivacy">《隐私政策》</text>
        </view>
      </view>

      <view class="footer">
        <text class="footer-text">已有账号?</text>
        <text class="login-link" @tap="onLogin">立即登录</text>
      </view>
    </view>
  </view>

</template>

<script setup>
import { ref, computed } from 'vue';
import { ENDPOINTS } from '@/stores/api';
const formData = ref({
  name: '',
  email: '',
  username: '',
  password: '',
  confirm_password: '',
  verification_code: '',
  phone: ''
});

const codeCountdown = ref(0);
const loading = ref(false);
const errorMsg = ref('');
const agreed = ref(true);

const handleAgreementChange = (e) => {
  agreed.value = e.detail.value[0]; // 通过 .value 修改 ref
};

// 表单验证
const validateForm = () => {
  if (!formData.value.name.trim()) {
    errorMsg.value = '请输入姓名';
    return false;
  }
  
  if (!formData.value.email.trim()) {
    errorMsg.value = '请输入邮箱';
    return false;
  }
  
  if (!/^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/.test(formData.value.email)) {
    errorMsg.value = '邮箱格式不正确';
    return false;
  }
  
  if (formData.value.username.length < 2) {
    errorMsg.value = '用户名至少2位';
    return false;
  }
  
  if (formData.value.password.length < 8) {
    errorMsg.value = '密码长度不能少于8位';
    return false;
  }
  
  if (formData.value.password !== formData.value.confirm_password) {
    errorMsg.value = '两次输入的密码不一致';
    return false;
  }
  
  if (!formData.value.verification_code) {
    errorMsg.value = '请输入验证码';
    return false;
  }
  
  if (!/^1[3-9]\d{9}$/.test(formData.value.phone)) {
    errorMsg.value = '手机号格式不正确';
    return false;
  }

  if (!agreed.value) {
    errorMsg.value = '请阅读并同意用户协议和隐私政策';
    return false;
  }
  
  errorMsg.value = '';
  return true;
};

// 发送验证码
function sendVerificationCode() {
  if (!formData.value.email) {
    errorMsg.value = '请输入邮箱';
    return;
  }
  
  uni.request({
    url: ENDPOINTS.user.sendVerificationCode,
    method: 'POST',
    data: {
      email: formData.value.email
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

// 注册
async function onRegister() {
  if (!validateForm()) return;
  
  loading.value = true;
  errorMsg.value = '';

  try {
    // 准备注册数据（简化版，仅包含必要字段）
    const registerData = {
      name: formData.value.name,
      email: formData.value.email,
      username: formData.value.username,
      code: formData.value.verification_code,
      password: formData.value.password,
      phone: formData.value.phone
    };
    
    // 发送注册请求
    const res = await uni.request({
      url: ENDPOINTS.user.register,
      method: 'POST',
      data: registerData,
      header: {
        'Content-Type': 'application/json'
      }
    });
    
    if (res.statusCode === 201 && res.data?.access_token && res.data?.refresh_token) {
      uni.showToast({ 
        title: '注册成功', 
        icon: 'success',
        success: () => {
          // 注册成功后跳转到登录页
            onLogin()
        }
      });
    } else {
      errorMsg.value = res.data?.detail || res.data?.message || '注册失败，请稍后重试';
    }
  } catch (error) {
    console.error('注册错误:', error);
    errorMsg.value = '网络错误，请稍后重试';
  } finally {
    loading.value = false;
  }
}

// 登录页跳转
function onLogin() {
  uni.navigateTo({
    url: '/pages/login/login'
  });
}

// 协议查看
function onViewAgreement() {
  uni.navigateTo({
    url: '/pages/agreement/agreement'
  });
}

// 隐私政策查看
function onViewPrivacy() {
  uni.navigateTo({
    url: '/pages/privacy/privacy'
  });
}

// 注册按钮启用条件（简化版，仅必要字段）
const canRegister = computed(() => {
  return (
    formData.value.name &&
    formData.value.email &&
    formData.value.username &&
    formData.value.password &&
    formData.value.confirm_password &&
    formData.value.verification_code &&
    formData.value.phone &&
    agreed.value
  );
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

.register-container {
  width: 100%;
  max-width: 800px;
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
  box-sizing: border-box;
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
  box-shadow: 0 0 0 4rpx rgba(25, 118, 210, 0.2);
  outline: none;
}

.placeholder {
  color: var(--text-tertiary);
  font-size: 28rpx;
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
  color: var(--text-tertiary);
  background-color: var(--bg-page);
}

/* 选择器样式 */
.picker-container {
  width: 100%;
  box-sizing: border-box;
}

.picker-view {
  width: 100%;
  height: 80rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid var(--border-default);
  border-radius: 12rpx;
  background-color: var(--bg-page);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s;
  box-sizing: border-box;
}

.picker-view:active {
  border-color: var(--color-primary);
  background-color: var(--bg-card);
  box-shadow: 0 0 0 2rpx rgba(42, 123, 246, 0.2);
}

.picker-arrow {
  color: var(--text-tertiary);
  font-size: 24rpx;
  transition: color 0.2s;
}

.picker-view:active .picker-arrow {
  color: var(--color-primary);
}

.placeholder {
  color: var(--text-tertiary);
  font-size: 28rpx;
}

.register-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  background-color: var(--color-primary);
  color: var(--bg-card);
  font-size: 34rpx;
  font-weight: 600;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4rpx 8rpx rgba(25, 118, 210, 0.3);
  text-transform: uppercase;
  letter-spacing: 2rpx;
}

.register-btn:active {
  background-color: var(--color-primary);
  box-shadow: 0 2rpx 4rpx rgba(25, 118, 210, 0.3);
  transform: translateY(2rpx);
}

.register-btn:disabled {
  background-color: var(--border-default);
  box-shadow: none;
  color: var(--text-tertiary);
}

.register-btn::after {
  border: none;
}

.error-msg {
  color: var(--color-error);
  font-size: 24rpx;
  text-align: center;
  margin-bottom: 20rpx;
  background-color: var(--bg-page);
  padding: 16rpx;
  border-radius: 8rpx;
  box-sizing: border-box;
}

.agreement {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.agreement-label {
  display: flex;
  align-items: center;
}

.agreement-text {
  font-size: 24rpx;
  color: var(--text-secondary);
}

.agreement-link {
  font-size: 24rpx;
  color: var(--color-primary);
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
  .register-container {
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
  
  .input-field, .picker-view {
    height: 90rpx;
    font-size: 30rpx;
  }
  
  .code-btn {
    height: 90rpx;
    line-height: 90rpx;
    font-size: 28rpx;
  }
  
  .register-btn {
    height: 100rpx;
    line-height: 100rpx;
    font-size: 36rpx;
  }
  
  .agreement-text,
  .agreement-link {
    font-size: 26rpx;
  }
}
</style>
