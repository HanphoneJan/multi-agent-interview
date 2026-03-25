<template>
  <WebNavbar>
    <view class="container">
    <form @submit="handleSubmit">
      <!-- 头像上传区域 -->
      <view class="avatar-section">
        <view class="avatar-wrapper" @click="chooseAvatar">
          <image
            class="avatar-image"
            :src="avatarUrl || defaultAvatar"
            mode="aspectFill"
          />
          <view class="avatar-overlay">
            <text class="avatar-text">更换头像</text>
          </view>
        </view>
      </view>

      <!-- 基本信息表单 -->
      <view class="form-group">
        <view class="form-item">
          <text class="label">姓名</text>
          <input 
            type="text" 
            v-model="formData.name" 
            placeholder="请输入姓名"
            class="input"
          />
        </view>

        <view class="form-item">
          <text class="label">昵称</text>
          <input 
            type="text" 
            v-model="formData.username" 
            placeholder="请输入昵称"
            class="input"
          />
        </view>
        
        <view class="form-item">
          <text class="label">电话</text>
          <input 
            type="tel" 
            v-model="formData.phone" 
            placeholder="请输入电话号码"
            class="input"
          />
        </view>
        
        <view class="form-item">
          <text class="label">性别</text>
          <!-- 性别选择器 -->
          <view class="input-group">
            <picker 
              class="picker-container" 
              mode="selector" 
              :range="genderRange" 
              :value="selectedGenderIndex"
              @change="onGenderChange"
            >
              <view class="picker-view">
                <text :class="{ 'placeholder': !displayGender }">
                  {{ displayGender || '请选择性别' }}
                </text>
                <view class="picker-arrow">▼</view>
              </view>
            </picker>
          </view>
        </view>
        
        <view class="form-item">
          <text class="label">民族</text>
          <input
            type="text"
            v-model="formData.ethnicity"
            placeholder="请输入民族"
            class="input"
          />
        </view>

        <view class="form-item">
          <text class="label">年龄</text>
          <input
            type="number"
            v-model="formData.age"
            placeholder="请输入年龄"
            class="input"
          />
        </view>
      </view>
      
      <!-- 教育信息表单 -->
      <view class="form-group">
        <view class="form-item">
          <text class="label">学校</text>
          <input 
            type="text" 
            v-model="formData.university" 
            placeholder="请输入学校名称"
            class="input"
          />
        </view>
        
        <view class="form-item">
          <text class="label">专业</text>
          <input 
            type="text" 
            v-model="formData.major" 
            placeholder="请输入专业"
            class="input"
          />
        </view>
        
        <view class="form-item">
          <text class="label">学习阶段</text>
          <view class="input-group">
            <picker
              class="picker-container"
              mode="selector"
              :range="stageRange"
              :value="selectedStageIndex"
              @change="onStageChange"
            >
              <view class="picker-view">
                <text :class="{ 'placeholder': !displayStage }">
                  {{ displayStage || '请选择学习阶段' }}
                </text>
                <view class="picker-arrow">▼</view>
              </view>
            </picker>
          </view>
        </view>
      </view>

      <!-- 地区信息表单 -->
      <view class="form-group">
        <view class="form-title">地区信息</view>

        <view class="form-item">
          <text class="label">省份</text>
          <view class="input-group">
            <picker
              class="picker-container"
              mode="selector"
              :range="provinces"
              range-key="fullname"
              :value="selectedProvinceIndex"
              @change="onProvinceChange"
              :disabled="loadingRegions"
            >
              <view class="picker-view">
                <text :class="{ 'placeholder': !formData.province }">
                  {{ formData.province || '请选择省份' }}
                </text>
                <view class="picker-arrow">▼</view>
              </view>
            </picker>
          </view>
        </view>

        <view class="form-item">
          <text class="label">城市</text>
          <view class="input-group">
            <picker
              class="picker-container"
              mode="selector"
              :range="cities"
              range-key="fullname"
              :value="selectedCityIndex"
              @change="onCityChange"
              :disabled="!formData.province || loadingRegions"
            >
              <view class="picker-view">
                <text :class="{ 'placeholder': !formData.city }">
                  {{ formData.city || '请选择城市' }}
                </text>
                <view class="picker-arrow">▼</view>
              </view>
            </picker>
          </view>
        </view>

        <view class="form-item">
          <text class="label">区县</text>
          <view class="input-group">
            <picker
              class="picker-container"
              mode="selector"
              :range="districts"
              range-key="fullname"
              :value="selectedDistrictIndex"
              @change="onDistrictChange"
              :disabled="!formData.city || loadingRegions"
            >
              <view class="picker-view">
                <text :class="{ 'placeholder': !formData.district }">
                  {{ formData.district || '请选择区县' }}
                </text>
                <view class="picker-arrow">▼</view>
              </view>
            </picker>
          </view>
        </view>

        <view class="form-item">
          <text class="label">详细地址</text>
          <input
            type="text"
            v-model="formData.address"
            placeholder="请输入详细地址"
            class="input"
          />
        </view>
      </view>

      <!-- 提交按钮 -->
      <button form-type="submit" class="submit-btn">保存修改</button>
    </form>
  </view>
  </WebNavbar>
