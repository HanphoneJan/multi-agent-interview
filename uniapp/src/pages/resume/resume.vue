<template>
  <WebNavbar>
    <view class="resume-container">
    <view class="resume-card">
      <view class="resume-header">
        <view class="header-icon">
          <image src="/static/resume/resume.svg" mode="aspectFit" class="svg-icon"></image>
        </view>
        <text class="resume-title">简历解析</text>
        <text class="resume-subtitle">请上传您的简历进行解析</text>
      </view>

      <view class="resume-form">
        <form @submit.prevent="handleSubmit">
          <view class="form-group">
            <label class="form-label">上传简历</label>
            <view class="file-upload-area" @click="selectFile">
              <view class="upload-icon">
                <image src="/static/resume/upload.svg" mode="aspectFit" class="svg-icon"></image>
              </view>
              <text class="upload-text">点击选择文件</text>
              <text class="upload-hint">支持PDF、Word格式，大小不超过5MB</text>
              <view class="file-preview" v-if="formState.resumePath">
                <text class="file-name">{{ formState.resumeName }}</text>
                <button type="button" class="file-remove" @click.stop="removeFile">
                  ×
                </button>
              </view>
            </view>
            <text class="form-error" v-if="formErrors.resume">{{ formErrors.resume }}</text>
          </view>

          <button type="submit" class="submit-button" @click="handleSubmit" :disabled="uploading || !formState.resumePath">
            {{ uploading ? '解析中...' : '开始解析' }}
          </button>
        </form>
      </view>
    </view>
  </view>
  </WebNavbar>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user.js'
import { ENDPOINTS } from '@/stores/api.js';
import { http } from '@/stores/request.js';
import WebNavbar from '@/components/WebNavbar.vue'
const userStore = useUserStore()
// 表单状态
const formState = reactive({
  resumePath: '',
  resumeName: ''
})

// 表单错误
const formErrors = reactive({
  resume: ''
})

// 上传状态
const uploading = ref(false)

// 选择文件
const selectFile = () => {
  if(userStore.isH5) {
      uni.chooseFile({
    count: 1,
    type: 'file',
    extension: ['.pdf', '.doc', '.docx'],
    success: (res) => {
      const file = res.tempFiles[0]
      
      // 文件大小检查
      if (file.size > 5 * 1024 * 1024) {
        uni.showToast({
          title: '文件大小不能超过5MB',
          icon: 'none'
        })
        return
      }
      
      // 更新表单状态
      formState.resumePath = file.path
      formState.resumeName = file.name
      formErrors.resume = ''
    },
    fail: (err) => {
      console.error('选择文件失败:', err)
      uni.showToast({
        title: '选择文件失败',
        icon: 'none'
      })
    }
  })
  }else {
    uni.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['.pdf', '.doc', '.docx'],
      success: (res) => {
        const file = res.tempFiles[0]
        
        // 文件大小检查
        if (file.size > 5 * 1024 * 1024) {       
          uni.showToast({
            title: '文件大小不能超过5MB',
            icon: 'none'
          })
          return
        }
        
        // 更新表单状态
        formState.resumePath = file.path
        formState.resumeName = file.name
        formErrors.resume = ''
      },
      fail: (err) => {
        console.error('选择文件失败:', err)
        uni.showToast({
          title: '选择文件失败',
          icon: 'none'
        })
      }
    })
  }

}

// 移除文件
const removeFile = () => {
  formState.resumePath = ''
  formState.resumeName = ''
}

// 表单验证
const validateForm = () => {
  formErrors.resume = formState.resumePath ? '' : '请上传简历'
  return !formErrors.resume
}

