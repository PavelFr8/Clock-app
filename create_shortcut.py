import os
import winshell
from win32com.client import Dispatch

desktop = winshell.desktop()

target = os.path.abspath("run.exe")

shortcut_name = "Smart Clock.lnk"

shortcut_path = os.path.join(desktop, shortcut_name)

if not os.path.exists(shortcut_path):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = os.path.abspath(r"Clock\img\clock.ico")  # Замените на реальный путь к иконке
    shortcut.Description = "The smartest clock in the world."
    shortcut.save()