</template>

<script setup>
import { ref,computed,onMounted } from 'vue'
import WebNavbar from '@/components/WebNavbar.vue'
import { useUserStore } from '@/stores/user.js'
import { ENDPOINTS } from '@/stores/api.js';
const userStore = useUserStore()
// 性别选项配置（同时支持显示文本和存储值）
const genderOptions = ref([
  { text: '男', value: 'M' },
  { text: '女', value: 'F' },
  { text: '其他', value: 'O' }
])

// 学习阶段配置（同时支持显示文本和存储值）
const learningStageOptions = ref([
  { text: '大一上', value: 'FRESHMAN_1' },
  { text: '大一下', value: 'FRESHMAN_2' },
  { text: '大二上', value: 'SOPHOMORE_1' },
  { text: '大二下', value: 'SOPHOMORE_2' },
  { text: '大三上', value: 'JUNIOR_1' },
  { text: '大三下', value: 'JUNIOR_2' },
  { text: '大四上', value: 'SENIOR_1' },
  { text: '大四下', value: 'SENIOR_2' },
  { text: '研究生', value: 'GRADUATE_STUDENT' },
  { text: '应届生', value: 'JOB_SEEKER' },
  { text: '社会人士', value: 'EMPLOYED' },
  { text: '其他', value: 'OTHER' }
])

// 表单数据
const formData = ref({
  name: '',
  phone: '',
  username: '', // 昵称字段
  gender: '',       // 存储值，如 'M', 'F', 'O'
  ethnicity: '',
  age: '',
  university: '',
  major: '',
  learningStage: '', // 存储值，如 'FRESHMAN_1' 等
  province: '',
  city: '',
  district: '',
  address: ''
})

// 省市区相关数据
const provinces = ref([])
const cities = ref([])
const districts = ref([])
const loadingRegions = ref(false)

// 头像相关
const avatarUrl = ref('')
const defaultAvatar = 'https://hanphone.top/images/zhuxun.jpg'
const isUploading = ref(false)

// 选择头像
const chooseAvatar = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempFilePath = res.tempFilePaths[0]
      uploadAvatar(tempFilePath)
    }
  })
}

// 上传头像
const uploadAvatar = (filePath) => {
  isUploading.value = true
  uni.showLoading({ title: '上传中...' })

  uni.uploadFile({
    url: 'https://hanphone.top/upload/avatar',
    filePath: filePath,
    name: 'avatar',
    success: (res) => {
      uni.hideLoading()
      isUploading.value = false

      if (res.statusCode === 200) {
        try {
          const data = JSON.parse(res.data)
          if (data.code === 200 && data.url) {
            avatarUrl.value = data.url
            uni.showToast({
              title: '上传成功',
              icon: 'success'
            })
          } else {
            uni.showToast({
              title: data.message || '上传失败',
              icon: 'none'
            })
          }
        } catch (e) {
          console.error('解析响应失败:', e)
          uni.showToast({
            title: '上传失败',
            icon: 'none'
          })
        }
      } else {
        uni.showToast({
          title: '上传失败',
          icon: 'none'
        })
      }
    },
    fail: (err) => {
      uni.hideLoading()
      isUploading.value = false
      console.error('上传头像失败:', err)
      uni.showToast({
        title: '网络错误',
        icon: 'none'
      })
    }
  })
}