// 处理表单提交
const handleSubmit = async () => {
  // 表单验证
  if (!validateForm()) {
    return;
  }
  
  uploading.value = true;
  
  try {
    // 上传文件到服务器
    const uploadResult = await new Promise((resolve, reject) => {
      uni.uploadFile({
        url: ENDPOINTS.evaluation.analyzeResume, 
        filePath: formState.resumePath,
        name: 'resume',
        formData: {
          filename: formState.resumeName
        },
        header: {
          'Authorization': `Bearer ${userStore.access}` // 使用用户的access token,拦截器无法拦截uplodFile请求
        },
        success: (res) => resolve(res),
        fail: (err) => reject(err)
      });
    });
    
    // 确保获取到响应后再判断状态码
    if (!uploadResult) {
      throw new Error('上传失败：未获取到响应');
    }
    
    // 处理上传结果
    if (uploadResult.statusCode === 200 || uploadResult.statusCode === 201) {
      // const response = JSON.parse(uploadResult.data)
      
      // 显示成功消息
      uni.showToast({
        title: '解析成功，请返回面试报告界面查看',
        icon: 'success'
      });
      
      // 重置表单
      formState.resumePath = '';
      formState.resumeName = '';
    } else {
      throw new Error(`上传失败: ${uploadResult.statusCode}`);
    }
  } catch (error) {
    console.error('上传或解析失败:', error);
    
    // 显示错误消息
    uni.showToast({
      title: '解析失败，请重试',
      icon: 'none'
    });
  } finally {
    uploading.value = false;
  }
};
</script>

<style lang="css" scoped>
/* 基础变量 */
:root {
  --primary-color: #2196F3;
  --primary-light: #E3F2FD;
  --primary-dark: #1565C0;
  --text-color: #333;
  --text-secondary: #666;
  --text-muted: #999;
  --border-color: #E0E0E0;
  --error-color: #F44336;
  --white: #FFFFFF;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}

/* 移动优先的基础样式 */
.resume-container {
  padding: 16px;
  max-width: 100%;
  box-sizing: border-box;
  background-color: var(--bg-page);
  min-height: 100vh;
}

.resume-card {
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.resume-header {
  text-align: center;
  margin-bottom: 32px;
}

.header-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background-color: var(--color-primary-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.svg-icon {
  width: 32px;
  height: 32px;
  color: var(--color-primary);
}

.resume-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  display: block;
}

.resume-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  display: block;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 8px;
  font-weight: 500;
}

.file-upload-area {
  border: 2px dashed var(--border-default);
  border-radius: 8px;
  padding: 24px 16px;
  text-align: center;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-upload-area:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.upload-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
}

.upload-text {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 4px;
  display: block;
  font-weight: 500;
}

.upload-hint {
  font-size: 14px;
  color: var(--text-tertiary);
  display: block;
}

.file-preview {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-primary-light);
  padding: 8px 12px;
  border-radius: 8px;
}

.file-name {
  font-size: 14px;
  color: var(--color-primary);
  margin-right: 8px;
  max-width: 80%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-right: 4px;
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--color-primary);
  border-radius: 50%;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: all 0.2s ease;
  transform-origin: center;
}

.file-remove:hover {
  background-color: rgba(239, 68, 68, 0.2);
  transform: scale(1.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.file-remove:active {
  transform: scale(0.95);
}

.form-error {
  display: block;
  color: var(--color-error);
  font-size: 14px;
  margin-top: 6px;
}

.submit-button {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-primary);
  color: var(--bg-card);
  font-size: 18px;
  font-weight: 600;
  border-radius: 6px;
  margin-bottom: 15px;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(25, 118, 210, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;

}

.submit-button:active {
  background-color: var(--color-primary-dark);
  box-shadow: 0 1px 2px rgba(25, 118, 210, 0.3);
  transform: translateY(1px);
}

.submit-button:disabled {
  background-color: var(--color-primary-light);
  box-shadow: none;
  color: var(--bg-card);
}

/* 移除默认边框 */
.submit-button::after {
  border: none;
}

/* PC端适配 */
@media (min-width: 768px) {
  .resume-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px 40px;
  }
  
  .resume-card {
    width: 100%;
    max-width: 500px;
    padding: 40px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  }
  
  .header-icon {
    width: 80px;
    height: 80px;
  }
  
  .resume-title {
    font-size: 28px;
  }
  
  .resume-subtitle {
    font-size: 16px;
  }
  
  .file-upload-area {
    padding: 32px;
  }
  
  .submit-button {
    height: 52px;
    font-size: 18px;
  }
}

/* #ifdef MP-WEIXIN */
@media(max-width: 568px) {
  .resume-container {
    padding-top:100px;
  }
}
/* #endif */
</style>