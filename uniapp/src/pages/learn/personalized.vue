<template>
  <WebNavbar>
  <view class="page-container">
    
    <!-- 加载状态 -->
    <transition name="fade">
      <view class="loading-state" v-if="loading">
        <view class="spinner"></view>
        <text class="loading-text">正在生成个性化提升资料...</text>
      </view>
    </transition>

    <!-- 主内容区 -->
    <transition name="fade">
      <view class="main-content">
        <view class="content-wrapper">
          <!-- 页面标题 -->
          <view class="page-header" v-if="!userStore.isH5">
            <text class="header-title">个性化提升资料</text>
            <text class="header-subtitle">根据您的面试表现推荐学习资源</text>
          </view>

          <!-- 资源列表 -->
          <view class="resources-container">
            <view class="resources-header">
              <text class="resources-title">推荐学习资源</text>
              <text class="resources-count">{{ filteredResources.length }} 个资源</text>
            </view>
            
            <view class="resources-grid">
              <view class="resource-card" v-for="(item, index) in filteredResources" :key="item.id" @click="goToResource(item.url)">
                <!-- 资源图标 -->
                <view class="resource-icon">
                  <image :src="getResourceIcon(item.resource_type)" mode="aspectFit" class="icon-image"></image>
                </view>
                
                <!-- 资源信息 -->
                <view class="resource-info">
                  <text class="resource-title">{{ item.name }}</text>
                  <text class="resource-tags">{{ item.tags }}</text>
                  
                  <view class="resource-meta">
                    <view class="meta-item" >
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

            <!-- 资源空状态 -->
            <transition name="fade">
              <view class="empty-state" v-if="!loading && filteredResources.length === 0 && questions.length > 0">
                <image src="/static/ready/empty-resource.png" mode="aspectFit" class="empty-image"></image>
                <text class="empty-text">暂无推荐的学习资源</text>
              </view>
            </transition>
          </view>

          <!-- 练习题列表 -->
          <view class="resources-container questions-container">
            <view class="resources-header">
              <text class="resources-title">推荐练习题</text>
              <text class="resources-count">{{ questions.length }} 道题目</text>
            </view>
            
            <view class="resources-grid">
              <view class="resource-card question-card" v-for="(item, index) in questions" :key="item.id" @click="goToQuestion(item.question_url)">
                <!-- 题目图标 -->
                <view class="resource-icon">
                  <image src="/static/resources/practice.png" mode="aspectFit" class="icon-image"></image>
                </view>
                
                <!-- 题目信息 -->
                <view class="resource-info">
                  <text class="resource-title">{{ item.name }}</text>
                  <text class="resource-tags">{{ item.resource_name }} · {{ item.resource_tags }}</text>
                  
                  <view class="resource-meta">
                    <view class="meta-item">
                      <image src="/static/resources/pass-rate.png" mode="aspectFit" class="meta-icon"></image>
                      <text>正确率：</text>
                      <text>{{ item.pass_rate }}</text>
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

            <!-- 练习题空状态 -->
            <transition name="fade">
              <view class="empty-state" v-if="!loading && questions.length === 0 && filteredResources.length > 0">
                <image src="/static/ready/empty-question.png" mode="aspectFit" class="empty-image"></image>
                <text class="empty-text">暂无推荐的练习题</text>
              </view>
            </transition>
          </view>

          <!-- 整体空状态 -->
          <transition name="fade">
            <view class="empty-state" v-if="!loading && filteredResources.length === 0 && questions.length === 0">
              <image src="/static/ready/empty-all.png" mode="aspectFit" class="empty-image"></image>
              <text class="empty-text">暂无推荐的学习资源和练习题</text>
              <button class="reset-filters" @click="goToResources">查看全部资源</button>
            </view>
          </transition>
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
import { http } from '@/stores/request.js'
import { useUserStore } from '@/stores/user.js';
import { onShow } from '@dcloudio/uni-app';
const userStore = useUserStore();

// 状态管理
const resources = ref([]);
const questions = ref([]);  // 新增练习题数据
const loading = ref(true);
const CACHE_KEY = 'personalized_resources_cache'; // 缓存键名

// 生命周期：获取个性化资源
onShow(() => {
  loadPersonalizedResources();
});

