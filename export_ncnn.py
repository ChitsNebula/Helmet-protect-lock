import os
import zipfile
from ultralytics import YOLO

print("=== Starting NCNN Export for YOLOv8n ===")
model_path = "/content/best.pt"
model = YOLO(model_path)

# Export to NCNN format
exported_path = model.export(format="ncnn", imgsz=640)
print(f"Exported NCNN folder: {exported_path}")

# Check files inside exported folder
if os.path.exists(exported_path):
    print("Files in exported NCNN folder:")
    for root, dirs, files in os.walk(exported_path):
        for f in files:
            p = os.path.join(root, f)
            print(f" - {os.path.relpath(p, exported_path)} ({os.path.getsize(p)} bytes)")

# Zip for download
zip_target = "/content/best_ncnn_model.zip"
with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(exported_path):
        for f in files:
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, exported_path)
            zipf.write(full_path, arcname)

print(f"Successfully compressed to: {zip_target} ({os.path.getsize(zip_target)/1024/1024:.2f} MB)")
print("=== NCNN Export Completed Successfully ===")
