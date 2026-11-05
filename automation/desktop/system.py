"""
System Control and Monitoring for Gagan AI.
Phase 4: Automation
"""
import os
import sys
import time
import subprocess
from datetime import datetime
import psutil
from PIL import ImageGrab

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'data', 'screenshots')
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def get_system_status() -> dict:
    """Get real-time CPU, RAM, Disk, and Battery telemetry."""
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("D:\\" if os.path.exists("D:\\") else "C:\\")
    battery = psutil.sensors_battery()
    
    battery_info = "Unknown"
    if battery:
        plugged = "Charging" if battery.power_plugged else "Discharging"
        battery_info = f"{battery.percent}% ({plugged})"

    return {
        "cpu_percent": cpu,
        "ram_total_gb": round(ram.total / (1024**3), 1),
        "ram_used_gb": round(ram.used / (1024**3), 1),
        "ram_percent": ram.percent,
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "disk_percent": disk.percent,
        "battery": battery_info
    }

def get_system_status_spoken() -> str:
    """Crisp 1-2 sentence spoken summary of system health."""
    status = get_system_status()
    return (
        f"CPU is running at {status['cpu_percent']}%. "
        f"RAM usage is {status['ram_percent']}%, using {status['ram_used_gb']} GB of {status['ram_total_gb']} GB. "
        f"Battery is at {status['battery']}."
    )

def take_screenshot(send_telegram: bool = False) -> tuple[bool, str]:
    """Capture full desktop screen and optionally dispatch to Telegram."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        img = ImageGrab.grab()
        img.save(filepath, "PNG")
        
        msg = f"Screenshot captured: {filename}"
        if send_telegram:
            try:
                from scripts.telegram_sender import send_telegram_photo
                send_telegram_photo(filepath, caption=f"📸 Gagan AI Desktop Screenshot ({timestamp})")
                msg += " and sent to Telegram."
            except Exception as e:
                msg += f" (Telegram send error: {e})"
                
        return True, msg
    except Exception as e:
        return False, f"Failed to take screenshot: {e}"

def lock_workstation() -> tuple[bool, str]:
    """Lock the computer immediately."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return True, "Workstation locked."
    except Exception as e:
        return False, f"Error locking workstation: {e}"

if __name__ == '__main__':
    print(get_system_status())
    print(get_system_status_spoken())
