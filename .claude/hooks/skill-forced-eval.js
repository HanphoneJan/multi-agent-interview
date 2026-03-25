// Skill Forced Evaluation Hook
// Triggers on every user prompt to force skill evaluation before response

const skills = [
  // BWF Development Skills
  { id: 'bwf-plan', name: 'BWF Plan', keywords: ['计划', '规划', 'plan', 'spec', '实施计划', '路线图'], description: '软件开发规划工作流：README → Spec → Plans' },
  { id: 'bwf-dev', name: 'BWF Dev', keywords: ['开发', '实现', 'coding', '编码', '编写代码', '功能实现'], description: '自动开发闭环：开发→验证→审核→修复→提交' },
  { id: 'deploy', name: 'Deploy', keywords: ['部署', '打包', '发布', 'deploy', 'build', '生产环境'], description: '打包 bw-crash 项目用于生产部署' },

  // Code Quality Skills
  { id: 'git-operator', name: 'Git Operator', keywords: ['git', '提交', 'commit', '分支', 'branch', '合并', 'merge', 'push'], description: 'Git 操作规范：提交代码、创建分支、生成规范 commit message' },
  { id: 'task-evaluator', name: 'Task Evaluator', keywords: ['评估', '审查', 'review', '验收', '验证', '检查完成度'], description: '评估已完成任务的质量和完整性' },
  { id: 'frontend-design', name: 'Frontend Design', keywords: ['前端', 'UI', '样式', '组件', '页面', 'Vue', 'React', 'CSS'], description: 'B端产品UI设计师评估专家' },
  { id: 'doc-updater', name: 'Doc Updater', keywords: ['文档', '更新', '同步', 'documentation', 'README', 'docs'], description: '全量检查并更新项目文档一致性' },
];

const agents = [
  { id: 'auto-developer', name: 'Auto Developer', keywords: ['自动开发', '自动实现', '全自动'], description: '自动开发代理' },
  { id: 'code-reviewer', name: 'Code Reviewer', keywords: ['代码审查', 'review代码', 'CR', 'code review'], description: '代码审查专家' },
  { id: 'dev-principles', name: 'Dev Principles', keywords: ['开发原则', '设计原则', '重构', '代码质量'], description: '开发原则与迭代专家' },
  { id: 'ops-reviewer', name: 'Ops Reviewer', keywords: ['运营', '产品需求', '运营视角', '数据展示'], description: '游戏运营人员视角评估专家' },
  { id: 'plan-generator', name: 'Plan Generator', keywords: ['生成计划', '生成实施计划', '创建plan'], description: '根据 Spec 生成可落地的实施计划' },
  { id: 'plan-reviewer', name: 'Plan Reviewer', keywords: ['审核计划', '审查plan', '评估计划'], description: '审核实施计划的可落地性' },
  { id: 'plan-fixer', name: 'Plan Fixer', keywords: ['修复计划', '修改plan', 'plan修复'], description: '根据审核报告修复 Plan 中的问题' },
  { id: 'project-reviewer', name: 'Project Reviewer', keywords: ['项目审查', '架构审查', '项目评估'], description: '项目架构审查专家' },
  { id: 'spec-generator', name: 'Spec Generator', keywords: ['生成spec', '创建规格', '需求规格'], description: '根据 README 生成功能规格文档' },
  { id: 'ui-designer', name: 'UI Designer', keywords: ['UI设计', '界面设计', '交互设计', '视觉效果'], description: 'B端产品UI设计师评估专家' },
];

const instructions = `## 强制技能/代理评估流程（必须执行）

在回答用户问题前，请完成以下评估步骤：

### 步骤 1 - 技能评估
针对以下每个技能，评估是否需要调用：

**可用 Skills：**
${skills.map(s => `- ${s.id}: ${s.description} [触发词: ${s.keywords.join(', ')}]`).join('\n')}

**可用 Agents：**
${agents.map(a => `- @${a.id}: ${a.description} [触发词: ${a.keywords.join(', ')}]`).join('\n')}

评估格式：
- [技能/代理名] - 是/否 - [理由]

### 步骤 2 - 激活
- 如果有任何 Skill 为"是" → 立即使用 Skill() 工具激活
- 如果有任何 Agent 为"是" → 立即使用 Task() 工具分派给对应代理
- 如果都不需要 → 说明"无需激活技能或代理"并继续

### 步骤 3 - 执行
只有在步骤 2 完成后，才能开始实现。

### 规则
1. 斜杠命令（如 /commit）不需要评估，直接执行
2. 开发类任务必须评估是否需要 bwf-plan / bwf-dev
3. Git 相关操作必须评估 git-operator
4. 前端开发必须评估 frontend-design
5. 代码完成后必须评估是否需要 code-reviewer
`;

console.log(instructions);
