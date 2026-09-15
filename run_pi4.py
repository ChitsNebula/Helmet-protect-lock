#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
🪖 HELMET PROTECT LOCK - PURE NCNN HIGH SPEED RUNNER FOR RASPBERRY PI 4
==============================================================================
สคริปต์ตรวจจับหมวกกันน็อกความเร็วสูงพิเศษ ปรับแต่งสำหรับ Raspberry Pi 4
- รันด้วย Pure NCNN C++ Binding (ไม่ต้องลง PyTorch หรือ Ultralytics ให้หนักเครื่อง!)
- ต้องการแค่: ncnn (5 MB), opencv และ numpy
- ระบบอ่านเฟรมกล้องแบบแยก Thread (Async Camera Capture) ไร้ดีเลย์
- ย่อขนาดภาพประมวลผล (imgsz 320 / 416 / 640) เพื่อรีด FPS สูงสุด 25 - 35+ FPS
- ระบบควบคุม Relay ปลดล็อกหมวกกันน็อกอัตโนมัติผ่าน GPIO เมื่อสวมหมวกถูกต้อง
==============================================================================
"""

import argparse
import os
import sys
import io

# ป้องกัน UnicodeEncodeError บน Windows Console
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
import time
import threading
import cv2
import numpy as np

# ปรับประสิทธิภาพสำหรับ Multi-core ARM Cortex-A72 บน Pi 4
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"

# 1. ตรวจสอบไลบรารี NCNN (พยายามใช้ Pure NCNN ก่อน เพื่อความเบาและเร็วสูงสุด)
USE_PURE_NCNN = False
USE_ULTRALYTICS = False

try:
    import ncnn
    USE_PURE_NCNN = True
except ImportError:
    try:
        from ultralytics import YOLO
        USE_ULTRALYTICS = True
    except ImportError:
        print("\n" + "=" * 60)
        print("❌ [ERROR] ยังไม่ได้ติดตั้งไลบรารี ncnn")
        print("👉 วิธีแก้: พิมพ์คำสั่งนี้ใน Terminal (ขนาดแค่ 5 MB เสร็จใน 3 วินาที!):")
        print("   pip3 install ncnn --no-deps")
        print("=" * 60 + "\n")
        sys.exit(1)

# นำเข้าไลบรารี GPIO (มี Mock Fallback หากไม่ได้รันบนบอร์ดจริง)
HAS_GPIO = False
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False


# ==============================================================================
# คลาสตรวจจับด้วย Pure NCNN Engine (เบา เร็ว ไม่ต้องพึ่ง PyTorch)
# ==============================================================================
class PureNCNNDetector:
    def __init__(self, model_dir, imgsz=320, num_threads=4):
        self.imgsz = imgsz
        self.names = {0: 'with-helmet', 1: 'without-helmet'}

        param_path = os.path.join(model_dir, "model.ncnn.param")
        bin_path = os.path.join(model_dir, "model.ncnn.bin")

        if not os.path.exists(param_path) or not os.path.exists(bin_path):
            raise FileNotFoundError(f"ไม่พบไฟล์ model.ncnn.param หรือ model.ncnn.bin ใน {model_dir}")

        self.net = ncnn.Net()
        self.net.opt.use_vulkan_compute = False
        self.net.opt.num_threads = num_threads
        self.net.load_param(param_path)
        self.net.load_model(bin_path)

        # ค่า Normalization สำหรับ YOLOv8 (RGB 0.0 - 1.0)
        self.mean_vals = [0.0, 0.0, 0.0]
        self.norm_vals = [1.0 / 255.0, 1.0 / 255.0, 1.0 / 255.0]

    def detect(self, frame, conf_thresh=0.45, iou_thresh=0.45):
        h_orig, w_orig = frame.shape[:2]

        # แปลง BGR เป็น RGB และย่อขนาดตาม imgsz
        in_mat = ncnn.Mat.from_pixels_resize(
            frame,
            ncnn.Mat.PixelType.PIXEL_BGR2RGB,
            w_orig,
            h_orig,
            self.imgsz,
            self.imgsz
        )
        in_mat.substract_mean_normalize(self.mean_vals, self.norm_vals)

        ex = self.net.create_extractor()
        ex.input("in0", in_mat)
        ret, out0 = ex.extract("out0")
        if ret != 0:
            return []

        out_arr = np.array(out0) # shape (6, num_anchors)
        preds = out_arr.T

        boxes = []
        confs = []
        class_ids = []

        scale_x = w_orig / self.imgsz
        scale_y = h_orig / self.imgsz

        for p in preds:
            cx, cy, w, h = p[:4]
            scores = p[4:]
            cls_id = int(np.argmax(scores))
            conf = float(scores[cls_id])

            if conf >= conf_thresh:
                x1 = int((cx - w / 2.0) * scale_x)
                y1 = int((cy - h / 2.0) * scale_y)
                bw = int(w * scale_x)
                bh = int(h * scale_y)
                boxes.append([x1, y1, bw, bh])
                confs.append(conf)
                class_ids.append(cls_id)

        if not boxes:
            return []

        indices = cv2.dnn.NMSBoxes(boxes, confs, conf_thresh, iou_thresh)
        results = []
        for idx in indices:
            i = idx[0] if isinstance(idx, (list, tuple, np.ndarray)) else idx
            x, y, w, h = boxes[i]
            x2 = x + w
            y2 = y + h
            cls_id = class_ids[i]
            results.append((
                (max(0, x), max(0, y), min(w_orig, x2), min(h_orig, y2)),
                self.names.get(cls_id, f"Class {cls_id}"),
                confs[i],
                cls_id
            ))
        return results


# ==============================================================================
# คลาสอ่านกล้องแบบ Asynchronous Multi-threading (ความเร็วสูงสุด ไร้ค้าง)
# ==============================================================================
class AsyncVideoCapture:
    def __init__(self, src=0, width=640, height=480):
        if str(src).isdigit():
            src = int(src)
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
# ระบบควบคุมรีเลย์ล็อกหมวกกันน็อก (GPIO Relay Controller)
# ==============================================================================
class HelmetLockController:
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
            initial_state = GPIO.HIGH if self.active_low else GPIO.LOW
            GPIO.output(self.pin, initial_state)
            print(f"[GPIO] ตั้งค่า RPi.GPIO Pin {self.pin} (Relay Locked) สำเร็จ")
        else:
            print(f"[GPIO MOCK] จำลองการทำงาน Relay Pin {self.pin} (ไม่ได้ต่อฮาร์ดแวร์จริง)")

    def unlock(self):
        with self.lock:
            if self.is_unlocked:
                return
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
# ฟังก์ชันหลักสำหรับรัน Real-time Detection
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="High-Speed Pure NCNN Helmet Detection for Raspberry Pi 4")
    parser.add_argument("--model", type=str, default="helmet_detector_ncnn_model", help="โฟลเดอร์โมเดล NCNN")
    parser.add_argument("--source", type=str, default="0", help="Camera Index (0) หรือ RTSP/HTTP URL")
    parser.add_argument("--imgsz", type=int, default=320, help="ขนาดภาพเข้า AI (320 = เร็วสุด ~30 FPS, 416 = ปานกลาง, 640 = คมสุด)")
    parser.add_argument("--conf", type=float, default=0.45, help="เกณฑ์ความมั่นใจ (Confidence Threshold)")
    parser.add_argument("--cam-w", type=int, default=640, help="ความกว้างภาพจากกล้อง (Default: 640)")
    parser.add_argument("--cam-h", type=int, default=480, help="ความสูงภาพจากกล้อง (Default: 480)")
    parser.add_argument("--relay-pin", type=int, default=17, help="หมายเลข GPIO Pin สำหรับคุม Relay (BCM 17)")
    parser.add_argument("--active-low", action="store_true", default=True, help="Relay ทำงานแบบ Active LOW")
    parser.add_argument("--unlock-sec", type=float, default=5.0, help="ระยะเวลาปลดล็อก (วินาที)")
    parser.add_argument("--require-frames", type=int, default=3, help="จำนวนเฟรมที่ต้องเห็นหมวกต่อเนื่องก่อนสั่งปลดล็อก")
    parser.add_argument("--headless", action="store_true", help="รันแบบไม่มีหน้าต่างแสดงผล (ประหยัดแรมและ CPU สูงสุด)")
    args = parser.parse_args()

    # ตรวจสอบพาธโมเดล
    model_path = args.model
    if not os.path.exists(model_path):
        for alt in ["best_ncnn_model", "helmet_detector_ncnn", "helmet_trained_bundle/helmet_detector_ncnn"]:
            if os.path.exists(alt):
                model_path = alt
                break
        else:
            print(f"[ERROR] ไม่พบโฟลเดอร์โมเดล NCNN: {args.model}")
            return

    engine_name = "Pure NCNN C++" if USE_PURE_NCNN else "Ultralytics NCNN"

    print("=" * 65)
    print(f"🚀 HELMET PROTECT LOCK - PI 4 FAST RUNNER ({engine_name})")
    print("=" * 65)
    print(f"📦 โมเดล NCNN     : {model_path}")
    print(f"⚡ ขนาดภาพ AI (imgsz): {args.imgsz}x{args.imgsz} (Speed Optimized)")
    print(f"📷 แหล่งภาพกล้อง   : {args.source} ({args.cam_w}x{args.cam_h})")
    print(f"🔌 Relay GPIO Pin : {args.relay_pin} (Active {'LOW' if args.active_low else 'HIGH'})")
    print(f"🖥️ แสดงหน้าต่างผลลัพธ์: {'ปิด (Headless Mode)' if args.headless else 'เปิด (GUI Display)'}")
    print("=" * 65)

    # 1. โหลดโมเดล
    print(f"[1/3] กำลังโหลดโมเดลด้วย {engine_name}...")
    t_start = time.time()
    if USE_PURE_NCNN:
        detector = PureNCNNDetector(model_path, imgsz=args.imgsz, num_threads=4)
    else:
        detector = YOLO(model_path, task="detect")
    print(f"[OK] โหลดโมเดลสำเร็จใน {time.time() - t_start:.2f} วินาที!")

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

    win_name = "Helmet AI - Pi 4 Pure NCNN Runner"
    if not args.headless:
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            curr_time = time.time()
            dt = curr_time - prev_time
            prev_time = curr_time
            if dt > 0:
                current_fps = 1.0 / dt
                fps_smooth = (fps_smooth * 0.8) + (current_fps * 0.2)

            has_helmet = False
            has_no_helmet = False
            boxes_to_draw = []

            # รันการตรวจจับ
            if USE_PURE_NCNN:
                detections = detector.detect(frame, conf_thresh=args.conf)
                for (x1, y1, x2, y2), class_name, conf_score, cls_id in detections:
                    if "with-helmet" in class_name.lower() or cls_id == 0:
                        has_helmet = True
                    else:
                        has_no_helmet = True
                    boxes_to_draw.append(((x1, y1, x2, y2), class_name, conf_score, cls_id))
            else:
                results = detector.predict(frame, imgsz=args.imgsz, conf=args.conf, verbose=False, device="cpu")
                if len(results) > 0 and results[0].boxes is not None:
                    for b in results[0].boxes:
                        cls_id = int(b.cls[0].item())
                        conf_score = float(b.conf[0].item())
                        box_xyxy = b.xyxy[0].cpu().numpy().astype(int)
                        class_name = detector.names.get(cls_id, f"Class {cls_id}")
                        if "with-helmet" in class_name.lower() or cls_id == 0:
                            has_helmet = True
                        else:
                            has_no_helmet = True
                        boxes_to_draw.append((box_xyxy, class_name, conf_score, cls_id))

            # เงื่อนไขการสั่งปลดล็อก
            if has_helmet and not has_no_helmet:
                consecutive_helmet_count += 1
                if consecutive_helmet_count >= args.require_frames:
                    lock_ctl.unlock()
            else:
                consecutive_helmet_count = max(0, consecutive_helmet_count - 1)

            # หน้าจอแสดงผล
            if not args.headless:
                display_frame = frame.copy()

                for (x1, y1, x2, y2), cname, conf_score, cls_id in boxes_to_draw:
                    color = (0, 230, 0) if cls_id == 0 else (0, 50, 255)
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    label_text = f"{cname} {conf_score*100:.0f}%"
                    cv2.putText(display_frame, label_text, (x1, max(20, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

                h, w, _ = display_frame.shape
                cv2.rectangle(display_frame, (0, 0), (w, 38), (20, 20, 20), -1)

                cv2.putText(display_frame, f"FPS: {fps_smooth:.1f} (Pi4 NCNN)", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

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
                if int(curr_time) % 5 == 0:
                    status = "UNLOCKED" if lock_ctl.is_unlocked else "LOCKED"
                    print(f"\r[Pi4] FPS: {fps_smooth:.1f} | Helmet: {'YES' if has_helmet else 'NO '} | Lock: {status} ", end="")

    except KeyboardInterrupt:
        print("\n[INFO] ผู้ใช้สั่งหยุดการทำงาน (Ctrl+C)")
    finally:
        print("[INFO] กำลังปิดระบบ...")
        cam.stop()
        lock_ctl.cleanup()
        if not args.headless:
            cv2.destroyAllWindows()
        print("[INFO] ปิดระบบเรียบร้อย ขอบคุณครับ!")


if __name__ == "__main__":
    main()
