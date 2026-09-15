#!/bin/bash
# ==============================================================================
# 🚀 Launcher Script for Raspberry Pi 4 (Max FPS Mode)
# ==============================================================================
cd "$(dirname "$0")"

# แนะนำ imgsz 320 เพื่อให้ได้ความเร็วสูงสุด ~25-35+ FPS บน Pi 4
# หากต้องการความคมชัดขึ้น ปรับเป็น --imgsz 416 ได้
python3 run_pi4.py \
    --model helmet_detector_ncnn_model \
    --source 0 \
    --imgsz 320 \
    --conf 0.45 \
    --cam-w 640 \
    --cam-h 480 \
    --relay-pin 17 \
    --unlock-sec 5.0
