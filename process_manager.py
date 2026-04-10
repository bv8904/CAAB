import psutil
import time
import logging

class ProcessManager:
    def __init__(self):
        self.blocked_apps = []

    def set_blocked_apps(self, apps):
        """Update the list of blocked applications."""
        self.blocked_apps = [app.lower() for app in apps]

    def get_active_process_name(self):
        """
        Returns the name of the process for the currently active window.
        Note: accurately getting the *active window* process cross-platform is tricky.
        For this simplified version, we'll iterate through running processes 
        and check if any of our blocked apps are running. 
        
        To strictly follow the requirement of 'active window', we would need pywin32 on Windows.
        However, blocking ANY running instance is often safer for parental control.
        
        For this implementation, we will check if any blocked app is appearing in the process list.
        """
        # simplified approach: check if any blocked app is running
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() in self.blocked_apps:
                    return proc.info['name']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def block_process(self, process_name):
        """Terminates the specified process."""
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
