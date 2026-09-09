"""
Script สำหรับรันโมเดล YOLOv8 NCNN บน PC
รองรับทั้ง Real-time Webcam, ไฟล์ภาพ, โฟลเดอร์ภาพ และไฟล์วิดีโอ
"""

import argparse
import os
import sys
import time
import glob
import cv2
import numpy as np
from ultralytics import YOLO

# บังคับใช้ UTF-8 บน Windows Console
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# สีสำหรับแต่ละคลาส (BGR Format)
# 0: with-helmet -> สีเขียว (0, 255, 0)
# 1: without-helmet -> สีแดง (0, 0, 255)
CLASS_COLORS = {
    0: (0, 220, 0),      # เขียวสว่าง (ใส่หมวก)
    1: (0, 50, 255),     # แดงสด (ไม่ใส่หมวก)
}

CLASS_NAMES = {
    0: "with-helmet",
    1: "without-helmet"
}


def draw_styled_box(frame, box, conf, cls_id):
    """วาด Bounding Box และ Label แบบพรีเมียม สวยงาม ชัดเจน"""
    x1, y1, x2, y2 = map(int, box)
    color = CLASS_COLORS.get(cls_id, (255, 255, 0))
    cls_name = CLASS_NAMES.get(cls_id, f"Class {cls_id}")
    label = f"{cls_name} {conf:.2f}"

    # 1. วาดกรอบสี่เหลี่ยมหลัก
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # 2. วาดมุมกรอบหนาขึ้นเพื่อความสวยงาม (Corner markers)
    corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
    if corner_len > 0:
        cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, 4)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, 4)
        cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, 4)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, 4)
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, 4)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, 4)
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, 4)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, 4)

    # 3. วาดพื้นหลัง Label
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    font_thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

    label_y1 = max(0, y1 - text_h - 8)
    label_y2 = y1
    cv2.rectangle(frame, (x1, label_y1), (x1 + text_w + 10, label_y2), color, -1)

    # 4. เขียนข้อความ Label สีขาว
    cv2.putText(
        frame,
        label,
        (x1 + 5, y1 - 5),
        font,
        font_scale,
        (255, 255, 255),
        font_thickness,
        cv2.LINE_AA,
    )


def process_frame(model, frame, conf_threshold=0.5):
    """ส่งเฟรมเข้า NCNN Model แล้ววาดผลลัพธ์พร้อมนับสถิติ"""
    results = model.predict(source=frame, conf=conf_threshold, verbose=False, task='detect')
    res = results[0]
    
    count_with = 0
    count_without = 0

    if res.boxes is not None and len(res.boxes) > 0:
        for b in res.boxes:
            box = b.xyxy[0].cpu().numpy()
            conf = float(b.conf[0].cpu().numpy())
            cls_id = int(b.cls[0].cpu().numpy())

            if cls_id == 0:
                count_with += 1
            elif cls_id == 1:
                count_without += 1

            draw_styled_box(frame, box, conf, cls_id)

    return frame, count_with, count_without


