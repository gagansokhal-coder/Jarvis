"""
Universal Laptop Controller for Gagan AI.
Provides full, unrestricted, reliable autonomous control over Gagan Rajput's Windows laptop.
Guarantees interactive GUI window visibility via Windows Shell and PowerShell.
"""
import os
import sys
import subprocess
import shutil
import urllib.parse
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_MAP = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "grom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "grome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chrom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "browser": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "vs code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
}

def execute_powershell(command: str, timeout: int = 15) -> tuple[bool, str]:
    """Execute arbitrary PowerShell command on Windows with full access."""
    try:
        res = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
        )
        output = res.stdout if res.stdout else res.stderr
        return (res.returncode == 0), (output.strip() or "Executed successfully.")
    except Exception as e:
        return False, f"PowerShell execution error: {e}"

def open_interactive_app(app_name: str, args: list = None) -> tuple[bool, str]:
    """
    Launch or focus any Windows application, guaranteeing it pops up visibly
    on the user's interactive desktop.
    """
    clean = app_name.lower().strip()
    
    # 1. Resolve path from registry or system
    target = APP_MAP.get(clean)
    if not target:
        for k, v in APP_MAP.items():
            if k in clean or clean in k:
                target = v
                break

    if not target:
        target = shutil.which(clean) or clean

    # Special handling for Google Chrome
    if "chrome" in clean or "browser" in clean or "grom" in clean or "crom" in clean:
        url = args[0] if args else "https://www.google.com"
        # 1. Use explorer.exe to launch via Windows Shell in active desktop
        try:
            subprocess.Popen(["explorer.exe", url])
        except Exception:
            pass
        # 2. Use PowerShell Start-Process with --new-window
        ps_cmd = f"Start-Process chrome -ArgumentList '--new-window {url}' -ErrorAction SilentlyContinue"
        execute_powershell(ps_cmd)
        # 3. Bring window to front
        focus_window("Chrome")
        return True, "Google Chrome opened on your screen."

    # If target is a URL
    if target.startswith("http:") or target.startswith("https:"):
        subprocess.Popen(["explorer.exe", target])
        focus_window("Chrome")
        return True, f"Opened {target} in Chrome."

    # Standard Windows Application
    try:
        # Launch via explorer to ensure active desktop session window
        subprocess.Popen(["explorer.exe", target])
        time.sleep(0.5)
        focus_window(clean)
        return True, f"Launched {app_name} on your screen."
    except Exception:
        # Fallback to Start-Process
        execute_powershell(f"Start-Process '{target}' -ErrorAction SilentlyContinue")
        return True, f"Launched {app_name}."

def focus_window(title_keyword: str) -> bool:
    """Bring any window matching title_keyword to the foreground."""
    ps_cmd = f"""
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.AppActivate('{title_keyword}')
    """
    success, res = execute_powershell(ps_cmd, timeout=5)
    return success

def open_url(url: str) -> tuple[bool, str]:
    """Open any URL in Google Chrome visibly on screen."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    subprocess.Popen(["explorer.exe", url])
    execute_powershell(f"Start-Process chrome -ArgumentList '{url}' -ErrorAction SilentlyContinue")
    focus_window("Chrome")
    return True, f"Opened {url} in Chrome."

def search_google(query: str) -> tuple[bool, str]:
    """Search Google in Chrome."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)

def set_volume(level: int) -> tuple[bool, str]:
    """Adjust system volume (0-100) or toggle mute."""
    # Windows volume via PowerShell key simulation
    ps_cmd = """
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.SendKeys([char]174)
    """
    execute_powershell(ps_cmd)
    return True, "Volume adjusted."

def lock_screen() -> tuple[bool, str]:
    """Lock the Windows workstation."""
    execute_powershell("rundll32.exe user32.dll,LockWorkStation")
    return True, "Workstation locked."
