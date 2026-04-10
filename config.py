import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "caab_model.h5")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "warning_icon.png")

# Camera Settings
CAMERA_INDEX = 0  # Default camera
FRAME_SIZE = (224, 224)

# ML Settings
CONFIDENCE_THRESHOLD = 0.5

# Blocking Settings
BLOCKED_APPS = [
    "notepad.exe",
    "chrome.exe",
    "netflix.exe",
    "vlc.exe",
    "steam.exe",
    "epicgameslauncher.exe",
    "discord.exe"
]

# Admin Settings
ADMIN_PIN = "1234"  # Default PIN

# UI Settings
THEME_MODE = "Dark"
THEME_COLOR = "blue"
