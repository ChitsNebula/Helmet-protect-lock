import os, glob, shutil, zipfile

print("=" * 60)
print("=== Checking Colab Training Progress & Artifacts ===")
print("=" * 60)

csv_path = "/content/runs/detect/train/results.csv"
if os.path.exists(csv_path):
    with open(csv_path, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    total_epochs = len(lines) - 1
    print(f"[STATUS] Total Epochs completed: {total_epochs}")
    if total_epochs > 0:
        print("Header:", lines[0])
        print(f"Latest Epoch ({total_epochs}):", lines[-1])
else:
    print("[STATUS] results.csv not found yet.")

weights = glob.glob("/content/runs/detect/train/weights/*.pt")
print("Weights files found:", weights)

# Check if best.pt exists
best_pt = "/content/runs/detect/train/weights/best.pt"
if os.path.exists(best_pt):
    print(f"[OK] best.pt exists! Size: {os.path.getsize(best_pt)/(1024*1024):.2f} MB")
    shutil.copy(best_pt, "/content/best.pt")

# Copy charts
for chart in ["results.png", "confusion_matrix.png", "confusion_matrix_normalized.png", "F1_curve.png", "PR_curve.png"]:
    src = os.path.join("/content/runs/detect/train", chart)
    if os.path.exists(src):
        shutil.copy(src, f"/content/{chart}")
        print(f"[OK] Copied {chart} to /content/")

# Export NCNN if best.pt exists and best_ncnn_model.zip doesn't exist yet
if os.path.exists(best_pt) and not os.path.exists("/content/best_ncnn_model.zip"):
    print("[*] Exporting best.pt to NCNN format...")
    try:
        from ultralytics import YOLO
        model = YOLO(best_pt)
        ncnn_dir = model.export(format="ncnn", imgsz=640)
        print(f"[OK] NCNN exported to {ncnn_dir}")
        
        zip_target = "/content/best_ncnn_model.zip"
        with zipfile.ZipFile(zip_target, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(ncnn_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    arc = os.path.relpath(fp, ncnn_dir)
                    zipf.write(fp, arc)
        print(f"[OK] Zipped NCNN model ({os.path.getsize(zip_target)/(1024*1024):.2f} MB)")
    except Exception as e:
        print("[ERROR] NCNN export failed:", e)

print("=" * 60)
print("=== Progress Check Complete ===")
print("=" * 60)