def draw_hud(frame, fps, count_with, count_without):
    """วาดแถบข้อมูลสถิติ (HUD Header) ด้านบนของหน้าจอ"""
    h, w, _ = frame.shape
    # สร้างแถบดำโปร่งแสงด้านบน
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 40), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # FPS Info
    cv2.putText(
        frame,
        f"FPS: {fps:.1f} (NCNN CPU)",
        (15, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # Count Info
    stats_text = f"With Helmet: {count_with} | Without Helmet: {count_without}"
    cv2.putText(
        frame,
        stats_text,
        (w - 380, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def run_webcam_or_video(model, source, conf_thresh, save_path=None, flip=True):
    """รัน Real-time Detection ผ่าน Webcam หรือ Video"""
    is_cam = source.isdigit() or source == "0"
    src = int(source) if is_cam else source
    cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        print(f"[Error] ไม่สามารถเปิดแหล่งวิดีโอ: {source}")
        return

    # ตั้งค่าความละเอียดสำหรับ Webcam
    if is_cam:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    window_name = f"Helmet Detection - NCNN Realtime ({'Webcam' if is_cam else 'Video'})"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    writer = None
    if save_path:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(save_path, fourcc, fps_in, (w, h))

    prev_time = time.time()
    fps_smooth = 0.0
    mirror_mode = flip if is_cam else False

    print("\n" + "=" * 60)
    print(f"กำลังเริ่มรัน NCNN Inference บน {source}...")
    print("กดคีย์ 'm' เพื่อเปิด/ปิดโหมดกลับกระจก (Mirror Flip)")
    print("กดคีย์ 'q' หรือ 'ESC' ที่หน้าต่างแสดงผลเพื่อหยุดการทำงาน")
    print("=" * 60 + "\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # กลับด้านกล้องแนวนอน (Mirror View) สำหรับกล้องหน้า/Webcam
        if mirror_mode:
            frame = cv2.flip(frame, 1)

        # Process Detection
        frame, count_with, count_without = process_frame(model, frame, conf_thresh)

        # คำนวณ FPS
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        fps_smooth = fps_smooth * 0.9 + fps * 0.1

        # วาดแถบข้อมูล HUD
        draw_hud(frame, fps_smooth, count_with, count_without)

        if writer:
            writer.write(frame)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' or ESC
            break
        elif key == ord('m') or key == ord('M'):  # Toggle Mirror mode
            mirror_mode = not mirror_mode
            print(f"[Mirror Mode]: {'เปิด (ON)' if mirror_mode else 'ปิด (OFF)'}")

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    print("[Finished] ปิดการทำงานเรียบร้อย")


def run_image(model, source_path, conf_thresh, output_dir="runs/ncnn_predict"):
    """รัน Detection บนไฟล์ภาพเดี่ยว หรือโฟลเดอร์ภาพ"""
    os.makedirs(output_dir, exist_ok=True)

    if os.path.isdir(source_path):
        image_files = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
            image_files.extend(glob.glob(os.path.join(source_path, ext)))
    else:
        image_files = [source_path]

    if not image_files:
        print(f"[Error] ไม่พบไฟล์ภาพใน: {source_path}")
        return

    print(f"กำลังประมวลผลทั้งหมด {len(image_files)} ภาพ...")
    for idx, img_path in enumerate(image_files, 1):
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        t0 = time.time()
        frame, count_with, count_without = process_frame(model, frame, conf_thresh)
        proc_time = (time.time() - t0) * 1000

        draw_hud(frame, 1000.0 / proc_time if proc_time > 0 else 0, count_with, count_without)

        out_name = os.path.basename(img_path)
        save_file = os.path.join(output_dir, out_name)
        cv2.imwrite(save_file, frame)
        print(f"[{idx}/{len(image_files)}] {out_name} -> {proc_time:.1f}ms | With: {count_with}, Without: {count_without} -> บันทึกที่ {save_file}")

    print(f"\n[Success] ประมวลผลและบันทึกภาพทั้งหมดไว้ที่โฟลเดอร์: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="YOLOv8 NCNN Helmet Detection on PC")
    parser.add_argument("--model", type=str, default="best_ncnn_model", help="Path ไปยังโฟลเดอร์ NCNN Model")
    parser.add_argument("--source", type=str, default="0", help="0 สำหรับ Webcam, หรือ path ของภาพ/วิดีโอ/โฟลเดอร์ภาพ")
    parser.add_argument("--conf", type=float, default=0.45, help="Confidence threshold (ค่าความมั่นใจขั้นต่ำ 0.0 - 1.0)")
    parser.add_argument("--save", type=str, default=None, help="Path สำหรับบันทึกไฟล์ผลลัพธ์ (ภาพ/วิดีโอ)")
    parser.add_argument("--no-flip", action="store_true", help="ปิดการกลับด้านกล้อง (Disable Mirror Mode)")
    args = parser.parse_args()

    # 1. โหลดโมเดล NCNN
    if not os.path.exists(args.model):
        print(f"[Error] ไม่พบโฟลเดอร์โมเดล NCNN ที่: {args.model}")
        return

    print(f"[Info] กำลังโหลดโมเดล NCNN จาก: {args.model}...")
    model = YOLO(args.model, task="detect")
    print("[Info] โหลดโมเดล NCNN สำเร็จ พร้อมประมวลผล!")

    # 2. เลือกว่าจะรันแบบใด
    src = args.source
    if src.isdigit() or src.endswith((".mp4", ".avi", ".mkv", ".mov")):
        run_webcam_or_video(model, src, args.conf, args.save, flip=not args.no_flip)
    else:
        out_dir = args.save if args.save else "runs/ncnn_predict"
        run_image(model, src, args.conf, out_dir)


if __name__ == "__main__":
    main()
