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
    # Google Chrome and Whisper phonetic variations (Indian / accented speech)
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "grom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "grome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chrom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chorm": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "chrme": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "crhome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "corom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "krome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "krom": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "browser": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google browser": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "web": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "internet": r"C:\Program Files\Google\Chrome\Application\chrome.exe",

    # Web Portals & Quick Destinations
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "web whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "chat gpt": "https://chatgpt.com",
    "gpt": "https://chatgpt.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "nitj": "https://www.nitj.ac.in",
    "nit jalandhar": "https://www.nitj.ac.in",

    # Desktop Applications
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

def focus_app(window_title: str) -> bool:
    """Bring any window to the foreground."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        return shell.AppActivate(window_title)
    except Exception:
        return False

def _spawn_interactive(target: str, args: list = None, app_name: str = "") -> tuple[bool, str]:
    """Reliably launch a Windows application and guarantee it appears on screen."""
    # Special handling for Chrome & browsers: force a visible interactive window
    chrome_variants = ["chrome", "browser", "chrme", "crome", "crhome", "grom", "grome", "crom", "chrom", "chorm", "corom", "krome"]
    if any(k in app_name.lower() or k in target.lower() for k in chrome_variants):
        try:
            # 1. If Chrome window is already open, focus it
            if focus_app("Chrome") or focus_app("Google Chrome"):
                return True, "Google Chrome brought to focus."
            # 2. Otherwise open a new visible window
            cmd = [target, "--new-window", "https://www.google.com"] if not args else [target] + args
            subprocess.Popen(cmd)
            return True, "Launched Google Chrome."
        except Exception:
            try:
                os.startfile(target)
                return True, "Launched Google Chrome."
            except Exception as e:
                return False, f"Failed to start Chrome: {e}"

    # For web portals & URLs
    if target.startswith("http:") or target.startswith("https:"):
        open_url_in_browser(target)
        return True, f"Opened {app_name} in Chrome."

    # For settings / protocols
    if target.startswith("ms-settings:"):
        os.startfile(target)
        return True, f"Opened {app_name}."

    # Standard desktop applications (VS Code, Notepad, Calc, Terminal, Explorer, etc.)
    try:
        os.startfile(target)
        return True, f"Launched {app_name}."
    except Exception:
        try:
            cmd = [target] + (args or [])
            subprocess.Popen(cmd)
            return True, f"Launched {app_name}."
        except Exception as e:
            return False, f"Failed to launch {app_name}: {e}"

def launch_app(app_name: str, args: list = None) -> tuple[bool, str]:
    """Launch a desktop application in milliseconds."""
    clean_name = app_name.lower().strip()
    
    # 1. Direct registry lookup
    if clean_name in APPS:
        target = APPS[clean_name]
        return _spawn_interactive(target, args=args, app_name=clean_name)

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
        return _spawn_interactive(target, args=args, app_name=name)

    # 3. Fallback to Windows os.startfile / shutil.which
    try:
        resolved = shutil.which(app_name) or app_name
        os.startfile(resolved)
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
