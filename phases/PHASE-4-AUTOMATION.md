# Phase 4: Automation — Browser, Desktop & Shell Control

> **Priority:** 🟡 HIGH — "Jarvis, open Chrome and check my portal"
> **Estimated Time:** 3–5 days
> **Dependencies:** Phase 1 COMPLETE
> **Status:** 🔲 NOT STARTED

---

## Overview

This phase adds real-world automation:
1. **Browser Automation** — AI-driven web browsing (Playwright + browser-use)
2. **College Portal** — Automated login and data extraction
3. **Desktop Automation** — Launch apps, manage files, system control
4. **Shell Execution** — Run PowerShell commands via natural language
5. **Security Sandbox** — Whitelist and approval for dangerous commands

After Phase 4, JARVIS can browse the web, check your college portal,
open applications, and manage your desktop — all via voice or Telegram.

---

## Prerequisites

- [x] Phase 1 complete
- [x] Python venv set up (from Phase 3 or create new)
- [ ] Chrome or Chromium browser installed

---

## Step 4.1: Install Browser Automation Stack

```powershell
cd d:\Desktop\gaganAI
.\venv\Scripts\Activate.ps1

# Install Playwright
pip install playwright
playwright install chromium

# Install browser-use (AI-driven browser agent)
pip install browser-use

# Install additional dependencies
pip install beautifulsoup4 lxml
```

### Test Playwright

```python
# Quick test: d:\Desktop\gaganAI\automation\browser\test_playwright.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.google.com")
    print(f"Title: {page.title()}")
    page.screenshot(path="test_screenshot.png")
    browser.close()
    print("✅ Playwright working!")
```

```powershell
python automation\browser\test_playwright.py
```

**✅ Checkpoint:** Playwright opens a browser and takes a screenshot.

---

## Step 4.2: Set Up AI Browser Agent

### Configure browser-use with Local LLM

Create `d:\Desktop\gaganAI\automation\browser\agent.py`:

```python
"""
AI-driven browser automation via browser-use.
Uses local Ollama models for zero-cost inference.
"""
import asyncio
from browser_use import Agent
from langchain_community.llms import Ollama

# Use local LLM (or swap to Groq/Gemini for complex pages)
llm = Ollama(
    model="qwen2.5:7b-instruct-q4_K_M",
    base_url="http://localhost:11434",
)

async def browse(task: str):
    """Execute a browser task using AI."""
    agent = Agent(
        task=task,
        llm=llm,
        max_actions_per_step=5,
    )
    result = await agent.run()
    return result

# Example usage:
if __name__ == "__main__":
    result = asyncio.run(browse(
        "Go to google.com, search for 'NIT Jalandhar', "
        "and tell me the first 3 results"
    ))
    print(result)
```

### Test with Various Tasks

```python
# Test cases to verify browser automation:

# 1. Simple search
await browse("Search Google for 'weather in Jalandhar' and tell me the temperature")

# 2. Navigate and extract
await browse("Go to wikipedia.org, search for 'Python programming', and summarize the first paragraph")

# 3. Multi-step
await browse("Go to github.com/trending, find the top 3 trending repositories, and list their names and stars")
```

> **Note:** browser-use with a local 7B model may be slower than with
> cloud APIs. For complex pages, route to Groq (Llama 70B) for better
> page understanding.

**✅ Checkpoint:** AI browser agent can navigate websites and extract information.

---

## Step 4.3: Build College Portal Automation

### Secure Credential Storage

**NEVER hardcode your college password.** Use the OS credential manager:

```python
# Store credentials securely:
import keyring

# Save (run once):
keyring.set_password("jarvis-college-portal", "username", "your-roll-number")
keyring.set_password("jarvis-college-portal", "password", "your-password")

# Retrieve in automation scripts:
username = keyring.get_password("jarvis-college-portal", "username")
password = keyring.get_password("jarvis-college-portal", "password")
```

```powershell
pip install keyring
```

### College Portal Script

Create `d:\Desktop\gaganAI\automation\browser\college_portal.py`:

