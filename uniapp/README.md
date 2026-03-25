# AI面试助手

<div align="center">
  <img src="./static/logo.png" alt="AI面试助手" width="200" height="200">
  <h3>基于AI驱动的跨平台面试模拟与职业学习应用</h3>
  <p>🌟 提升面试技能，加速职业成长 🌟</p>

  <div style="margin-top: 20px;">
    <img src="https://img.shields.io/badge/uni--app-v3.0.0-blue.svg" alt="uni-app">
    <img src="https://img.shields.io/badge/Vue-3.4.21-green.svg" alt="Vue">
    <img src="https://img.shields.io/badge/Pinia-3.0.3-orange.svg" alt="Pinia">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  </div>
</div>

## 📋 项目简介

AI面试助手是一个基于uni-app开发的跨平台应用，旨在为用户提供AI驱动的面试模拟、职业学习和面试报告分析功能。无论您是正在寻找工作的求职者，还是希望提升面试技能的在职人士，AI面试助手都能为您提供个性化的学习和模拟体验，帮助您在面试中脱颖而出。

## ✨ 功能特性

### 🎯 面试模拟
- **多类型面试**: 支持技术面试、HR面试、行业特定面试等多种类型
- **AI实时对话**: 智能AI面试官，实时提问和反馈
- **视频/语音模式**: 支持视频面试和语音面试两种模式
- **表情与语音分析**: 实时分析面部表情和语音语调，提供全方位反馈

### 📚 职业学习
- **丰富学习资源**: 提供视频课程、练习题目、学习计划等
- **个性化推荐**: 根据职业目标和水平，推荐定制化学习内容
- **学习进度跟踪**: 记录学习历程，可视化学习成果

### 📊 面试报告
- **详细分析报告**: 面试结束后生成全面的面试报告
- **多维度评分**: 从回答质量、沟通能力、专业知识等多维度评分
- **改进建议**: 提供针对性的改进建议和学习资源推荐
- **PDF导出**: 支持将报告导出为PDF格式

### 📄 简历优化
- **简历上传解析**: 支持多种格式简历上传和内容提取
- **AI智能优化**: 提供简历优化建议和关键词分析
- **简历管理**: 方便管理多份简历版本

### 👤 个人中心
- **完整用户体系**: 注册、登录、个人信息管理
- **历史记录**: 查看面试和学习历史
- **个性化设置**: 根据个人需求调整应用设置

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| 核心框架 | uni-app | 3.0.0 |
| 前端框架 | Vue | 3.4.21 |
| 状态管理 | Pinia | 3.0.3 |
| UI组件库 | uni-ui | 1.5.10 |
| 图表库 | @qiun/ucharts | 2.5.0 |
| CSS框架 | Tailwind CSS | 4.1.11 |
| 样式预处理器 | Sass | 1.89.2 |
| 国际化 | vue-i18n | 9.1.9 |
| 构建工具 | Vite | 5.2.8 |
| E2E测试 | Playwright | 1.50.0 |

## 🚀 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0
- HBuilderX (推荐，用于uni-app开发)

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/xiaoqimi1/11.git
cd 11

# 安装依赖
npm install
# 或使用yarn
yarn install
```

### 运行项目

#### H5平台
```bash
npm run dev:h5
# 或
yarn dev:h5
```

访问 http://localhost:5173 查看应用

#### 微信小程序
```bash
npm run dev:mp-weixin
# 或
yarn dev:mp-weixin
```

使用微信开发者工具导入 `unpackage/dist/dev/mp-weixin` 目录

#### 支付宝小程序
```bash
npm run dev:mp-alipay
# 或
yarn dev:mp-alipay
```

使用支付宝开发者工具导入 `unpackage/dist/dev/mp-alipay` 目录

### 构建项目

#### 构建H5
```bash
npm run build:h5
# 或
yarn build:h5
```

#### 构建微信小程序
```bash
npm run build:mp-weixin
# 或
yarn build:mp-weixin
```

#### 构建支付宝小程序
```bash
npm run build:mp-alipay
# 或
yarn build:mp-alipay
```

### E2E测试

项目使用 Playwright 进行端到端测试。

```bash
# 安装 Playwright 浏览器
npx playwright install

