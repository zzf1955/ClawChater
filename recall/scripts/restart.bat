@echo off
cd /d "%~dp0"
conda run -n recall python restart.py
pause
