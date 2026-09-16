#!/bin/bash
# ==============================================================================
# 🪖 Launcher Script for Raspberry Pi 4 (Turbo High-Speed Mode)
# ==============================================================================
cd "$(dirname "$0")"

# รันด้วยโมเดล NCNN 256x256 FP16 พร้อม MJPEG 30 FPS บน Pi 4
python3 run_pi4.py \
    --model best_ncnn_model \
    --source 0 \
    --imgsz 256 \
    --threads 3 \
    --conf 0.45 \
    --cam-w 640 \
    --cam-h 480 \
    --relay-pin 17 \
    --unlock-sec 5.0
