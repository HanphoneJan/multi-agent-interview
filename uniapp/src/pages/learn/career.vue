<template>
  <WebNavbar>
    <view class="career-container">
    <!-- 主要内容 -->
    <view class="main-content">
      <!-- 加载状态 -->
      <view v-if="loading" class="loading-container">
        <uni-load-more status="loading"></uni-load-more>
      </view>
      
      <view class="form-section">
        <text class="section-title">职业规划信息填写</text>
        
        <view class="form-item">
          <text class="form-label">毕业院校</text>
          <input class="form-input" v-model="formData.university" placeholder="请输入您的毕业院校" />
        </view>
        
        <view class="form-item">
          <text class="form-label">所学专业</text>
          <input class="form-input" v-model="formData.major" placeholder="请输入您的专业" />
        </view>
        
        <view class="form-item">
          <text class="form-label">就业城市</text>
          <input class="form-input" v-model="formData.address" placeholder="请输入您的就业意向城市" />
        </view>

        <view class="form-item">
          <text class="form-label">职业意向</text>
          <radio-group @change="radioChange" class="radio-group">
            <label class="radio-item" v-for="item in careerOptions" :key="item.value">
              <radio :value="item.value" :checked="formData.careerDirection === item.value" color="#4a90e2" />
              <text>{{item.label}}</text>
            </label>
            <label class="radio-item other-item">
              <radio value="other" :checked="formData.careerDirection === 'other'" color="#4a90e2" />
              <text>其他</text>
              <input 
                v-if="formData.careerDirection === 'other'" 
                class="other-input" 
                v-model="formData.otherCareer" 
                placeholder="请填写您的职业意向" 
              />
            </label>
          </radio-group>
        </view>
      </view>
      
      <!-- 结果展示 -->
      <view class="results-section">
        <text class="section-title">您的职业规划建议</text>
        
        <view class="advice-card">
          <text class="advice-title">职业发展建议</text>
          <text class="advice-content">
            {{ hasInput ? careerAdvice : '请填写您的职业信息以获取个性化建议' }}
          </text>
        </view>
        
        <view class="jobs-card">
          <text class="jobs-title">推荐就业岗位 ({{ hasInput ? recommendedJobs.length + '个' : '待推荐' }})</text>
          <view class="job-list">
            <template v-if="hasInput && recommendedJobs.length">
              <view v-for="(job, index) in recommendedJobs" :key="index" class="job-item">
                <text class="job-name">{{ index + 1 }}. {{ job.title }}</text>
                <text class="job-desc">{{ job.description }}</text>
                <text class="job-info">薪资范围：{{ job.salary_range }}</text>
                <text class="job-detail">技能要求：{{ job.required_skills?.join('、') }}</text>
                <text class="job-detail">发展路径：{{ job.growth_path }}</text>
              </view>
            </template>
            <template v-else>
              <view class="job-item-placeholder">
                <text>填写完整信息后，将为您推荐合适的岗位</text>
              </view>
            </template>
          </view>
        </view>
      </view>
    </view>
  </view>
  </WebNavbar>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useUserStore } from '@/stores/user.js'
import { ENDPOINTS } from '@/stores/api.js';
import { http } from '@/stores/request.js';
import WebNavbar from '@/components/WebNavbar.vue'

const userStore = useUserStore()

// 表单数据
const formData = ref({
  address: '',
  university: '',
  major: '',
  careerDirection: '',
  otherCareer: ''
})

// 职业选项 - 新增人工智能选项
const careerOptions = ref([
  { value: 'technology', label: '技术研发' },
  { value: 'product', label: '产品经理' },
  { value: 'design', label: '设计创意' },
  { value: 'marketing', label: '市场营销' },
  { value: 'finance', label: '金融财务' },
  { value: 'management', label: '运营管理' },
])

