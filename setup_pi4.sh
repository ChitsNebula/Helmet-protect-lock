#!/bin/bash
# ==============================================================================
# 🪖 Helmet Protect Lock - Raspberry Pi 4 Fast Setup Script
# ==============================================================================
echo "======================================================================"
echo "    🪖 HELMET PROTECT LOCK - RASPBERRY PI 4 SETUP INSTALLER"
echo "======================================================================"
echo ""

set -e

echo "[1/4] กำลังอัปเดตระบบและติดตั้ง System Packages..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-opencv \
    libcamera-v4l2 \
    v4l-utils \
    libatlas-base-dev \
    libopenblas-dev

echo "[2/4] กำลังติดตั้ง Ultralytics และไลบรารี Python สำหรับ AI..."
pip3 install --upgrade pip
pip3 install ultralytics

echo "[3/4] ตรวจสอบสิทธิ์การเข้าถึงกล้องและ GPIO..."
sudo usermod -a -G video,gpio $USER || true

echo "[4/4] ปรับสิทธิ์การรันไฟล์สคริปต์..."
chmod +x run_pi4.py start_pi4.sh || true

echo ""
echo "======================================================================"
echo "🎉 ติดตั้งระบบทั้งหมดบน Raspberry Pi 4 เสร็จสมบูรณ์แล้ว!"
echo "👉 สั่งรันตรวจจับความเร็วสูงได้ทันทีด้วยคำสั่ง: ./start_pi4.sh"
echo "======================================================================"
