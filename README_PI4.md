# 🪖 Helmet Protect Lock - สำหรับ Raspberry Pi 4 (Pure NCNN Mode)

คู่มือการรันระบบตรวจจับหมวกกันน็อกความเร็วสูง (25-35+ FPS) บน Raspberry Pi 4

---

### ⚡ ทำไมต้อง Pure NCNN?
1. **ไม่ต้องลง PyTorch หรือ Ultralytics** (ไม่ต้องโหลดเป็น GB ไม่ต้องเสียเวลาบิวด์หลายชั่วโมง)
2. **ใช้ไลบรารีเพียง 5 MB (`ncnn`)** ร่วมกับ OpenCV และ NumPy ที่ติดตั้งผ่าน `apt` เรียบร้อยแล้ว
3. **ใช้ C++ Engine และ ARM NEON Vector Acceleration** รันบน CPU Cortex-A72 ทั้ง 4 Cores เต็มพิกัด

---

### 🚀 ขั้นตอนการติดตั้งและรันบน Raspberry Pi 4

1. **เปิด Terminal แล้วรันคำสั่งติดตั้ง ncnn (เสร็จใน 3 วินาที):**
   ```bash
   pip3 install ncnn --no-deps
   ```

2. **สั่งรันระบบได้ทันที:**
   ```bash
   ./start_pi4.sh
   ```
   หรือรันแบบระบุพารามิเตอร์:
   ```bash
   python3 run_pi4.py --model best_ncnn_model --imgsz 320
   ```

---

### 🔌 การต่อวงจร Relay ปลดล็อกหมวก
- **VCC** -> 5V (Pin 2 หรือ 4)
- **GND** -> GND (Pin 6 หรือ 9)
- **IN** -> GPIO 17 (Pin 11) (หรือระบุด้วย `--relay-pin <number>`)
