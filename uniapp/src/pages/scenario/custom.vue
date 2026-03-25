<template>
  <WebNavbar>
    <view class="custom-container">
    <!-- 主要内容 -->
    <view class="main-content">
      <!-- 加载状态遮罩 -->
      <view v-if="loading" class="loading-mask">
        <view class="loading-container">
          <uni-load-more status="loading"></uni-load-more>
          <text class="loading-text">提交中...</text>
        </view>
      </view>
      
      <view v-else class="form-container">
        <text class="section-title">自定义面试岗位</text>
        <text class="section-desc">请填写详细信息，帮助更好地匹配面试内容</text>
        
        <form class="custom-form" @submit="handleSubmit">
                <!-- 岗位名称 -->
                <view class="form-group">
                <text class="form-label">岗位名称 *</text>
                <input 
                    type="text" 
                    v-model="formData.name"
                    placeholder="例如：数据科学家面试" 
                    @blur="validateField('name')"
                    name="name"
                    class="form-input"
                />
                <text class="error-text" v-if="errors.name">{{ errors.name }}</text>
                </view>

                <!-- 技术领域 -->
                <view class="form-group">
                <text class="form-label">技术领域 *</text>
                <input 
                    type="text" 
                    v-model="formData.technology_field"
                    placeholder="例如：Data Science、前端开发、人工智能" 
                    class="form-input"
                    @blur="validateField('technology_field')"
                    name="technology_field"
                />
                <text class="error-text" v-if="errors.technology_field">{{ errors.technology_field }}</text>
                </view>

                <!-- 岗位描述 -->
                <view class="form-group">
                <text class="form-label">岗位描述 *</text>
                <textarea 
                    :value="formData.description" 
                    @input="formData.description = $event.detail.value"
                    placeholder="请详细描述考察内容，例如：考察机器学习、统计分析和Python" 
                    class="form-textarea"
                    :class="{ 'input-error': errors.description }"
                    rows="4"
                    @blur="validateField('description')"
                    name="description"
                ></textarea>
                <text class="char-count">{{ formData.description.length }}/500</text>
                <text class="error-text" v-if="errors.description">{{ errors.description }}</text>
                </view>

                <!-- 技能要求 -->
                <view class="form-group">
                <text class="form-label">技能要求 *</text>
                <textarea 
                    :value="formData.requirements" 
                    @input="formData.requirements = $event.detail.value"
                    placeholder="请描述所需技能，例如：熟练使用Python语言" 
                    class="form-textarea"
                    :class="{ 'input-error': errors.requirements }"
                    rows="3"
                    @blur="validateField('requirements')"
                    name="requirements"
                ></textarea>
                <text class="char-count">{{ formData.requirements.length }}/300</text>
                <text class="error-text" v-if="errors.requirements">{{ errors.requirements }}</text>
                </view>
          
          <!-- 全局错误提示 -->
          <view v-if="globalError" class="global-error">
            <uni-icons type="warn" size="16" color="#e74c3c"></uni-icons>
            <text>{{ globalError }}</text>
          </view>
          
          <!-- 提交按钮 -->
          <button 
            type="submit"
            class="submit-btn"
            @click="handleSubmit"
            :disabled=" loading"
          >
            确认上传
          </button>
        </form>
      </view>
    </view>

    <!-- 确认弹窗 -->
    <uni-popup ref="confirmDialog" type="dialog" :animation="true">
      <uni-popup-dialog 
        type="info" 
        title="确认上传" 
        :content="confirmContent" 
        @confirm="submitCustomScenario" 
        @close="closeConfirmDialog"
      ></uni-popup-dialog>
    </uni-popup>

    <!-- 成功提示弹窗 -->
    <uni-popup ref="successDialog" type="dialog" :animation="true">
      <uni-popup-dialog 
        type="success" 
        title="上传成功" 
        :content="`自定义面试岗位已成功上传，${countdown}秒后返回面试准备界面`" 
        @confirm="navigateBack" 
      ></uni-popup-dialog>
    </uni-popup>
  </view>
  </WebNavbar>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user.js'
import { ENDPOINTS } from '@/stores/api.js';
import WebNavbar from '@/components/WebNavbar.vue'
import uniIcons from '@dcloudio/uni-ui/lib/uni-icons/uni-icons.vue'

const userStore = useUserStore()

// 表单数据 - 确保初始化为空字符串
const formData = ref({
  name: '',
  technology_field: '',
  description: '',
  requirements: ''
})

