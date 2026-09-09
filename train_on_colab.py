import os
import shutil
import zipfile
import torch
from ultralytics import YOLO

print("=" * 60)
print("=== Google Colab GPU Environment Check ===")
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU Device:", torch.cuda.get_device_name(0))
    print("Memory Allocated:", f"{torch.cuda.memory_allocated(0)/(1024**2):.2f} MB")
print("=" * 60)

# 1. Clean & Extract Dataset properly
dataset_zip = "/content/dataset.zip"
extract_dir = "/content/dataset"

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
    print("Dataset extracted and normalized successfully!")
else:
    print(f"Error: {dataset_zip} not found!")

yaml_path = os.path.join(extract_dir, "data.yaml")
print(f"Checking data.yaml at: {yaml_path}")
if os.path.exists(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        print("--- data.yaml ---")
        print(f.read())
        print("-----------------")

train_img_dir = os.path.join(extract_dir, "train", "images")
valid_img_dir = os.path.join(extract_dir, "valid", "images")
print(f"Train images count: {len(os.listdir(train_img_dir)) if os.path.exists(train_img_dir) else 'NOT FOUND'}")
print(f"Valid images count: {len(os.listdir(valid_img_dir)) if os.path.exists(valid_img_dir) else 'NOT FOUND'}")

# 2. Train YOLOv8n (50 Epochs)
print("\n" + "=" * 60)
print("=== Starting YOLOv8n Training (50 Epochs) on Tesla T4 ===")
print("=" * 60)

model = YOLO('yolov8n.pt')

results = model.train(
    data=yaml_path,
    epochs=50,
    imgsz=640,
    batch=16,
    device=0 if torch.cuda.is_available() else 'cpu',
    project='/content/runs/detect',
    name='train',
    exist_ok=True,
    verbose=True
)

print("\n" + "=" * 60)
print("=== Training Successfully Finished! ===")
weights_path = "/content/runs/detect/train/weights/best.pt"
if os.path.exists(weights_path):
    size_mb = os.path.getsize(weights_path) / (1024 * 1024)
    print(f"SUCCESS: Best model saved at {weights_path} ({size_mb:.2f} MB)")
else:
    print("Weights file not found at expected path.")

# 3. Automatic NCNN Export
print("\n" + "=" * 60)
print("=== Exporting Trained Model to NCNN Format ===")
print("=" * 60)

best_model = YOLO(weights_path)
ncnn_path = best_model.export(format="ncnn", imgsz=640)
print(f"Exported NCNN folder: {ncnn_path}")

# Zip NCNN model for easy download
zip_target = "/content/best_ncnn_model.zip"
with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(ncnn_path):
        for f in files:
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, ncnn_path)
            zipf.write(full_path, arcname)

print(f"Successfully zipped NCNN model to: {zip_target} ({os.path.getsize(zip_target)/1024/1024:.2f} MB)")
print("=" * 60)
print("=== ALL TRAINING & EXPORT TASKS FINISHED! ===")
print("=" * 60)
