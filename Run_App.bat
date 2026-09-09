@echo off
cd /d "%~dp0"
start pythonw app_gui.py
if errorlevel 1 (
    python app_gui.py
)