# 运行所有测试（需要先启动前后端服务）
set SKIP_WEB_SERVER=true
set TEST_API_URL=http://localhost:8000/api/v1
npx playwright test

# 运行指定测试文件
npx playwright test e2e/tests/auth.spec.js

# 带浏览器界面运行
npx playwright test --headed

# 调试模式
npx playwright test --debug
```

更多测试信息请参考：
- [E2E测试计划](./docs/E2E_TEST_PLAN.md)
- [测试报告](./docs/TEST_REPORT.md)
- [开发指南](./docs/DEVELOPMENT_GUIDE.md)

## 📁 项目结构

```
├── src/                      # 源代码目录
│   ├── components/           # 公共组件
│   ├── pages/                # 页面文件
│   │   ├── interview/        # 面试相关页面
│   │   ├── learn/            # 学习相关页面
│   │   ├── report/           # 报告页面
│   │   ├── resume/           # 简历页面
│   │   └── ...               # 其他页面
│   ├── static/               # 静态资源
│   ├── stores/               # Pinia状态管理
│   ├── App.vue               # 应用入口组件
│   ├── main.js               # 应用入口文件
│   └── pages.json            # 页面路由配置
├── static/                   # 根目录静态资源
├── package.json              # 项目依赖配置
├── vite.config.js            # Vite配置
└── README.md                 # 项目说明文档
```

## 📖 使用说明

### 1. 注册与登录
- 下载应用或访问H5版本
- 使用手机号注册账号
- 登录后完善个人信息和职业目标

### 2. 开始面试
- 在首页选择"AI面试"功能
- 选择面试类型和难度
- 开始AI模拟面试
- 面试结束后查看详细报告

### 3. 学习提升
- 进入"学习中心"查看推荐内容
- 选择感兴趣的课程或练习
- 完成学习任务，跟踪学习进度

### 4. 简历优化
- 上传简历或手动填写简历信息
- 查看AI优化建议
- 根据建议完善简历内容

## 🤝 贡献指南

我们欢迎并感谢所有形式的贡献！无论是报告bug、提出新功能建议，还是提交代码，都能帮助我们改进项目。

### 贡献流程

1. **Fork 项目**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **开启 Pull Request**

### 开发规范

- 遵循Vue 3和uni-app的开发规范
- 使用ESLint进行代码检查
- 提交代码前确保所有测试通过
- 编写清晰的提交信息

## 📚 文档

| 文档 | 说明 |
|------|------|
| [API迁移指南](./docs/API_MIGRATION_GUIDE.md) | FastAPI后端迁移指南 |
| [E2E测试计划](./docs/E2E_TEST_PLAN.md) | 端到端测试计划与用例 |
| [项目结构](./docs/PROJECT_STRUCTURE.md) | 项目目录结构与说明 |
| [开发指南](./docs/DEVELOPMENT_GUIDE.md) | 开发规范与调试技巧 |
| [测试报告](./docs/TEST_REPORT.md) | E2E测试报告 |
| [迁移计划](./docs/UNIAPP_MIGRATION_PLAN.md) | UniApp迁移计划 |

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- **项目维护者**: HanphoneJan
- **邮箱**: 1195560097@qq.com
- **GitHub**: [https://github.com/xiaoqimi1/11](https://github.com/xiaoqimi1/11)

## 🙏 致谢

感谢所有为项目做出贡献的开发者和用户！

## 📈 项目统计

<div align="center">
  <img src="https://komarev.com/ghpvc/?username=xiaoqimi1&label=项目访问量&color=blue&style=flat" alt="项目访问量">
</div>

---

<div align="center">
  <p>🌟 如果你觉得这个项目有用，请给我们一个星标！ 🌟</p>
</div>