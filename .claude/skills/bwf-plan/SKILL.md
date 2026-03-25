---
name: bwf-plan
description: 软件开发规划工作流。README → Spec → Plans，支持审核修复闭环。
argument-hint: [--skip-spec] [--max-rounds=<N>] [--auto-fix]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, AskUserQuestion
---

# /bwf-plan - 软件开发规划

<command-name>bwf-plan</command-name>

## 概述

BW Framework 规划阶段工作流，从 README 生成可落地的实施计划：

```
README.md → Spec (WHAT) → Plans (HOW) → Review → Fix → ✅
```

## 语法

```bash
/bwf-plan [选项]

# 示例
/bwf-plan                     # 完整流程
/bwf-plan --skip-spec         # 跳过 Spec 生成（已有 spec.md）
/bwf-plan --max-rounds=5      # 最多审核迭代 5 轮
/bwf-plan --auto-fix          # 自动修复，不逐条确认
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--skip-spec` | 跳过 Spec 检查和生成 | false |
| `--max-rounds` | 每个 Plan 最大审核轮次 | 3 |
| `--auto-fix` | 自动应用修复 | false |

---

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 0: 环境检查                                           │
│  - README.md 必须存在                                        │
│  - 检查 docs/ 目录结构                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Spec 生成                                          │
│  - 调用 spec-generator agent                                │
│  - 输出: docs/spec.md                                       │
│  - 定义 WHAT + WHY（用户故事、功能模块、验收标准）            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Plan 生成                                          │
│  - 调用 plan-generator agent                                │
│  - 输出: docs/plans/*.md                                    │
│  - 定义 HOW（技术方案、任务拆解、验证命令）                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: 审核修复循环                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  For each Plan:                                        │ │
│  │    1. plan-reviewer → 审核报告                         │ │
│  │    2. 通过条件: Critical=0 && High=0                   │ │
│  │    3. plan-fixer → 修复问题                            │ │
│  │    4. git commit                                       │ │
│  │    5. 重复直到通过或达到 max-rounds                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: 输出报告                                           │
│  - 所有 Plan 状态                                            │
│  - Spec 覆盖检查                                             │
│  - 下一步: /bwf-dev                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 输出结构

```
project/
├── README.md                   # 项目愿景（输入）
├── docs/
│   ├── spec.md                 # 功能规格 (WHAT + WHY)
│   ├── data-model.md           # 数据模型（可选）
│   └── plans/                  # 实施计划 (HOW)
│       ├── index.md            # Plan 索引
│       ├── plan-infrastructure.md
│       ├── plan-*.md           # 各模块 Plan
│       └── ...
```

---

## Plan 文件格式要求

每个 Plan 必须包含 **验证命令**，用于 `/bwf-dev` 自动验证：

```markdown
## 任务清单

### Task 1.1: 创建项目脚手架

**执行**:
- pnpm create vite admin --template react-ts

**验证**:
- `pnpm run build` → exit_code == 0
- `pnpm run dev` → 启动成功

**输出文件**:
- admin/package.json
- admin/vite.config.ts
```

**安全/边界要求**（如任务涉及接口/凭证/上传下载/缓存/响应头）：
- 在 Task 中补充「安全/边界」小节，明确约束（例如：缓存失效、上传大小限制、响应头清洗）。

这种格式让 AI 可以自动执行和验证每个任务。

---

## 错误处理

| 错误 | 处理方式 |
|------|----------|
| README.md 不存在 | 报错，提示创建 |
| Spec 验证失败 | 调用 spec-generator 补充 |
| Plan 审核超过 max-rounds | 标记需人工处理 |
| Git 未初始化 | 跳过提交，警告 |

---

## 与 /bwf-dev 的衔接

`/bwf-plan` 完成后，输出：

```
═══════════════════════════════════════════════════════════════
  BW Framework 规划完成
═══════════════════════════════════════════════════════════════

📄 Spec: docs/spec.md
📂 Plans: docs/plans/ (11 个 Plan)

所有 Plan 已通过审核 ✅

下一步:
  /bwf-dev docs/plans/plan-infrastructure.md   # 按顺序开发
  /bwf-dev --all                               # 开发所有 Plan
═══════════════════════════════════════════════════════════════
```

---

*BW Framework v1.0*
