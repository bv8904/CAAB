import threading
import time
import customtkinter as ctk
import config
from process_manager import ProcessManager
from ml_engine import AgeClassifier
from camera_service import CameraService
from admin_auth import AdminAuth
from sound_manager import SoundManager
from ui_dashboard import CAAB_Dashboard
import datetime

def main():
    # Initialize Core Components
    pm = ProcessManager()
    pm.set_blocked_apps(config.BLOCKED_APPS)
    
    cam = CameraService()
    cam.start() # Start immediately for demo purposes
    ml = AgeClassifier()
    admin = AdminAuth()
    sound = SoundManager()

    # Initialize UI
    app = CAAB_Dashboard(pm, cam, admin, ml, sound)

    # Monitoring Thread Logic
    def monitoring_loop():
        # wait for UI to start a bit
        time.sleep(2)
        
        while app.running:
            # 1. Check for blocked apps
            active_blocked_process = pm.get_active_process_name()
            
            if active_blocked_process:
                app.safe_update_status(system_text=f"Detected: {active_blocked_process}", system_color="orange")
                
                # Check User Age
                is_child = False
                
                # Check Simulation Mode
                # Note: getting Tkinter vars from thread is also risky, but usually reading is okay-ish. 
                # Better to use a getter on the main thread, but for now we'll try reading directly.
                if app.simulation_mode.get():
                    is_child = app.simulation_child.get()
                    app.safe_update_status(user_text=f"Simulated: {'Child' if is_child else 'Adult'}")
                else:
                    # Real Detection
                    if not cam.is_running:
                        cam.start()
                        time.sleep(1) # Warmup
                    
                    frame = cam.get_frame()
                    if frame is not None:
                        prediction = ml.predict(frame)
                        is_child = (prediction == 0)
                        app.safe_update_status(user_text=f"Detected: {'Child' if is_child else 'Adult'}")
                    else:
                         app.safe_update_status(user_text="Camera Error")

                # Action
                if is_child:
                    # BLOCK
                    killed = pm.block_process(active_blocked_process)
                    if killed:
                        msg = f"Blocked {active_blocked_process}."
                        # app.log_message accesses GUI widget, need safe wrapper
                        app.after(0, lambda m=msg: app.log_message(m))
                        sound.play_alert()
                else:
                    # ALLOW
                    pass
                    
            else:
                app.safe_update_status(system_text="System: Active", system_color="green", user_text="Scanning...")
                
            time.sleep(1)

    # Start Monitoring Thread
    monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitor_thread.start()

    # Run UI Loop
    app.mainloop()

    # Cleanup
    cam.stop()

if __name__ == "__main__":
    main()