// 默认职业建议 
const defaultAdvice = {
  technology: "根据您提供的信息和搜索结果，以下是针对您的职业规划建议：\n\n 1. 职业发展路径\n- 初级工程师：作为软件工程或人工智能专业的毕业生，您可以从基础的软件开发、测试和维护工作开始。这些职位通常要求掌握编程语言（如Python、Java等）和基本的算法知识。\n- 中级工程师：随着经验的积累和技术能力的提升，您可以逐步过渡到更复杂的项目开发和管理角色，例如参与人工智能算法的设计和应用开发。\n- 高级工程师/专家：在积累了丰富的行业经验和技术深度后，可以考虑成为团队的技术负责人或领域内的专家顾问。此外，也可以尝试向项目管理方向发展。\n- 创业/自由职业者：如果您对创新有浓厚的兴趣并具备一定的商业洞察力的话，还可以考虑创办自己的科技公司或者以咨询顾问的形式为其他企业提供服务。\n\n 2. 技能提升建议\n- 深化专业知识：加强对机器学习、深度学习等领域的理解与实践能力；同时了解最新的AI技术和趋势变化情况也很重要。可以通过在线课程平台学习相关课程来补充理论知识体系不足之处；参加行业内的研讨会和技术交流活动也是很好的方式之一用来拓宽视野并结识同行朋友共同进步成长的机会所在之地啦！另外还可以尝试阅读一些经典书籍比如《统计学习方法》这类由周志华教授所著的作品对于初学者来说非常友好且易于理解的内容安排上也十分合理呢~当然了如果条件允许的话最好能够亲自动手编写代码实现某些功能模块以此来加深印象效果更佳哦~最后但同样重要的是记得定期回顾总结所学知识点及时查漏补缺保持持续学习的态度才是关键所在呀！至于具体选择哪家公司进行实习则完全取决于个人喜好以及未来发展目标等因素综合考量之后做出最适合自己的决定即可啦~希望我的建议对你有所帮助吧！加油鸭(≧▽≦)/",
  product: "作为产品经理方向的求职者，建议您系统学习产品设计方法论，培养数据分析能力。可以尝试分析热门产品，输出产品体验报告，积累产品sense。",
  design: "对于设计创意方向，建议您构建完整的作品集，展示多样化的设计风格。关注设计趋势，参与设计比赛，并通过实习积累实际项目经验。",
  marketing: "市场营销方向需要强大的沟通能力和数据分析能力。建议您学习数字营销工具，尝试运营自媒体账号，并通过实习积累实际的营销策划经验。",
  finance: "金融财务方向需要扎实的专业知识和相关证书。建议您考取CPA、CFA等证书，关注金融市场动态，并通过实习积累实际操作经验。",
  management: "运营管理方向需要综合能力。建议您学习项目管理知识，培养数据分析能力，并通过实习或校园活动积累团队管理和项目执行经验。",
  other: "基于您的个性化职业方向，建议您深入研究行业趋势，构建专业知识体系，并通过实习或项目积累相关经验。同时拓展行业人脉，关注目标岗位的能力要求。"
}

