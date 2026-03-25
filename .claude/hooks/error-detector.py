#!/usr/bin/env python3
"""
Self-Improvement Error Detector Hook
Triggers on PostToolUse for Bash to detect command failures
Reads CLAUDE_TOOL_OUTPUT environment variable
"""

import os
import sys

# Error patterns to detect (case-insensitive)
ERROR_PATTERNS = [
    "error:",
    "Error:",
    "ERROR:",
    "failed",
    "FAILED",
    "command not found",
    "No such file",
    "Permission denied",
    "fatal:",
    "Exception",
    "Traceback",
    "npm ERR!",
    "ModuleNotFoundError",
    "SyntaxError",
    "TypeError",
    "exit code",
    "non-zero",
]

def main():
    output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

    # Check if output contains any error pattern
    contains_error = any(pattern in output for pattern in ERROR_PATTERNS)

    # Only output reminder if error detected
    if contains_error:
        print("""<error-detected>
A command error was detected. Consider logging this to .learnings/ERRORS.md if:
- The error was unexpected or non-obvious
- It required investigation to resolve
- It might recur in similar contexts
- The solution could benefit future sessions

Use the self-improvement skill format: [ERR-YYYYMMDD-XXX]
</error-detected>""")

    return 0

if __name__ == "__main__":
    sys.exit(main())
