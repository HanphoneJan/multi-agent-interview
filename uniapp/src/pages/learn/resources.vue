<template>
  <WebNavbar>
  <view class="page-container">
    
    <!-- 加载状态（带动添加过渡动画效果） -->
    <transition name="fade">
      <view class="loading-state" v-if="loading">
        <view class="spinner"></view>
        <text class="loading-text">加载中...</text>
      </view>
    </transition>

    <!-- 主内容区（添加过渡效果） -->
    <transition name="fade">
      <view class="main-content">
        <view class="content-wrapper">
          <!-- 页面标题 -->
          <view class="page-header" v-if="!userStore.isH5">
            <text class="header-title">学习资源库</text>
            <text class="header-subtitle">探索丰富的学习材料，提升你的技能</text>
          </view>

          <!-- 搜索和筛选区 -->
          <view class="search-filter-container">
            <view class="search-box">
              <image src="/static/resources/search.png" mode="aspectFit" class="search-icon"></image>
              <input type="text" placeholder="搜索学习资源..." v-model="searchKeyword" class="search-input" />
            </view>
            
            <button class="filter-btn" @click="showFilter = !showFilter">
              <text>筛选</text>
              <image src="/static/resources/filter.png" mode="aspectFit" class="filter-icon"></image>
            </button>
          </view>

          <!-- 筛选面板（使用transition组件） -->
          <transition name="overlay">
            <view class="filter-overlay" v-if="showFilter" @click="showFilter = false"></view>
          </transition>
          
          <transition name="panel">
            <view class="filter-panel" v-if="showFilter">
              <view class="filter-header">
                <text class="filter-title">筛选条件</text>
              </view>
              
              <view class="filter-content">
                <view class="filter-section">
                  <text class="filter-section-title">资源类型</text>
                  <view class="filter-tags">
                    <button class="filter-tag" :class="{ active: selectedType === 'all' }" @click="selectedType = 'all'">全部</button>
                    <button class="filter-tag" :class="{ active: selectedType === 'question' }" @click="selectedType = 'question'">题库</button>
                    <button class="filter-tag" :class="{ active: selectedType === 'video' }" @click="selectedType = 'video'">视频</button>
                    <button class="filter-tag" :class="{ active: selectedType === 'course' }" @click="selectedType = 'course'">课程</button>
                  </view>
                </view>
                
                <view class="filter-section">
                  <text class="filter-section-title">难度等级</text>
                  <view class="filter-tags">
                    <button class="filter-tag" :class="{ active: selectedDifficulty === 'all' }" @click="selectedDifficulty = 'all'">全部</button>
                    <button class="filter-tag" :class="{ active: selectedDifficulty === 'easy' }" @click="selectedDifficulty = 'easy'">简单</button>
                    <button class="filter-tag" :class="{ active: selectedDifficulty === 'medium' }" @click="selectedDifficulty = 'medium'">中等</button>
                    <button class="filter-tag" :class="{ active: selectedDifficulty === 'hard' }" @click="selectedDifficulty = 'hard'">困难</button>
                  </view>
                </view>
              </view>
              
              <view class="filter-actions">
                <button class="reset-btn" @click="resetFilters">重置</button>
                <button class="confirm-btn" @click="showFilter = false">确认</button>
              </view>
            </view>
          </transition>

          <!-- 资源列表 -->
          <view class="resources-container">
            <view class="resources-header">
              <text class="resources-title">资源列表</text>
              <text class="resources-count">{{ filteredResources.length }} 个资源</text>
            </view>
            
            <view class="resources-grid">
              <view class="resource-card" v-for="(item, index) in filteredResources" :key="item.id" @click="goToResource(item)">
                <!-- 资源图标 -->
                <view class="resource-icon">
                  <image :src="getResourceIcon(item.resource_type)" mode="aspectFit" class="icon-image"></image>
                </view>
                
                <!-- 资源信息 -->
                <view class="resource-info">
                  <text class="resource-title">{{ item.name }}</text>
                  <text class="resource-tags">{{ item.tags }}</text>
                  
                  <view class="resource-meta">
                    <view class="meta-item">
                      <image src="/static/resources/duration.png" mode="aspectFit" class="meta-icon"></image>
                      <text>时长/题量：</text>
                      <text>{{ item.duration_or_quantity }}</text>
                    </view>
                    <view class="meta-item">
                      <image src="/static/resources/difficulty.png" mode="aspectFit" class="meta-icon"></image>
                      <text>难度：</text>
                      <text :class="getDifficultyClass(item.difficulty)">{{ getDifficultyText(item.difficulty) }}</text>
                    </view>
                  </view>
                </view>
                
                <!-- 箭头图标 -->
                <view class="arrow-icon">
                  <image src="/static/ready/arrow-right.png" mode="aspectFit" class="arrow-image"></image>
                </view>
              </view>
            </view>
            
            <!-- 空状态（添加过渡效果） -->
            <transition name="fade">
              <view class="empty-state" v-if="filteredResources.length === 0">
                <image src="/static/ready/empty-resource.png" mode="aspectFit" class="empty-image"></image>
                <text class="empty-text">没有找到匹配的资源</text>
                <button class="reset-filters" @click="resetFilters">重置筛选条件</button>
              </view>
            </transition>
          </view>
        </view>
      </view>
    </transition>
  </view>
  </WebNavbar>