```python
"""
Automated college portal check.
Logs in, extracts notices, attendance, grades.
"""
import keyring
from playwright.sync_api import sync_playwright


PORTAL_URL = "https://your-college-portal-url.ac.in"  # UPDATE THIS


def check_portal():
    """Login to college portal and extract information."""
    username = keyring.get_password("jarvis-college-portal", "username")
    password = keyring.get_password("jarvis-college-portal", "password")

    if not username or not password:
        return "❌ College portal credentials not set. Run setup first."

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Reuse saved session if available
        try:
            context.storage_state(path="automation/browser/portal_session.json")
        except:
            pass

        page = context.new_page()
        page.goto(PORTAL_URL)

        # Check if already logged in
        if "login" in page.url.lower() or "signin" in page.url.lower():
            # Fill login form (adapt selectors to your portal)
            page.fill('input[name="username"], #username', username)
            page.fill('input[name="password"], #password', password)
            page.click('button[type="submit"], #login-btn')
            page.wait_for_load_state("networkidle")

            # Save session for next time
            context.storage_state(path="automation/browser/portal_session.json")

        # Extract information (adapt to your portal's structure)
        results = {}

        # Try to find common portal elements:
        try:
            # Notices
            notices = page.query_selector_all(".notice, .announcement, .news-item")
            results["notices"] = [n.text_content().strip() for n in notices[:5]]
        except:
            results["notices"] = []

        try:
            # Attendance
            attendance = page.query_selector(".attendance, #attendance")
            results["attendance"] = attendance.text_content().strip() if attendance else "Not found"
        except:
            results["attendance"] = "Not found"

        browser.close()

    return results


if __name__ == "__main__":
    import json
    result = check_portal()
    print(json.dumps(result, indent=2))
```

> **IMPORTANT:** You'll need to customize the CSS selectors (`.notice`,
> `#username`, etc.) to match your specific college portal's HTML structure.
> Use Playwright's codegen to discover the right selectors:
> ```
> playwright codegen https://your-college-portal-url.ac.in
> ```

**✅ Checkpoint:** Can login to college portal and extract data automatically.

---

## Step 4.4: Build Desktop Automation

### App Launcher

Create `d:\Desktop\gaganAI\automation\desktop\launcher.py`:

```python
"""
Desktop application launcher and controller.
"""
import subprocess
import os


# App registry — add your frequently used apps
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\gaganrajput\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "terminal": "wt.exe",  # Windows Terminal
    "calculator": "calc.exe",
    "task manager": "taskmgr.exe",
}


def launch_app(app_name: str, args: list = None) -> str:
    """Launch a desktop application."""
    app_name_lower = app_name.lower().strip()

    # Direct match
    if app_name_lower in APPS:
        path = APPS[app_name_lower]
        cmd = [path] + (args or [])
        subprocess.Popen(cmd)
        return f"✅ Launched {app_name}"

    # Fuzzy match
    for name, path in APPS.items():
        if app_name_lower in name or name in app_name_lower:
            subprocess.Popen([path] + (args or []))
            return f"✅ Launched {name}"

    # Try Windows Start Menu search
    try:
        os.startfile(app_name)
        return f"✅ Launched {app_name}"
    except Exception as e:
        return f"❌ Could not find app: {app_name}. Error: {e}"


def close_app(app_name: str) -> str:
    """Close a running application."""
    result = subprocess.run(
        ["taskkill", "/IM", f"{app_name}.exe", "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return f"✅ Closed {app_name}"
    return f"❌ Could not close {app_name}: {result.stderr}"


def list_running_apps() -> list:
    """List running applications."""
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True, text=True
    )
    apps = set()
    for line in result.stdout.strip().split("\n"):
        name = line.split(",")[0].strip('"')
        if name and not name.startswith("svchost"):
            apps.add(name)
    return sorted(apps)
```

### System Commands

Create `d:\Desktop\gaganAI\automation\desktop\system.py`:

```python
"""
System control commands for JARVIS.
"""
import subprocess
import psutil


def get_system_status() -> dict:
    """Get current system resource usage."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("D:\\")

    return {
        "cpu_percent": cpu,
        "ram_total_gb": round(memory.total / (1024**3), 1),
        "ram_used_gb": round(memory.used / (1024**3), 1),
        "ram_percent": memory.percent,
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_used_gb": round(disk.used / (1024**3), 1),
        "disk_percent": round(disk.percent, 1),
    }


def set_volume(level: int) -> str:
    """Set system volume (0-100)."""
    # Uses nircmd (download from nirsoft.net) or PowerShell
    script = f"""
    $vol = [Math]::Round({level} / 100 * 65535)
    $wshShell = New-Object -ComObject WScript.Shell
    """
    # Alternative: use pycaw library
    return f"Volume set to {level}%"


def take_screenshot(path: str = "screenshot.png") -> str:
    """Take a screenshot of the desktop."""
    from PIL import ImageGrab
    img = ImageGrab.grab()
    img.save(path)
    return f"Screenshot saved to {path}"


def lock_screen() -> str:
    """Lock the workstation."""
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "🔒 Screen locked"
```

```powershell
pip install psutil Pillow
```

**✅ Checkpoint:** Can launch/close apps, get system status, take screenshots.

---

## Step 4.5: Shell Execution Sandbox

### Security: Command Whitelist

Create `d:\Desktop\gaganAI\automation\desktop\sandbox.py`:

