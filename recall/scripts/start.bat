@echo off
cd /d "%~dp0\.."
start "" /B conda run -n recall pythonw main.py
echo Recall 已在后台启动，查看系统托盘图标
timeout /t 3 >nul