// 小程序picker需要的纯文本数组
const genderRange = computed(() => genderOptions.value.map(item => item.text))
const stageRange = computed(() => learningStageOptions.value.map(item => item.text))

// 计算当前选中的性别显示文本
const displayGender = computed(() => {
  if (!formData.value.gender) return ''
  const matched = genderOptions.value.find(item => item.value === formData.value.gender)
  return matched ? matched.text : ''
})

// 计算当前选中的性别索引
const selectedGenderIndex = computed(() => {
  if (!formData.value.gender) return 0
  return genderOptions.value.findIndex(item => item.value === formData.value.gender)
})

// 计算当前选中的学习阶段显示文本
const displayStage = computed(() => {
  if (!formData.value.learningStage) return ''
  const matched = learningStageOptions.value.find(item => item.value === formData.value.learningStage)
  return matched ? matched.text : ''
})

// 计算当前选中的学习阶段索引
const selectedStageIndex = computed(() => {
  if (!formData.value.learningStage) return 0
  return learningStageOptions.value.findIndex(item => item.value === formData.value.learningStage)
})

// 计算省市区选择索引
const selectedProvinceIndex = computed(() => {
  if (!formData.value.province) return 0
  return provinces.value.findIndex(item => item.fullname === formData.value.province)
})

const selectedCityIndex = computed(() => {
  if (!formData.value.city) return 0
  return cities.value.findIndex(item => item.fullname === formData.value.city)
})

const selectedDistrictIndex = computed(() => {
  if (!formData.value.district) return 0
  return districts.value.findIndex(item => item.fullname === formData.value.district)
})

// 处理性别选择变化
const onGenderChange = (e) => {
  const selectedIndex = e.detail.value
  formData.value.gender = genderOptions.value[selectedIndex].value
}

// 处理学习阶段选择变化
const onStageChange = (e) => {
  const selectedIndex = e.detail.value
  formData.value.learningStage = learningStageOptions.value[selectedIndex].value
}

// 获取行政区划数据
const fetchRegions = (parentId, type) => {
  loadingRegions.value = true
  uni.request({
    url: ENDPOINTS.user.address,
    method: 'GET',
    data: { id: parentId },
    success: (res) => {
      loadingRegions.value = false
      const result = res.data
      if (result.status === 0 && result.result && result.result.length > 0) {
        const data = result.result[0] || []
        if (type === 'provinces') {
          provinces.value = data
        } else if (type === 'cities') {
          cities.value = data
        } else if (type === 'districts') {
          districts.value = data
        }
      }
    },
    fail: () => {
      loadingRegions.value = false
    }
  })
}

// 省份选择变更
const onProvinceChange = (e) => {
  const index = e.detail.value
  const selected = provinces.value[index]
  if (!selected) return
  formData.value.province = selected.fullname
  formData.value.city = ''
  formData.value.district = ''
  cities.value = []
  districts.value = []
  fetchRegions(selected.id, 'cities')
}

// 城市选择变更
const onCityChange = (e) => {
  const index = e.detail.value
  const selected = cities.value[index]
  if (!selected) return
  formData.value.city = selected.fullname
  formData.value.district = ''
  districts.value = []
  fetchRegions(selected.id, 'districts')
}

// 区县选择变更
const onDistrictChange = (e) => {
  const index = e.detail.value
  const selected = districts.value[index]
  if (selected) {
    formData.value.district = selected.fullname
  }
}