const defaultJobs = {
  technology: [
        {
            "职位": "对日软件开发工程师（赴日出差）",
            "薪资": "1-2万",
            "公司": "得力欧系统软件（长春）有限公司",
            "城市": "广州",
            "区域": "南沙",
            "学历": "学历不限",
            "领域": "IT服务",
            "规模": "20-99人",
            "链接": "http://company.zhaopin.com/CZ131277470.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "赴日软件开发工程师",
            "薪资": "1.7-3万",
            "公司": "杭州优灿科技有限公司",
            "城市": "广州",
            "区域": "天河",
            "学历": "学历不限",
            "领域": "计算机软件",
            "规模": "500-999人",
            "链接": "http://company.zhaopin.com/CZ272317030.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "软件销售实习生（专业不限、提供实习证明）",
            "薪资": "4000-7000元",
            "公司": "广州经传多赢投资咨询有限公司",
            "城市": "广州",
            "区域": "番禺",
            "学历": "大专",
            "领域": "证券/期货",
            "规模": "500-999人",
            "链接": "http://company.zhaopin.com/CZ284049080.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "计算机软件工程师",
            "薪资": "8000-15000元",
            "公司": "广州晨新自控设备有限公司",
            "城市": "广州",
            "区域": "黄埔",
            "学历": "本科",
            "领域": "仪器仪表制造",
            "规模": "100-299人",
            "链接": "http://company.zhaopin.com/CZ263290510.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "软件工程实习生（偏Python）",
            "薪资": "3000-4000元",
            "公司": "广州玻思韬控释药业有限公司",
            "城市": "广州",
            "区域": "黄埔",
            "学历": "本科",
            "领域": "医药制造",
            "规模": "300-499人",
            "链接": "http://company.zhaopin.com/CZ625351920.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "人工智能软件销售（独角兽企业）",
            "薪资": "1.5-3万",
            "公司": "探迹科技",
            "城市": "广州",
            "区域": "海珠",
            "学历": "大专",
            "领域": "互联网",
            "规模": "1000-9999人",
            "链接": "http://company.zhaopin.com/CZ406882580.htm",
            "搜索条件": "职业意向"
        }
  ],

  other: [
            {
            "职位": "赴日软件开发工程师",
            "薪资": "1.7-3万",
            "公司": "杭州优灿科技有限公司",
            "城市": "广州",
            "区域": "天河",
            "学历": "学历不限",
            "领域": "计算机软件",
            "规模": "500-999人",
            "链接": "http://company.zhaopin.com/CZ272317030.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "计算机软件工程师",
            "薪资": "8000-15000元",
            "公司": "广州晨新自控设备有限公司",
            "城市": "广州",
            "区域": "黄埔",
            "学历": "本科",
            "领域": "仪器仪表制造",
            "规模": "100-299人",
            "链接": "http://company.zhaopin.com/CZ263290510.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "软件定义工程师（公路\\土木\\交通工程专业-应届毕业生）",
            "薪资": "4000-8000元",
            "公司": "广州炎晟信息科技有限公司",
            "城市": "广州",
            "区域": "番禺",
            "学历": "大专",
            "领域": "计算机软件",
            "规模": "20-99人",
            "链接": "http://company.zhaopin.com/CZ393310020.htm",
            "搜索条件": "专业"
        },
        {
            "职位": "硬件维护工程师",
            "薪资": "8000-12000元",
            "公司": "微分视界信息科技(西安)有限公司",
            "城市": "广州",
            "区域": "南沙",
            "学历": "学历不限",
            "领域": "企业服务",
            "规模": "100-299人",
            "链接": "http://company.zhaopin.com/CZL1485751060.htm",
            "搜索条件": "职业意向"
        },
        {
            "职位": "诚聘普工/操作工-月入8000（包住）",
            "薪资": "7000-8000元",
            "公司": "广东龙驰供应链管理有限公司",
            "城市": "广州",
            "区域": "天河",
            "学历": "学历不限",
            "领域": "企业服务",
            "规模": "100-299人",
            "链接": "http://company.zhaopin.com/CZL1474300300.htm",
            "搜索条件": "职业意向"
        },
        {
            "职位": "急招普工/操作工-五险一金-四人间",
            "薪资": "7000-8000元",
            "公司": "广东捷聘企业管理有限公司",
            "城市": "广州",
            "区域": "增城",
            "学历": "学历不限",
            "领域": "人力资源服务",
            "规模": "500-999人",
            "链接": "http://company.zhaopin.com/CZL1485726410.htm",
            "搜索条件": "职业意向"
        },
        {
            "职位": "硬件维护工程师",
            "薪资": "8000-12000元",
            "公司": "微分视界信息科技(西安)有限公司",
            "城市": "广州",
            "区域": "花都",
            "学历": "学历不限",
            "领域": "企业服务",
            "规模": "100-299人",
            "链接": "http://company.zhaopin.com/CZL1485751060.htm",
            "搜索条件": "职业意向"
        },
        {
            "职位": "电脑销售专员（提供住宿）",
            "薪资": "9000-17000元",
            "公司": "广东创众智网络科技有限公司",
            "城市": "广州",
            "区域": "天河",
            "学历": "学历不限",
            "领域": "计算机硬件",
            "规模": "100-299人",
            "链接": "http://company.zhaopin.com/CZ508364380.htm",
            "搜索条件": "职业意向"
        }
  ]
}

// 结果数据
const careerAdvice = ref('')
const recommendedJobs = ref([])
const loading = ref(false)

// 表单验证
const formValid = computed(() => {
  return formData.value.address && 
         formData.value.university && 
         formData.value.major && 
         (formData.value.careerDirection === 'other' ? formData.value.otherCareer : formData.value.careerDirection)
})

// 是否有输入
const hasInput = computed(() => {
  return formData.value.address || 
         formData.value.university || 
         formData.value.major || 
         formData.value.careerDirection || 
         formData.value.otherCareer
})

// 单选按钮变化
const radioChange = (e) => {
  formData.value.careerDirection = e.detail.value
  if (e.detail.value !== 'other') {
    formData.value.otherCareer = ''
  }
}

// 获取职业建议
const getCareerAdvice = async () => {
  if (!formValid.value) {
    careerAdvice.value = '请填写您的职业信息以获取个性化建议'
    recommendedJobs.value = []
    return
  }
  
  loading.value = true
  
  try {
    const careerDirection = formData.value.careerDirection === 'other' 
      ? formData.value.otherCareer 
      : formData.value.careerDirection
    
    // 使用新的FastAPI端点获取职业建议
    const data = await http.post(ENDPOINTS.recommendation.career, {
      major: formData.value.major,
      learning_stage: userStore.learningStage || '',
      interests: [careerDirection],
      skills: []
    });

    // 适配FastAPI响应格式
    careerAdvice.value = data.advice || getDefaultAdvice(careerDirection);
    // 转换suggestions为jobs格式
    recommendedJobs.value = data.suggestions?.map(job => ({
      title: job.career,
      description: job.description,
      salary_range: job.salary_range,
      required_skills: job.required_skills,
      growth_path: job.growth_path
    })) || getDefaultJobs(careerDirection)
  } catch (err) {
    console.error('获取职业建议失败:', err)
    const careerDirection = formData.value.careerDirection === 'other' 
      ? 'other' 
      : formData.value.careerDirection
    
    careerAdvice.value = getDefaultAdvice(careerDirection)
    recommendedJobs.value = getDefaultJobs(careerDirection)
    
    // uni.showToast({
    //   title: '使用默认建议数据',
    //   icon: 'none'
    // })
  } finally {
    loading.value = false
  }
}

