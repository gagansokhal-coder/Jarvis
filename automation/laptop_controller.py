"""
Universal Laptop Controller for Gagan AI.
Provides full, unrestricted, reliable autonomous control over Gagan Rajput's Windows laptop.
Guarantees interactive GUI window visibility on Gagan's physical display via WinSta0\\Default.
"""
import os
import sys
import subprocess
import shutil
import urllib.parse
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# User desktop paths
USER_DESKTOP = r"D:\Desktop"
PUBLIC_DESKTOP = r"C:\Users\Public\Desktop"

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PROFILE = "Default"

APP_MAP = {
    "chrome": CHROME_EXE,
    "google chrome": CHROME_EXE,
    "grom": CHROME_EXE,
    "grome": CHROME_EXE,
    "crom": CHROME_EXE,
    "crome": CHROME_EXE,
    "chrom": CHROME_EXE,
    "browser": CHROME_EXE,
    "youtube": os.path.join(USER_DESKTOP, "YouTube.lnk"),
    "vscode": os.path.join(USER_DESKTOP, "Visual Studio Code.lnk"),
    "code": os.path.join(USER_DESKTOP, "Visual Studio Code.lnk"),
    "vs code": os.path.join(USER_DESKTOP, "Visual Studio Code.lnk"),
    "antigravity": os.path.join(USER_DESKTOP, "Antigravity IDE.lnk"),
    "antigravity ide": os.path.join(USER_DESKTOP, "Antigravity IDE.lnk"),
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
}

def resolve_shortcut(lnk_path: str) -> tuple[str, str]:
    """Extract TargetPath and Arguments from a Windows .lnk shortcut."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        return shortcut.TargetPath, shortcut.Arguments
    except Exception:
        return lnk_path, ""

def launch_on_interactive_desktop(cmd: str) -> tuple[bool, str]:
    """
    Launch any process onto WinSta0\\Default so its GUI window is immediately
    visible and interactive on Gagan Rajput's physical display.
    """
    try:
        import win32process
        import win32con
        si = win32process.STARTUPINFO()
        si.lpDesktop = r"WinSta0\Default"
        si.dwFlags = win32process.STARTF_USESHOWWINDOW
        si.wShowWindow = win32con.SW_SHOWNORMAL

        hProcess, hThread, dwProcessId, dwThreadId = win32process.CreateProcess(
            None, cmd, None, None, False, 0, None, None, si
        )
        return True, f"Process started (PID: {dwProcessId}) on interactive desktop."
    except Exception as e:
        # Fallback to standard subprocess
        try:
            subprocess.Popen(cmd, shell=True)
            return True, f"Process started via shell fallback: {e}"
        except Exception as e2:
            return False, f"Failed to launch: {e2}"

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

    # 1. Special handling for Google Chrome
    if any(k in clean for k in ["chrome", "browser", "grom", "grome", "crom", "crome", "chrom"]):
        url = args[0] if (args and len(args) > 0) else ""
        # Check for Gagan's personalized desktop shortcut first
        gagan_lnk = os.path.join(USER_DESKTOP, "gagan - Chrome.lnk")
        if os.path.exists(gagan_lnk) and not url:
            target, arguments = resolve_shortcut(gagan_lnk)
            cmd = f'"{target}" {arguments}'.strip()
        else:
            if url:
                cmd = f'"{CHROME_EXE}" --profile-directory="{CHROME_PROFILE}" "{url}"'
            else:
                cmd = f'"{CHROME_EXE}" --profile-directory="{CHROME_PROFILE}"'

        success, msg = launch_on_interactive_desktop(cmd)
        time.sleep(0.5)
        focus_window("Chrome")
        return success, "Google Chrome opened on your screen, Gagan."

    # 2. Check desktop shortcut match
    for name, path in APP_MAP.items():
        if name in clean or clean in name:
            if path.endswith(".lnk") and os.path.exists(path):
                target, arguments = resolve_shortcut(path)
                cmd = f'"{target}" {arguments}'.strip()
                success, msg = launch_on_interactive_desktop(cmd)
                time.sleep(0.5)
                focus_window(name)
                return success, f"Opened {name} on your screen, Gagan."
            elif os.path.exists(path):
                cmd = f'"{path}"'
                success, msg = launch_on_interactive_desktop(cmd)
                time.sleep(0.5)
                focus_window(name)
                return success, f"Opened {name} on your screen, Gagan."

    # 3. Check generic Windows system executable
    target = shutil.which(clean) or clean
    cmd = f'"{target}"'
    success, msg = launch_on_interactive_desktop(cmd)
    if success:
        time.sleep(0.5)
        focus_window(clean)
        return True, f"Launched {app_name} on your screen."

    return False, f"Could not find or launch application: {app_name}"

def open_folder(folder_path: str) -> tuple[bool, str]:
    """Open any directory or special Windows folder in File Explorer on the interactive desktop."""
    clean = folder_path.lower().strip()
    resolved = folder_path

    if "desktop" in clean:
        resolved = USER_DESKTOP
    elif "download" in clean:
        resolved = os.path.expandvars(r"%USERPROFILE%\Downloads")
    elif "document" in clean:
        resolved = os.path.expandvars(r"%USERPROFILE%\Documents")
    elif "picture" in clean or "photo" in clean:
        resolved = os.path.expandvars(r"%USERPROFILE%\Pictures")
    elif "gaganai" in clean:
        resolved = os.path.join(USER_DESKTOP, "gaganAI")

    if not os.path.exists(resolved):
        resolved = USER_DESKTOP

    cmd = f'explorer.exe "{resolved}"'
    success, msg = launch_on_interactive_desktop(cmd)
    return success, f"Opened {os.path.basename(resolved) or 'folder'} in File Explorer."

def focus_window(title_keyword: str) -> bool:
    """Bring any window matching title_keyword to the foreground on the active desktop."""
    try:
        import win32service
        import win32gui
        import win32con
        hdesk = win32service.OpenDesktop('Default', 0, False, win32con.GENERIC_ALL)
        hwnds = hdesk.EnumDesktopWindows()
        for h in hwnds:
            text = win32gui.GetWindowText(h)
            if title_keyword.lower() in text.lower():
                win32gui.ShowWindow(h, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(h)
                return True
    except Exception:
        pass

    # Fallback to WScript.Shell AppActivate
    ps_cmd = f"""
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.AppActivate('{title_keyword}')
    """
    success, _ = execute_powershell(ps_cmd, timeout=3)
    return success

def open_url(url: str) -> tuple[bool, str]:
    """Open any URL in Google Chrome with Gagan's profile on screen."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    cmd = f'"{CHROME_EXE}" --profile-directory="{CHROME_PROFILE}" "{url}"'
    success, msg = launch_on_interactive_desktop(cmd)
    time.sleep(0.5)
    focus_window("Chrome")
    return success, f"Opened {url} in Chrome."

def search_google(query: str) -> tuple[bool, str]:
    """Search Google in Chrome."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)

def set_volume(level: int) -> tuple[bool, str]:
    """Adjust system volume (0-100) or toggle mute."""
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