// 状态管理
const loading = ref(false)
const globalError = ref(null)
const confirmDialog = ref(null)
const successDialog = ref(null)
const countdown = ref(3)
let countdownTimer = null

// 字段错误信息
const errors = ref({
  name: '',
  technology_field: '',
  description: '',
  requirements: ''
})


// 处理表单提交
const handleSubmit = () => {
    console.log(11)
  if (loading.value) return; // 防止重复提交
  
  // 表单提交时进行全量验证
  if (1) {
    // 验证通过，显示确认弹窗
    console.log(222)
    confirmDialog.value.open()
  } else {
    // 验证失败，滚动到第一个错误字段
    const firstErrorField = Object.keys(errors.value).find(field => errors.value[field])
    if (firstErrorField) {
      const element = document.querySelector(`[name="${firstErrorField}"]`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        element.focus()
      }
    }
    // 显示全局错误提示
    globalError.value = '表单填写有误，请检查并修正后再提交'
    // 3秒后自动清除全局错误提示
    setTimeout(() => {
      globalError.value = null
    }, 3000)
  }
}

// 字段验证
const validateField = (field) => {
  switch(field) {
    case 'name':
      if (!formData.value.name.trim()) {
        errors.value.name = '请输入岗位名称'
      } else if (formData.value.name.length > 50) {
        errors.value.name = '岗位名称不能超过50个字符'
      } else {
        errors.value.name = ''
      }
      break
      
    case 'technology_field':
      if (!formData.value.technology_field.trim()) {
        errors.value.technology_field = '请输入技术领域'
      } else if (formData.value.technology_field.length > 100) {
        errors.value.technology_field = '技术领域不能超过100个字符'
      } else {
        errors.value.technology_field = ''
      }
      break
      
    case 'description':
      if (!formData.value.description.trim()) {
        errors.value.description = '请输入岗位描述'
      } else if (formData.value.description.length < 10) {
        errors.value.description = '岗位描述不能少于10个字符'
      } else if (formData.value.description.length > 500) {
        errors.value.description = '岗位描述不能超过500个字符'
      } else {
        errors.value.description = ''
      }
      break
      
    case 'requirements':
      if (!formData.value.requirements.trim()) {
        errors.value.requirements = '请输入技能要求'
      } else if (formData.value.requirements.length < 5) {
        errors.value.requirements = '技能要求不能少于5个字符'
      } else if (formData.value.requirements.length > 300) {
        errors.value.requirements = '技能要求不能超过300个字符'
      } else {
        errors.value.requirements = ''
      }
      break
  }
}



// 确认弹窗内容
const confirmContent = computed(() => {
  return `
    您确定要上传以下岗位信息吗？\n
    岗位名称：${formData.value.name}\n
    技术领域：${formData.value.technology_field}\n
    岗位描述：${formData.value.description.substring(0, 20)}${formData.value.description.length > 20 ? '...' : ''}\n
    技能要求：${formData.value.requirements.substring(0, 20)}${formData.value.requirements.length > 20 ? '...' : ''}
  `
})

// 对话框控制
const closeConfirmDialog = () => {
  confirmDialog.value.close()
}

// 提交自定义岗位
const submitCustomScenario = async () => {
  loading.value = true
  globalError.value = null
  
  try {
    // 准备提交的数据
    const submitData = {
      name: formData.value.name.trim(),
      technology_field: formData.value.technology_field.trim(),
      description: formData.value.description.trim(),
      requirements: formData.value.requirements.trim()
    }
    
    const res = await uni.request({
      url: ENDPOINTS.interview.scenarios,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: JSON.stringify(submitData)
    })
    
    if (res.statusCode === 200 || res.statusCode === 201) {
      // 上传成功，显示成功提示
      closeConfirmDialog()
      successDialog.value.open()
      startCountdown()
    } else {
      // 处理后端返回的字段错误
      if (res.data.errors) {
        Object.keys(res.data.errors).forEach(field => {
          if (errors.value.hasOwnProperty(field)) {
            errors.value[field] = res.data.errors[field][0]
          }
        })
      } else {
        throw new Error(res.data.message || '上传自定义岗位失败')
      }
    }
  } catch (err) {
    console.error('上传失败:', err)
    globalError.value = err.message
    uni.showToast({
      title: err.message || '上传失败，请重试',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

// 倒计时功能
const startCountdown = () => {
  countdown.value = 3
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      navigateBack()
    }
  }, 1000)
}

// 返回场景列表页
const navigateBack = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  successDialog.value.close()
    uni.switchTab({
    url: `/pages/learn/ready`
    })
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  // 清理所有输入定时器
  Object.keys(formData.value).forEach(field => {
    clearTimeout(window[`${field}Timer`]);
  });
})
</script>