</template>

<script setup>
import WebNavbar from '@/components/WebNavbar.vue';
import { ref, computed } from 'vue';
import { ENDPOINTS } from '@/stores/api.js';
import { http } from '@/stores/request.js';
import { useUserStore } from '@/stores/user.js';
import { onShow } from '@dcloudio/uni-app';
const userStore = useUserStore();

// 状态管理
const resources = ref([]);
// 新增一个ref存储随机排序后的资源
const shuffledResources = ref([]);
const searchKeyword = ref('');
const showFilter = ref(false);
const selectedType = ref('all');
const selectedDifficulty = ref('all');
const loading = ref(true);
const CACHE_KEY = 'learning_resources_cache'; // 缓存键名

// 生命周期：获取资源数据
onShow(() => {
  loadResources();
});

// 加载资源：优先网络请求，失败则读取缓存
const loadResources = async () => {
  loading.value = true;
  try {
    // 尝试从网络获取
    const data = await fetchResourcesFromNetwork();
    resources.value = data;
    // 对数据进行随机排序
    shuffledResources.value = shuffleArray([...data]);
    // 存入缓存
    await saveToCache(data);

  } catch (error) {
    console.error('网络请求失败，尝试读取缓存:', error);
    // 网络请求失败，尝试从缓存读取
    const cachedData = await getFromCache();
    if (cachedData) {
      resources.value = cachedData;
      // 对缓存数据进行随机排序
      shuffledResources.value = shuffleArray([...cachedData]);
      uni.showToast({
        title: '使用缓存数据',
        icon: 'none',
        duration: 1500
      });
    } else {
      // 缓存也没有数据
      shuffledResources.value = [];
      uni.showToast({
        title: '获取数据失败',
        icon: 'none',
        duration: 1500
      });
    }
  } finally {
    loading.value = false;
  }
};

// 新增：数组随机排序函数 (Fisher-Yates 洗牌算法)
const shuffleArray = (array) => {
  const newArray = [...array];
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
  }
  return newArray;
};

// 从网络获取资源数据
const fetchResourcesFromNetwork = async () => {
  try {
    const data = await http.get(ENDPOINTS.learning.resources);
    // FastAPI returns paginated response with items array
    if (data && data.items && Array.isArray(data.items)) {
      return data.items;
    }
    // Fallback for non-paginated response
    if (Array.isArray(data)) {
      return data;
    }
    throw new Error('Invalid response format');
  } catch (error) {
    console.error('获取资源失败:', error);
    throw error;
  }
};

// 保存数据到缓存
const saveToCache = async (data) => {
  return new Promise((resolve, reject) => {
    // 缓存数据包含时间戳，便于后续判断缓存有效期
    const cacheData = {
      data,
      timestamp: Date.now()
    };
    uni.setStorage({
      key: CACHE_KEY,
      data: cacheData,
      success: () => {
        console.log('数据已存入缓存');
        resolve();
      },
      fail: (err) => {
        console.error('缓存保存失败:', err);
        reject(err);
      }
    });
  });
};

