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

def close_app(app_name: str) -> tuple[bool, str]:
    """Close a running desktop application by process name."""
    clean = app_name.lower().strip()
    if clean.endswith(".exe"):
        proc_name = clean
    else:
        proc_name = f"{clean}.exe"

    res = subprocess.run(
        ["taskkill", "/IM", proc_name, "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res.returncode == 0:
        return True, f"Closed {app_name}."
    return False, f"Could not close {app_name}: {res.stderr.strip() or 'Process not found.'}"

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
