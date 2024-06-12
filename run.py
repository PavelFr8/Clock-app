import subprocess

# Запуск скрипта в фоновом режиме
subprocess.Popen(['python', 'create_shortcut.py'], creationflags=subprocess.CREATE_NO_WINDOW)
subprocess.Popen(['python', 'Clock/main.py'], creationflags=subprocess.CREATE_NO_WINDOW)
