## System Prompt

# SYSTEM PROMPT: AUTONOMOUS VIDEO GENERATION AGENT
You are an advanced autonomous DevOps and software automation engineer. Your goal is to build, run, and execute a local Python-based pipeline that automatically generates animated financial stick-figure explainer videos from a single user topic.

## 1. OPERATIONAL CORE
You have full access to execute terminal commands, write scripts, handle files, and install necessary packages. Do not just explain how to do it; you must write the scripts, run them, manage error logs, and produce the final `.mp4` video file in the workspace.

## 2. THE SYSTEM ARCHITECTURE TO BUILD

You must write and maintain an integrated Python workflow (`generate_video.py`) that implements this exact multi-stage engine:
1.  **Scripting Engine:** Call the OpenAI API (or Anthropic API) to create a 3-scene video blueprint returned as a strict JSON structure containing `narration_text` and `visual_prompt` strings.
2.  **Audio Engine:** Pass the narration strings to the ElevenLabs API to download separate scene `.mp3` voiceover files.
3.  **Image Generator:** Use Stability AI (or similar REST API) to generate static 16:9 minimalist stick figures. Enforce strict black-and-white vector aesthetics via negative prompting.
4.  **Animation Engine:** Send the generated static images to an Image-to-Video API (like Luma Dream Machine or Kling AI) to create short animated video clips.
5.  **Composition Engine:** Programmatically stitch the audio and animated clips together using the `MoviePy` Python library, matching video scene lengths perfectly to the voiceover audio length.

## 3. YOUR EXECUTION STEPS

When the user gives you a video topic, you must execute these steps sequentially without further prompting:

### Step 1: Environment Setup

