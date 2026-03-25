<template>
  <WebNavbar>
    <view class="container">    
    <!-- 主内容区 -->
    <view class="content">
      <!-- 功能卡片列表 -->
      <view class="features-grid">

        
        <!-- 定制面试官 -->
        <view class="feature-card" @click="goToCustomInterviewer">
          <view class="card-icon">
            <image src="/static/ready/hr.png" mode="aspectFit" class="icon-image"></image>
          </view>
          <text class="card-title">定制面试官</text>
          <text class="card-desc">自定义面试官的音色、风格</text>
          <view class="card-hover-effect"></view>
        </view>
        
        <!-- 自定义面试场景 -->
        <view class="feature-card" @click="goToCustomScenario">
          <view class="card-icon">
            <image src="/static/ready/job.png" mode="aspectFit" class="icon-image"></image>
          </view>
          <text class="card-title">自定义面试场景</text>
          <text class="card-desc">模拟各类场景，提前演练</text>
          <view class="card-hover-effect"></view>
        </view>
        
                <!-- 简历解析 -->
        <view class="feature-card" @click="goToResumeSubmit">
          <view class="card-icon">
            <image src="/static/ready/resume-icon.png" mode="aspectFit" class="icon-image"></image>
          </view>
          <text class="card-title">简历解析</text>
          <text class="card-desc">专业简历解析，上传获取评析</text>
          <view class="card-hover-effect"></view>
        </view>

        <!-- 资料库学习 -->
        <view class="feature-card" @click="goToCareerSuggestion">
          <view class="card-icon">
            <image src="/static/ready/career.png" mode="aspectFit" class="icon-image"></image>
          </view>
          <text class="card-title">职业规划</text>
          <text class="card-desc">智能AI帮助规划职业方向</text>
          <view class="card-hover-effect"></view>
        </view>
      </view>
      
      <!-- 推荐内容区域 -->
      <view class="recommendation-section">
        <view class="section-header">
          <text class="section-title">热门推荐</text>
          <text class="section-subtitle" v-if="loading">加载中...</text>
        </view>
        <view class="recommendation-list" v-if="!loading">
          <view class="recommendation-item"
                v-for="(item, index) in recommendations"
                :key="index"
                @click="goToRecommendation(item.path)">
            <view class="rec-content">
              <text class="recommendation-title">{{ item.title }}</text>
              <view class="rec-tags" v-if="item.tags">
                <text class="rec-tag" v-for="(tag, tagIndex) in item.tags.slice(0, 3)" :key="tagIndex">{{ tag }}</text>
              </view>
              <text class="recommendation-desc">{{ item.desc }}</text>
            </view>
            <!-- 添加上箭头图标表示可点击跳转 -->
            <view class="arrow-icon">
              <image src="/static/ready/arrow-right.png" mode="aspectFit" class="arrow-image"></image>
            </view>
          </view>
        </view>
        <!-- 加载骨架屏 -->
        <view class="recommendation-list" v-else>
          <view class="recommendation-item skeleton" v-for="i in 4" :key="i">
            <view class="rec-content">
              <view class="skeleton-title"></view>
              <view class="skeleton-desc"></view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
  </WebNavbar>
</template>

<script setup>
import WebNavbar from '@/components/WebNavbar.vue';
import { ref, onMounted } from 'vue';
import { http } from '@/stores/request.js'
import { ENDPOINTS } from '@/stores/api.js'

// 响应式数据声明
const recommendations = ref([]);
const loading = ref(false);

// 获取热门推荐
const fetchPopularRecommendations = async () => {
  loading.value = true;
  try {
    const data = await http.get(ENDPOINTS.recommendation.popular + '?limit=6');

    if (data && data.recommendations) {
      recommendations.value = data.recommendations.map(item => ({
        title: item.name,
        desc: item.reason || `${item.resource_type} · ${item.difficulty || '通用'}`,
        path: item.url,
        tags: item.tags,
        type: item.resource_type,
        difficulty: item.difficulty
      }));
    } else {
      // 降级到默认推荐
      useDefaultRecommendations();
    }
  } catch (error) {
    console.error('获取热门推荐失败:', error);
    // API 失败时使用默认推荐
    useDefaultRecommendations();
  } finally {
    loading.value = false;
  }
};

