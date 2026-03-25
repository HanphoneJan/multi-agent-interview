---
name: git-operator
description: Git 操作规范。用于提交代码、创建分支、查看状态、生成规范的 commit message。当用户要求提交代码、创建分支、查看 git 状态时使用此技能。
---

# Git 操作规范

## 适用场景

- 提交代码变更
- 创建/切换分支
- 查看仓库状态
- 生成规范的 commit message

## Commit Message 规范

遵循 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>
```

### Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | 新增 ROI 分析模块 |
| fix | 修复 bug | 修复图表不显示问题 |
| docs | 文档更新 | 更新实施路线图 |
| style | 代码格式 | 调整缩进 |
| refactor | 重构 | 重构查询服务 |
| perf | 性能优化 | 优化 SQL 查询 |
| test | 测试相关 | 添加单元测试 |
| chore | 构建/工具 | 更新依赖版本 |

### Scope 范围（本项目）

| Scope | 说明 |
|-------|------|
| docs | 文档（docs/ 目录） |
| preview | 预览页面（preview/ 目录） |
| agents | Agent 配置 |
| skills | Skill 配置 |
| config | 配置文件 |

### Subject 规则

- 使用中文描述
- 不超过 50 字符
- 不以句号结尾
- 使用祈使语气（添加、修复、更新，而非添加了、修复了）

### Body 规则

- 详细描述改动内容
- 使用列表形式列出主要改动
- 说明 why 而不是 what

## 提交操作流程

### 1. 检查状态

```bash
git status
```

### 2. 查看差异

```bash
git diff              # 未暂存的改动
git diff --staged     # 已暂存的改动
```

### 3. 暂存文件

```bash
git add <files>       # 指定文件
git add .             # 所有文件
```

### 4. 执行提交

```bash
git commit -m "<type>(<scope>): <subject>

- 改动点 1
- 改动点 2"
```

### 5. 验证提交

```bash
git log -1
git status
```

## 安全规则

| 操作 | 允许 | 说明 |
|------|------|------|
| `git push` | ✅ | 正常推送 |
| `git push --force` | ❌ | 禁止强制推送 |
| `git reset --hard` | ❌ | 禁止硬重置（除非明确要求） |
| 提交 `.env` | ❌ | 禁止提交敏感文件 |
| 提交密钥文件 | ❌ | 禁止提交密钥 |

## 提交前检查清单

```
提交前检查：
- [ ] git status 确认要提交的文件
- [ ] git diff 确认改动内容
- [ ] 检查是否有敏感文件（.env、密钥）
- [ ] 确认 .gitignore 是否生效
- [ ] commit message 符合规范
```

## 示例

### 文档更新

```
docs(实施路线图): 补充二期 SSE 流式通信和 AI 对话前端任务

- 新增 5.3.1 前后端通信方式说明
- 新增 5.7.6 SSE 流式通信详细实现
- 新增 5.7.9 AI 对话前端任务清单
- 更新里程碑和任务依赖关系
```

### 预览页面更新

```
feat(preview): Dashboard 付费分析增加分钟级实时监控

- 新增分钟级付费金额实时累计图表
- 支持双Y轴显示（分钟级 + 累计）
- 添加 dataZoom 滑块支持缩放
```

### 配置变更

```
chore(config): 新增 git-operator skill

- 从 agents 迁移到 skills
- 更新技能描述和使用场景
```

### 多文档批量更新

```
docs: 完善实施路线图和相关文档

主要更新：
- 实施路线图 v7.5：补充项目目录结构、前端任务清单
- PRD v3.1：更新数据来源为 ETL 同步模式
- 数据字典 v2.1：添加 batchId 字段支持 ETL 回滚
- CLAUDE.md v5.2：修正预览页面数量为 6 个
```

## 分支管理

### 创建分支

```bash
git checkout -b <branch-name>
```

### 切换分支

```bash
git checkout <branch-name>
```

### 查看分支

```bash
git branch -a         # 所有分支
git branch -v         # 带最后提交信息
```

### 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| feature/ | 新功能 | feature/roi-analysis |
| fix/ | 修复 | fix/chart-display |
| docs/ | 文档 | docs/update-prd |
| refactor/ | 重构 | refactor/query-service |
