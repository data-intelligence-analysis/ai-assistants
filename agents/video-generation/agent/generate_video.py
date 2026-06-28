import os
from pathlib import Path

# ==============================================================================
# STEP 1: INITIALIZATION & SECURE ENVIRONMENT LOADER
# ==============================================================================
try:
    from dotenv import load_dotenv
except ImportError:
    import subprocess
    import sys
    print("[!] 'python-dotenv' package missing. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

# Locate and explicitly load the local .env file
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("[✓] Found and loaded configuration variables from local '.env' file.")
else:
    print("[!] Warning: No '.env' file detected at project root. Falling back to system variables.")

# Securely extract authenticated API configuration strings
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
STABILITY_KEY = os.getenv("STABILITY_KEY")
LUMA_KEY = os.getenv("LUMA_API_KEY")

# Extract optional layout custom parameters with reliable fallback defaults
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace"))
VIDEO_CODEC = os.getenv("VIDEO_CODEC", "libx264")
OUTPUT_FPS = int(os.getenv("OUTPUT_FPS", 24))
DEFAULT_VOICE_ID = os.getenv("DEFAULT_VOICEOVER_ID", "21m00Tcm4TlvDq8ikWAM")

# Automated Pipeline Validation Check
required_keys = {
    "OPENAI_API_KEY": OPENAI_KEY,
    "ELEVENLABS_API_KEY": ELEVENLABS_KEY,
    "STABILITY_KEY": STABILITY_KEY,
    "LUMA_API_KEY": LUMA_KEY
}

missing_keys = [key for key, value in required_keys.items() if not value or "your_" in value]

if missing_keys:
    print("\n[X] CRITICAL CONFIGURATION ERROR: Missing API credentials!")
    print(f"The pipeline cannot run because the following keys are unassigned: {', '.join(missing_keys)}")
    print("Please open your '.env' file, enter your live tokens, and restart the agent.")
    sys.exit(1)

# Dynamically construct isolated asset cache folders
audio_dir = WORKSPACE_DIR / "audio"
image_dir = WORKSPACE_DIR / "images"
video_dir = WORKSPACE_DIR / "videos"

for folder in [audio_dir, image_dir, video_dir]:
    folder.mkdir(parents=True, exist_ok=True)

print(f"[✓] Workspace verified. Build assets targeting folder: '{WORKSPACE_DIR}'\n")