// 默认推荐（降级方案）
const useDefaultRecommendations = () => {
  recommendations.value = [
    {
      title: "自我介绍的黄金公式",
      desc: "掌握结构化自我介绍，给面试官留下深刻印象",
      path: 'https://www.bilibili.com/opus/737940806873120790'
    },
    {
      title: "常见面试问题及回答技巧",
      desc: "48个高频面试问题，总结高分回答模板",
      path: 'https://www.nowcoder.com/discuss/364011316049125376/'
    },
    {
      title: "如何应对压力面试",
      desc: "压力情境下保持冷静的实用技巧",
      path: 'https://blog.ihr360.com/p/59768/'
    },
    {
      title: "STAR法则详解及举例分析",
      desc: "在实战中使用STAR法则回答面试问题。",
      path: 'https://www.zhipin.com/article/75.html/'
    },
    {
      title: "面试礼仪和面试着装",
      desc: "打造专业形象，提升面试第一印象",
      path: 'https://www.bilibili.com/opus/628170878656451231'
    },
    {
      title: "远程面试注意事项",
      desc: "视频面试的设备准备与沟通技巧",
      path: 'https://www.zhipin.com/article/85.html/'
    }
  ];
};

// 跳转方法
const goToResumeSubmit = () => {
  uni.navigateTo({
    url: '/pages/resume/resume'
  });
};

const goToCustomInterviewer = () => {
  uni.navigateTo({
    url: '/pages/interview/interviewer'
  });
};

const goToCustomScenario = () => {
  uni.navigateTo({
    url: '/pages/scenario/custom'
  });
};

const goToCareerSuggestion = () => {
  uni.navigateTo({
    url: '/pages/learn/career'
  });
};

const goToRecommendation = (path) => {
  uni.navigateTo({
    // 使用encodeURIComponent处理特殊字符
    url: `/pages/learn/single-resource?url=${encodeURIComponent(path)}`
  });
};

// 页面加载时获取热门推荐
onMounted(() => {
  fetchPopularRecommendations();
});
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-page);
}

/* 导航栏样式 */
.navbar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-default);
  padding-top: 20rpx;
}

.navbar-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--text-primary);
}

/* 主内容区样式 */
.content {
  flex: 1;
  padding: 20rpx;
}

/* 功能卡片网格 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
  margin-bottom: 30rpx;
}

/* 功能卡片样式 */
.feature-card {
  background-color: var(--bg-card);
  border-radius: 16rpx;
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease;
}

.feature-card:active {
  transform: scale(0.98);
}

.card-icon {
  width: 80rpx;
  height: 80rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-image {
  width: 100%;
  height: 100%;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 10rpx;
}

.card-desc {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.4;
}

.card-hover-effect {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.03);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.feature-card:active .card-hover-effect {
  opacity: 1;
}

/* 推荐内容区域 */
.recommendation-section {
  background-color: var(--bg-card);
  border-radius: 16rpx;
  padding: 25rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 20rpx;
  display: block;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.recommendation-item {
  padding: 20rpx 0;
  border-bottom: 1px solid var(--border-default);
  position: relative;
  padding-right: 40rpx; /* 为箭头留出空间 */
  cursor: pointer; /* 显示手型光标 */
}

.recommendation-item:last-child {
  border-bottom: none;
}

.recommendation-item:active {
  background-color: rgba(0, 0, 0, 0.02);
}

.recommendation-title {
  font-size: 15px;
  color: var(--text-primary);
  display: block;
  margin-bottom: 8rpx;
  font-weight: 500;
}

.recommendation-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 区域标题样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 推荐内容样式 */
.rec-content {
  flex: 1;
  padding-right: 40rpx;
}

.rec-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-bottom: 8rpx;
}

.rec-tag {
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(58, 132, 255, 0.1);
  color: var(--color-primary);
  border-radius: 8rpx;
}

/* 骨架屏样式 */
.skeleton {
  opacity: 0.6;
}

.skeleton-title {
  width: 60%;
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-desc {
  width: 80%;
  height: 12px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 箭头图标样式 */
.arrow-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 60rpx;
  height: 60rpx;
}

.arrow-image {
  width: 100%;
  height: 100%;
  opacity: 1;
  filter: invert(39%) sepia(93%) saturate(7475%) hue-rotate(212deg) brightness(97%) contrast(109%);
}

/* 响应式调整 */
@media (min-width: 768px) {
  .features-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 30rpx;
  }
}

/* #ifdef MP-WEIXIN */
@media (max-width:568px) {
  .content{
    margin-top:60px;
  }
}
/* #endif */
</style>