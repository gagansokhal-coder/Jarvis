"""
Desktop Application Launcher and Controller for Gagan AI.
Phase 4: Automation
100% Dynamic: Zero hardcoded drives, paths, or usernames.
"""
import os
import sys
import subprocess
import shutil
import difflib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from automation.laptop_controller import (
    open_interactive_app, open_url, focus_window, discover_installed_apps
)

def launch_app(app_name: str, args: list = None) -> tuple[bool, str]:
    """Launch or focus any desktop application dynamically."""
    return open_interactive_app(app_name, args=args)

KNOWN_PROCESS_MAP = {
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "msedge": "msedge.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "vscode": "Code.exe",
    "vs code": "Code.exe",
    "visual studio code": "Code.exe",
    "code": "Code.exe",
    "notepad": "notepad.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "terminal": "WindowsTerminal.exe",
    "windows terminal": "WindowsTerminal.exe",
    "calculator": "CalculatorApp.exe",
    "task manager": "Taskmgr.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "hacker gui": "pythonw.exe",
    "tactical console": "pythonw.exe",
    "gui": "pythonw.exe",
}

def close_app(app_name: str) -> tuple[bool, str]:
    """
    Intelligently close any running desktop application.
    Resolves aliases, fuzzy matches process names, and terminates them reliably.
    """
    import psutil
    import re
    clean = app_name.lower().strip()
    clean = re.sub(r'^(?:the|my|app|window|program)\s+', '', clean).strip()

    # 1. Check known process mappings
    target_exe = KNOWN_PROCESS_MAP.get(clean)

    # 2. Dynamic scan of running processes if not in alias map
    if not target_exe:
        if clean.endswith(".exe"):
            target_exe = clean
        else:
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    pname = p.info['name'] or ''
                    if clean in pname.lower():
                        target_exe = pname
                        break
                except Exception:
                    pass

    if not target_exe:
        target_exe = f"{clean}.exe"

    res = subprocess.run(
        ["taskkill", "/IM", target_exe, "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    display_name = clean.title() if not clean.endswith(".exe") else clean
    if res.returncode == 0:
        return True, f"Closed {display_name} on your screen, Gagan."

    if "not found" in res.stderr.lower():
        return True, f"{display_name} is not currently running, Gagan."

    return False, f"Could not close {clean}: {res.stderr.strip()}"

def list_running_apps() -> list:
    """List distinct running user-level applications."""
    try:
        res = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        apps = set()
        system_ignores = {"svchost.exe", "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe"}
        for line in res.stdout.strip().splitlines():
            parts = line.split(",")
            if parts:
                pname = parts[0].strip('"').lower()
                if pname and pname not in system_ignores and not pname.startswith("fontdrv"):
                    apps.add(pname)
        return sorted(list(apps))
    except Exception:
        return []

def open_url_in_browser(url: str) -> tuple[bool, str]:
    """Open a URL in Chrome on the interactive screen."""
    return open_url(url)

if __name__ == "__main__":
    print("Testing dynamic app list:")
    running = list_running_apps()
    print(f"Total running processes: {len(running)}")
