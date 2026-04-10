import customtkinter as ctk
import tkinter as tk
from threading import Thread
import time
from PIL import Image, ImageTk
import cv2
import datetime
import config

class CAAB_Dashboard(ctk.CTk):
    def __init__(self, process_manager, camera_service, admin_auth, ml_engine, sound_manager):
        super().__init__()

        self.process_manager = process_manager
        self.camera_service = camera_service
        self.admin_auth = admin_auth
        self.ml_engine = ml_engine
        self.sound_manager = sound_manager

        # Window Setup
        self.title("CAAB - Context-Aware Application Blocker")
        self.geometry("900x600")
        ctk.set_appearance_mode(config.THEME_MODE)
        ctk.set_default_color_theme(config.THEME_COLOR)

        # State Variables
        self.running = True
        self.simulation_mode = tk.BooleanVar(value=False)
        self.simulation_child = tk.BooleanVar(value=True) # True=Child, False=Adult

        # Build UI
        self._setup_layout()
        
        # Hook Close Event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Start Update Loop
        self.after(100, self._update_ui)

    def _setup_layout(self):
        # Grid Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar (Navigation)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar_label = ctk.CTkLabel(self.sidebar, text="CAAB Control", font=ctk.CTkFont(size=20, weight="bold"))
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=20)

        # Tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_history = self.tab_view.add("History & Logs")
        self.tab_settings = self.tab_view.add("Settings")

        # --- Dashboard Tab ---
        self._build_dashboard_tab()

        # --- History Tab ---
        self._build_history_tab()

        # --- Settings Tab ---
        self._build_settings_tab()
    
    def _build_dashboard_tab(self):
        self.status_frame = ctk.CTkFrame(self.tab_dashboard)
        self.status_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_system = ctk.CTkLabel(self.status_frame, text="System: Active", text_color="green", font=("Arial", 16))
        self.lbl_system.pack(side="left", padx=20)
        
        self.lbl_user_status = ctk.CTkLabel(self.status_frame, text="Detected: Scanning...", font=("Arial", 16))
        self.lbl_user_status.pack(side="right", padx=20)

        # Camera Preview
        self.camera_frame = ctk.CTkFrame(self.tab_dashboard, width=400, height=300)
        self.camera_frame.pack(pady=20)
        self.lbl_camera = ctk.CTkLabel(self.camera_frame, text="Camera Feed Disabled")
        self.lbl_camera.pack(expand=True)

        # Simulation Controls
        self.sim_frame = ctk.CTkFrame(self.tab_dashboard)
        self.sim_frame.pack(pady=10)
        self.chk_sim = ctk.CTkSwitch(self.sim_frame, text="Enable Simulation Mode", variable=self.simulation_mode)
        self.chk_sim.pack(side="left", padx=10)
        self.rad_child = ctk.CTkRadioButton(self.sim_frame, text="Simulate Child", variable=self.simulation_child, value=True)
        self.rad_child.pack(side="left", padx=10)
        self.rad_adult = ctk.CTkRadioButton(self.sim_frame, text="Simulate Adult", variable=self.simulation_child, value=False)
        self.rad_adult.pack(side="left", padx=10)

    def _build_history_tab(self):
        self.history_box = ctk.CTkTextbox(self.tab_history, width=600, height=400)
        self.history_box.pack(padx=10, pady=10, expand=True, fill="both")
        self.history_box.insert("0.0", "--- Activity Log ---\n")
        self.history_box.configure(state="disabled")

    def _build_settings_tab(self):
        self.lbl_blocked = ctk.CTkLabel(self.tab_settings, text="Blocked Applications (One per line):")
        self.lbl_blocked.pack(pady=5)
        
        self.txt_blocked = ctk.CTkTextbox(self.tab_settings, height=200)
        self.txt_blocked.pack(padx=20, pady=5, fill="x")
        self.txt_blocked.insert("0.0", "\n".join(config.BLOCKED_APPS))

        self.btn_save = ctk.CTkButton(self.tab_settings, text="Save Settings", command=self._save_settings)
        self.btn_save.pack(pady=10)

        self.btn_exit = ctk.CTkButton(self.tab_settings, text="Exit App", fg_color="red", command=self._on_close)
        self.btn_exit.pack(pady=20)

    def _save_settings(self):
        if not self._prompt_pin():
            return
        
        raw_text = self.txt_blocked.get("0.0", "end")
        new_apps = [line.strip() for line in raw_text.split('\n') if line.strip()]
        config.BLOCKED_APPS = new_apps
        self.process_manager.set_blocked_apps(new_apps)
        self.log_message("Settings updated.")

    def _prompt_pin(self):
        dialog = ctk.CTkInputDialog(text="Enter Admin PIN:", title="Admin Auth")
        pin = dialog.get_input()
        if self.admin_auth.verify_pin(pin):
            return True
        else:
            tk.messagebox.showerror("Error", "Incorrect PIN")
            return False

    def log_message(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}\n"
        self.history_box.configure(state="normal")
        self.history_box.insert("end", full_msg)
        self.history_box.see("end")
        self.history_box.configure(state="disabled")

    def _update_ui(self):
        if not self.running:
            return

        # Update Camera Feed
        frame = self.camera_service.get_frame()
        if frame is not None:
            # Convert to Tkinter format
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((400, 300)) # logical size for preview
            tk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 300))
            self.lbl_camera.configure(image=tk_img, text="")
        else:
             self.lbl_camera.configure(text="Camera Active (No Frame)", image=None)

        self.after(50, self._update_ui)

    def safe_update_status(self, system_text=None, system_color=None, user_text=None):
        def _update():
            if system_text:
                self.lbl_system.configure(text=system_text)
            if system_color:
                self.lbl_system.configure(text_color=system_color)
            if user_text:
                self.lbl_user_status.configure(text=user_text)
        self.after(0, _update)

    def _on_close(self):
        if self._prompt_pin():
            self.running = False
            self.destroy()

