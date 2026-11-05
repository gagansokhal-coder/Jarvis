"""
Windows Laptop Screen & Lock State Controller.
Supports:
- Detecting if the laptop screen is locked
- Keeping system active in Away Mode during display sleep
- Auto-unlocking Windows with password/PIN '1008' upon voice trigger
"""

import time
import ctypes
import os

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Execution states for Windows Power Management
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040

# Virtual Key Codes
VK_SPACE = 0x20
VK_RETURN = 0x0D
VK_MAP = {
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39
}

def enable_background_listen_state():
    """
    Prevents the CPU from suspending when the laptop display turns off.
    Allows wake-word acoustic listening to stay active without costing extra battery.
    """
    try:
        kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED)
        return True
    except Exception as e:
        print(f"Error setting thread execution state: {e}")
        return False

def is_workstation_locked() -> bool:
    """
    Check if the Windows workstation is currently locked or displaying Winlogon.
    Returns True if locked, False if desktop is accessible.
    """
    try:
        desk = user32.OpenDesktopW("Default", 0, False, 0x0100)
        if desk:
            user32.CloseDesktop(desk)
            return False
        return True
    except Exception:
        return False

def wake_display():
    """Wake display from screen sleep by nudging mouse cursor and tapping Shift."""
    try:
        # Subtle mouse nudge
        user32.mouse_event(0x0001, 1, 1, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(0x0001, -1, -1, 0, 0)
        # Tap Shift key (safe non-destructive key)
        user32.keybd_event(0x10, 0, 0, 0) # Shift down
        time.sleep(0.02)
        user32.keybd_event(0x10, 0, 2, 0) # Shift up
    except Exception as e:
        print(f"Error waking display: {e}")

def unlock_laptop(pin: str = "1008") -> bool:
    """
    Simulates user action to dismiss the lock screen and enter the PIN/password.
    """
    print(f"🔓 [Unlock Request] Detected locked workstation. Unlocking with PIN...")

    # 1. Wake display
    wake_display()
    time.sleep(0.2)

    # 2. Press Space / Enter to dismiss wallpaper & expose password entry box
    user32.keybd_event(VK_SPACE, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(VK_SPACE, 0, 2, 0)
    time.sleep(0.4)

    # 3. Type PIN digits
    for digit in str(pin):
        vk = VK_MAP.get(digit)
        if vk:
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.04)
            user32.keybd_event(vk, 0, 2, 0)
            time.sleep(0.04)

    # 4. Press Enter to submit PIN
    time.sleep(0.15)
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(VK_RETURN, 0, 2, 0)

    # Wait for desktop switch
    time.sleep(0.8)

    locked = is_workstation_locked()
    if not locked:
        print("✅ [Unlock Succeeded] Laptop screen successfully unlocked!")
        return True
    else:
        print("⚠️ [Unlock Verification] Workstation might still be unlocking or in transition.")
        return False

if __name__ == "__main__":
    enable_background_listen_state()
    locked = is_workstation_locked()
    print(f"Current lock state: {'LOCKED' if locked else 'UNLOCKED'}")

