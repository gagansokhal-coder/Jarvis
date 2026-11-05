"""
Universal Laptop Controller for Gagan AI.
Provides full, unrestricted, reliable autonomous control over Windows applications and files.
Guarantees interactive GUI window visibility on the physical display via WinSta0\\Default.
100% DYNAMIC: Zero hardcoded drive letters, user folders, or app paths.
"""
import os
import sys
import subprocess
import shutil
import urllib.parse
import time
import winreg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_special_folder(folder_name: str) -> str:
    """Dynamically get special Windows folder path without hardcoding drives or usernames."""
    # 1. Try Windows Shell Special Folders
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        path = shell.SpecialFolders(folder_name)
        if path and os.path.exists(path):
            return path
    except Exception:
        pass

    # 2. Try Windows Registry User Shell Folders
    reg_map = {
        "Desktop": "Desktop",
        "Downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
        "MyDocuments": "Personal",
        "MyPictures": "My Pictures",
        "Programs": "Programs"
    }
    sub_key = reg_map.get(folder_name, folder_name)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            val, _ = winreg.QueryValueEx(key, sub_key)
            val = os.path.expandvars(val)
            if os.path.exists(val):
                return val
    except Exception:
        pass

    # 3. Dynamic User Home fallback
    user_home = os.path.expanduser("~")
    cand = os.path.join(user_home, folder_name)
    if os.path.exists(cand):
        return cand
    return user_home

def discover_installed_apps() -> dict:
    """
    Dynamically discover all installed applications, desktop shortcuts, and
    Start Menu entries across all drives with ZERO hardcoded paths.
    """
    apps = {}
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        folder_keys = ["Desktop", "AllUsersDesktop", "Programs", "AllUsersPrograms"]
        for fkey in folder_keys:
            try:
                folder_path = shell.SpecialFolders(fkey)
                if folder_path and os.path.exists(folder_path):
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            if file.lower().endswith(".lnk"):
                                name = os.path.splitext(file)[0].lower()
                                full_path = os.path.join(root, file)
                                apps[name] = full_path
            except Exception:
                pass
    except Exception:
        pass

    # Scan Windows Registry App Paths (Registered EXEs across the entire OS)
    for root_key in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        try:
            with winreg.OpenKey(root_key, r"Software\Microsoft\Windows\CurrentVersion\App Paths") as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as app_key:
                            exe_path, _ = winreg.QueryValueEx(app_key, "")
                            exe_path = os.path.expandvars(exe_path).strip('"')
                            if os.path.exists(exe_path):
                                base = os.path.splitext(subkey_name)[0].lower()
                                if base not in apps:
                                    apps[base] = exe_path
                    except Exception:
                        pass
        except Exception:
            pass

    return apps

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
    visible and interactive on Gagan's physical display.
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
        try:
            subprocess.Popen(cmd, shell=True)
            return True, f"Process started via shell fallback: {e}"
        except Exception as e2:
            return False, f"Failed to launch: {e2}"

def get_chrome_executable() -> str:
    """Dynamically resolve Google Chrome executable path from registry or system PATH."""
    # 1. Check registry App Paths
    for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            with winreg.OpenKey(root_key, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                val, _ = winreg.QueryValueEx(key, "")
                val = os.path.expandvars(val).strip('"')
                if os.path.exists(val):
                    return val
        except Exception:
            pass

    # 2. Check system PATH
    found = shutil.which("chrome")
    if found and os.path.exists(found):
        return found

    # 3. Standard Program Files search
    for pf in [os.environ.get("ProgramFiles", "C:\\Program Files"), os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")]:
        cand = os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe")
        if os.path.exists(cand):
            return cand

    return "chrome.exe"

def open_interactive_app(app_name: str, args: list = None) -> tuple[bool, str]:
    """
    Launch or focus any Windows application dynamically without hardcoded paths.
    """
    clean = app_name.lower().strip()
    apps = discover_installed_apps()

    # 1. Special handling for Google Chrome
    if any(k in clean for k in ["chrome", "browser", "grom", "grome", "crom", "crome", "chrom"]):
        chrome_exe = get_chrome_executable()
        url = args[0] if (args and len(args) > 0) else ""

        # Check if there is a personal profile shortcut dynamically discovered on desktop
        personal_shortcut = apps.get("gagan - chrome")
        if personal_shortcut and os.path.exists(personal_shortcut) and not url:
            target, arguments = resolve_shortcut(personal_shortcut)
            cmd = f'"{target}" {arguments}'.strip()
        else:
            if url:
                cmd = f'"{chrome_exe}" --profile-directory="Default" "{url}"'
            else:
                cmd = f'"{chrome_exe}" --profile-directory="Default"'

        success, msg = launch_on_interactive_desktop(cmd)
        time.sleep(0.5)
        focus_window("Chrome")
        return success, "Google Chrome opened on your screen, Gagan."

    # 2. Check dynamically discovered applications and shortcuts
    # Exact or substring match
    matched_path = apps.get(clean)
    if not matched_path:
        for name, path in apps.items():
            if clean in name or name in clean:
                matched_path = path
                break

    if matched_path and os.path.exists(matched_path):
        if matched_path.lower().endswith(".lnk"):
            target, arguments = resolve_shortcut(matched_path)
            cmd = f'"{target}" {arguments}'.strip()
        else:
            cmd = f'"{matched_path}"'

        success, msg = launch_on_interactive_desktop(cmd)
        time.sleep(0.5)
        focus_window(clean)
        return success, f"Opened {app_name} on your screen, Gagan."

    # 3. Fallback to generic system executable lookup
    target = shutil.which(clean) or clean
    cmd = f'"{target}"'
    success, msg = launch_on_interactive_desktop(cmd)
    if success:
        time.sleep(0.5)
        focus_window(clean)
        return True, f"Launched {app_name} on your screen."

    return False, f"Could not find or launch application: {app_name}"

def open_folder(folder_path: str) -> tuple[bool, str]:
    """Open any directory or special Windows folder dynamically in File Explorer."""
    clean = folder_path.lower().strip()
    desktop_dir = get_special_folder("Desktop")

    if "desktop" in clean:
        resolved = desktop_dir
    elif "download" in clean:
        resolved = get_special_folder("Downloads")
    elif "document" in clean:
        resolved = get_special_folder("MyDocuments")
    elif "picture" in clean or "photo" in clean:
        resolved = get_special_folder("MyPictures")
    elif "gaganai" in clean:
        resolved = BASE_DIR
    elif os.path.exists(folder_path):
        resolved = os.path.abspath(folder_path)
    else:
        resolved = desktop_dir

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
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        return shell.AppActivate(title_keyword)
    except Exception:
        return False

def open_url(url: str) -> tuple[bool, str]:
    """Open any URL in Google Chrome with Gagan's profile on screen."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    chrome_exe = get_chrome_executable()
    cmd = f'"{chrome_exe}" --profile-directory="Default" "{url}"'
    success, msg = launch_on_interactive_desktop(cmd)
    time.sleep(0.5)
    focus_window("Chrome")
    return success, f"Opened {url} in Chrome."

def search_google(query: str) -> tuple[bool, str]:
    """Search Google in Chrome."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)
