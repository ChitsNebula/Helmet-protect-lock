#!/bin/bash
# ==============================================================================
# 🪖 HELMET PROTECT LOCK - ONE-CLICK INSTALL AND RUN (PI 4)
# ==============================================================================
cd "$(dirname "$0")"

echo "======================================================================"
echo "    🪖 HELMET PROTECT LOCK - AUTO SETUP AND START (PI 4)"
echo "======================================================================"

# 1. ติดตั้ง NCNN ถ้ายังไม่ได้ติดตั้ง
if ! python3 -c "import ncnn" 2>/dev/null; then
    echo "[1/2] กำลังติดตั้ง NCNN Engine..."
    if ls ncnn*.whl 1> /dev/null 2>&1; then
        pip3 install ncnn*.whl --no-deps
    else
        pip3 install ncnn --no-deps
    fi
else
    echo "[1/2] ตรวจพบ NCNN Engine ติดตั้งพร้อมใช้งานแล้ว!"
fi

# 2. ให้สิทธิ์รันสคริปต์
chmod +x run_pi4.py start_pi4.sh || true

# 3. รันระบบทันที
echo "[2/2] เริ่มต้นรันระบบตรวจจับหมวกกันน็อก..."
./start_pi4.sh
