"""
Helmet Protect Lock - Modern Desktop GUI Control Center
ระบบควบคุมการตรวจจับหมวกกันน็อก (YOLOv8 NCNN) และถ่าย Dataset อัตโนมัติด้วยคลิกเดียว
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2

# บังคับใช้ UTF-8
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class HelmetAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Helmet AI Control Center - YOLOv8 NCNN")
        self.root.geometry("640x720")
        self.root.minsize(580, 680)
        self.root.configure(bg="#121418")

        # ตัวแปรสถานะ
        self.running_process = None

        self._setup_style()
        self._build_header()
        self._build_tabs()
        self._build_footer()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        # สีสไตล์ Dark Modern
        self.bg_dark = "#121418"
        self.card_bg = "#1B1F27"
        self.card_border = "#2B3240"
        self.accent_blue = "#3E6AE1"
        self.accent_green = "#00C853"
        self.accent_orange = "#FF9100"
        self.text_white = "#FFFFFF"
        self.text_gray = "#A0AAB8"

        style.configure("TNotebook", background=self.bg_dark, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#1E232E",
            foreground=self.text_white,
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.accent_blue)],
            foreground=[("selected", "#FFFFFF")],
        )

        style.configure("TLabel", background=self.card_bg, foreground=self.text_white, font=("Segoe UI", 10))
        style.configure("TEntry", fieldbackground="#242B38", foreground="#FFFFFF", bordercolor="#363E50")
        style.configure("TCombobox", fieldbackground="#242B38", foreground="#FFFFFF")

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg="#181C24", height=75)
        header_frame.pack(fill="x", padx=0, pady=0)

        title_label = tk.Label(
            header_frame,
            text="🪖 HELMET AI CONTROL CENTER",
            font=("Segoe UI", 15, "bold"),
            fg="#FFFFFF",
            bg="#181C24",
        )
        title_label.pack(anchor="w", padx=20, pady=(12, 2))

        subtitle = tk.Label(
            header_frame,
            text="YOLOv8 NCNN Real-time Detection & Auto Dataset Collector",
            font=("Segoe UI", 9),
            fg="#6C7A92",
            bg="#181C24",
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 10))

    def _build_tabs(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=15, pady=12)

        # Tab 1: ตรวจจับหมวกกันน็อก
        self.tab_detect = tk.Frame(notebook, bg=self.bg_dark)
        notebook.add(self.tab_detect, text="  🎯 ตรวจจับหมวกกันน็อก (NCNN)  ")
        self._build_detect_tab(self.tab_detect)

        # Tab 2: ถ่ายรูป Dataset อัตโนมัติ
        self.tab_capture = tk.Frame(notebook, bg=self.bg_dark)
        notebook.add(self.tab_capture, text="  📸 ถ่ายรูป Dataset อัตโนมัติ  ")
        self._build_capture_tab(self.tab_capture)

        # Tab 3: โมเดลและกราฟสถิติ
        self.tab_results = tk.Frame(notebook, bg=self.bg_dark)
        notebook.add(self.tab_results, text="  📊 ข้อมูลโมเดล & กราฟ  ")
        self._build_results_tab(self.tab_results)

    # ---------------- TAB 1: DETECT ----------------
    def _build_detect_tab(self, parent):
        container = tk.Frame(parent, bg=self.card_bg, highlightbackground=self.card_border, highlightthickness=1)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # แหล่งข้อมูลภาพ
        lbl_source = tk.Label(container, text="แหล่งภาพ / วิดีโอ (Source):", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_source.pack(anchor="w", padx=20, pady=(15, 5))

        self.detect_source_type = tk.StringVar(value="webcam")
        src_row = tk.Frame(container, bg=self.card_bg)
        src_row.pack(fill="x", padx=20, pady=2)

        r1 = tk.Radiobutton(
            src_row, text="กล้อง Webcam (สด)", variable=self.detect_source_type, value="webcam",
            bg=self.card_bg, fg="#FFFFFF", selectcolor="#2B3240", font=("Segoe UI", 9)
        )
        r1.pack(side="left", padx=(0, 15))

        r2 = tk.Radiobutton(
            src_row, text="เลือกไฟล์ภาพ / วิดีโอ / โฟลเดอร์", variable=self.detect_source_type, value="file",
            bg=self.card_bg, fg="#FFFFFF", selectcolor="#2B3240", font=("Segoe UI", 9)
        )
        r2.pack(side="left")

        # ช่องกรอก Path ไฟล์
        file_row = tk.Frame(container, bg=self.card_bg)
        file_row.pack(fill="x", padx=20, pady=(6, 12))

        self.detect_source_path = tk.StringVar(value="0")
        self.entry_detect_path = tk.Entry(file_row, textvariable=self.detect_source_path, bg="#242B38", fg="#FFFFFF", insertbackground="white", font=("Segoe UI", 9))
        self.entry_detect_path.pack(side="left", fill="x", expand=True, ipady=4)

        btn_browse_img = tk.Button(file_row, text="เลือกไฟล์...", bg="#333D4F", fg="#FFFFFF", font=("Segoe UI", 8), command=self._browse_detect_file)
        btn_browse_img.pack(side="left", padx=(6, 0))

        btn_browse_folder = tk.Button(file_row, text="เลือกโฟลเดอร์...", bg="#333D4F", fg="#FFFFFF", font=("Segoe UI", 8), command=self._browse_detect_folder)
        btn_browse_folder.pack(side="left", padx=(4, 0))

        # เลือกรุ่นโมเดล
        lbl_model = tk.Label(container, text="โมเดลที่ใช้ประมวลผล (Model):", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_model.pack(anchor="w", padx=20, pady=(5, 5))

        self.model_choice = tk.StringVar(value="best_ncnn_model")
        model_row = tk.Frame(container, bg=self.card_bg)
        model_row.pack(fill="x", padx=20, pady=(0, 12))

        m1 = tk.Radiobutton(
            model_row, text="best_ncnn_model (NCNN เร็วสุดบน CPU)", variable=self.model_choice, value="best_ncnn_model",
            bg=self.card_bg, fg="#00E676", selectcolor="#2B3240", font=("Segoe UI", 9, "bold")
        )
        m1.pack(anchor="w")

        m2 = tk.Radiobutton(
            model_row, text="best.pt (PyTorch ดั้งเดิม)", variable=self.model_choice, value="best.pt",
            bg=self.card_bg, fg="#82B1FF", selectcolor="#2B3240", font=("Segoe UI", 9)
        )
        m2.pack(anchor="w", pady=(2, 0))

        # Confidence Slider
        lbl_conf = tk.Label(container, text="ความมั่นใจขั้นต่ำ (Confidence):", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_conf.pack(anchor="w", padx=20, pady=(5, 2))

        conf_row = tk.Frame(container, bg=self.card_bg)
        conf_row.pack(fill="x", padx=20, pady=(0, 10))

        self.conf_val = tk.DoubleVar(value=0.45)
        self.conf_slider = tk.Scale(
            conf_row, from_=0.10, to=0.95, resolution=0.05, orient="horizontal",
            variable=self.conf_val, bg=self.card_bg, fg="#00E5FF", highlightthickness=0,
            troughcolor="#242B38", font=("Segoe UI", 8)
        )
        self.conf_slider.pack(fill="x")

        # Mirror Mode Checkbox
        self.flip_var = tk.BooleanVar(value=True)
        chk_flip = tk.Checkbutton(
            container, text="เปิดโหมดกระจก (Mirror Flip) สำหรับ Webcam",
            variable=self.flip_var, bg=self.card_bg, fg="#FFFFFF", selectcolor="#2B3240", font=("Segoe UI", 9)
        )
        chk_flip.pack(anchor="w", padx=20, pady=(0, 15))

        # Action Button
        self.btn_start_detect = tk.Button(
            container, text="▶️  เปิดกล้องตรวจจับหมวกกันน็อก (START)",
            bg="#00C853", fg="#FFFFFF", font=("Segoe UI", 11, "bold"),
            relief="flat", cursor="hand2", command=self._start_detection
        )
        self.btn_start_detect.pack(fill="x", padx=20, ipady=8, pady=(0, 10))

    def _browse_detect_file(self):
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์ภาพหรือวิดีโอ",
            filetypes=[("Media Files", "*.jpg *.jpeg *.png *.mp4 *.avi *.mkv *.mov"), ("All Files", "*.*")]
        )
        if file_path:
            self.detect_source_path.set(file_path)
            self.detect_source_type.set("file")

    def _browse_detect_folder(self):
        folder_path = filedialog.askdirectory(title="เลือกโฟลเดอร์ภาพ")
        if folder_path:
            self.detect_source_path.set(folder_path)
            self.detect_source_type.set("file")

    def _start_detection(self):
        src_type = self.detect_source_type.get()
        source = "0" if src_type == "webcam" else self.detect_source_path.get()
        model_name = self.model_choice.get()
        conf = self.conf_val.get()
        no_flip = not self.flip_var.get()

        model_path = os.path.join(BASE_DIR, model_name)
        if not os.path.exists(model_path):
            messagebox.showerror("ไม่พบโมเดล", f"ไม่พบไฟล์หรือโฟลเดอร์โมเดลที่:\n{model_path}")
            return

        cmd = [
            sys.executable,
            os.path.join(BASE_DIR, "run_ncnn.py"),
            "--model", model_path,
            "--source", source,
            "--conf", str(conf),
        ]
        if no_flip:
            cmd.append("--no-flip")

        threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True).start()

    # ---------------- TAB 2: CAPTURE ----------------
    def _build_capture_tab(self, parent):
        container = tk.Frame(parent, bg=self.card_bg, highlightbackground=self.card_border, highlightthickness=1)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        title = tk.Label(container, text="ระบบถ่ายรูปเก็บ Dataset อัตโนมัติ (Hands-Free)", font=("Segoe UI", 11, "bold"), fg="#FFB300", bg=self.card_bg)
        title.pack(anchor="w", padx=20, pady=(15, 10))

        # โฟลเดอร์ปลายทาง
        lbl_out = tk.Label(container, text="โฟลเดอร์สำหรับเซฟภาพ:", font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_out.pack(anchor="w", padx=20, pady=(2, 2))

        out_row = tk.Frame(container, bg=self.card_bg)
        out_row.pack(fill="x", padx=20, pady=(0, 10))

        self.cap_output_dir = tk.StringVar(value=os.path.join(BASE_DIR, "custom_dataset", "images"))
        entry_out = tk.Entry(out_row, textvariable=self.cap_output_dir, bg="#242B38", fg="#FFFFFF", insertbackground="white", font=("Segoe UI", 9))
        entry_out.pack(side="left", fill="x", expand=True, ipady=4)

        btn_browse_cap = tk.Button(out_row, text="เลือกโฟลเดอร์...", bg="#333D4F", fg="#FFFFFF", font=("Segoe UI", 8), command=self._browse_cap_folder)
        btn_browse_cap.pack(side="left", padx=(6, 0))

        # พรีเซตคลาส
        lbl_preset = tk.Label(container, text="คำนำหน้าชื่อภาพ (Class Prefix):", font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_preset.pack(anchor="w", padx=20, pady=(2, 2))

        self.cap_prefix = tk.StringVar(value="with_helmet")
        preset_row = tk.Frame(container, bg=self.card_bg)
        preset_row.pack(fill="x", padx=20, pady=(0, 10))

        p1 = tk.Radiobutton(preset_row, text="with_helmet (ใส่หมวก)", variable=self.cap_prefix, value="with_helmet", bg=self.card_bg, fg="#00E676", selectcolor="#2B3240", font=("Segoe UI", 9))
        p1.pack(side="left", padx=(0, 15))

        p2 = tk.Radiobutton(preset_row, text="without_helmet (ไม่ใส่หมวก)", variable=self.cap_prefix, value="without_helmet", bg=self.card_bg, fg="#FF5252", selectcolor="#2B3240", font=("Segoe UI", 9))
        p2.pack(side="left")

        # Grid สำหรับกำหนดตัวเลข
        grid_frame = tk.Frame(container, bg=self.card_bg)
        grid_frame.pack(fill="x", padx=20, pady=5)

        # จำนวนภาพ
        tk.Label(grid_frame, text="จำนวนภาพที่ต้องการถ่าย:", font=("Segoe UI", 9), fg="#FFFFFF", bg=self.card_bg).grid(row=0, column=0, sticky="w", pady=4)
        self.cap_count = tk.IntVar(value=50)
        spin_count = tk.Spinbox(grid_frame, from_=10, to=1000, increment=10, textvariable=self.cap_count, width=10, bg="#242B38", fg="#FFFFFF", insertbackground="white")
        spin_count.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        # เว้นกี่วิ
        tk.Label(grid_frame, text="เว้นระยะห่างต่อภาพ (วินาที):", font=("Segoe UI", 9), fg="#FFFFFF", bg=self.card_bg).grid(row=1, column=0, sticky="w", pady=4)
        self.cap_interval = tk.DoubleVar(value=1.5)
        spin_interval = tk.Spinbox(grid_frame, from_=0.5, to=10.0, increment=0.5, textvariable=self.cap_interval, width=10, bg="#242B38", fg="#FFFFFF", insertbackground="white")
        spin_interval.grid(row=1, column=1, sticky="w", padx=10, pady=4)

        # คำแนะนำ
        info_box = tk.Label(
            container,
            text="💡 ทริค: เมื่อกล้องเปิดขึ้นมา ระบบจะอยู่ในโหมด [PAUSED]\nให้คุณตั้งท่าให้พร้อม แล้วกด [SPACEBAR] กล้องจะเริ่มถ่ายอัตโนมัติทันที\n(กด 'c' ถ่ายทีละภาพ, กด 'm' สลับกระจก, 'q' เพื่อออก)",
            font=("Segoe UI", 8),
            fg="#90A4AE",
            bg="#1E232E",
            justify="left",
            padx=12,
            pady=8,
        )
        info_box.pack(fill="x", padx=20, pady=12)

        # ปุ่ม Start Capture
        btn_start_cap = tk.Button(
            container, text="📸  เปิดกล้องถ่ายภาพอัตโนมัติ (START CAPTURE)",
            bg="#3E6AE1", fg="#FFFFFF", font=("Segoe UI", 11, "bold"),
            relief="flat", cursor="hand2", command=self._start_capture
        )
        btn_start_cap.pack(fill="x", padx=20, ipady=8, pady=(0, 10))

        # ปุ่มเปิดโฟลเดอร์ภาพ
        btn_open_folder = tk.Button(
            container, text="📂  เปิดโฟลเดอร์ภาพที่ถ่ายเก็บไว้",
            bg="#2B3240", fg="#FFFFFF", font=("Segoe UI", 9),
            relief="flat", cursor="hand2", command=self._open_dataset_folder
        )
        btn_open_folder.pack(fill="x", padx=20, ipady=4)

    def _browse_cap_folder(self):
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์เก็บภาพ")
        if folder:
            self.cap_output_dir.set(folder)

    def _start_capture(self):
        out_dir = self.cap_output_dir.get()
        count = self.cap_count.get()
        interval = self.cap_interval.get()
        prefix = self.cap_prefix.get()

        cmd = [
            sys.executable,
            os.path.join(BASE_DIR, "auto_capture.py"),
            "--output", out_dir,
            "--count", str(count),
            "--interval", str(interval),
            "--prefix", prefix,
        ]
        threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True).start()

    def _open_dataset_folder(self):
        path = self.cap_output_dir.get()
        os.makedirs(path, exist_ok=True)
        os.startfile(path)

    # ---------------- TAB 3: RESULTS ----------------
    def _build_results_tab(self, parent):
        container = tk.Frame(parent, bg=self.card_bg, highlightbackground=self.card_border, highlightthickness=1)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_head = tk.Label(container, text="สรุปประสิทธิภาพโมเดลที่เทรนสำเร็จ", font=("Segoe UI", 11, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_head.pack(anchor="w", padx=20, pady=(15, 10))

        # ตารางผลลัพธ์
        metrics_frame = tk.Frame(container, bg="#1E232E", padx=15, pady=12)
        metrics_frame.pack(fill="x", padx=20, pady=5)

        metrics = [
            ("mAP50 Accuracy", "99.2%", "#00E676"),
            ("Precision", "98.2%", "#00E5FF"),
            ("Recall", "98.5%", "#FFD600"),
            ("NCNN Inference Speed", "~90 ms (CPU)", "#FF80AB"),
        ]

        for idx, (k, v, c) in enumerate(metrics):
            row_frame = tk.Frame(metrics_frame, bg="#1E232E")
            row_frame.pack(fill="x", pady=3)
            tk.Label(row_frame, text=k, font=("Segoe UI", 9), fg="#B0BEC5", bg="#1E232E").pack(side="left")
            tk.Label(row_frame, text=v, font=("Segoe UI", 10, "bold"), fg=c, bg="#1E232E").pack(side="right")

        # ปุ่มดูกราฟ
        btn_view_graph = tk.Button(
            container, text="📈  เปิดดูกราฟการเทรน (results.png)",
            bg="#2B3240", fg="#FFFFFF", font=("Segoe UI", 9),
            relief="flat", cursor="hand2", command=self._open_results_graph
        )
        btn_view_graph.pack(fill="x", padx=20, ipady=6, pady=(15, 6))

        btn_view_cm = tk.Button(
            container, text="🔍  เปิดดู Confusion Matrix (ความแม่นยำรายคลาส)",
            bg="#2B3240", fg="#FFFFFF", font=("Segoe UI", 9),
            relief="flat", cursor="hand2", command=self._open_cm_graph
        )
        btn_view_cm.pack(fill="x", padx=20, ipady=6, pady=(0, 6))

        btn_open_model_dir = tk.Button(
            container, text="📂  เปิดโฟลเดอร์โมเดล NCNN (best_ncnn_model)",
            bg="#2B3240", fg="#FFFFFF", font=("Segoe UI", 9),
            relief="flat", cursor="hand2", command=self._open_model_dir
        )
        btn_open_model_dir.pack(fill="x", padx=20, ipady=6)

    def _open_results_graph(self):
        p = os.path.join(BASE_DIR, "results.png")
        if os.path.exists(p):
            os.startfile(p)
        else:
            messagebox.showwarning("แจ้งเตือน", "ไม่พบไฟล์ results.png")

    def _open_cm_graph(self):
        p = os.path.join(BASE_DIR, "confusion_matrix.png")
        if os.path.exists(p):
            os.startfile(p)
        else:
            messagebox.showwarning("แจ้งเตือน", "ไม่พบไฟล์ confusion_matrix.png")

    def _open_model_dir(self):
        p = os.path.join(BASE_DIR, "best_ncnn_model")
        if os.path.exists(p):
            os.startfile(p)
        else:
            messagebox.showwarning("แจ้งเตือน", "ไม่พบโฟลเดอร์ best_ncnn_model")

    def _run_subprocess(self, cmd):
        try:
            self.running_process = subprocess.Popen(cmd)
            self.running_process.wait()
        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", str(e))
        finally:
            self.running_process = None

    def _build_footer(self):
        footer = tk.Frame(self.root, bg="#121418", height=30)
        footer.pack(fill="x", side="bottom", pady=6)
        tk.Label(footer, text="Helmet Protection System • Standalone GUI App", font=("Segoe UI", 8), fg="#546E7A", bg="#121418").pack()


if __name__ == "__main__":
    root = tk.Tk()
    app = HelmetAppGUI(root)
    root.mainloop()
