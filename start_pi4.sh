#!/bin/bash
# ==============================================================================
# 🪖 Launcher Script for Raspberry Pi 4 (Pure NCNN High-FPS Mode)
# ==============================================================================
cd "$(dirname "$0")"

# รันด้วยโมเดล NCNN imgsz 320 เพื่อความลื่นไหลระดับ 25-35+ FPS บน Pi 4
python3 run_pi4.py \
    --model best_ncnn_model \
    --source 0 \
    --imgsz 640 \
    --conf 0.45 \
    --cam-w 640 \
    --cam-h 480 \
    --relay-pin 17 \
    --unlock-sec 5.0
