import win32com.client
import os

sh = win32com.client.Dispatch("WScript.Shell")
shortcuts = [
    r"D:\Desktop\gagan - Chrome.lnk",
    r"C:\Users\Public\Desktop\Google Chrome.lnk",
    r"D:\Desktop\YouTube.lnk",
    r"D:\Desktop\Antigravity IDE.lnk"
]

for sc in shortcuts:
    if os.path.exists(sc):
        lnk = sh.CreateShortcut(sc)
        print(f"=== {sc} ===")
        print(f"TargetPath: {lnk.TargetPath}")
        print(f"Arguments:  {lnk.Arguments}")
        print(f"WorkingDir: {lnk.WorkingDirectory}")