// 页面加载时获取当前用户信息
onMounted(() => {
  // 从用户存储中加载数据到表单
  formData.value = {
    name: userStore.name || '',
    username: userStore.username || '',
    phone: userStore.phone || '',
    gender: userStore.gender || '',
    ethnicity: userStore.ethnicity || '',
    age: userStore.age || '',
    university: userStore.university || '',
    major: userStore.major || '',
    learningStage: userStore.learningStage || '',
    province: userStore.province || '',
    city: userStore.city || '',
    district: userStore.district || '',
    address: userStore.address || ''
  }
  // 加载头像
  avatarUrl.value = userStore.avatarUrl || ''
  // 加载省份列表
  fetchRegions('', 'provinces')
  // 如果已有省份，加载城市
  if (formData.value.province) {
    const province = provinces.value.find(p => p.fullname === formData.value.province)
    if (province) {
      fetchRegions(province.id, 'cities')
    }
  }
})

// 提交表单
const handleSubmit = () => {
  // 准备提交数据（转换年龄为数字，添加头像URL）
  const submitData = {
    ...formData.value,
    age: formData.value.age ? parseInt(formData.value.age) : null,
    avatar_url: avatarUrl.value
  }

  // 发送更新请求
  uni.request({
    url: ENDPOINTS.user.updateProfile,
    method: 'PUT',
    data: submitData,
    header: {
      'Authorization': `Bearer ${userStore.access}`
    },
    success: (res) => {
      if (res.statusCode === 200) {
        // 更新用户存储
        Object.keys(formData.value).forEach(key => {
          if (userStore[key] !== undefined) {
            userStore[key] = formData.value[key]
          }
        })
        // 更新头像
        userStore.avatarUrl = avatarUrl.value

        // 提示成功并返回个人资料页
        uni.showToast({
          title: '修改成功',
          icon: 'success'
        })
        // 返回上一页
        setTimeout(() => {
          uni.navigateBack({
            delta: 1
          });
        }, 1500)
      } else {
        uni.showToast({
          title: res.data?.detail || '修改失败',
          icon: 'none'
        })
      }
    },
    fail: (err) => {
      console.error('提交失败:', err)
      uni.showToast({
        title: '网络错误',
        icon: 'none'
      })
    }
  })
}
</script>

<style lang="css" scoped>
.container {
  padding: 20rpx 30rpx;
  background-color: var(--bg-page);
  min-height: 100vh;
}

/* 头像上传区域 */
.avatar-section {
  display: flex;
  justify-content: center;
  padding: 40rpx 0;
}

.avatar-wrapper {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: var(--shadow-md);
  cursor: pointer;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60rpx;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.avatar-wrapper:hover .avatar-overlay,
.avatar-wrapper:active .avatar-overlay {
  opacity: 1;
}

.avatar-text {
  color: #fff;
  font-size: 24rpx;
}

.form-group {
  background-color: var(--bg-card);
  border-radius: 16rpx;
  padding: 20rpx 0;
  margin-bottom: 30rpx;
  box-shadow: var(--shadow-md);
}

.form-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--text-primary);
  padding: 20rpx 30rpx;
  border-bottom: 1rpx solid var(--border-default);
}

.form-item {
  display: flex;
  align-items: center;
  padding: 25rpx 30rpx;
  border-bottom: 1rpx solid var(--border-default);
}

.form-item:last-child {
  border-bottom: none;
}

.label {
  font-size: 32rpx;
  color: var(--text-primary);
  width: 160rpx;
}

.input {
  flex: 1;
  font-size: 32rpx;
  color: var(--text-secondary);
  padding: 10rpx 0;
  border: none;
  outline: none;
}
.input-group {
  flex: 1;
}

.picker-container {
  width: 100%;
}

.picker-view {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 32rpx;
  padding: 10rpx 0;
}

.placeholder {
  color: var(--text-tertiary);
}

.picker-arrow {
  color: var(--text-tertiary);
  font-size: 24rpx;
}

.submit-btn {
  width: 100%;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--text-inverse);
  border: none;
  border-radius: 50rpx;
  height: 90rpx;
  line-height: 90rpx;
  font-size: 32rpx;
  margin-top: 40rpx;
}

/* PC适配 */
@media (min-width: 768px) {
  .container {
    max-width: 600px;
    margin: 0 auto;
    padding: 40rpx;
  }
}

/* #ifdef MP-WEIXIN */
@media(max-width: 768px) {
  .container {
    margin-top: 60px;
  }
}
/* #endif */
</style>