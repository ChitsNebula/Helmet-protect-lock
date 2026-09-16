#!/bin/bash
# ==============================================================================
# 🪖 Launcher Script for Raspberry Pi 4 (Ultra High-Speed Mode)
# ==============================================================================
cd "$(dirname "$0")"

# รันด้วยโมเดล NCNN 320x320 พร้อมระบบ Async AI Worker เพื่อความลื่นไหล 30 FPS บน Pi 4
python3 run_pi4.py \
    --model best_ncnn_model \
    --source 0 \
    --imgsz 320 \
    --conf 0.45 \
    --cam-w 640 \
    --cam-h 480 \
    --relay-pin 17 \
    --unlock-sec 5.0
