#!/usr/bin/env python3
"""
AI Video Generation Pipeline (End-to-End Orchestrator)
Handles automated scriptwriting, voiceover extraction, vector stick-figure 
generation, animation rendering, and synchronization into a final .mp4 movie file.
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path
from typing import List

# ==============================================================================
# STEP 1: INITIALIZATION & SECURE ENVIRONMENT LOADER
# ==============================================================================
def check_and_install_dependencies():
    required_packages = {
        "dotenv": "python-dotenv",
        "openai": "openai",
        "pydantic": "pydantic",
        "moviepy": "moviepy==1.0.3"  # Fixed version for predictable rendering
    }
    for module_name, pip_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            print(f"[!] '{pip_name}' package missing. Installing now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

check_and_install_dependencies()

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip

# Explicitly load local credentials file
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("[✓] Loaded configurations from local '.env' file.")
else:
    print("[!] Warning: No '.env' file detected at root. Using system variables.")

# Extract Secure Tokens
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
STABILITY_KEY = os.getenv("STABILITY_KEY")
LUMA_KEY = os.getenv("LUMA_API_KEY")

# Layout Custom Parameters with Fallbacks
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace"))
VIDEO_CODEC = os.getenv("VIDEO_CODEC", "libx264")
OUTPUT_FPS = int(os.getenv("OUTPUT_FPS", 24))
DEFAULT_VOICE_ID = os.getenv("DEFAULT_VOICEOVER_ID", "21m00Tcm4TlvDq8ikWAM")

# Validate System Credentials
required_keys = {
    "OPENAI_API_KEY": OPENAI_KEY,
    "ELEVENLABS_API_KEY": ELEVENLABS_KEY,
    "STABILITY_KEY": STABILITY_KEY,
}
missing_keys = [k for k, v in required_keys.items() if not v or "your_" in v]
if missing_keys:
    print(f"\n[X] CRITICAL CONFIGURATION ERROR: Missing keys: {', '.join(missing_keys)}")
    print("Please populate your '.env' file before restarting execution.")
    sys.exit(1)

# Construct Asset Directories
audio_dir = WORKSPACE_DIR / "audio"
image_dir = WORKSPACE_DIR / "images"
video_dir = WORKSPACE_DIR / "videos"
for folder in [audio_dir, image_dir, video_dir]:
    folder.mkdir(parents=True, exist_ok=True)

# Define Pydantic Schema for the Script
class Scene(BaseModel):
    scene_id: int
    narration_text: str = Field(description="The spoken voiceover script for this scene.")
    visual_prompt: str = Field(description="Visual description for image generation. Must explicitly request a minimalist line art stick figure on a pure white background.")
    estimated_duration: float = Field(description="Estimated duration of speech. Keep between 4.0 to 6.0 seconds.")

class VideoBlueprint(BaseModel):
    topic: str
    scenes: List[Scene]

# ==============================================================================
# STEP 2: CORE CONTENT ENGINE (OpenAI structured JSON parsing)
# ==============================================================================
def generate_script(topic: str) -> VideoBlueprint:
    print(f"\n[1/5] Generating structured video script for: '{topic}'...")
    client = OpenAI(api_key=OPENAI_KEY)
    
    prompt = f"""
    Create a 3-scene video script explaining a critical financial blindspot or concept related to: "{topic}".
    The target aesthetic is a simple, highly engaging whiteboard sketch stick figure animation.
    Break the explanation down into 3 clear chronological progression scenes.
    Keep the narrative fast-paced, educational, and clear.
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional financial education explainer scriptwriter."},
            {"role": "user", "content": prompt}
        ],
        response_format=VideoBlueprint,
    )
    return completion.choices.message.parsed

