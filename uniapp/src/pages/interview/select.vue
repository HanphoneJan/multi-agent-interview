<template>
  <WebNavbar>
    <view class="interview-container">

    <!-- 搜索区域 -->
    <view class="search-section">
      <view class="search-bar">
        <uni-icons type="search" size="18" color="#999"></uni-icons>
        <input 
          class="search-input" 
          type="text" 
          v-model="searchKeyword" 
          placeholder="搜索岗位或技术领域" 
          placeholder-class="placeholder-class"
        />
        <uni-icons v-if="searchKeyword" @click="searchKeyword = ''" type="clear" size="18" color="#ccc"></uni-icons>
      </view>
    </view>

    <!-- 主要内容 -->
    <view class="main-content" :class="{ 'has-footer': currentScenario }">
      
      <!-- 加载状态 -->
      <view v-if="loading" class="loading-container">
        <uni-load-more status="loading"></uni-load-more>
      </view>
      
      <!-- 列表区域 -->
      <view v-else class="scenario-list">
        <view class="list-header">
          <text class="section-title">选择面试场景</text>
          <text v-if="filteredScenarios.length > 0" class="result-count">共 {{ filteredScenarios.length }} 个结果</text>
        </view>
        
        <view class="grid-container">
          <label 
            class="scenario-card" 
            v-for="item in filteredScenarios" 
            :key="item.id"
            :class="{ 'selected': item.id === currentScenario }"
          >
            <!-- 选择逻辑绑定在卡片上，提升操作便捷性 -->
            <radio-group @change="radioChange" class="hidden-radio">
               <radio :value="item.id.toString()" :checked="item.id === currentScenario" />
            </radio-group>
            
            <view class="card-header">
              <text class="scenario-name">{{item.name}}</text>
              <view class="check-icon" v-if="item.id === currentScenario">
                <uni-icons type="checkmarkempty" size="14" color="#fff"></uni-icons>
              </view>
            </view>
            
            <view class="card-body">
              <text class="scenario-field">{{item.technology_field}}</text>
              <text class="scenario-desc">{{item.description}}</text>
            </view>
            
            <view class="card-footer">
              <!-- 移除了 Emoji，使用纯文字描述 -->
              <text class="scenario-type">{{item.is_realtime ? '实时面试' : '非实时面试'}}</text>
            </view>
          </label>
        </view>
        
        <!-- 空状态提示 -->
        <view v-if="filteredScenarios.length === 0 && !loading" class="empty-tip">
          <image class="empty-img" src="/static/images/empty-search.png" mode="aspectFit"></image>
          <text class="empty-text">{{ searchKeyword ? '未找到相关岗位' : '暂无可用面试场景' }}</text>
          <text v-if="searchKeyword" class="empty-sub" @click="searchKeyword = ''">清除搜索</text>
        </view>
      </view>
    </view>

    <!-- 底部吸底操作栏 -->
    <view class="footer-action-bar" v-if="!loading">
      <view class="selection-preview">
        <text class="preview-label">当前选择：</text>
        <text class="preview-value">{{ currentScenarioName || '请从上方列表选择' }}</text>
      </view>
      <button class="confirm-btn-fixed" :disabled="!currentScenario" @click="showConfirmDialog">
        确认选择
      </button>
    </view>

    <!-- 确认弹窗 -->
    <uni-popup ref="confirmDialog" type="dialog">
      <uni-popup-dialog 
        type="info" 
        title="确认选择" 
        :content="confirmContent" 
        @confirm="goToInterview" 
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
import { ENDPOINTS } from '@/stores/api.js';
import { http } from '@/stores/request.js';
import WebNavbar from '@/components/WebNavbar.vue'

const userStore = useUserStore()

// 初始化状态
const currentScenario = ref(null)
const scenarios = ref([])
const loading = ref(false)
const error = ref(null)
const interviewSessionId = ref(null)
const searchKeyword = ref('') // 搜索关键词

// 计算属性：过滤后的场景列表
const filteredScenarios = computed(() => {
  if (!searchKeyword.value) return scenarios.value;
  const keyword = searchKeyword.value.toLowerCase();
  return scenarios.value.filter(item => 
    (item.name && item.name.toLowerCase().includes(keyword)) || 
    (item.technology_field && item.technology_field.toLowerCase().includes(keyword))
  );
})

// 计算属性：当前选中项的名称
const currentScenarioName = computed(() => {
  if (!currentScenario.value) return '';
  const scenario = scenarios.value.find(item => item.id === currentScenario.value);
  return scenario ? `${scenario.name} (${scenario.technology_field})` : '';
})

// 计算属性：弹窗内容
const confirmContent = computed(() => {
  if (!currentScenario.value) return ''
  const scenario = scenarios.value.find(item => item.id === currentScenario.value)
  return scenario ? `您确定要选择${scenario.technology_field}领域的${scenario.name}场景吗？` : ''
})

// 获取面试场景数据
const fetchScenarios = async () => {
  loading.value = true;
  error.value = null;
  try {
    const data = await http.get(ENDPOINTS.interview.scenarios);
    scenarios.value = data.items || data || [];
    uni.setStorageSync('interviewScenarios', scenarios.value);
  } catch (err) {
    console.error('获取面试场景失败:', err);
    error.value = err.message;
    uni.showToast({ title: '加载失败，读取缓存', icon: 'none' });
    const cachedScenarios = uni.getStorageSync('interviewScenarios');
    if (cachedScenarios) scenarios.value = cachedScenarios;
  } finally {
    loading.value = false;
  }
}

