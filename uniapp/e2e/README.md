# UniApp E2E 测试

使用 Playwright 进行端到端测试，验证用户核心业务流程。

## 快速开始

### 1. 安装依赖

```bash
# 安装 Playwright 浏览器
npm run playwright:install

# 或手动安装
npx playwright install chromium
```

### 2. 配置环境变量

创建 `.env` 文件（可选）：

```env
TEST_BASE_URL=http://localhost:3000
TEST_API_URL=http://localhost:8000/api/v1
```

### 3. 运行测试

```bash
# 运行所有测试
npm run test:e2e

# 带 UI 界面运行
npm run test:e2e:ui

# 调试模式
npm run test:e2e:debug

# 有界面模式（可看到浏览器）
npm run test:e2e:headed

# 运行特定测试文件
npx playwright test e2e/tests/auth.spec.js

# 运行特定测试
npx playwright test -g "用户登录成功"
```

### 4. 查看测试报告

```bash
npm run test:e2e:report
```

## 项目结构

```
e2e/
├── tests/              # 测试用例
│   ├── auth.spec.js    # 用户认证测试
│   ├── interview.spec.js  # 面试流程测试
│   ├── learning.spec.js   # 学习资源测试
│   └── profile.spec.js    # 个人中心测试
├── pages/              # Page Object Models
│   ├── LoginPage.js    # 登录页
│   ├── HomePage.js     # 首页
│   ├── InterviewPage.js   # 面试页
│   └── LearningPage.js    # 学习资源页
├── fixtures/           # 测试数据
│   ├── users.json      # 测试用户
│   └── scenarios.json  # 面试场景
├── utils/              # 工具函数
│   ├── test-helpers.js # 测试辅助函数
│   └── api-client.js   # API 客户端
└── README.md           # 本文档
```

## 测试用例覆盖

### 用户认证模块

- ✅ TC-AUTH-001: 用户登录成功（邮箱/手机号）
- ✅ TC-AUTH-002: 用户登录失败
- ✅ TC-AUTH-003: 表单验证
- ✅ TC-AUTH-004: Token 自动刷新

### 面试流程模块

- ✅ TC-IV-001: 选择面试场景
- ✅ TC-IV-002: 创建面试会话
- ✅ TC-IV-003: 面试过程中暂停/恢复
- ✅ TC-IV-004: 面试消息交互
- ✅ TC-IV-005: 结束面试

### 学习资源模块

- ✅ TC-LR-001: 浏览学习资源
- ✅ TC-LR-002: 查看个性化推荐

### 个人中心模块

- ✅ TC-PC-001: 查看个人资料
- ✅ TC-PC-002: 编辑个人资料

## 测试数据

测试数据存储在 `fixtures/` 目录下：

- `users.json` - 测试用户账号信息
- `scenarios.json` - 面试场景数据

## Page Object Model

测试使用 Page Object 模式组织，提高可维护性：

```javascript
// 示例：使用 LoginPage
const { LoginPage } = require('../pages/LoginPage');

const loginPage = new LoginPage(page);
await loginPage.goto();
await loginPage.login('test@example.com', 'password123');
```

## 调试技巧

### 1. 使用 Playwright Inspector

```bash
npx playwright test --debug
```

### 2. 单步执行

```bash
npx playwright test --headed --slowmo 500
```

### 3. 生成追踪

测试结果会自动生成追踪文件，可在报告中查看。

## CI/CD 集成

测试已配置 GitHub Actions 工作流：

- 文件：`.github/workflows/e2e.yml`
- 触发条件：push 到 main/develop 分支或相关 PR
- 运行环境：Ubuntu + Chromium

## 注意事项

1. **后端依赖**：部分测试需要 FastAPI 后端服务运行
2. **测试账号**：确保测试账号在后端数据库中存在
3. **网络延迟**：测试中超时设置考虑了网络延迟
4. **浏览器**：仅在 Chromium 中测试（H5 模式）

## 常见问题

### Q: 测试无法找到页面元素？

A: 可能是选择器需要更新。检查 UniApp 页面源码，更新 Page Object 中的选择器。

### Q: 登录测试失败？

A: 确认测试账号在后端数据库中存在，且密码正确。

### Q: WebSocket 测试失败？

A: 面试测试需要 WebSocket 服务正常运行，确保 FastAPI 后端已启动。

## 维护指南

### 添加新测试

1. 在 `pages/` 中创建新的 Page Object（如需）
2. 在 `tests/` 中创建测试文件
3. 参考现有测试用例格式
4. 运行测试确保通过

### 更新选择器

当 UI 变更时，更新对应 Page Object 中的选择器：

```javascript
this.selectors = {
  loginButton: '.new-login-btn, button:has-text("登录")',
};
```

### 添加测试数据

在 `fixtures/` 中添加新的 JSON 数据文件，然后在测试中引用。
