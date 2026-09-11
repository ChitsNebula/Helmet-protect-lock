import os
import sys
import subprocess
import shutil
import zipfile

print("=" * 60)
print("=== Step 1: Checking & Installing Dependencies ===")
print("=" * 60)

try:
    import ultralytics
    print(f"[OK] Ultralytics already installed: v{ultralytics.__version__}")
except ImportError:
    print("[*] Installing ultralytics...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics"])
    import ultralytics
    print(f"[OK] Installed ultralytics: v{ultralytics.__version__}")

import torch
from ultralytics import YOLO

print("=" * 60)
print("=== Step 2: GPU Environment Check ===")
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU Device:", torch.cuda.get_device_name(0))
    print("Total GPU Memory:", f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
else:
    print("[WARNING] CUDA is not available. Training will run on CPU!")
print("=" * 60)

# 3. Clean & Extract Dataset
dataset_zip = "/content/dataset.zip"
extract_dir = "/content/dataset"

# Reassemble chunked dataset if present
if not os.path.exists(dataset_zip):
    part_files = sorted([f for f in os.listdir('/content') if f.startswith('dataset.part_')])
    if part_files:
        print(f"Reassembling {len(part_files)} chunks into {dataset_zip}...")
        with open(dataset_zip, 'wb') as outfile:
            for pf in part_files:
                p_path = os.path.join('/content', pf)
                with open(p_path, 'rb') as infile:
                    outfile.write(infile.read())
                os.remove(p_path)
        print(f"[OK] Reassembled {dataset_zip} ({os.path.getsize(dataset_zip)/(1024*1024):.2f} MB)")

if os.path.exists(extract_dir):
    shutil.rmtree(extract_dir)
os.makedirs(extract_dir, exist_ok=True)

if os.path.exists(dataset_zip):
    print(f"Extracting {dataset_zip} to {extract_dir}...")
    with zipfile.ZipFile(dataset_zip, 'r') as zip_ref:
        for member in zip_ref.namelist():
            normalized = member.replace('\\', '/')
            target_path = os.path.join(extract_dir, normalized)
            if normalized.endswith('/'):
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zip_ref.open(member) as src, open(target_path, 'wb') as dst:
                    dst.write(src.read())
    print("[OK] Dataset extracted and structure normalized successfully!")
else:
    print(f"[ERROR] {dataset_zip} not found in /content/!")

yaml_path = os.path.join(extract_dir, "data.yaml")
print(f"Checking data.yaml at: {yaml_path}")
if os.path.exists(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        print("--- data.yaml content ---")
        print(f.read())
        print("-------------------------")

train_img_dir = os.path.join(extract_dir, "train", "images")
valid_img_dir = os.path.join(extract_dir, "valid", "images")
print(f"Train images count: {len(os.listdir(train_img_dir)) if os.path.exists(train_img_dir) else 'NOT FOUND'}")
print(f"Valid images count: {len(os.listdir(valid_img_dir)) if os.path.exists(valid_img_dir) else 'NOT FOUND'}")

# 4. Train YOLOv8n (200 Epochs)
print("\n" + "=" * 60)
print("=== Step 3: Starting YOLOv8n Training (200 Epochs) ===")
print("=" * 60)

model = YOLO('yolov8n.pt')

results = model.train(
    data=yaml_path,
    epochs=200,
    imgsz=640,
    batch=16,
    patience=50,
    device=0 if torch.cuda.is_available() else 'cpu',
    project='/content/runs/detect',
    name='train',
    exist_ok=True,
    verbose=True,
    save=True
)

print("\n" + "=" * 60)
print("=== Step 4: Training Finished! Collecting Artifacts ===")
print("=" * 60)

weights_path = "/content/runs/detect/train/weights/best.pt"
if os.path.exists(weights_path):
    size_mb = os.path.getsize(weights_path) / (1024 * 1024)
    print(f"SUCCESS: Best model saved at {weights_path} ({size_mb:.2f} MB)")
    shutil.copy(weights_path, "/content/best.pt")
else:
    print("[ERROR] Best weights file not found!")

for chart_name in ["results.png", "confusion_matrix.png", "confusion_matrix_normalized.png", "F1_curve.png", "PR_curve.png"]:
    src_chart = os.path.join("/content/runs/detect/train", chart_name)
    if os.path.exists(src_chart):
        shutil.copy(src_chart, os.path.join("/content", chart_name))
        print(f"Copied {chart_name} to /content/{chart_name}")

# 5. Automatic NCNN Export
print("\n" + "=" * 60)
print("=== Step 5: Exporting Trained Model to NCNN Format ===")
print("=" * 60)

best_model = YOLO(weights_path)
ncnn_path = best_model.export(format="ncnn", imgsz=640)
print(f"Exported NCNN folder: {ncnn_path}")

zip_target = "/content/best_ncnn_model.zip"
with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(ncnn_path):
        for f in files:
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, ncnn_path)
            zipf.write(full_path, arcname)

print(f"Successfully zipped NCNN model to: {zip_target} ({os.path.getsize(zip_target)/1024/1024:.2f} MB)")
print("=" * 60)
print("=== ALL TRAINING & EXPORT TASKS COMPLETED SUCCESSFULLY! ===")
print("=" * 60)