<style lang="css" scoped>
/* 全局容器样式 - 更柔和的背景渐变 */
.custom-container {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-page) 0%, #e8f1ff 100%);
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
}

/* 主要内容区域 - 添加更精致的阴影 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  padding: 20px 0;
}

/* 加载状态遮罩 - 更现代的加载效果 */
.loading-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
  backdrop-filter: blur(3px);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  background: var(--bg-card);
  padding: 30px 40px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(74, 144, 226, 0.15);
}

.loading-text {
  color: var(--color-primary);
  font-size: 16px;
  font-weight: 500;
}

/* 表单容器 - 更精致的卡片效果 */
.form-container {
  width: 100%;
  background-color: var(--bg-card);
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 8px 24px rgba(74, 144, 226, 0.1);
  margin-bottom: 25px;
  transition: all 0.3s ease;
}

.section-title {
  display: block;
  font-size: 20px;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: 8px;
  text-align: center;
  letter-spacing: 0.5px;
}

.section-desc {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 30px;
  line-height: 1.5;
}

/* 表单样式 - 更精致的输入控件 */
.custom-form {
  width: 100%;
}

.form-group {
  margin-bottom: 24px;
  position: relative;
}

.form-label {
  display: block;
  font-size: 15px;
  color: var(--text-primary);
  margin-bottom: 10px;
  font-weight: 500;
}

.form-input {
  width: 95%;
  font-size: 15px;
  color: var(--text-primary);
  padding: 12px 15px;
  border: 1px solid var(--border-default);
  border-radius: 10px;
  transition: all 0.3s ease;
  background-color: var(--bg-page);
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2);
  background-color: var(--bg-card);
}

.form-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--border-default);
  border-radius: 10px;
  font-size: 15px;
  box-sizing: border-box;
  transition: all 0.3s ease;
  background-color: var(--bg-page);
  line-height: 1.6;
}

.form-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2);
  background-color: var(--bg-card);
}

/* 错误状态样式 - 更明显的错误提示 */
.input-error {
  border-color: var(--color-error) !important;
}

.error-text {
  display: block;
  color: var(--color-error);
  font-size: 13px;
  margin-top: 6px;
  line-height: 1.4;
}

.global-error {
  color: var(--color-error);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 15px;
  background-color: #fff5f5;
  border-radius: 10px;
  margin: 20px 0;
  border: 1px solid #ffdddd;
}

/* 字符计数 - 更精致的设计 */
.char-count {
  display: block;
  text-align: right;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 5px;
}

/* 提交按钮样式 - 渐变按钮效果 */
.submit-btn {
  width: 100%;
  max-width: 300px;
  background: linear-gradient(135deg, var(--color-primary) 0%, #3a7bd5 100%);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 16px;
  font-size: 16px;
  font-weight: 500;
  margin: 25px auto 10px;
  display: block;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
  transition: all 0.3s ease;
  cursor: pointer;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
}

.submit-btn:disabled {
  background: var(--text-tertiary);
  box-shadow: none;
  transform: none !important;
  cursor: not-allowed;
}

.submit-btn:not(:disabled):active {
  transform: translateY(1px);
  box-shadow: 0 2px 10px rgba(74, 144, 226, 0.3);
}

/* 响应式调整 - 更好的移动端体验 */
@media (max-width: 568px) {
  .custom-container {
    padding: 15px;
  }
  


  .form-container {
    padding: 20px;
    border-radius: 12px;
  }
  
  .section-title {
    font-size: 18px;
    margin-top:30px;
  }
  
  .section-desc {
    font-size: 13px;
  }
  
  .form-input, .form-textarea {
    padding: 12px;
  }
  
  .submit-btn {
    padding: 14px;
  }
}

/* 添加微妙的动画效果 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-container {
  animation: fadeIn 0.4s ease-out forwards;
}

.form-group {
  animation: fadeIn 0.5s ease-out forwards;
}

/* 延迟每个表单项的动画 */
.form-group:nth-child(1) { animation-delay: 0.1s; }
.form-group:nth-child(2) { animation-delay: 0.2s; }
.form-group:nth-child(3) { animation-delay: 0.3s; }
.form-group:nth-child(4) { animation-delay: 0.4s; }
</style>
    