// 加载个性化资源：优先网络请求，失败则读取缓存
const loadPersonalizedResources = async () => {
  loading.value = true;
  try {
    // 从缓存获取面试记录
    const interviewRecord = uni.getStorageSync('selectedInterview');
    if (!interviewRecord) {
      throw new Error('未找到面试记录');
    }
    console.log(interviewRecord)
    // 尝试从网络获取个性化资源和练习题
    const data = await fetchPersonalizedResourcesFromNetwork(interviewRecord);
    resources.value = data.resources || [];  // 从resources字段读取资源
    questions.value = data.questions || [];  // 从questions字段读取练习题
    // 存入缓存
    await saveToCache({ resources: resources.value, questions: questions.value });
  } catch (error) {
    console.error('获取个性化资源失败:', error);
    // 网络请求失败，尝试从缓存读取
    const cachedData = await getFromCache();
    if (cachedData) {
      resources.value = cachedData.resources || [];
      questions.value = cachedData.questions || [];
      uni.showToast({
        title: '使用缓存的推荐内容',
        icon: 'none',
        duration: 1500
      });
    } else {
      // 缓存也没有数据
      resources.value = [];
      questions.value = [];
      uni.showToast({
        title: '获取推荐内容失败',
        icon: 'none',
        duration: 1500
      });
    }
  } finally {
    loading.value = false;
  }
};

// 从网络获取个性化资源和练习题数据
const fetchPersonalizedResourcesFromNetwork = async () => {
  try {
    // 使用新的FastAPI端点 - 个性化推荐
    const data = await http.post(ENDPOINTS.recommendation.personalized, {
      limit: 10
    });

    // 适配FastAPI响应格式
    return {
      resources: data.recommendations?.map(rec => ({
        id: rec.resource_id,
        name: rec.name,
        resource_type: rec.resource_type,
        tags: Array.isArray(rec.tags) ? rec.tags.join(',') : rec.tags,
        url: rec.url,
        duration_or_quantity: rec.duration_or_quantity,
        difficulty: rec.difficulty,
        views: rec.views || 0,
        completions: rec.completions || 0,
        rating: rec.score || 0,
        reason: rec.reason
      })) || [],
      questions: []
    };
  } catch (error) {
    console.error('获取个性化推荐失败:', error);
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
        console.log('个性化资源和练习题已存入缓存');
        resolve();
      },
      fail: (err) => {
        console.error('个性化内容缓存保存失败:', err);
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
        // 缓存有效期判断，12小时内有效
        const cacheValidity = 12 * 60 * 60 * 1000; // 12小时有效期
        const now = Date.now();
        
        if (now - res.data.timestamp < cacheValidity) {
          console.log('从缓存读取个性化资源和练习题');
          resolve(res.data.data);
        } else {
          console.log('个性化内容缓存已过期');
          // 清除过期缓存
          uni.removeStorage({ key: CACHE_KEY });
          resolve(null);
        }
      },
      fail: () => {
        console.log('缓存中没有个性化内容数据');
        resolve(null);
      }
    });
  });
};

// 计算属性：过滤资源
const filteredResources = computed(() => {
  return resources.value;
});

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

// 跳转到资源详情
const goToResource = (url) => {
  uni.navigateTo({
    url: `/pages/learn/single-resource?url=${encodeURIComponent(url)}`
  });
};

// 新增：跳转到练习题
const goToQuestion = (url) => {
  uni.navigateTo({
    url: `/pages/learn/single-resource?url=${encodeURIComponent(url)}`
  });
};

// 跳转到全部资源页面
const goToResources = () => {
  uni.navigateTo({
    url: '/pages/learn/resources'
  });
};
</script>

<style lang="css" scoped>
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

/* 资源和练习题容器通用样式 */
.resources-container {
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px; /* 增加容器之间的间距 */
}

/* 练习题容器额外样式 */
.questions-container {
  background-color: var(--bg-card);
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
  padding: 20px;
  background-color: var(--bg-page);
  border-radius: 12px;
  transition: all 0.2s ease;
  min-height: 100px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  margin-bottom: 5px;
}

/* 练习题卡片样式 */
.question-card {
  background-color: var(--bg-page);
}

.resource-card:active {
  transform: scale(0.98);
  background-color: var(--border-default);
}

.question-card:active {
  background-color: var(--border-default);
}

.resource-icon {
  width: 60px;
  height: 60px;
  margin-right: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e3f2fd;
  border-radius: 10px;
  flex-shrink: 0;
}

/* 练习题图标容器样式 */
.question-card .resource-icon {
  background-color: #dbeafe;
}

.icon-image {
  width: 24px;
  height: 24px;
}

.resource-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.resource-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  line-height: 1.3;
}

.resource-tags {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
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
}

/* 响应式设计 - 桌面 */
@media (min-width: 992px) {
  .resources-grid {
    grid-template-columns: repeat(3, 1fr);
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