// 表单处理
const radioChange = (e) => {
  // 兼容 card 点击和 radio 原生点击
  currentScenario.value = e.detail.value ? parseInt(e.detail.value) : e; 
}

// 对话框控制
const confirmDialog = ref(null)
const showConfirmDialog = () => {
  if (!currentScenario.value) return
  confirmDialog.value.open()
}

const closeConfirmDialog = () => {
  confirmDialog.value.close()
}

// 开始面试
const goToInterview = async () => {
  // 先检查登录状态（优先使用 localStorage，因为 Pinia 可能还没恢复）
  const hasToken = userStore.access || uni.getStorageSync('access_token');
  const isLoggedIn = userStore.isLoggedIn || !!hasToken;

  if (!isLoggedIn || !hasToken) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' });
    }, 1500);
    return;
  }

  // 如果 Pinia 没有 token 但 localStorage 有，同步一下
  if (!userStore.access && uni.getStorageSync('access_token')) {
    userStore.access = uni.getStorageSync('access_token');
    userStore.refresh = uni.getStorageSync('refresh_token');
    userStore.isLoggedIn = true;
  }

  loading.value = true;
  try {
    const data = await http.post(ENDPOINTS.interview.sessions, {
      scenario_id: parseInt(currentScenario.value)
    });
    interviewSessionId.value = data.id;
    userStore.sessionId = data.id;

    // 跳转到面试入口页面，由入口页面根据 is_realtime 自动路由
    uni.navigateTo({
      url: `/pages/interview/index?id=${data.id}`
    });
  } catch (err) {
    console.error('创建面试会话失败:', err);
    uni.showToast({ title: err.message || '创建面试会话失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 重新加载用户状态（解决 Pinia 持久化延迟问题）
const reloadUserState = () => {
  const access = uni.getStorageSync('access_token');
  const refresh = uni.getStorageSync('refresh_token');
  const tokenExpire = uni.getStorageSync('token_expire');

  if (access) {
    userStore.access = access;
    userStore.refresh = refresh;
    userStore.tokenExpire = tokenExpire;
    userStore.isLoggedIn = true;
  }
};

// 生命周期钩子
onShow(() => {
  reloadUserState();
  fetchScenarios();
})
</script>

<style lang="css" scoped>
/* 变量定义 */
:root {
  --bg-page: #f5f7fa;
  --bg-card: #ffffff;
  --color-primary: #4a90e2;
  --text-primary: #333333;
  --text-secondary: #666666;
  --text-tertiary: #999999;
  --border-default: #e8e8e8;
}

.interview-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 120px; /* 为底部操作栏留出空间 */
}

/* 搜索区域样式 */
.search-section {
  padding: 15px 20px;
  background-color: #fff;
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid #f0f0f0;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #f5f7fa;
  border-radius: 20px;
  padding: 8px 15px;
}

.search-input {
  flex: 1;
  margin: 0 10px;
  font-size: 14px;
  color: #333;
}

.placeholder-class {
  color: #999;
}

/* 主内容区域 */
.main-content {
  padding: 0 15px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 15px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.result-count {
  font-size: 12px;
  color: #999;
}

/* 双列瀑布流布局 */
.grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* 场景卡片样式 */
.scenario-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease-in-out;
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
}

.scenario-card:active {
  transform: scale(0.98);
}

.scenario-card.selected {
  border-color: #4a90e2;
  background-color: #f0f7ff;
}

/* 隐藏原生Radio样式，保留语义 */
.hidden-radio {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.scenario-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  line-height: 1.3;
  flex: 1;
  padding-right: 5px;
}

.check-icon {
  width: 20px;
  height: 20px;
  background-color: #4a90e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-body {
  flex: 1;
  margin-bottom: 10px;
}

.scenario-field {
  display: inline-block;
  font-size: 12px;
  color: #4a90e2;
  background-color: rgba(74, 144, 226, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.scenario-desc {
  display: block;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2; /* 限制描述行数 */
  overflow: hidden;
}

.card-footer {
  border-top: 1px solid #f5f5f5;
  padding-top: 10px;
  margin-top: auto;
}

.scenario-type {
  font-size: 12px;
  color: #999;
}

/* 空状态优化 */
.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60px;
}

.empty-img {
  width: 120px;
  height: 120px;
  margin-bottom: 20px;
  opacity: 0.8;
}

.empty-text {
  color: #999;
  font-size: 14px;
  margin-bottom: 10px;
}

.empty-sub {
  color: #4a90e2;
  font-size: 13px;
  text-decoration: underline;
}

/* 底部吸底操作栏 */
.footer-action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #fff;
  padding: 12px 20px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom)); /* 适配iPhone X底部安全区 */
  box-shadow: 0 -4px 12px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 100;
}

.selection-preview {
  display: flex;
  flex-direction: column;
}

.preview-label {
  font-size: 12px;
  color: #999;
}

.preview-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.confirm-btn-fixed {
  background-color: #4a90e2;
  color: white;
  font-size: 16px;
  font-weight: 500;
  padding: 0 30px;
  height: 44px;
  line-height: 44px;
  border-radius: 22px;
  border: none;
  flex-shrink: 0;
  margin: 0;
}

.confirm-btn-fixed:disabled {
  background-color: #e0e0e0;
  color: #fff;
}

/* 兼容小程序与响应式 */
@media (min-width: 768px) {
  .interview-container {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .footer-action-bar {
    max-width: 800px;
    left: 50%;
    transform: translateX(-50%);
  }
}

/* #ifdef MP-WEIXIN */
/* 针对小程序的顶部导航适配 */
.interview-container {
  margin-top: 0; 
  /* WebNavbar组件通常处理了导航栏高度 */
}
/* #endif */
</style>