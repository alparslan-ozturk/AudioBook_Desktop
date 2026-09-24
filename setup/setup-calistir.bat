@echo off
chcp 65001 >nul
cd /d "C:\Users\Alparslan\Documents\Default Project"
py -3.11 "C:\Users\Alparslan\Documents\Default Project\setup_gui.py"
if errorlevel 1 python "C:\Users\Alparslan\Documents\Default Project\setup_gui.py"
pause