// 获取默认建议
const getDefaultAdvice = (direction) => {
  return defaultAdvice[direction] || defaultAdvice.other
}

// 获取默认岗位
const getDefaultJobs = (direction) => {
  console.log(direction)
  return defaultJobs[direction] || defaultJobs.other
}

// 监听表单变化
watch(formData, () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    getCareerAdvice()
  }, 500)
}, { deep: true })

let debounceTimer = null
</script>

<style lang="css" scoped>
/* 全局容器样式 */
.career-container {
  min-height: 100vh;
  background-color: var(--bg-page);
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center; /* 全局水平居中 */
}

/* 主要内容区域 - 限制最大宽度并居中 */
.main-content {
  width: 100%;
  max-width: 600px; /* 保持最大宽度限制 */
  display: flex;
  flex-direction: column;
  align-items: center; /* 内部元素居中对齐 */
}

/* 加载状态 - 居中显示 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  width: 100%; /* 占满宽度 */
}

/* 表单区域 */
.form-section {
  width: 100%;
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.08);
  margin-bottom: 25px;
  box-sizing: border-box; /* 确保padding不影响宽度 */
}

/* 标题样式 */
.section-title {
  display: block;
  font-size: 18px;
  color: var(--color-primary);
  font-weight: 600;
  margin-bottom: 25px;
  text-align: center;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-default);
}

/* 表单项 */
.form-item {
  margin-bottom: 22px;
  width: 100%;
}

.form-label {
  display: block;
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;
  margin-bottom: 10px;
  padding-left: 2px;
}

.form-input {
  width: 100%;
  height: 44px;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 0 15px;
  font-size: 15px;
  background-color: var(--bg-page);
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--color-primary);
  outline: none;
}

/* 单选组 - 优化布局 */
.radio-group {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 12px; /* 统一间距 */
  padding: 5px 0;
}

/* 单选项 */
.radio-item {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--text-primary);
  padding: 8px 15px;
  border-radius: 6px;
  background-color: var(--bg-page);
  border: 1px solid var(--border-default);
  flex: 0 0 calc(33.333% - 8px); /* 三列布局，考虑间距 */
  box-sizing: border-box;
  transition: all 0.2s;
}

.radio-item:hover {
  background-color: var(--bg-page);
}

/* 其他选项单独占一行 */
.radio-item.other-item {
  flex: 0 0 100%;
  padding: 10px 15px;
}

/* 单选按钮与文本间距 */
.radio-item radio {
  margin-right: 8px;
  transform: scale(1.1); /* 稍微放大单选按钮 */
}

.other-input {
  flex: 1;
  height: 38px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  padding: 0 12px;
  margin-left: 12px;
  font-size: 14px;
  background-color: var(--bg-page);
}

/* 结果区域 */
.results-section {
  width: 100%;
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 20px; /* 使用gap替代margin-bottom */
}

.advice-card, .jobs-card {
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.08);
  width: 100%;
  box-sizing: border-box;
}

.advice-title, .jobs-title {
  display: block;
  font-size: 16px;
  color: var(--color-primary);
  font-weight: 500;
  margin-bottom: 18px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-default);
}

.advice-content {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.7;
  text-align: justify; /* 文本两端对齐 */
  padding: 5px 0;
  white-space: pre-line; /* 新增：保留文本中的换行符 */
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.job-item {
  padding: 15px;
  border-radius: 8px;
  background-color: var(--bg-page);
  transition: transform 0.2s;
}

.job-item:hover {
  transform: translateY(-2px);
}

.job-item:last-child {
  margin-bottom: 0;
}

.job-item-placeholder {
  padding: 30px 15px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 15px;
  background-color: var(--bg-page);
  border-radius: 8px;
}

.job-name {
  display: block;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.job-info {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.job-detail {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  line-height: 1.5;
}

.job-desc {
  display: block;
  font-size: 13px;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.job-link {
  display: inline-block;
  font-size: 14px;
  color: var(--color-primary);
  text-decoration: underline;
}

/* 响应式调整 */
@media (max-width: 568px) {
  .career-container {
    padding: 15px;
  }

/* #ifdef MP-WEIXIN */
  .main-content{
    margin-top:60px;
  }
/* #endif */

  .form-section, .advice-card, .jobs-card {
    padding: 18px;
  }

  /* 小屏幕下单选按钮改为两列 */
  .radio-item {
    flex: 0 0 calc(50% - 6px);
  }

  .section-title {
    font-size: 17px;
    margin-bottom: 20px;
  }
}
</style>