Check for required Python dependencies (`openai`, `requests`, `moviepy`, `pydantic`). If missing, run the appropriate `pip install` commands in the environment. Verify that the required environment variables are active (`OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `STABILITY_KEY`, `LUMA_API_KEY`). If any are missing, alert the user immediately.

### Step 2: Write the Automation Code

Write a robust Python script named `generate_video.py` matching the system architecture. Include full error handling, API polling loops for the video generator, and automatic folder management (`./workspace/audio`, `./workspace/images`, `./workspace/videos`).

### Step 3: Run and Monitor Execution

Execute the script using the user's provided topic. Monitor the terminal outputs. If an API call fails or a library throws a compilation error (e.g., a `MoviePy` binary glitch), capture the stack trace, patch the code autonomously, and re-run.

### Step 4: Final Verification

Confirm the output file `final_explainer.mp4` has been successfully compiled and saved to disk. Present a summary of the generated scenes to the user.

## 4. CONSTRAINTS & BEHAVIOR

*   **Be Direct:** Do not output long textual tutorials. Create files, run commands, and report status.*   **Idempotency:** Cache completed steps so that if a video animation API takes too long or errors out, you can resume execution without re-billing the user for already-generated images or audio clips.
*   **Stick Figure Quality:** Programmatically append style keywords like `"clean black line art stick figure, isolated on pure white background, whiteboard style"` to every visual prompt sent to the image engine.

## 5. INITIALIZATION

Acknowledge this prompt by checking the system's current directory, listing any missing API keys, and asking the user for their first video topic.

------------------------------
## How to use this in your agentic workspace

   1. For Claude Code: Save the markdown block above as video_agent_prompt.md. Start your terminal session and initialize it by running:
   
   claude "Read video_agent_prompt.md and initialize yourself with these instructions. Tell me what API keys you need."
   
   2. For OpenInterpreter / OpenCode: Paste the prompt directly into your system profile settings or load it at launch:
   
   interpreter --system_message "$(cat video_agent_prompt.md)"
   
   
Once initialized, you can simply type: "Generate a stick figure video about 'Why high-interest credit cards are a blindspot'", and the agent will handle everything from code writing to video compiling.
Would you like me to help you set up a .env file template so your agent can safely access your API keys without exposing them in your terminal history?

Here is the structured .env template. You can copy this file directly into your project root directory.
Your agentic environment (Claude Code, OpenCode, or Open Interpreter) will look for this file to authenticate your API connections securely without exposing keys in your terminal logs or script history.
## The .env Configuration File
Create a file named .env in the exact folder where you are running your agent, and paste the following block into it:

# ==============================================================================
# SECURE ENVIRONMENT VARIABLES FOR AI VIDEO PIPELINE
# Save this file as '.env' in your root workspace directory.
# DO NOT COMMIT THIS FILE TO PUBLIC VERSION CONTROL (GIT).
# ==============================================================================

# 1. Core Script Generation Engine
# Required for generating structured JSON scene outlines and visual prompts.
OPENAI_API_KEY="your_openai_api_key_here"

# 2. Audio Generation Pipeline
# Required for synthesizing realistic text-to-speech narration audio files.
ELEVENLABS_API_KEY="your_elevenlabs_api_key_here"

# 3. Visual Asset Generation Engine
# Required for generating high-resolution, minimalist stick-figure sketches.
STABILITY_KEY="your_stability_api_key_here"

# 4. Advanced Video Animation Engine
# Required for transforming static sketch assets into moving cartoon clips.
LUMA_API_KEY="your_luma_labs_api_key_here"

# ==============================================================================
# OPTIONAL PIPELINE TUNING CONFIGURATIONS
# Modify these parameters to customize standard workspace performance.
# ==============================================================================
WORKSPACE_DIR="./workspace"
VIDEO_CODEC="libx264"
OUTPUT_FPS=24
DEFAULT_VOICEOVER_ID="21m00Tcm4TlvDq8ikWAM"

------------------------------
## How to use this with your AI Agent

   1. Paste your live keys inside the double quotes for each respective variable.
   2. Ensure you add .env to a .gitignore file if you are tracking your workspace using Git, to avoid accidentally publishing your secret credentials.
   3. Once created, you can prompt your agent like this:
   
   "Read the credentials inside the local .env file, install python-dotenv if needed, and run the video generation script for the topic: 'Hidden Bank Account Maintenance Fees'."
   
   
The agent will seamlessly extract the keys and run the backend script cleanly.
Would you like me to rewrite the Step 1 Initialization block of your Python code to automatically include python-dotenv handling so it loads these file variables natively?

Here is the updated Step 1 Initialization block that handles loading variables directly from your .env file.
This update utilizes python-dotenv to safely load variables into the system environment, handles configuration overrides seamlessly, and implements an automated configuration validation check to instantly flag any missing keys before the script consumes any compute time.
## The Updated Initialization Code
Replace the initialization block at the top of your generate_video.py script with this production-ready module:

```python
import os
from pathlib import Path
# ==============================================================================# STEP 1: INITIALIZATION & SECURE ENVIRONMENT LOADER# ==============================================================================try:
    from dotenv import load_dotenvexcept ImportError:
    import subprocess
    import sys
    print("[!] 'python-dotenv' package missing. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv
# Locate and explicitly load the local .env fileenv_path = Path('.') / '.env'if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("[✓] Found and loaded configuration variables from local '.env' file.")else:
    print("[!] Warning: No '.env' file detected at project root. Falling back to system variables.")
# Securely extract authenticated API configuration stringsOPENAI_KEY = os.getenv("OPENAI_API_KEY")ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")STABILITY_KEY = os.getenv("STABILITY_KEY")LUMA_KEY = os.getenv("LUMA_API_KEY")
# Extract optional layout custom parameters with reliable fallback defaultsWORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace"))VIDEO_CODEC = os.getenv("VIDEO_CODEC", "libx264")OUTPUT_FPS = int(os.getenv("OUTPUT_FPS", 24))DEFAULT_VOICE_ID = os.getenv("DEFAULT_VOICEOVER_ID", "21m00Tcm4TlvDq8ikWAM")
# Automated Pipeline Validation Checkrequired_keys = {
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
# Dynamically construct isolated asset cache foldersaudio_dir = WORKSPACE_DIR / "audio"image_dir = WORKSPACE_DIR / "images"video_dir = WORKSPACE_DIR / "videos"
for folder in [audio_dir, image_dir, video_dir]:
    folder.mkdir(parents=True, exist_ok=True)

print(f"[✓] Workspace verified. Build assets targeting folder: '{WORKSPACE_DIR}'\n")
```
------------------------------
## What Your Agent Gains From This Update

* Self-Healing Setup: If the agent runs this script in a fresh workspace, it will automatically run the pip install terminal logic for python-dotenv behind the scenes without failing.
* Fail-Fast Mechanism: If you forget to populate one of your keys, the agent will instantly catch the error string "your_" or an empty space and halt execution before making partial network requests.
* Centralized Controls: Your video editing frame rates (OUTPUT_FPS) and directory layouts are completely controlled out of the clean text configurations file.

Now that the initialization layer is secured, would you like me to rewrite the Step 4 Animation block to add a backup rendering strategy in case the Luma API undergoes a processing timeout or rate-limit error?


