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

# บังคับใช้ UTF-8 บน Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_available_cameras():
    """ค้นหารายชื่อและ index ของกล้องที่เชื่อมต่ออยู่จริงบนเครื่อง"""
    cam_names = []
    if sys.platform == "win32":
        try:
            import win32com.client
            wmi = win32com.client.GetObject("winmgmts:")
            devices = wmi.InstancesOf("Win32_PnPEntity")
            for d in devices:
                pnp = getattr(d, "PNPClass", "")
                if pnp in ["Camera", "Image"]:
                    name = getattr(d, "Name", "")
                    if name and name not in cam_names:
                        cam_names.append(name)
        except Exception:
            pass

    cams = []
    for i in range(6):
        opened = False
        if sys.platform == "win32":
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                opened = True
                cap.release()
        if not opened:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                opened = True
                cap.release()

        if opened:
            name = cam_names[i] if i < len(cam_names) else f"USB / Camera {i}"
            cams.append((i, f"📷 กล้อง {i}: {name}"))

    if not cams:
        cams.append((0, "📷 กล้อง 0: กล้องเริ่มต้น (Default)"))
    return cams


class HelmetAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Helmet AI Control Center - YOLOv8 NCNN")
        self.root.geometry("660x740")
        self.root.minsize(600, 700)
        self.root.configure(bg="#121418")

        # ตัวแปรสถานะ
        self.running_process = None
        self.camera_list = []      # list of (index, label)
        self.camera_map = {}       # label -> index
        self.selected_camera = tk.StringVar()
        self.selected_cap_camera = tk.StringVar()
        self.cam_status_text = tk.StringVar(value="กำลังสแกนหากล้อง...")

        self._setup_style()
        self._build_header()

        # สแกนกล้องครั้งแรก
        self._refresh_camera_list(initial=True)

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
        style.configure(
            "TCombobox",
            fieldbackground="#242B38",
            background="#2B3240",
            foreground="#FFFFFF",
            selectbackground=self.accent_blue,
            selectforeground="#FFFFFF",
            arrowcolor="#FFFFFF",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#242B38")],
            selectbackground=[("readonly", self.accent_blue)],
            selectforeground=[("readonly", "#FFFFFF")],
        )

        # ตั้งค่า Dropdown Listbox popup ให้เป็นโทนเข้ม
        self.root.option_add("*TCombobox*Listbox.background", "#242B38")
        self.root.option_add("*TCombobox*Listbox.foreground", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.accent_blue)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

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

    def _refresh_camera_list(self, initial=False):
        """สแกนและอัปเดตรายชื่อกล้องใน Dropdown"""
        cams = get_available_cameras()
        self.camera_list = cams
        self.camera_map = {label: idx for idx, label in cams}
        labels = [label for _, label in cams]

        prev_sel = self.selected_camera.get()
        if prev_sel in labels:
            self.selected_camera.set(prev_sel)
        else:
            self.selected_camera.set(labels[0] if labels else "")

        prev_cap_sel = self.selected_cap_camera.get()
        if prev_cap_sel in labels:
            self.selected_cap_camera.set(prev_cap_sel)
        else:
            self.selected_cap_camera.set(labels[0] if labels else "")

        self.cam_status_text.set(f"✓ ตรวจพบกล้องทั้งหมด {len(cams)} ตัว พร้อมใช้งาน")

        # อัปเดต Dropdown widget ถ้าสร้างเสร็จแล้ว
        if hasattr(self, "combo_cameras") and self.combo_cameras:
            self.combo_cameras["values"] = labels
        if hasattr(self, "combo_cap_cameras") and self.combo_cap_cameras:
            self.combo_cap_cameras["values"] = labels

        if not initial:
            messagebox.showinfo("สแกนกล้องเสร็จสิ้น", f"พบกล้องทั้งหมด {len(cams)} ตัว:\n\n" + "\n".join(labels))

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
            bg=self.card_bg, fg="#FFFFFF", selectcolor="#2B3240", font=("Segoe UI", 9),
            command=self._on_source_type_changed
        )
        r1.pack(side="left", padx=(0, 15))

        r2 = tk.Radiobutton(
            src_row, text="เลือกไฟล์ภาพ / วิดีโอ / โฟลเดอร์", variable=self.detect_source_type, value="file",
            bg=self.card_bg, fg="#FFFFFF", selectcolor="#2B3240", font=("Segoe UI", 9),
            command=self._on_source_type_changed
        )
        r2.pack(side="left")

        # Container กลางสำหรับสลับระหว่าง Webcam กับ File
        self.source_container = tk.Frame(container, bg=self.card_bg)
        self.source_container.pack(fill="x", padx=20, pady=(6, 10))

        # Frame 1: กล่องเลือกกล้อง Webcam (Combobox)
        self.frame_webcam_select = tk.Frame(self.source_container, bg=self.card_bg)
        self.frame_webcam_select.pack(fill="x")

        cam_box_row = tk.Frame(self.frame_webcam_select, bg=self.card_bg)
        cam_box_row.pack(fill="x")

        labels = [label for _, label in self.camera_list]
        self.combo_cameras = ttk.Combobox(
            cam_box_row,
            textvariable=self.selected_camera,
            values=labels,
            state="readonly",
            font=("Segoe UI", 9),
        )
        self.combo_cameras.pack(side="left", fill="x", expand=True, ipady=4)

        btn_rescan = tk.Button(
            cam_box_row,
            text="🔄 สแกนหากล้องใหม่",
            bg="#2B3240",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            command=lambda: self._refresh_camera_list(initial=False)
        )
        btn_rescan.pack(side="left", padx=(8, 0), ipady=3)

        lbl_cam_status = tk.Label(
            self.frame_webcam_select,
            textvariable=self.cam_status_text,
            font=("Segoe UI", 8),
            fg="#00E676",
            bg=self.card_bg
        )
        lbl_cam_status.pack(anchor="w", pady=(3, 0))

        # Frame 2: ช่องเลือกไฟล์ภาพ / วิดีโอ / โฟลเดอร์ (ซ่อนไว้ก่อน)
        self.frame_file_select = tk.Frame(self.source_container, bg=self.card_bg)

        self.detect_source_path = tk.StringVar(value="")
        file_box_row = tk.Frame(self.frame_file_select, bg=self.card_bg)
        file_box_row.pack(fill="x")

        self.entry_detect_path = tk.Entry(
            file_box_row,
            textvariable=self.detect_source_path,
            bg="#242B38",
            fg="#FFFFFF",
            insertbackground="white",
            font=("Segoe UI", 9)
        )
        self.entry_detect_path.pack(side="left", fill="x", expand=True, ipady=4)

        btn_browse_img = tk.Button(file_box_row, text="เลือกไฟล์...", bg="#333D4F", fg="#FFFFFF", font=("Segoe UI", 8), command=self._browse_detect_file)
        btn_browse_img.pack(side="left", padx=(6, 0))

        btn_browse_folder = tk.Button(file_box_row, text="เลือกโฟลเดอร์...", bg="#333D4F", fg="#FFFFFF", font=("Segoe UI", 8), command=self._browse_detect_folder)
        btn_browse_folder.pack(side="left", padx=(4, 0))

        # เลือกรุ่นโมเดล
        lbl_model = tk.Label(container, text="โมเดลที่ใช้ประมวลผล (Model):", font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_model.pack(anchor="w", padx=20, pady=(10, 5))

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

    def _on_source_type_changed(self):
        """สลับการแสดงผลระหว่างกล่องเลือกกล้อง กับช่องเลือกไฟล์"""
        stype = self.detect_source_type.get()
        if stype == "webcam":
            self.frame_file_select.pack_forget()
            self.frame_webcam_select.pack(fill="x")
        else:
            self.frame_webcam_select.pack_forget()
            self.frame_file_select.pack(fill="x")

    def _browse_detect_file(self):
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์ภาพหรือวิดีโอ",
            filetypes=[("Media Files", "*.jpg *.jpeg *.png *.mp4 *.avi *.mkv *.mov"), ("All Files", "*.*")]
        )
        if file_path:
            self.detect_source_path.set(file_path)
            self.detect_source_type.set("file")
            self._on_source_type_changed()

    def _browse_detect_folder(self):
        folder_path = filedialog.askdirectory(title="เลือกโฟลเดอร์ภาพ")
        if folder_path:
            self.detect_source_path.set(folder_path)
            self.detect_source_type.set("file")
            self._on_source_type_changed()

    def _start_detection(self):
        src_type = self.detect_source_type.get()
        if src_type == "webcam":
            cam_label = self.selected_camera.get()
            cam_idx = self.camera_map.get(cam_label, 0)
            source = str(cam_idx)
        else:
            source = self.detect_source_path.get().strip()
            if not source:
                messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกไฟล์ภาพ วิดีโอ หรือโฟลเดอร์ที่ต้องการตรวจจับ")
                return

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

    # ---------------- TAB 2: DATASET CAPTURE ----------------
    def _build_capture_tab(self, parent):
        container = tk.Frame(parent, bg=self.card_bg, highlightbackground=self.card_border, highlightthickness=1)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        title = tk.Label(container, text="ระบบถ่ายรูปเก็บ Dataset อัตโนมัติ (Hands-Free)", font=("Segoe UI", 11, "bold"), fg="#FFB300", bg=self.card_bg)
        title.pack(anchor="w", padx=20, pady=(15, 8))

        # กล่องเลือกกล้องสำหรับถ่าย Dataset
        lbl_cam = tk.Label(container, text="กล้องสำหรับถ่ายภาพ (Camera):", font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=self.card_bg)
        lbl_cam.pack(anchor="w", padx=20, pady=(2, 2))

        cam_row = tk.Frame(container, bg=self.card_bg)
        cam_row.pack(fill="x", padx=20, pady=(0, 10))

        labels = [label for _, label in self.camera_list]
        self.combo_cap_cameras = ttk.Combobox(
            cam_row,
            textvariable=self.selected_cap_camera,
            values=labels,
            state="readonly",
            font=("Segoe UI", 9),
        )
        self.combo_cap_cameras.pack(side="left", fill="x", expand=True, ipady=4)

        btn_rescan_cap = tk.Button(
            cam_row,
            text="🔄 สแกนใหม่",
            bg="#2B3240",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            command=lambda: self._refresh_camera_list(initial=False)
        )
        btn_rescan_cap.pack(side="left", padx=(8, 0), ipady=3)

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

        preset_row = tk.Frame(container, bg=self.card_bg)
        preset_row.pack(fill="x", padx=20, pady=(0, 10))

        self.cap_prefix = tk.StringVar(value="with_helmet")
        p1 = tk.Radiobutton(preset_row, text="with_helmet (ใส่หมวก)", variable=self.cap_prefix, value="with_helmet", bg=self.card_bg, fg="#00E676", selectcolor="#2B3240", font=("Segoe UI", 9))
        p1.pack(side="left", padx=(0, 20))

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

        cam_label = self.selected_cap_camera.get()
        cam_idx = self.camera_map.get(cam_label, 0)

        cmd = [
            sys.executable,
            os.path.join(BASE_DIR, "auto_capture.py"),
            "--output", out_dir,
            "--count", str(count),
            "--interval", str(interval),
            "--prefix", prefix,
            "--cam", str(cam_idx),
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
