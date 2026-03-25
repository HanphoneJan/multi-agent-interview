<template>
  <WebNavbar>
    <view class="interviewer-container">
    <!-- 主要内容 -->
    <view class="main-content">
      <!-- 加载状态 -->
      <view v-if="loading" class="loading-container">
        <uni-load-more status="loading"></uni-load-more>
      </view>
      
      <view v-else class="customize-form">
        <text class="section-title">定制您的面试官</text>
        
        <!-- 性别选择 -->
        <view class="form-section">
          <text class="section-label">选择性别</text>
          <radio-group @change="handleGenderChange" class="radio-group">
            <label class="radio-item" v-for="gender in genders" :key="gender.value">
              <text class="radio-text">{{ gender.label }}</text>
              <radio :value="gender.value" :checked="selectedGender === gender.value" color="var(--color-primary)" />
            </label>
          </radio-group>
        </view>
        
        <!-- 语速选择 -->
        <view class="form-section">
          <text class="section-label">语速设置</text>
          <view class="speed-control">
            <text class="speed-label">慢</text>
            <slider
              :value="selectedSpeed"
              min="1"
              max="5"
              step="1"
              @change="handleSpeedChange"
              activeColor="var(--color-primary)"
              backgroundColor="var(--bg-page)"
            ></slider>
            <text class="speed-label">快</text>
          </view>
          <text class="speed-value">{{ speedOptions[selectedSpeed - 1].label }}</text>
        </view>
        
        <!-- 音色选择 -->
        <view class="form-section">
          <text class="section-label">选择音色</text>
          <radio-group @change="handleVoiceChange" class="radio-group">
            <label class="radio-item" v-for="voice in voiceTypes" :key="voice.value">
              <text class="radio-text">{{ voice.label }}</text>
              <radio :value="voice.value" :checked="selectedVoice === voice.value" color="var(--color-primary)" />
            </label>
          </radio-group>
        </view>
        
        <!-- 面试风格选择 -->
        <view class="form-section">
          <text class="section-label">面试风格</text>
          <radio-group @change="handleStyleChange" class="radio-group">
            <label class="radio-item" v-for="style in interviewStyles" :key="style.value">
              <text class="radio-text">{{ style.label }}</text>
              <radio :value="style.value" :checked="selectedStyle === style.value" color="var(--color-primary)" />
            </label>
          </radio-group>
        </view>
      </view>
      
      <button class="confirm-btn" :disabled="!isValid || loading" @click="showConfirmDialog">
        确认设置
      </button>
    </view>

    <!-- 确认弹窗 -->
    <uni-popup ref="confirmDialog" type="dialog">
      <uni-popup-dialog 
        type="info" 
        title="确认设置" 
        :content="confirmContent" 
        @confirm="saveSettings" 
        @close="closeConfirmDialog"
      ></uni-popup-dialog>
    </uni-popup>
  </view>
  </WebNavbar>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app';
import { useUserStore } from '@/stores/user.js'
import { http } from '@/stores/request.js'
import { ENDPOINTS } from '@/stores/api.js'
import WebNavbar from '@/components/WebNavbar.vue'

const userStore = useUserStore()

// 状态管理
const loading = ref(false)
const error = ref(null)

// 选择项数据
const genders = [
  { label: '男性', value: 'male' },
  { label: '女性', value: 'female' },
]

const speedOptions = [
  { label: '极慢', value: 1 },
  { label: '较慢', value: 2 },
  { label: '适中', value: 3 },
  { label: '较快', value: 4 },
  { label: '极快', value: 5 }
]

const voiceTypes = [
  { label: '标准清晰', value: 'standard' },
  { label: '低沉稳重', value: 'deep' },
  { label: '清脆明亮', value: 'clear' },
  { label: '柔和亲切', value: 'soft' },
  { label: '激情澎湃', value: 'passionate' },
  { label: '富有磁性', value: 'magnetic' }
]

const interviewStyles = [
  { label: '严肃专业', value: 'serious' },
  { label: '随和亲切', value: 'friendly' },
  { label: '挑战型', value: 'challenging' },
  { label: '引导型', value: 'guiding' },
  { label: '技术型', value: 'technical' },
  { label: '总裁型', value: 'boss' }
]

