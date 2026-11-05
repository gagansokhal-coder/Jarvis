import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.laptop_controller import launch_via_explorer_desktop
import win32gui, win32service, win32con

pythonw = os.path.join(r"d:\Desktop\gaganAI", "venv", "Scripts", "pythonw.exe")
gui_script = os.path.join(r"d:\Desktop\gaganAI", "gui", "hacker_gui.py")

ok, msg = launch_via_explorer_desktop(pythonw, f'"{gui_script}"')
print("Launch result:", ok, msg)

time.sleep(2)
hdesk = win32service.OpenDesktop('Default', 0, False, win32con.GENERIC_ALL)
found = False
for h in hdesk.EnumDesktopWindows():
    t = win32gui.GetWindowText(h)
    if 'gagan' in t.lower() or 'tactical' in t.lower() or 'hacker' in t.lower() or 'console' in t.lower():
        print(f"FOUND GUI WINDOW: {int(h)}, '{t}'")
        found = True

if not found:
    print("Window not found, checking process list...")
    import psutil
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if p.info['cmdline'] and 'hacker_gui' in ' '.join(p.info['cmdline']):
            print(f"Running PID {p.info['pid']}: {p.info['cmdline']}")

