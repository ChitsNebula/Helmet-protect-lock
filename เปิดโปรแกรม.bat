@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Helmet AI Control Center - Launcher
color 0B

echo ======================================================================
echo           🪖 HELMET AI CONTROL CENTER - SYSTEM LAUNCHER
echo ======================================================================
echo.

:: 1. เช็คว่ามี Python ติดตั้งอยู่ในเครื่องหรือไม่
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] ไม่พบ Python ในเครื่องนี้!
    echo กรุณาติดตั้ง Python (แนะนำเวอร์ชัน 3.10 หรือ 3.11)
    echo และอย่าลืมติ๊กถูก "Add Python to PATH" ตอนติดตั้งด้วย
    echo.
    echo ดาวน์โหลดได้ที่: https://www.python.org/downloads/
    echo ======================================================================
    pause
    exit /b
)

:: 2. ตรวจสอบว่า Library สำคัญถูกติดตั้งครบหรือยัง
echo [*] กำลังตรวจสอบความพร้อมของระบบ...
python -c "import cv2, ultralytics, torch, numpy" >nul 2>&1

if %errorlevel% neq 0 (
    color 0E
    echo.
    echo [!] ตรวจพบว่ายังไม่ได้ติดตั้ง Library ที่จำเป็นสำหรับเครื่องนี้
    echo [*] กำลังเริ่มติดตั้ง Library อัตโนมัติ (อาจใช้เวลา 1-3 นาที แค่ครั้งแรก)...
    echo ----------------------------------------------------------------------
    
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] ติดตั้ง Library ไม่สำเร็จ! กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
        echo ----------------------------------------------------------------------
        pause
        exit /b
    )
    echo ----------------------------------------------------------------------
    echo [OK] ติดตั้ง Library ครบถ้วนเรียบร้อยแล้ว!
    echo.
) else (
    echo [OK] สภาพแวดล้อมพร้อมใช้งาน (Library ครบถ้วนแล้ว)
)

:: 3. รันโปรแกรมหลัก
echo [*] กำลังเปิดหน้าต่างโปรแกรม Helmet AI...
echo ======================================================================
echo.

python app_gui.py

:: 4. ดักจับข้อผิดพลาดกรณีที่โปรแกรมปิดตัวกะทันหัน
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ======================================================================
    echo [CRASH] โปรแกรมหยุดทำงานกะทันหันเนื่องจากมีข้อผิดพลาดด้านบน
    echo ======================================================================
    pause
)