// 选中的值 - 确保初始值在滑块的取值范围内
const selectedGender = ref('male')
const selectedSpeed = ref(3) // 默认适中，在1-5范围内
const selectedVoice = ref('standard')
const selectedStyle = ref('serious')

// 验证是否所有选项都已选择
const isValid = computed(() => {
  return !!selectedGender.value && 
         selectedSpeed.value >= 1 && selectedSpeed.value <= 5 &&
         !!selectedVoice.value && !!selectedStyle.value
})

// 确认弹窗内容
const confirmContent = computed(() => {
  const genderLabel = genders.find(g => g.value === selectedGender.value)?.label || ''
  const speedLabel = speedOptions.find(s => s.value === selectedSpeed.value)?.label || ''
  const voiceLabel = voiceTypes.find(v => v.value === selectedVoice.value)?.label || ''
  const styleLabel = interviewStyles.find(s => s.value === selectedStyle.value)?.label || ''
  
  return `您已选择：\n性别：${genderLabel}\n语速：${speedLabel}\n音色：${voiceLabel}\n风格：${styleLabel}\n确认使用这些设置吗？`
})

// 事件处理
const handleGenderChange = (e) => {
  selectedGender.value = e.detail.value
}

const handleSpeedChange = (e) => {
  // 确保值在1-5范围内
  const value = parseInt(e.detail.value)
  if (value >= 1 && value <= 5) {
    selectedSpeed.value = value
  }
}

const handleVoiceChange = (e) => {
  selectedVoice.value = e.detail.value
}

const handleStyleChange = (e) => {
  selectedStyle.value = e.detail.value
}

// 对话框控制
const confirmDialog = ref(null)
const showConfirmDialog = () => {
  if (!isValid.value) return
  confirmDialog.value.open()
}

const closeConfirmDialog = () => {
  confirmDialog.value.close()
}

// 保存设置并进入下一步
const saveSettings = async () => {
  loading.value = true
  try {
    // 保存面试官设置
    const interviewerSettings = {
      gender: selectedGender.value,
      speed: selectedSpeed.value,
      voice: selectedVoice.value,
      style: selectedStyle.value
    }

    // 存储到本地缓存
    uni.setStorageSync('interviewerSettings', interviewerSettings)

    // 同步到后端
    try {
      await http.put(ENDPOINTS.user.interviewerSettings, interviewerSettings)
      console.log('面试官设置已同步到后端')
    } catch (err) {
      console.error('同步面试官设置到后端失败:', err)
      // 不影响本地保存和跳转，仅记录错误
    }

    // 跳转到面试页面
    uni.switchTab({
      url: `/pages/learn/ready`
    })
  } catch (err) {
    console.error('保存面试官设置失败:', err)
    uni.showToast({
      title: '保存设置失败，请重试',
      icon: 'none'
    })
  } finally {
    loading.value = false
    closeConfirmDialog()
  }
}

// 生命周期钩子
onShow(async () => {
  loading.value = true
  try {
    // 优先从后端获取设置
    const { data: backendSettings } = await http.get(ENDPOINTS.user.interviewerSettings)
    if (backendSettings) {
      selectedGender.value = backendSettings.gender || 'male'
      selectedSpeed.value = (backendSettings.speed >= 1 && backendSettings.speed <= 5) ? backendSettings.speed : 3
      selectedVoice.value = backendSettings.voice || 'standard'
      selectedStyle.value = backendSettings.style || 'serious'
      // 同步更新本地缓存
      uni.setStorageSync('interviewerSettings', {
        gender: selectedGender.value,
        speed: selectedSpeed.value,
        voice: selectedVoice.value,
        style: selectedStyle.value
      })
      console.log('已从后端加载面试官设置')
    }
  } catch (err) {
    console.error('从后端获取面试官设置失败，使用本地缓存:', err)
    // 尝试从本地缓存加载
    const cachedSettings = uni.getStorageSync('interviewerSettings')
    if (cachedSettings) {
      selectedGender.value = cachedSettings.gender || 'male'
      const speed = parseInt(cachedSettings.speed)
      selectedSpeed.value = (speed >= 1 && speed <= 5) ? speed : 3
      selectedVoice.value = cachedSettings.voice || 'standard'
      selectedStyle.value = cachedSettings.style || 'serious'
    }
  } finally {
    loading.value = false
  }
})
</script>

