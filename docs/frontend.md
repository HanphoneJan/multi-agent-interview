# 前端开发文档

本文面向日常维护这个项目前端的开发者，重点说明：

- 前端代码在哪里
- 本地怎么启动
- 和后端怎么联调
- 页面和状态管理从哪里下手

## 1. 技术栈

- uni-app
- Vue 3
- Pinia
- Vite
- Playwright

前端代码目录：`uniapp/`

## 2. 目录结构

前端主要代码在 `uniapp/src/`：

- `pages/`：业务页面
- `components/`：公共组件
- `stores/`：Pinia 状态管理
- `composables/`：组合式逻辑
- `config/`：前端配置
- `styles/`：样式和主题
- `static/`：静态资源

常用文件：

- `uniapp/src/main.js`：前端入口
- `uniapp/src/pages.json`：页面路由
- `uniapp/src/stores/api.js`：接口访问封装
- `uniapp/src/stores/request.js`：请求层

## 3. 本地启动方式

### 3.1 先准备后端

建议先在项目根目录执行：

```powershell
.\start-dev.ps1
```

然后单独启动后端：

```powershell
cd fastapi
.venv\Scripts\python -m uvicorn app.main:app --reload --port 18000
```

### 3.2 启动前端

```powershell
cd uniapp
npm install
npm run dev:h5
```

如果你开发的是微信小程序：

```powershell
cd uniapp
npm install
npm run dev:mp-weixin
```

## 4. 常用脚本

开发：

- `npm run dev:h5`
- `npm run dev:mp-weixin`

构建：

- `npm run build:h5`
- `npm run build:mp-weixin`

质量和测试：

- `npm run lint`
- `npm run lint:fix`
- `npm run test:e2e`

## 5. 和后端联调

联调前至少要保证：

- PostgreSQL / Redis / Milvus 已启动
- FastAPI 已启动
- 数据库已经做过迁移和种子导入

如果登录、场景列表、面试流程报 404 或空数据，优先检查：

1. 后端是否已经运行
2. 是否执行过 `migrate_db.py`
3. 是否执行过 `seed_db.py`

## 6. 页面开发从哪里入手

如果你要改页面，优先看：

- `uniapp/src/pages/`

如果你要改公共组件，优先看：

- `uniapp/src/components/`

如果你要改接口调用或登录态，优先看：

- `uniapp/src/stores/api.js`
- `uniapp/src/stores/request.js`
- `uniapp/src/stores/user.js`

如果你要改音视频或实时面试逻辑，优先看：

- `uniapp/src/pages/interview/`
- `uniapp/src/composables/interview/`

## 7. E2E 测试

项目已经包含 Playwright 测试。

运行前建议：

1. 启动后端
2. 启动前端
3. 确认测试账号可登录

执行：

```powershell
cd uniapp
npm run test:e2e
```

调试：

```powershell
cd uniapp
npm run test:e2e:headed
npm run test:e2e:debug
```

## 8. 开发建议

- 改页面先确认它在 `pages.json` 中的路由位置
- 改接口前先确认后端真实端点，不要只看旧注释
- 改登录或请求层时，优先从 `stores` 往外查
- 涉及实时面试时，先确认当前是在 H5、微信小程序还是其他端