// 从缓存获取数据
const getFromCache = async () => {
  return new Promise((resolve) => {
    uni.getStorage({
      key: CACHE_KEY,
      success: (res) => {
        // 缓存有效期判断，24小时内有效
        const cacheValidity = 24 * 60 * 60 * 1000; // 24小时有效期
        const now = Date.now();
        
        if (now - res.data.timestamp < cacheValidity) {
          console.log('从缓存读取数据');
          resolve(res.data.data);
        } else {
          console.log('缓存已过期');
          // 清除过期缓存
          uni.removeStorage({ key: CACHE_KEY });
          resolve(null);
        }
      },
      fail: () => {
        console.log('缓存中没有数据');
        resolve(null);
      }
    });
  });
};

// 根据资源类型获取对应图标
const getResourceIcon = (type) => {
  switch (type) {
    case 'question':
      return '/static/resources/practice.png';
    case 'video':
      return '/static/resources/video.png';
    case 'course':
      return '/static/resources/course.png';
    default:
      return '/static/resources/practice.png';
  }
};

// 格式化难度文本
const getDifficultyText = (difficulty) => {
  const map = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  };
  return map[difficulty] || difficulty;
};

// 获取难度对应的样式类
const getDifficultyClass = (difficulty) => {
  return `difficulty-${difficulty}`;
};

// 筛选资源 - 修改为基于随机排序后的数组进行筛选
const filteredResources = computed(() => {
  return shuffledResources.value.filter(item => {
    // 搜索关键词筛选
    const matchesSearch = item.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) || 
                         item.tags.toLowerCase().includes(searchKeyword.value.toLowerCase());
    
    // 类型筛选
    const matchesType = selectedType.value === 'all' || item.resource_type === selectedType.value;
    
    // 难度筛选
    const matchesDifficulty = selectedDifficulty.value === 'all' || item.difficulty === selectedDifficulty.value;
    
    return matchesSearch && matchesType && matchesDifficulty;
  });
});

// 跳转到资源详情
const goToResource = (item) => {
  uni.navigateTo({
    url: `/pages/learn/single-resource?url=${encodeURIComponent(item.url)}&id=${item.id}`
  });
};

// 重置筛选条件
const resetFilters = () => {
  searchKeyword.value = '';
  selectedType.value = 'all';
  selectedDifficulty.value = 'all';
  showFilter.value = false;
};
</script>

<style lang="css" scoped>
/* 基础布局 */
.page-container {
  min-height: 100vh;
  background-color: var(--bg-page);
  padding-bottom: 20px;
}

.main-content {
  padding: 15px;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
}

/* 过渡动画样式 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.overlay-enter-active, .overlay-leave-active {
  transition: opacity 0.3s ease;
}
.overlay-enter-from, .overlay-leave-to {
  opacity: 0;
}

.panel-enter-active, .panel-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.panel-enter-from {
  transform: translateX(100%);
}
.panel-leave-to {
  transform: translateX(100%);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-primary);
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 页面标题 */
.page-header {
  margin-bottom: 25px;
  text-align: center;
}

.header-title {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.header-subtitle {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
}

/* 搜索和筛选区 */
.search-filter-container {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-box {
  flex: 1;
  background-color: var(--bg-card);
  border-radius: 8px;
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.search-icon {
  width: 18px;
  height: 18px;
  margin-right: 10px;
}

.search-input {
  flex: 1;
  height: 100%;
  font-size: 14px;
  color: var(--text-primary);
}

.filter-btn {
  background-color: var(--bg-card);
  border-radius: 8px;
  height: 40px;
  padding: 0 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--text-primary);
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.filter-icon {
  width: 16px;
  height: 16px;
  margin-left: 6px;
}

/* 筛选面板 */
.filter-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 998;
}

.filter-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 300px;
  max-width: 100%;
  height: 100vh;
  background-color: var(--bg-card);
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 999;
  padding: 20px;
  overflow-y: auto;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-default);
}

.filter-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-section {
  margin-bottom: 25px;
}

