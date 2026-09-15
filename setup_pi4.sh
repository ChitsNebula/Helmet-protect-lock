#!/bin/bash
# ==============================================================================
# 🪖 Helmet Protect Lock - Raspberry Pi 4 Fast Setup Script (Pure NCNN)
# ==============================================================================
echo "======================================================================"
echo "    🪖 HELMET PROTECT LOCK - RASPBERRY PI 4 SETUP INSTALLER"
echo "======================================================================"
echo ""

set -e

echo "[1/3] ตรวจสอบและติดตั้ง System Packages ที่จำเป็น..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-opencv \
    libcamera-v4l2 \
    v4l-utils \
    libatlas-base-dev \
    libopenblas-dev

echo "[2/3] ติดตั้ง Pure NCNN Engine (ขนาด 5 MB เสร็จในไม่กี่วินาที ไม่ต้องลง PyTorch)..."
pip3 install ncnn --no-deps

echo "[3/3] ตั้งค่าสิทธิ์กล้อง, GPIO และสิทธิ์การรันสคริปต์..."
sudo usermod -a -G video,gpio $USER || true
chmod +x run_pi4.py start_pi4.sh setup_pi4.sh || true

echo ""
echo "======================================================================"
echo "🎉 การติดตั้งเสร็จสมบูรณ์ พร้อมรันบน Raspberry Pi 4 แบบเร็วแรงสุดขีด!"
echo "👉 เริ่มต้นรันระบบตรวจจับความเร็วสูงได้ทันทีด้วย: ./start_pi4.sh"
echo "======================================================================"