# ==============================================================================
# STEP 3: AUDIO GENERATION PIPELINE (ElevenLabs API)
# ==============================================================================
def generate_audio(scene_id: int, text: str) -> Path:
    print(f"[2/5] Synthesizing narration track for Scene {scene_id}...")
    url = f"https://elevenlabs.io{DEFAULT_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    
    response = requests.post(url, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    
    file_path = audio_dir / f"scene_{scene_id}.mp3"
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path

# ==============================================================================
# STEP 4: VISUAL ASSET GENERATION (Stability AI Core API)
# ==============================================================================
def generate_image(scene_id: int, visual_prompt: str) -> Path:
    print(f"[3/5] Generating minimalist stick figure image for Scene {scene_id}...")
    url = "https://stability.ai"
    headers = {
        "authorization": f"Bearer {STABILITY_KEY}",
        "accept": "image/*"
    }
    # Forcing black ink vector styles via positive and negative parameters
    data = {
        "prompt": f"{visual_prompt}, clean black marker line drawing, simple icon style, cartoon vector art",
        "negative_prompt": "colors, shading, gradients, realistic textures, complex busy backgrounds, 3d render, shadows",
        "output_format": "png",
        "aspect_ratio": "16:9"
    }
    
    response = requests.post(url, headers=headers, files={"none": ""}, data=data, timeout=30)
    response.raise_for_status()
    
    file_path = image_dir / f"scene_{scene_id}.png"
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path

# ==============================================================================
# STEP 5: ASSET ANIMATION ENGINE WITH RUNWAY & LOCAL FALLBACKS
# ==============================================================================
def animate_image(scene_id: int, image_path: Path, duration: float) -> Path:
    print(f"[4/5] Running video animation pipeline for Scene {scene_id}...")
    output_video_path = video_dir / f"scene_{scene_id}.mp4"
    mock_hosted_url = f"https://your-storage-bucket.com{image_path.name}"
    
    # Tier 1: Luma Dream Machine
    if LUMA_KEY and "your_" not in LUMA_KEY:
        try:
            print("   -> Trying Tier 1: Luma Dream Machine API...")
            luma_url = "https://lumalabs.ai"
            headers = {"Authorization": f"Bearer {LUMA_KEY}", "Content-Type": "application/json"}
            data = {
                "prompt": "The vector lines animate naturally as if being hand-sketched on a whiteboard.",
                "keyframes": {"frame0": {"type": "image", "url": mock_hosted_url}}
            }
            res = requests.post(luma_url, json=data, headers=headers, timeout=15)
            res.raise_for_status()
            gen_id = res.json()["id"]
            
            start_time = time.time()
            while time.time() - start_time < 120:
                status_res = requests.get(f"{luma_url}/{gen_id}", headers={"Authorization": f"Bearer {LUMA_KEY}"})
                status_data = status_res.json()
                if status_data.get("state") == "completed":
                    video_bytes = requests.get(status_data["assets"]["video"]).content
                    with open(output_video_path, "wb") as f:
                        f.write(video_bytes)
                    print(f"   [✓] Tier 1 Success: Scene {scene_id} rendered via Luma.")
                    return output_video_path
                elif status_data.get("state") == "failed":
                    break
                time.sleep(15)
        except Exception as e:
            print(f"   [!] Tier 1 Failed: {e}")

    # Tier 2: Runway Gen-3 Fallback
    runway_key = os.getenv("RUNWAY_API_KEY")
    if runway_key:
        try:
            print("   -> Trying Tier 2: Runway Gen-3 API...")
            runway_url = "https://runwayml.com"
            headers = {"Authorization": f"Bearer {runway_key}", "Content-Type": "application/json"}
            data = {"image_url": mock_hosted_url, "prompt": "Whiteboard whiteboard animation.", "duration": int(duration)}
            res = requests.post(runway_url, json=data, headers=headers, timeout=15)
            res.raise_for_status()
            task_id = res.json()["id"]
            
            start_time = time.time()
            while time.time() - start_time < 120:
                status_res = requests.get(f"https://runwayml.com{task_id}", headers={"Authorization": f"Bearer {runway_key}"})
                status_data = status_res.json()
                if status_data["status"] == "SUCCEEDED":
                    video_bytes = requests.get(status_data["output"]).content
                    with open(output_video_path, "wb") as f:
                        f.write(video_bytes)
                    print(f"   [✓] Tier 2 Success: Scene {scene_id} rendered via Runway.")

==============================================================================WORKFLOW ORCHESTRATION GATEWAY==============================================================================
def main():
topic = sys.argv[1] if len(sys.argv) > 1 else "Lifestyle Creep"
# 1. Generate Narrative Scriptblueprint = generate_script(topic)audio_assets = []video_assets = []# 2. Iterate and generate scene assetsfor scene in blueprint.scenes:print(f"\n====== PROCESSING SCENE {scene.scene_id} ======")audio_path = generate_audio(scene.scene_id, scene.narration_text)audio_assets.append(audio_path)# Calculate narration audio duration for pacing downstreamvoice_duration = AudioFileClip(str(audio_path)).durationimage_path = generate_image(scene.scene_id, scene.visual_prompt)video_path = animate_image(scene.scene_id, image_path, voice_duration)video_assets.append(video_path)# 3. Master Mix Edit Assemblyassemble_final_video(blueprint, audio_assets, video_assets)if name == "main":main()