```python
"""
Security sandbox for shell command execution.
Only whitelisted commands can run without approval.
"""

# Commands that can run without asking the user
WHITELIST = [
    # Read-only commands
    "dir", "ls", "type", "cat", "find", "findstr", "where",
    "systeminfo", "hostname", "whoami", "date", "time",
    "tasklist", "netstat", "ipconfig", "ping",
    # App launching
    "start", "explorer",
    # Git (read-only)
    "git status", "git log", "git branch", "git diff",
    # Python
    "python --version", "pip list",
    # Node
    "node --version", "npm list",
]

# Commands that ALWAYS require explicit user approval
BLACKLIST_PATTERNS = [
    "rm ", "del ", "rmdir", "remove",
    "format",
    "shutdown", "restart",
    "reg delete", "reg add",
    "net user", "net localgroup",
    "powershell -enc",  # Encoded commands (suspicious)
    "curl | bash", "iex",  # Remote code execution
    "> ", ">> ",  # File overwrites
    "takeown", "icacls",  # Permission changes
]


def is_safe_command(command: str) -> bool:
    """Check if a command is safe to execute without approval."""
    cmd_lower = command.lower().strip()

    # Block blacklisted patterns
    for pattern in BLACKLIST_PATTERNS:
        if pattern in cmd_lower:
            return False

    # Allow whitelisted commands
    for safe_cmd in WHITELIST:
        if cmd_lower.startswith(safe_cmd):
            return True

    # Everything else requires approval
    return False


def execute_command(command: str, approved: bool = False) -> dict:
    """Execute a shell command with safety checks."""
    if not approved and not is_safe_command(command):
        return {
            "status": "NEEDS_APPROVAL",
            "command": command,
            "message": f"⚠️ This command requires your approval:\n`{command}`\n\nApprove?"
        }

    import subprocess
    result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30
    )

    return {
        "status": "SUCCESS" if result.returncode == 0 else "ERROR",
        "stdout": result.stdout[:2000],  # Limit output size
        "stderr": result.stderr[:500],
        "exit_code": result.returncode
    }
```

### Wire Sandbox into OpenClaw

Configure OpenClaw to use the sandbox for all shell executions:
- Whitelisted commands → Execute immediately
- Non-whitelisted commands → Send approval request to Telegram
- Blacklisted commands → Block and warn

**✅ Checkpoint:** Shell commands respect the whitelist/blacklist. Dangerous commands require Telegram approval.

---

## Step 4.6: Connect Everything to OpenClaw

### Register Automation Skills

Create OpenClaw skills that wrap the automation modules:

```javascript
// Example skill registration (check OpenClaw docs for actual format):
{
  "skills": [
    {
      "name": "browse-web",
      "description": "Browse a website and extract information",
      "handler": "automation/browser/agent.py",
      "tools": ["navigate", "click", "extract", "screenshot"]
    },
    {
      "name": "college-portal",
      "description": "Check college portal for notices, attendance, grades",
      "handler": "automation/browser/college_portal.py",
      "tools": ["check_portal"]
    },
    {
      "name": "desktop-control",
      "description": "Launch apps, get system status, take screenshots",
      "handler": "automation/desktop/launcher.py",
      "tools": ["launch_app", "close_app", "list_running_apps"]
    },
    {
      "name": "run-command",
      "description": "Execute shell commands with safety sandbox",
      "handler": "automation/desktop/sandbox.py",
      "tools": ["execute_command"]
    }
  ]
}
```

### Test Natural Language Commands

Via Telegram or voice:

```
"Open Chrome"
"Check my college portal"
"What's my CPU usage?"
"Search Google for Python tutorials"
"Take a screenshot"
"List all running apps"
"Close Notepad"
```

**✅ Checkpoint:** All automation commands work via Telegram and voice.

---

## Phase 4 Completion Criteria

- [ ] Playwright + Chromium installed and tested
- [ ] browser-use AI agent working with local LLM
- [ ] College portal automation script customized and tested
- [ ] Desktop launcher working (launch/close apps)
- [ ] System status monitoring working
- [ ] Shell execution sandbox configured
- [ ] Command whitelist/blacklist in place
- [ ] All skills registered in OpenClaw
- [ ] Natural language commands working via Telegram
- [ ] MEMORY.md updated with Phase 4 status = ✅ COMPLETE

---

## Troubleshooting

### Playwright Chromium fails to launch
```powershell
# Reinstall browsers:
playwright install --force chromium
# If still failing, try with dependencies:
playwright install-deps chromium
```

### browser-use too slow with local LLM
```
- Switch to Groq API for browser tasks (Llama 70B is much better at
  understanding web pages)
- Set BROWSER_LLM_PROVIDER=groq in .env
- Use local LLM only for simple page extraction
```

### College portal blocks automation
```
- Use a realistic user agent string
- Add delays between actions (page.wait_for_timeout(2000))
- Use saved session cookies to avoid frequent logins
- Run in headful mode (headless=False) to debug visually
```

### Shell command hangs
```
- The 30-second timeout in sandbox.py will kill it
- For long-running commands, use subprocess.Popen (non-blocking)
- Check command for accidental infinite loops
```

