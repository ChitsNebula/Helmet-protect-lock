#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
🪖 HELMET PROTECT LOCK - HIGH PERFORMANCE INFERENCE FOR RASPBERRY PI 4
==============================================================================
สคริปต์ตรวจจับหมวกกันน็อกความเร็วสูงพิเศษ ปรับจูนสำหรับ Raspberry Pi 4 (Quad-Core ARM Cortex-A72)
- ประมวลผลด้วยโมเดล YOLOv8 NCNN (ARM NEON Acceleration)
- ระบบอ่านเฟรมกล้องแบบแยก Thread (Async Camera Capture) ไร้ดีเลย์
- ย่อขนาดภาพประมวลผล (imgsz 320 / 416) เพื่อรีด FPS สูงสุด 25 - 35+ FPS
- ระบบควบคุม Relay ปลดล็อกหมวกกันน็อกอัตโนมัติผ่าน GPIO เมื่อสวมหมวกถูกต้อง
- รองรับโหมด Headless (ไม่ต่อจอ) สำหรับติดตั้งบนรถจักรยานยนต์
==============================================================================
"""

import argparse
import os
import sys
import time
import threading
import cv2
import numpy as np

# ปรับประสิทธิภาพสำหรับ Multi-core ARM Cortex-A72
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"

# นำเข้า Ultralytics YOLO
try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] กรุณาติดตั้ง Ultralytics ก่อน: pip3 install ultralytics")
    sys.exit(1)

# นำเข้าไลบรารี GPIO (มี Mock Fallback หากไม่ได้รันบนบอร์ดจริง)
HAS_GPIO = False
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    try:
        from gpiozero import OutputDevice
        HAS_GPIO = "gpiozero"
    except ImportError:
        HAS_GPIO = False


# ==============================================================================
# 1. คลาสอ่านกล้องแบบ Asynchronous Multi-threading (ความเร็วสูงสุด ไร้ค้าง)
# ==============================================================================
class AsyncVideoCapture:
    """อ่านภาพจากกล้องใน Thread แยก เพื่อไม่ให้การอ่านภาพเป็นคอขวดของการประมวลผล AI"""
    def __init__(self, src=0, width=640, height=480):
        if str(src).isdigit():
            src = int(src)
            # บน Linux/Pi4 ให้ใช้ V4L2 backend ซึ่งเร็วและเสถียรที่สุด
            if sys.platform.startswith("linux"):
                self.cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
            elif sys.platform == "win32":
                self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(src)
        else:
            self.cap = cv2.VideoCapture(src)

        if not self.cap.isOpened():
            raise RuntimeError(f"ไม่สามารถเปิดกล้องได้ที่ source: {src}")

        # ตั้งขนาดภาพของกล้อง
        if isinstance(src, int):
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.ret, self.frame = self.cap.read()
        self.running = True
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.cap.release()


# ==============================================================================
# 2. ระบบควบคุมรีเลย์ล็อกหมวกกันน็อก (GPIO Relay Controller)
# ==============================================================================
class HelmetLockController:
    """ควบคุม Relay สั่งปลดล็อก/ล็อก กลอนโซลินอยด์ของหมวกกันน็อก"""
    def __init__(self, pin=17, active_low=True, unlock_duration=5.0):
        self.pin = pin
        self.active_low = active_low
        self.unlock_duration = unlock_duration
        self.is_unlocked = False
        self.unlock_timer = None
        self.lock = threading.Lock()

        if HAS_GPIO is True:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.pin, GPIO.OUT)
            # สถานะเริ่มต้น: ล็อก (Relay OFF)
            initial_state = GPIO.HIGH if self.active_low else GPIO.LOW
            GPIO.output(self.pin, initial_state)
            print(f"[GPIO] ตั้งค่า RPi.GPIO Pin {self.pin} (Relay Locked) สำเร็จ")
        else:
            print(f"[GPIO MOCK] จำลองการทำงาน Relay Pin {self.pin} (ไม่ได้ต่อฮาร์ดแวร์จริง)")

    def unlock(self):
        """สั่งปลดล็อกเป็นเวลาที่กำหนด"""
        with self.lock:
            if self.is_unlocked:
                return  # กำลังปลดล็อกอยู่แล้ว
            self.is_unlocked = True
            print("\n" + "=" * 55)
            print("🔓 >>> [ACTION] ตรวจพบหมวกกันน็อก! สั่งปลดล็อก Relay แล้ว <<<")
            print("=" * 55)

            if HAS_GPIO is True:
                on_state = GPIO.LOW if self.active_low else GPIO.HIGH
                GPIO.output(self.pin, on_state)

            if self.unlock_timer and self.unlock_timer.is_alive():
                self.unlock_timer.cancel()

            self.unlock_timer = threading.Timer(self.unlock_duration, self._auto_lock)
            self.unlock_timer.daemon = True
            self.unlock_timer.start()

    def _auto_lock(self):
        """ล็อกอัตโนมัติเมื่อครบเวลา"""
        with self.lock:
            self.is_unlocked = False
            print("\n🔒 >>> [ACTION] ครบเวลาแล้ว สั่งล็อก Relay กลับสู่โหมดปลอดภัย <<<")
            if HAS_GPIO is True:
                off_state = GPIO.HIGH if self.active_low else GPIO.LOW
                GPIO.output(self.pin, off_state)

    def cleanup(self):
        if HAS_GPIO is True:
            off_state = GPIO.HIGH if self.active_low else GPIO.LOW
            GPIO.output(self.pin, off_state)
            GPIO.cleanup()


# ==============================================================================
# 3. ฟังก์ชันหลักสำหรับรัน Real-time Detection
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="High-Speed YOLOv8 NCNN Helmet Detection for Raspberry Pi 4")
    parser.add_argument("--model", type=str, default="helmet_detector_ncnn_model", help="โฟลเดอร์โมเดล NCNN")
    parser.add_argument("--source", type=str, default="0", help="Camera Index (0) หรือ RTSP/HTTP URL")
    parser.add_argument("--imgsz", type=int, default=320, help="ขนาดภาพเข้า AI (320 = เร็วสุด ~30 FPS, 416 = ปานกลาง, 640 = คมสุด)")
    parser.add_argument("--conf", type=float, default=0.45, help="เกณฑ์ความมั่นใจ (Confidence Threshold)")
    parser.add_argument("--cam-w", type=int, default=640, help="ความกว้างภาพจากกล้อง (Default: 640)")
    parser.add_argument("--cam-h", type=int, default=480, help="ความสูงภาพจากกล้อง (Default: 480)")
    parser.add_argument("--relay-pin", type=int, default=17, help="หมายเลข GPIO Pin สำหรับคุม Relay (BCM 17)")
    parser.add_argument("--active-low", action="store_true", default=True, help="Relay ทำงานแบบ Active LOW (ค่าปกติของโมดูลรีเลย์)")
    parser.add_argument("--unlock-sec", type=float, default=5.0, help="ระยะเวลาปลดล็อก (วินาที)")
    parser.add_argument("--require-frames", type=int, default=3, help="จำนวนเฟรมที่ต้องเห็นหมวกต่อเนื่องก่อนสั่งปลดล็อก")
    parser.add_argument("--headless", action="store_true", help="รันแบบไม่มีหน้าต่างแสดงผล (สำหรับติดตั้งในตัวรถ กินแรมน้อยสุด)")
    args = parser.parse_args()

    # ตรวจสอบพาธโมเดล (รองรับทั้งชื่อ helmet_detector_ncnn_model และ best_ncnn_model)
    model_path = args.model
    if not os.path.exists(model_path):
        if os.path.exists("best_ncnn_model"):
            model_path = "best_ncnn_model"
        else:
            print(f"[ERROR] ไม่พบโฟลเดอร์โมเดล NCNN: {args.model}")
            return

    print("=" * 65)
    print("🚀 HELMET PROTECT LOCK - RASPBERRY PI 4 HIGH SPEED RUNNER")
    print("=" * 65)
    print(f"📦 โมเดล NCNN     : {model_path}")
    print(f"⚡ ขนาดภาพ AI (imgsz): {args.imgsz}x{args.imgsz} (Speed Optimized)")
    print(f"📷 แหล่งภาพกล้อง   : {args.source} ({args.cam_w}x{args.cam_h})")
    print(f"🔌 Relay GPIO Pin : {args.relay_pin} (Active {'LOW' if args.active_low else 'HIGH'})")
    print(f"🖥️ แสดงหน้าต่างผลลัพธ์: {'ปิด (Headless Mode)' if args.headless else 'เปิด (GUI Display)'}")
    print("=" * 65)

    # 1. โหลดโมเดล NCNN
    print("[1/3] กำลังโหลดโมเดล NCNN เข้าสู่หน่วยความจำ...")
    t_start = time.time()
    model = YOLO(model_path, task="detect")
    print(f"[OK] โหลดโมเดลสำเร็จใน {time.time() - t_start:.2f} วินาที! คลาส: {model.names}")

    # 2. เริ่มต้นระบบควบคุมล็อก
    lock_ctl = HelmetLockController(
        pin=args.relay_pin,
        active_low=args.active_low,
        unlock_duration=args.unlock_sec
    )

    # 3. เปิดกล้องแบบ Asynchronous Multi-threaded
    print("[2/3] กำลังเชื่อมต่อกล้อง...")
    try:
        cam = AsyncVideoCapture(src=args.source, width=args.cam_w, height=args.cam_h)
    except Exception as e:
        print(f"[ERROR] ไม่สามารถเปิดกล้องได้: {e}")
        lock_ctl.cleanup()
        return
    print("[OK] เชื่อมต่อกล้องสำเร็จ!")

    # 4. ลูปประมวลผลความเร็วสูง
    print("[3/3] ระบบพร้อมทำงานแล้ว! กำลังเริ่มตรวจจับแบบเรียลไทม์...")
    print("💡 กด 'q' ที่หน้าต่างกล้อง หรือ Ctrl+C บน Terminal เพื่อออก\n")

    consecutive_helmet_count = 0
    fps_smooth = 0.0
    prev_time = time.time()

    win_name = "Helmet AI - Pi 4 Fast Runner"
    if not args.headless:
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            # จับเวลาสำหรับคำนวณ FPS
            curr_time = time.time()
            dt = curr_time - prev_time
            prev_time = curr_time
            if dt > 0:
                current_fps = 1.0 / dt
                fps_smooth = (fps_smooth * 0.8) + (current_fps * 0.2)

            # รันโมเดล NCNN ด้วย imgsz ที่ปรับให้ไวสุดๆ บน Pi4
            results = model.predict(
                frame,
                imgsz=args.imgsz,
                conf=args.conf,
                verbose=False,
                device="cpu"
            )

            has_helmet = False
            has_no_helmet = False
            boxes_to_draw = []

            if len(results) > 0 and results[0].boxes is not None:
                for b in results[0].boxes:
                    cls_id = int(b.cls[0].item())
                    conf_score = float(b.conf[0].item())
                    box_xyxy = b.xyxy[0].cpu().numpy().astype(int)

                    class_name = model.names.get(cls_id, f"Class {cls_id}")
                    if "with-helmet" in class_name.lower() or cls_id == 0:
                        has_helmet = True
                    else:
                        has_no_helmet = True

                    boxes_to_draw.append((box_xyxy, class_name, conf_score, cls_id))

            # ตรวจสอบเงื่อนไขการสั่งปลดล็อก
            if has_helmet and not has_no_helmet:
                consecutive_helmet_count += 1
                if consecutive_helmet_count >= args.require_frames:
                    lock_ctl.unlock()
            else:
                consecutive_helmet_count = max(0, consecutive_helmet_count - 1)

            # หากเปิดโหมดแสดงผลหน้าจอ
            if not args.headless:
                display_frame = frame.copy()

                # วาดกรอบสี่เหลี่ยม
                for (x1, y1, x2, y2), cname, conf_score, cls_id in boxes_to_draw:
                    color = (0, 230, 0) if cls_id == 0 else (0, 50, 255)
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    label_text = f"{cname} {conf_score*100:.0f}%"
                    cv2.putText(display_frame, label_text, (x1, max(20, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

                # แถบแสดงสถานะด้านบน
                h, w, _ = display_frame.shape
                cv2.rectangle(display_frame, (0, 0), (w, 38), (20, 20, 20), -1)

                # FPS
                cv2.putText(display_frame, f"FPS: {fps_smooth:.1f} (Pi4 NCNN)", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

                # Lock Status
                if lock_ctl.is_unlocked:
                    status_str = "STATUS: UNLOCKED [OPEN]"
                    status_col = (0, 255, 0)
                else:
                    status_str = "STATUS: LOCKED [SAFE]"
                    status_col = (0, 70, 255)

                cv2.putText(display_frame, status_str, (w - 280, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_col, 2, cv2.LINE_AA)

                cv2.imshow(win_name, display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
            else:
                # โหมด Headless: พิมพ์ FPS สรุปทุกๆ 5 วินาที
                if int(curr_time) % 5 == 0:
                    status = "UNLOCKED" if lock_ctl.is_unlocked else "LOCKED"
                    print(f"\r[Pi4] FPS: {fps_smooth:.1f} | Helmet: {'YES' if has_helmet else 'NO '} | Lock: {status} ", end="")

    except KeyboardInterrupt:
        print("\n[INFO] ผู้ใช้สั่งหยุดการทำงาน (Ctrl+C)")
    finally:
        print("[INFO] กำลังปิดระบบและคืนค่าทรัพยากร...")
        cam.stop()
        lock_ctl.cleanup()
        if not args.headless:
            cv2.destroyAllWindows()
        print("[INFO] ปิดระบบเรียบร้อย ขอบคุณครับ!")


if __name__ == "__main__":
    main()
