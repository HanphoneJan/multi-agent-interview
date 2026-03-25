// Session Start Hook
// Triggers when Claude Code session starts
// Shows project status and quick commands menu

const fs = require('fs');
const { execSync } = require('child_process');

function getGitStatus() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8', cwd: process.cwd() }).trim();
    const status = execSync('git status --short', { encoding: 'utf8', cwd: process.cwd() }).trim();
    const recentCommits = execSync('git log --oneline -5', { encoding: 'utf8', cwd: process.cwd() }).trim();
    return { branch, status, recentCommits };
  } catch (e) {
    return { branch: 'unknown', status: '', recentCommits: '' };
  }
}

function getProjectInfo() {
  return {
    name: '游戏数据分析 AI Agent 平台',
    type: 'FastAPI + Vue3 + ClickHouse'
  };
}

function showSessionStart() {
  const git = getGitStatus();
  const project = getProjectInfo();

  const output = `
╔══════════════════════════════════════════════════════════════╗
║  游戏数据分析 AI Agent 平台                                    ║
║  ${project.type.padEnd(56)} ║
╠══════════════════════════════════════════════════════════════╣
║  Git 状态                                                    ║
║  分支: ${git.branch.padEnd(50)} ║
${git.status ? `║  未提交: ${git.status.split('\n').length.toString().padEnd(48)} ║` : '║  工作区: 干净'.padEnd(63) + '║'}
╠══════════════════════════════════════════════════════════════╣
║  快捷命令                                                    ║
║  /commit  - 提交代码并生成规范 commit message                ║
║  Skill()  - 激活专业技能                                     ║
║  @agent   - 调用子任务代理 (如 @code-reviewer)               ║
╠══════════════════════════════════════════════════════════════╣
║  技能提示                                                    ║
║  • 开发功能前使用 bwf-plan → bwf-dev 工作流                  ║
║  • 代码完成后使用 @code-reviewer 进行审查                    ║
║  • 修复Bug前查阅 memory/BUG_FIXES.md                         ║
╚══════════════════════════════════════════════════════════════╝
`;

  console.log(output);
}

showSessionStart();
