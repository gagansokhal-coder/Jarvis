"""
Desktop Application Launcher and Controller for Gagan AI.
Phase 4: Automation
"""
import os
import sys
import subprocess
import shutil
import difflib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# App registry with auto-resolved paths
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chrme": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crhome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "browser": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "vs code": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "files": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "settings": "ms-settings:",
    "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
}

def launch_app(app_name: str, args: list = None) -> tuple[bool, str]:
    """Launch a desktop application in milliseconds."""
    clean_name = app_name.lower().strip()
    
    # 1. Direct registry lookup
    if clean_name in APPS:
        target = APPS[clean_name]
        try:
            if target.startswith("ms-settings:"):
                os.startfile(target)
                return True, f"Opened Windows Settings."
            if os.path.exists(target) or shutil.which(target):
                cmd = [target] + (args or [])
                subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
                return True, f"Launched {app_name}."
        except Exception as e:
            return False, f"Failed to launch {app_name}: {e}"

    # 2. Substring & Fuzzy match in registry
    best_match = None
    best_score = 0.0
    for name, target in APPS.items():
        if clean_name in name or name in clean_name:
            best_match = (name, target)
            break
        ratio = difflib.SequenceMatcher(None, clean_name, name).ratio()
        if ratio > best_score:
            best_score = ratio
            if ratio >= 0.72:
                best_match = (name, target)

    if best_match:
        name, target = best_match
        try:
            if os.path.exists(target) or shutil.which(target):
                cmd = [target] + (args or [])
                subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
                return True, f"Launched {name}."
        except Exception:
            pass

    # 3. Fallback to Windows os.startfile
    try:
        os.startfile(app_name)
        return True, f"Launched {app_name}."
    except Exception as e:
        return False, f"Could not find or launch application '{app_name}'."

def close_app(app_name: str) -> tuple[bool, str]:
    """Close a running desktop application."""
    clean_name = app_name.lower().strip()
    
    exe_map = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "browser": "chrome.exe",
        "vscode": "Code.exe",
        "code": "Code.exe",
        "vs code": "Code.exe",
        "notepad": "notepad.exe",
        "calculator": "CalculatorApp.exe",
        "calc": "CalculatorApp.exe",
        "edge": "msedge.exe",
        "terminal": "WindowsTerminal.exe"
    }
    target_exe = exe_map.get(clean_name, f"{clean_name}.exe")
    
    try:
        res = subprocess.run(["taskkill", "/IM", target_exe, "/F"], capture_output=True, text=True)
        if res.returncode == 0:
            return True, f"Closed {clean_name}."
        return False, f"Could not close {clean_name} (it may not be running)."
    except Exception as e:
        return False, f"Error closing {app_name}: {e}"

def open_url_in_browser(url: str) -> tuple[bool, str]:
    """Open a URL in Google Chrome (or default browser)."""
    chrome_path = APPS["chrome"]
    try:
        if os.path.exists(chrome_path):
            subprocess.Popen([chrome_path, url], creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
        else:
            import webbrowser
            webbrowser.open(url)
        return True, f"Opened {url}"
    except Exception as e:
        return False, f"Error opening URL: {e}"

def search_google(query: str) -> tuple[bool, str]:
    """Search Google in Chrome."""
    import urllib.parse
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url_in_browser(url)

def launch_hacker_gui():
    """Signals or launches the Cyberpunk Hacker GUI."""
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    signal_file = os.path.join(data_dir, "gui_trigger.signal")
    try:
        with open(signal_file, "w") as f:
            f.write("show")
    except Exception:
        pass

    try:
        res = subprocess.run(
            ['powershell', '-Command', 'Get-CimInstance Win32_Process -Filter "CommandLine like \'%hacker_gui%\'"'],
            capture_output=True, text=True, timeout=3
        )
        if "hacker_gui" not in res.stdout:
            venv_pythonw = os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe")
            python_exe = venv_pythonw if os.path.exists(venv_pythonw) else sys.executable
            gui_script = os.path.join(BASE_DIR, "gui", "hacker_gui.py")
            subprocess.Popen([python_exe, gui_script], creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
    except Exception as e:
        print(f"Error launching Hacker GUI: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        success, msg = launch_app(sys.argv[1])
        print(msg)
