// Pre-Tool-Use Hook
// Triggers before AI uses any tool (Bash, Write, Edit, etc.)
// Provides safety checks and warnings for dangerous operations

// Dangerous command patterns to block
const BLOCKED_PATTERNS = [
  { pattern: /rm\s+-rf\s+\//i, reason: '将删除整个文件系统' },
  { pattern: /rm\s+-rf\s+\*+/i, reason: '将递归强制删除当前目录所有内容' },
  { pattern: /dd\s+if=.+of=\/dev\/sd/i, reason: '将覆盖磁盘数据' },
  { pattern: /mkfs\./i, reason: '将格式化文件系统' },
  { pattern: /:\(\)\{\s*:\|:\s*&\s*\};:\s*\)/i, reason: 'Fork Bomb 危险命令' },
  { pattern: /shutdown\s+-h\s+now/i, reason: '将关闭系统' },
  { pattern: /reboot/i, reason: '将重启系统' },
  { pattern: /drop\s+database/i, reason: '将删除数据库' },
  { pattern: /drop\s+table/i, reason: '将删除数据表' },
];

// Sensitive operations requiring warning
const WARNING_PATTERNS = [
  { pattern: /rm\s+-rf/i, reason: '递归强制删除，请确认目标正确' },
  { pattern: /rm\s+-f/i, reason: '强制删除，无回收站保护' },
  { pattern: /git\s+push\s+--force/i, reason: '强制推送可能覆盖他人提交' },
  { pattern: /git\s+reset\s+--hard/i, reason: '硬重置将丢失未提交更改' },
  { pattern: /git\s+clean\s+-f/i, reason: '将永久删除未跟踪文件' },
  { pattern: /chmod\s+-R\s+777/i, reason: '赋予所有人所有权限，有安全风险' },
  { pattern: /curl\s+.*\|\s*(ba)?sh/i, reason: '管道执行远程脚本，请验证来源安全' },
  { pattern: /wget\s+.*\|\s*(ba)?sh/i, reason: '管道执行远程脚本，请验证来源安全' },
];

function checkToolUse() {
  // Read tool use info from environment
  const toolName = process.env.CLAUDE_TOOL_NAME || '';
  const toolInput = process.env.CLAUDE_TOOL_INPUT || '';

  // For Bash tool, check command safety
  if (toolName === 'Bash') {
    const command = toolInput;

    // Check blocked patterns
    for (const blocked of BLOCKED_PATTERNS) {
      if (blocked.pattern.test(command)) {
        console.error(`
[安全拦截] 检测到危险操作！
命令: ${command}
原因: ${blocked.reason}
该命令已被阻止执行。请重新评估操作安全性。
`);
        process.exit(1);
      }
    }

    // Check warning patterns
    for (const warning of WARNING_PATTERNS) {
      if (warning.pattern.test(command)) {
        console.log(`
[安全警告] ${warning.reason}
命令: ${command}
请确认该操作是预期行为且目标正确。
`);
      }
    }
  }

  // For Write/Edit tools, check file paths
  if (toolName === 'Write' || toolName === 'Edit') {
    const filePath = toolInput;

    // Warning for sensitive files
    const sensitiveFiles = [
      '.env',
      '.env.production',
      'config.yaml',
      'config.yml',
      'settings.json',
      'credentials.json',
      'private.key',
    ];

    for (const sensitive of sensitiveFiles) {
      if (filePath.includes(sensitive)) {
        console.log(`
[敏感文件警告] 正在修改配置文件: ${filePath}
请确保不会意外泄露敏感信息（如密码、密钥）。
`);
      }
    }
  }

  process.exit(0);
}

checkToolUse();
