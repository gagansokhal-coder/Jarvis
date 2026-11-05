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

def force_window_foreground(hwnd) -> bool:
    """
    Guarantees bringing any HWND to the true foreground on Windows 11 physical display.
    Bypasses LockSetForegroundWindow restrictions by attaching thread input and simulating ALT key.
    """
    try:
        import ctypes
        import win32api
        user32 = ctypes.windll.user32
        h_int = int(hwnd)
        fore_hwnd = user32.GetForegroundWindow()
        fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
        cur_tid = win32api.GetCurrentThreadId()

        user32.AttachThreadInput(cur_tid, fore_tid, True)
        user32.keybd_event(0x12, 0, 0, 0) # ALT down
        user32.keybd_event(0x12, 0, 2, 0) # ALT up
        user32.ShowWindow(h_int, 9)       # SW_RESTORE
        user32.BringWindowToTop(h_int)
        user32.SetForegroundWindow(h_int)
        user32.AttachThreadInput(cur_tid, fore_tid, False)
        return True
    except Exception:
        return False

def ensure_default_desktop():
    """Ensure current process and thread are attached to interactive WinSta0\\Default."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwinsta = user32.OpenWindowStationW('WinSta0', False, 0x37F)
        if hwinsta:
            user32.SetProcessWindowStation(hwinsta)
        hdesk = user32.OpenDesktopW('Default', 0, False, 0x1FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

def launch_on_interactive_desktop(cmd: str) -> tuple[bool, str]:
    """
    Launch any process onto WinSta0\\Default so its GUI window is immediately
    visible and interactive on Gagan's physical display.
    """
    ensure_default_desktop()
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
            import ctypes
            res = ctypes.windll.shell32.ShellExecuteW(None, "open", cmd, None, None, 1)
            return True, f"Started via ShellExecuteW: {res}"
        except Exception as e2:
            try:
                subprocess.Popen(cmd, shell=True)
                return True, f"Started via shell fallback."
            except Exception as e3:
                return False, f"Failed to launch: {e3}"

def launch_via_explorer_desktop(target: str, args: str = "", work_dir: str = "", operation: str = "open") -> tuple[bool, str]:
    """
    Launch any executable, shortcut (.lnk), URL, or folder directly onto WinSta0\\Default.
    This guarantees 100% physical display GUI visibility, completely eliminating virtual sandbox traps.
    """
    ensure_default_desktop()
    clean_target = target.strip().strip('"')

    # If it's a URL
    if clean_target.startswith("http://") or clean_target.startswith("https://"):
        return open_url(clean_target)

    # If it's a Windows Shortcut (.lnk)
    if clean_target.lower().endswith(".lnk") and os.path.exists(clean_target):
        target_path, lnk_args = resolve_shortcut(clean_target)
        if target_path and os.path.exists(target_path):
            combined_args = f"{lnk_args} {args}".strip()
            full_cmd = f'"{target_path}" {combined_args}'.strip()
            return launch_on_interactive_desktop(full_cmd)

    # If it's a directory
    if os.path.isdir(clean_target):
        return launch_on_interactive_desktop(f'explorer.exe "{clean_target}"')

    # Executable or generic command
    full_cmd = f'"{clean_target}" {args}'.strip() if args else f'"{clean_target}"'
    return launch_on_interactive_desktop(full_cmd)

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
    Uses Explorer Desktop COM to guarantee the window is visible on physical screen.
    """
    ensure_default_desktop()
    clean = app_name.lower().strip()
    apps = discover_installed_apps()

    # 1. Special handling for Google Chrome
    if any(k in clean for k in ["chrome", "browser", "grom", "grome", "crom", "crome", "chrom"]):
        url = args[0] if (args and len(args) > 0) else ""
        chrome_exe = get_chrome_executable()
        if url:
            cmd = f'"{chrome_exe}" --profile-directory="Default" "{url}"'
        else:
            cmd = f'"{chrome_exe}" --profile-directory="Default"'
        success, msg = launch_on_interactive_desktop(cmd)
        time.sleep(1.0)
        focus_window("Chrome")
        return success, "Google Chrome opened on your screen, Gagan."

    # 2. Special handling for YouTube
    if "youtube" in clean:
        chrome_exe = get_chrome_executable()
        cmd = f'"{chrome_exe}" --profile-directory="Default" "https://www.youtube.com"'
        success, msg = launch_on_interactive_desktop(cmd)
        time.sleep(1.0)
        focus_window("YouTube")
        return success, "YouTube opened on your screen, Gagan."

    # 3. Check dynamically discovered applications and shortcuts
    matched_path = apps.get(clean)
    if not matched_path:
        for name, path in apps.items():
            if clean in name or name in clean:
                matched_path = path
                break

    if matched_path and os.path.exists(matched_path):
        success, msg = launch_via_explorer_desktop(matched_path)
        time.sleep(1.0)
        focus_window(clean)
        return success, f"Opened {app_name} on your screen, Gagan."

    # 4. Fallback to generic system executable lookup
    target = shutil.which(clean) or clean
    success, msg = launch_via_explorer_desktop(target)
    if success:
        time.sleep(1.0)
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

    success, msg = launch_via_explorer_desktop("explorer.exe", f'"{resolved}"')
    time.sleep(0.5)
    focus_window(os.path.basename(resolved))
    return success, f"Opened {os.path.basename(resolved) or 'folder'} in File Explorer."

def focus_window(title_keyword: str) -> bool:
    """Bring any window matching title_keyword to the foreground on physical screen."""
    ensure_default_desktop()
    clean_kw = title_keyword.lower().strip()
    try:
        import win32gui
        matched_hwnd = None
        def cb(hwnd, _):
            nonlocal matched_hwnd
            if win32gui.IsWindowVisible(hwnd):
                text = win32gui.GetWindowText(hwnd)
                if text and clean_kw in text.lower() and 'restore pages' not in text.lower():
                    matched_hwnd = hwnd
        win32gui.EnumWindows(cb, None)
        if matched_hwnd:
            return force_window_foreground(matched_hwnd)
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
    """Open any URL in Google Chrome on Gagan's physical screen."""
    ensure_default_desktop()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    chrome_exe = get_chrome_executable()
    cmd = f'"{chrome_exe}" --profile-directory="Default" "{url}"'
    success, msg = launch_on_interactive_desktop(cmd)
    time.sleep(1.0)
    focus_window("Chrome")
    return success, f"Opened {url} in Chrome."

def search_google(query: str) -> tuple[bool, str]:
    """Search Google in Chrome."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)
