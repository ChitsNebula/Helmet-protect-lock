@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Helmet AI Control Center - Launcher
color 0B

echo ======================================================================
echo           🪖 HELMET AI CONTROL CENTER - AUTO LAUNCHER
echo ======================================================================
echo.

set "PY_CMD="

:: 1. ตรวจสอบคำสั่ง python ทั่วไป
python -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :PYTHON_FOUND
)

:: 2. ตรวจสอบ py launcher
py -3 -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    goto :PYTHON_FOUND
)

:: 3. ค้นหาในโฟลเดอร์ AppData / ProgramFiles ทั่วไป
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    goto :PYTHON_FOUND
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :PYTHON_FOUND
)
if exist "%ProgramFiles%\Python311\python.exe" (
    set "PY_CMD=%ProgramFiles%\Python311\python.exe"
    goto :PYTHON_FOUND
)
if exist "%ProgramFiles%\Python310\python.exe" (
    set "PY_CMD=%ProgramFiles%\Python310\python.exe"
    goto :PYTHON_FOUND
)
if exist "%ProgramFiles%\Python39\python.exe" (
    set "PY_CMD=%ProgramFiles%\Python39\python.exe"
    goto :PYTHON_FOUND
)

:: 4. ถ้าไม่มี Python ในเครื่องเลย -> โหลดและติดตั้งอัตโนมัติแบบ Silent
color 0E
echo [!] ไม่พบ Python ในเครื่องนี้
echo [*] กำลังดาวน์โหลดและติดตั้ง Python 3.11 แบบอัตโนมัติ กรุณารอสักครู่...
echo ----------------------------------------------------------------------

powershell -NoProfile -ExecutionPolicy Bypass -Command "$installer = Join-Path $env:TEMP 'python_installer.exe'; Write-Host '[1/2] กำลังดาวน์โหลด Python...'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe', $installer); Write-Host '[2/2] กำลังติดตั้ง Python อัตโนมัติ...'; Start-Process -FilePath $installer -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_tcltk=1 SimpleInstall=1' -Wait; Remove-Item $installer -Force -ErrorAction SilentlyContinue;"

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :PYTHON_FOUND
)

python -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :PYTHON_FOUND
)

color 0C
echo.
echo [ERROR] ติดตั้ง Python ไม่สำเร็จ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
pause
exit /b

:PYTHON_FOUND
color 0B
echo [OK] ตรวจพบสภาพแวดล้อม Python: %PY_CMD%

:: 5. ตรวจสอบ Library ที่จำเป็น
echo [*] กำลังตรวจสอบความพร้อมของ Library...
%PY_CMD% -c "import cv2, ultralytics, torch, numpy" >nul 2>&1
if %errorlevel% equ 0 goto :ALL_READY

color 0E
echo.
echo [!] กำลังติดตั้ง Library ที่จำเป็นสำหรับโปรแกรมนี้ อัตโนมัติ...
echo ----------------------------------------------------------------------

%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install -r requirements.txt

if %errorlevel% neq 0 goto :INSTALL_FAILED

echo ----------------------------------------------------------------------
echo [OK] ติดตั้ง Library ทั้งหมดเสร็จสิ้นเรียบร้อย!
echo.
goto :ALL_READY

:INSTALL_FAILED
color 0C
echo.
echo [ERROR] ติดตั้ง Library ไม่สำเร็จ กรุณาตรวจสอบอินเทอร์เน็ต
pause
exit /b

:ALL_READY
color 0A
echo [OK] สภาพแวดล้อมและ Library พร้อมใช้งานแล้ว
echo [*] กำลังเปิดหน้าต่าง Helmet AI Control Center...
echo ======================================================================
echo.

%PY_CMD% app_gui.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ======================================================================
    echo [CRASH] โปรแกรมหยุดทำงานเนื่องจากมีข้อผิดพลาด
    echo ======================================================================
    pause
)
