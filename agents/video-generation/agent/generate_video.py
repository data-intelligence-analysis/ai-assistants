import os
from pathlib import Path
import time
import requests
from moviepy.editor import ImageClip

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

import time
import requests
from pathlib import Path
from moviepy.editor import ImageClip

# ==============================================================================
# STEP 4: ASSET ANIMATION WITH MULTI-TIERED API & LOCAL FALLBACKS
# ==============================================================================
def animate_image(scene_id: int, image_path: Path, duration: float) -> Path:
    print(f"[4/5] Processing animation for Scene {scene_id}...")
    output_video_path = video_dir / f"scene_{scene_id}.mp4"
    
    # Mock hosted URL required by video APIs (Replace with real cloud storage URL in production)
    mock_hosted_url = f"https://your-storage-bucket.com{image_path.name}"
    
    # --------------------------------------------------------------------------
    # TIER 1: Primary Animation Engine (Luma Labs Dream Machine)
    # --------------------------------------------------------------------------
    try:
        print("   -> Attempting Tier 1: Luma Dream Machine API...")
        if not LUMA_KEY:
            raise ValueError("Luma API key not configured.")
            
        luma_url = "https://lumalabs.ai"
        headers = {"Authorization": f"Bearer {LUMA_KEY}", "Content-Type": "application/json"}
        data = {
            "prompt": "The minimalist stick figure animates smoothly on a pure white background, whiteboard style.",
            "keyframes": {"frame0": {"type": "image", "url": mock_hosted_url}}
        }
        
        response = requests.post(luma_url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        gen_id = response.json()["id"]
        
        # Poll Luma status with explicit timeout safety
        status_url = f"{luma_url}/{gen_id}"
        start_time = time.time()
        while time.time() - start_time < 120:  # 2 minute safety cutoff
            status_res = requests.get(status_url, headers={"Authorization": f"Bearer {LUMA_KEY}"})
            status_data = status_res.json()
            state = status_data.get("state")
            
            if state == "completed":
                video_url = status_data["assets"]["video"]
                video_bytes = requests.get(video_url).content
                with open(output_video_path, "wb") as f:
                    f.write(video_bytes)
                print(f"   [✓] Tier 1 Success: Scene {scene_id} rendered via Luma.")
                return output_video_path
            elif state == "failed":
                raise Exception("Luma rendering backend reported an internal failure.")
                
            time.sleep(10)
        raise TimeoutError("Luma generation timed out past 120 seconds.")
        
    except Exception as e:
        print(f"   [!] Tier 1 Failed: {e}")

    # --------------------------------------------------------------------------
    # TIER 2: Secondary Animation Engine (Runway Gen-3 Fallback)
    # --------------------------------------------------------------------------
    try:
        print("   -> Attempting Tier 2 Fallback: Runway Gen-3 API...")
        runway_key = os.getenv("RUNWAY_API_KEY")
        if not runway_key:
            raise ValueError("Runway API key not available in environment.")
            
        runway_url = "https://runwayml.com"
        headers = {"Authorization": f"Bearer {runway_key}", "Content-Type": "application/json"}
        data = {
            "image_url": mock_hosted_url,
            "prompt": "Continuous line art vector stick figure movements, slow cartoon whiteboard animation.",
            "duration": int(duration)
        }
        
        response = requests.post(runway_url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        task_id = response.json()["id"]
        
        # Poll Runway status
        status_url = f"https://runwayml.com{task_id}"
        start_time = time.time()
        while time.time() - start_time < 120:
            status_res = requests.get(status_url, headers={"Authorization": f"Bearer {runway_key}"})
            status_data = status_res.json()
            
            if status_data["status"] == "SUCCEEDED":
                video_url = status_data["output"][0]
                video_bytes = requests.get(video_url).content
                with open(output_video_path, "wb") as f:
                    f.write(video_bytes)
                print(f"   [✓] Tier 2 Success: Scene {scene_id} rendered via Runway.")
                return output_video_path
            elif status_data["status"] == "FAILED":
                raise Exception("Runway engineering pipeline failed.")
                
            time.sleep(10)
        raise TimeoutError("Runway generation timed out past 120 seconds.")
        
    except Exception as e:
        print(f"   [!] Tier 2 Failed: {e}")

    # --------------------------------------------------------------------------
    # TIER 3: Local Offline Fallback (MoviePy Dynamic Zoom & Ken Burns Effect)
    # --------------------------------------------------------------------------
    print("   -> Attempting Tier 3 Fallback: Generating local motion clips via MoviePy...")
    try:
        # Load the static image asset generated in Step 3
        static_clip = ImageClip(str(image_path)).set_duration(duration)
        
        # Apply a smooth whiteboard pan/zoom animation using a custom frame filter function
        # This keeps the image fluidly moving so it doesn't feel like a frozen slide
        animated_clip = static_clip.resize(lambda t: 1.0 + 0.04 * t)  # Subtle, continuous organic zoom-in
        
        # Export the freshly built local movie track
        animated_clip.write_videofile(
            str(output_video_path), 
            fps=OUTPUT_FPS, 
            codec=VIDEO_CODEC, 
            verbose=False, 
            logger=None
        )
        
        print(f"   [✓] Tier 3 Success: Scene {scene_id} compiled locally via Image-Pan engine.")
        return output_video_path
        
    except Exception as local_err:
        print(f"   [X] CRITICAL: All fallback mechanisms exhausted for Scene {scene_id}!")
        raise local_err

