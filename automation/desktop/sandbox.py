"""
Security Sandbox for Shell Command Execution.
Only safe/whitelisted commands execute automatically.
Dangerous or destructive commands require explicit user approval.
Zero hardcoded paths — fully dynamic.
"""
import os
import sys
import subprocess
import re

# Read-only and informational commands that can run safely
WHITELIST_PREFIXES = [
    # Directory & file inspection
    "dir", "ls", "type", "cat", "find", "findstr", "where", "get-childitem", "gci", "get-content", "gc",
    # System info & networking
    "systeminfo", "hostname", "whoami", "date", "time", "get-date",
    "tasklist", "get-process", "gps", "netstat", "ipconfig", "ping", "tracert",
    # Safe application launching
    "start", "explorer", "start-process",
    # Git read-only
    "git status", "git log", "git branch", "git diff", "git show", "git remote",
    # Environment info
    "python --version", "python -v", "pip list", "node --version", "npm list",
    "echo", "write-output"
]

# Destructive or security-sensitive commands requiring confirmation
BLACKLIST_PATTERNS = [
    "rm ", "del ", "rmdir", "remove-item", "ri ",
    "format", "diskpart",
    "shutdown", "restart-computer", "stop-computer",
    "reg delete", "reg add",
    "net user", "net localgroup",
    "powershell -enc", "-encodedcommand",
    "curl | bash", "iex", "invoke-expression",
    "> ", ">> ", "set-content", "add-content",
    "takeown", "icacls"
]

def is_safe_command(command: str) -> bool:
    """Check if a command is safe to execute without explicit confirmation."""
    clean = command.strip().lower()

    # Block blacklisted patterns
    for pattern in BLACKLIST_PATTERNS:
        if pattern in clean:
            return False

    # Check against whitelisted safe command prefixes
    for safe in WHITELIST_PREFIXES:
        if clean.startswith(safe):
            return True

    return False

def execute_command(command: str, approved: bool = False, timeout: int = 25) -> dict:
    """Execute a PowerShell command with security sandbox verification."""
    clean_cmd = command.strip()

    if not approved and not is_safe_command(clean_cmd):
        return {
            "status": "NEEDS_APPROVAL",
            "command": clean_cmd,
            "message": f"⚠️ Command requires operator approval:\n`{clean_cmd}`\n\nApprove execution?",
            "stdout": "",
            "stderr": "Command blocked: requires explicit approval.",
            "exit_code": -1
        }

    try:
        res = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", clean_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )

        return {
            "status": "SUCCESS" if res.returncode == 0 else "ERROR",
            "command": clean_cmd,
            "stdout": (res.stdout or "").strip()[:2000],
            "stderr": (res.stderr or "").strip()[:500],
            "exit_code": res.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "TIMEOUT",
            "command": clean_cmd,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds.",
            "exit_code": -2
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "command": clean_cmd,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -3
        }

if __name__ == "__main__":
    print("Testing Sandbox:")
    print("Safe dir:", execute_command("dir")["status"])
    print("Unsafe del:", execute_command("del important.txt")["status"])
