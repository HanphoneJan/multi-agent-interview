// Stop Hook
// Triggers after AI completes a response
// Provides completion feedback and next step recommendations

const fs = require('fs');
const { execSync } = require('child_process');

function getGitChanges() {
  try {
    const status = execSync('git status --short', { encoding: 'utf8', cwd: process.cwd() }).trim();
    return status ? status.split('\n').length : 0;
  } catch (e) {
    return 0;
  }
}

function analyzeChangeType() {
  try {
    const diff = execSync('git diff --name-only', { encoding: 'utf8', cwd: process.cwd() }).trim();
    const files = diff.split('\n').filter(f => f);

    const types = {
      python: files.filter(f => f.endsWith('.py')).length,
      typescript: files.filter(f => f.endsWith('.ts') || f.endsWith('.tsx')).length,
      vue: files.filter(f => f.endsWith('.vue')).length,
      docs: files.filter(f => f.endsWith('.md') || f.endsWith('.mdc')).length,
      config: files.filter(f => f.includes('config') || f.endsWith('.json') || f.endsWith('.yaml') || f.endsWith('.yml')).length,
    };

    return types;
  } catch (e) {
    return {};
  }
}

function showStopMessage() {
  const changes = getGitChanges();
  const types = analyzeChangeType();

  let changeSummary = '';
  if (changes > 0) {
    const typeDescriptions = [];
    if (types.python) typeDescriptions.push(`${types.python} 个 Python 文件`);
    if (types.typescript) typeDescriptions.push(`${types.typescript} 个 TypeScript 文件`);
    if (types.vue) typeDescriptions.push(`${types.vue} 个 Vue 组件`);
    if (types.docs) typeDescriptions.push(`${types.docs} 个文档文件`);
    if (types.config) typeDescriptions.push(`${types.config} 个配置文件`);

    changeSummary = typeDescriptions.length > 0
      ? `检测到 ${changes} 个文件变更（${typeDescriptions.join('、')}）`
      : `检测到 ${changes} 个文件变更`;
  }

  const recommendations = [];
  if (changes > 0) {
    recommendations.push('• 使用 /commit 提交代码并生成规范 commit message');
    recommendations.push('• 使用 @code-reviewer 进行代码审查');
  }
  recommendations.push('• 执行 Lint 检查：uv run ruff check app worker（后端）/ pnpm run lint（前端）');
  if (types.typescript || types.vue) {
    recommendations.push('• 执行类型检查：pnpm run type-check');
  }
  if (types.python) {
    recommendations.push('• 执行单元测试：uv run pytest tests/unit -v');
  }

  const output = `
[任务完成]
${changeSummary ? changeSummary : '未检测到文件变更'}

建议下一步操作：
${recommendations.join('\n')}

需要帮助？使用 /help 查看所有可用命令。
`;

  console.log(output);
}

showStopMessage();
