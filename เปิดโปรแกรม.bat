@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo กำลังเปิดหน้าต่าง Helmet AI Control Center...
start pythonw app_gui.py
if errorlevel 1 (
    python app_gui.py
)
