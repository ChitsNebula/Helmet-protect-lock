"""
Script สำหรับถ่ายรูปเก็บ Dataset อัตโนมัติผ่าน Webcam สำหรับนำไปเทรนโมเดล YOLO
คุณสมบัติ:
- กำหนดจำนวนภาพที่ต้องการถ่ายได้ (--count)
- กำหนดเวลาหน่วงระหว่างการถ่ายแต่ละภาพได้ (--interval)
- แสดงสถานะบนหน้าจอแบบเรียลไทม์ (จำนวนภาพที่ถ่ายไปแล้ว, Progress Bar, ตัวนับถอยหลัง)
- มีเอฟเฟกต์ Shutter Flash ตอนกดถ่ายภาพ
- สั่งเริ่ม/หยุดชั่วคราวได้ด้วยปุ่ม SPACEBAR
- กดปุ่ม 'c' เพื่อถ่ายช็อตเดี่ยวแบบแมนนวลได้
- กดปุ่ม 'm' เพื่อเปิด/ปิดโหมดกระจก (Mirror view)
"""

import argparse
import os
import sys
import time
import cv2

# บังคับใช้ UTF-8 บน Windows Console เพื่อป้องกัน UnicodeEncodeError
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def draw_header_hud(frame, status_text, status_color, progress_str, next_shot_str, mirror_mode):
    """วาด HUD แสดงสถานะและแถบความคืบหน้าด้านบนของหน้าจอ"""
    h, w, _ = frame.shape

    # 1. แถบพื้นหลังสีเข้มโปร่งแสง
    hud_h = 75
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, hud_h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # 2. ข้อความสถานะ (CAPTURING / PAUSED)
    cv2.putText(
        frame,
        status_text,
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        status_color,
        2,
        cv2.LINE_AA,
    )

    # 3. จำนวนภาพที่ถ่ายไปแล้ว (Progress)
    cv2.putText(
        frame,
        progress_str,
        (15, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # 4. เวลานับถอยหลังถ่ายภาพถัดไป
    if next_shot_str:
        cv2.putText(
            frame,
            next_shot_str,
            (w - 240, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 200, 0),
            2,
            cv2.LINE_AA,
        )

    # 5. ข้อมูลการควบคุมด้านล่างขวา
    mirror_label = f"Mirror: {'ON' if mirror_mode else 'OFF'}"
    cv2.putText(
        frame,
        mirror_label,
        (w - 240, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )


def draw_bottom_bar(frame, current, total):
    """วาดแถบ Progress Bar และปุ่มแนะนำการกดด้านล่าง"""
    h, w, _ = frame.shape
    bar_h = 35

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - bar_h), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # แถบ Progress Bar
    if total > 0:
        ratio = min(1.0, current / total)
        bar_w = int(w * ratio)
        cv2.rectangle(frame, (0, h - 5), (bar_w, h), (0, 220, 0), -1)

    # คำแนะนำปุ่ม
    helper_text = "[SPACE]: Start/Pause | [C]: Single Shot | [M]: Mirror | [Q/ESC]: Quit"
    cv2.putText(
        frame,
        helper_text,
        (15, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )


def main():
    parser = argparse.ArgumentParser(description="Auto Webcam Dataset Collector for YOLO")
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="custom_dataset/images",
        help="โฟลเดอร์สำหรับบันทึกภาพ (Default: custom_dataset/images)"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=50,
        help="จำนวนภาพทั้งหมดที่ต้องการถ่าย (Default: 50)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=1.5,
        help="เวลาหน่วงระหว่างการถ่ายแต่ละภาพ (วินาที) (Default: 1.5)"
    )
    parser.add_argument(
        "--prefix", "-p",
        type=str,
        default="helmet",
        help="คำนำหน้าชื่อไฟล์ เช่น helmet, person (Default: helmet)"
    )
    parser.add_argument(
        "--cam",
        type=int,
        default=0,
        help="ลำดับกล้อง Webcam (Default: 0)"
    )
    parser.add_argument(
        "--no-flip",
        action="store_true",
        help="ปิดโหมดกระจก (Disable Mirror Flip)"
    )
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # ค้นหา index ภาพที่มีอยู่เดิมเพื่อไม่ให้บันทึกทับ
    existing_files = [f for f in os.listdir(args.output) if f.startswith(args.prefix) and f.endswith((".jpg", ".png"))]
    img_counter = len(existing_files)

    cap = cv2.VideoCapture(args.cam)
    if not cap.isOpened():
        print(f"[Error] ไม่สามารถเปิดกล้อง Webcam index: {args.cam}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    window_name = "Auto Dataset Collector - YOLO"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    mirror_mode = not args.no_flip
    is_capturing = False
    captured_count = 0
    target_count = args.count
    interval = args.interval
    last_capture_time = time.time()
    flash_frames = 0

    print("=" * 60)
    print("=== Auto Dataset Collector เปิดทำงานแล้ว ===")
    print(f"บันทึกลงโฟลเดอร์ : {os.path.abspath(args.output)}")
    print(f"เป้าหมายจำนวนภาพ : {target_count} ภาพ")
    print(f"ระยะห่างต่อช็อต  : {interval} วินาที")
    print("-" * 60)
    print("ปุ่มควบคุม:")
    print("  [SPACE] : สั่ง เริ่มต้น (Start) / หยุดพักชั่วคราว (Pause)")
    print("  [C]     : ถ่ายรูป 1 ภาพทันที (Manual Capture)")
    print("  [M]     : สลับโหมดกระจก (Toggle Mirror Flip)")
    print("  [Q/ESC] : ออกจากโปรแกรม")
    print("=" * 60)

    while True:
        ret, raw_frame = cap.read()
        if not ret:
            print("[Warning] ไม่สามารถอ่านเฟรมจากกล้อง")
            break

        if mirror_mode:
            raw_frame = cv2.flip(raw_frame, 1)

        # เก็บ clean_frame สำหรับเซฟไฟล์ (ไม่มีตัวหนังสือ HUD ทับ)
        save_frame = raw_frame.copy()
        display_frame = raw_frame.copy()

        now = time.time()
        time_since_last = now - last_capture_time
        time_left = max(0.0, interval - time_since_last)

        trigger_capture = False

        # ตรวจสอบการถ่ายอัตโนมัติ
        if is_capturing:
            if captured_count >= target_count:
                is_capturing = False
                print(f"\n[Success] ถ่ายภาพครบตามเป้าหมาย {target_count} ภาพเรียบร้อยแล้ว!")
            elif time_since_last >= interval:
                trigger_capture = True

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # Q or ESC
            break
        elif key == 32:  # SPACEBAR
            is_capturing = not is_capturing
            if is_capturing:
                last_capture_time = time.time()
                print(f"[Status] เริ่มถ่ายภาพอัตโนมัติ (ทุกๆ {interval} วินาที)...")
            else:
                print("[Status] หยุดพักชั่วคราว (Paused)")
        elif key == ord('c') or key == ord('C'):  # Manual single capture
            trigger_capture = True
        elif key == ord('m') or key == ord('M'):  # Toggle mirror
            mirror_mode = not mirror_mode

        # ทำการบันทึกภาพ
        if trigger_capture and captured_count < target_count:
            img_counter += 1
            captured_count += 1
            filename = f"{args.prefix}_{img_counter:04d}_{int(time.time()*1000)%100000:05d}.jpg"
            save_path = os.path.join(args.output, filename)
            cv2.imwrite(save_path, save_frame)
            last_capture_time = time.time()
            flash_frames = 3  # แสดงแสงแฟลช 3 เฟรม

            progress_pct = (captured_count / target_count) * 100
            print(f"[Captured {captured_count}/{target_count}] ({progress_pct:.1f}%) -> บันทึก: {filename}")

            if captured_count >= target_count:
                is_capturing = False
                print(f"\n[Complete] บันทึกครบ {target_count} ภาพแล้ว! ไฟล์อยู่ที่ {args.output}")

        # เอฟเฟกต์ Shutter Flash สีขาว
        if flash_frames > 0:
            white_flash = 255 * (display_frame * 0 + 1)
            cv2.addWeighted(white_flash.astype(display_frame.dtype), 0.6, display_frame, 0.4, 0, display_frame)
            flash_frames -= 1

        # จัดเตรียมข้อความ HUD
        if captured_count >= target_count:
            status_text = "[COMPLETE - FINISHED]"
            status_color = (0, 255, 0)
            next_str = ""
        elif is_capturing:
            status_text = "[CAPTURING...]"
            status_color = (0, 255, 0)
            next_str = f"Next in: {time_left:.1f}s"
        else:
            status_text = "[PAUSED - Press SPACE]"
            status_color = (0, 165, 255)  # Orange
            next_str = "Paused"

        progress_str = f"Captured: {captured_count} / {target_count} ({int((captured_count/target_count)*100)}%)"

        draw_header_hud(display_frame, status_text, status_color, progress_str, next_str, mirror_mode)
        draw_bottom_bar(display_frame, captured_count, target_count)

        cv2.imshow(window_name, display_frame)

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[Summary] จบการทำงาน รวมถ่ายได้ทั้งหมด: {captured_count} ภาพ ในรอบนี้")
    print(f"โฟลเดอร์ไฟล์: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