<style lang="css" scoped>
/* 全局容器样式 - 优化移动端布局 */
.interviewer-container {
  min-height: 100vh;
  background-color: var(--bg-page);
  display: flex;
  flex-direction: column;
  padding: 16px; /* 减小移动端内边距 */
  box-sizing: border-box;
}

/* 主要内容区域 - 确保居中并限制最大宽度 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 500px; /* 适当减小最大宽度，更适合移动端 */
  margin: 0 auto;
  padding: 10px 0;
}

/* 表单容器 - 优化移动端内边距 */
.customize-form {
  width: 100%;
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 16px; /* 减小内边距适应小屏幕 */
  box-shadow: 0 4px 12px rgba(57, 100, 254, 0.1);
  margin-bottom: 20px;
  box-sizing: border-box; /* 确保padding不影响整体宽度 */
}

/* 单选组样式 - 优化移动端排列 */
.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 2px; /* 增加内边距避免边缘过挤 */
}

.radio-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  min-width: calc(50% - 10px); /* 精确计算宽度，确保两列布局整齐 */
  padding: 10px 12px; /* 减小 padding 适应小屏幕 */
  background-color: var(--bg-page);
  border-radius: 8px;
  border: 1px solid var(--border-default);
  transition: all 0.3s ease;
  box-sizing: border-box; /* 确保padding不影响宽度计算 */
}

/* 语速控制 - 优化移动端显示 */
.speed-control {
  display: flex;
  align-items: center;
  gap: 8px; /* 减小间距 */
  margin-bottom: 10px;
  width: 100%;
  padding: 0 5px;
  box-sizing: border-box;
}

/* 确认按钮 - 优化移动端点击区域 */
.confirm-btn {
  width: 100%;
  max-width: 300px;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: 25px;
  padding: 12px;
  font-size: 16px;
  font-weight: 500;
  margin-top: 10px; /* 减小顶部间距 */
  box-shadow: 0 4px 8px rgba(57, 100, 254, 0.2);
  transition: all 0.3s ease;
  box-sizing: border-box;
}

/* #ifdef MP-WEIXIN */
@media (max-width: 568px) {
  .main-content {
    margin-top:40px;
  }
}
/* #endif */

/* 响应式调整 - 针对更小屏幕 */
@media (max-width: 368px) {
  .interviewer-container {
    padding: 12px 8px; /* 进一步减小边距 */
  }
  


  .customize-form {
    padding: 12px;
  }
  
  .form-section {
    margin-bottom: 20px;
    padding-bottom: 10px;
  }
  
  .radio-item {
    min-width: 100%; /* 小屏幕时改为单列布局 */
  }
  
  .section-title {
    font-size: 15px;
    margin-bottom: 15px;
  }
  
  .section-label {
    font-size: 14px;
    margin-bottom: 10px;
  }
}

/* 保持其他原有样式不变 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.section-title {
  display: block;
  font-size: 16px;
  color: var(--color-primary);
  font-weight: 500;
  margin-bottom: 20px;
  text-align: center;
}

.form-section {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-default);
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 10px;
  padding-bottom: 0;
}

.radio-text {
  font-size: 14px;
  color: var(--text-primary);
  margin-right: 10px;
}

.speed-label {
  font-size: 13px;
  color: var(--text-secondary);
  width: 30px;
  text-align: center;
}

slider {
  flex: 1;
  height: 6px;
}

.speed-value {
  display: block;
  text-align: center;
  font-size: 13px;
  color: var(--color-primary);
  margin-top: 5px;
}

.confirm-btn:disabled {
  background-color: var(--text-tertiary);
  box-shadow: none;
  opacity: 0.7;
}

.confirm-btn:active:not(:disabled) {
  transform: translateY(2px);
  box-shadow: 0 2px 4px rgba(57, 100, 254, 0.2);
}
</style>