.filter-section-title {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-tag {
  padding: 6px 12px;
  background-color: var(--bg-page);
  border-radius: 16px;
  font-size: 13px;
  color: var(--text-primary);
  border: none;
  transition: all 0.2s ease;
}

.filter-tag.active {
  background-color: var(--color-primary);
  color: var(--bg-card);
}

.filter-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--border-default);
}

.reset-btn, .confirm-btn {
  flex: 1;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  border: none;
  transition: background-color 0.2s ease;
  /* 添加以下属性确保文字居中 */
  display: flex;
  align-items: center;
  justify-content: center;
  /* 移除默认内边距影响 */
  padding: 0;
}
.reset-btn {
  background-color: var(--bg-page);
  color: var(--text-primary);
}

.reset-btn:active {
  background-color: var(--border-default);
}

.confirm-btn {
  background-color: var(--color-primary);
  color: var(--bg-card);
}

.confirm-btn:active {
  background-color: var(--color-primary);
}

/* 资源列表 */
.resources-container {
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.resources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.resources-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.resources-count {
  font-size: 13px;
  color: var(--text-secondary);
}

.resources-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
}

.resource-card {
  display: flex;
  align-items: center;
  padding: 20px; /* 增大内边距 */
  background-color: var(--bg-page);
  border-radius: 12px; /* 增大圆角 */
  transition: all 0.2s ease;
  min-height: 100px; /* 设置最小高度 */
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05); /* 添加轻微阴影 */
  margin-bottom: 5px; /* 增加卡片间距 */
}

.resource-card:active {
  transform: scale(0.98);
  background-color: var(--border-default);
}

.resource-icon {
  width: 60px; /* 增大图标容器 */
  height: 60px;
  margin-right: 20px; /* 增大右边距 */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e3f2fd;
  border-radius: 10px; /* 增大圆角 */
  flex-shrink: 0; /* 防止图标被压缩 */
}


.icon-image {
  width: 24px;
  height: 24px;
}
.resource-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 垂直居中内容 */
}

.resource-title {
  display: block;
  font-size: 16px; /* 增大字体 */
  font-weight: 600; /* 加粗 */
  color: var(--text-primary);
  margin-bottom: 6px; /* 调整间距 */
  line-height: 1.3; /* 调整行高 */
}

.resource-tags {
  display: block;
  font-size: 13px; /* 增大字体 */
  color: var(--text-secondary);
  margin-bottom: 12px; /* 增大间距 */
  line-height: 1.3;
}

.resource-meta {
  display: flex;
  gap: 15px;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
}

.meta-icon {
  width: 12px;
  height: 12px;
  margin-right: 4px;
}

.difficulty-easy {
  color: var(--color-success);
}

.difficulty-medium {
  color: var(--color-warning);
}

.difficulty-hard {
  color: var(--color-error);
}

.arrow-icon {
  width: 20px;
  height: 20px;
  margin-left: 10px;
}

.arrow-image {
  width: 100%;
  height: 100%;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.empty-image {
  width: 120px;
  height: 120px;
  margin-bottom: 15px;
  opacity: 0.7;
}

.empty-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.reset-filters {
  background-color: var(--color-primary);
  color: var(--bg-card);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
}

/* 响应式设计 - 平板及以上 */
@media (min-width: 768px) {
  .main-content {
    padding: 25px;
  }
  
  .resources-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-panel {
    width: 350px;
  }
}

/* 响应式设计 - 桌面 */
@media (min-width: 992px) {
  .resources-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .search-filter-container {
    margin-bottom: 30px;
  }
  
  .page-header {
    margin-bottom: 35px;
  }
  
  .header-title {
    font-size: 28px;
  }
  
  .header-subtitle {
    font-size: 16px;
  }
  
  .filter-panel {
    width: 400px;
  }
}

/* #ifdef MP-WEIXIN */
@media (max-width:568px) {
  .main-content{
    margin-top:30px;
  }
}
/* #endif */

@media (max-width:568px) {
  .resource-meta {
    flex-direction: column;  /* 小屏幕下垂直排列 */
    gap: 5px;               /* 减小垂直间距 */
  }
  
  .meta-item {
    font-size: 11px;         /* 适当缩小字体 */
  }

}
</style>