# Video Generation Agent

## Overview

This repository contains tools to build video generation agent that supports growth across YouTube, TikTok, Instagram, Threads, and X. The goal is to automate idea generation, script creation, short-form video production, captioning, hashtags, and publishing strategies for social media channels.

## Goals

- Create social media videos quickly with AI-generated scripts, visuals, and audio.
- Optimize content for each platform’s format and audience.
- Automate publishing and performance tracking.
- Scale content creation while maintaining brand consistency.

## What this agent can do

- Generate video ideas based on trending topics and niches.
- Draft short and long-form scripts for reels, stories, and YouTube shorts.
- Create captions, titles, hashtags, and descriptions tailored to each platform.
- Produce simple AI-driven video content with clips, transitions, and voiceover.
- Build variations optimized for YouTube, TikTok, Instagram, Threads, and X.
- Suggest posting schedules and engagement prompts.

## Core components

- Idea discovery: trending topics, niche analysis, audience insights.
- Script writer: format-aware text generation for captions, scripts, descriptions.
- Visual generator: AI or template-based clip assembly for vertical and landscape video.
- Voice and audio: text-to-speech or narration generation.
- Platform adapter: rules for YouTube, TikTok, Instagram, Threads, X.
- Publishing planner: schedule, hashtags, cross-platform copy.

## Architecture


                       +-------------------------+

                       |       USER INPUT        |
                       | (Idea, Target Audience) |
                       +------------+------------+
                                    |
                                    v
+-----------------------------------------------------------------------+

| 1. CORE CONTENT ENGINE                                                |
|                                                                       |
|   +-------------------+     Prompt      +-------------------------+   |
|   |  Financial Topic  | --------------->|       ChatGPT / LLM     |   |
|   +-------------------+                 +------------+------------+   |
|                                                      |                |
|                                                      v                |
|                                         +-------------------------+   |
|                                         |  Structured Video Script|   |
|                                         | (Scenes, Visual Prompts)|   |
|                                         +------------+------------+   |
+------------------------------------------------------|----------------+
                                                       |
                             +-------------------------+-------------------------+

                             |                                                   |
                             v                                                   v
+--------------------------------------------+      +--------------------------------------------+

| 2. AUDIO GENERATION PIPELINE               |      | 3. VISUAL GENERATION PIPELINE              |
|                                            |      |                                            |
|   +------------------------------------+   |      |   +------------------------------------+   |
|   |          Dialogue / Script         |   |      |   |        Scene Visual Prompts        |   |
|   +-----------------+------------------+   |      |   +-----------------+------------------+   |
|                     |                      |      |                     |                      |
|                     v                      |      |                     v                      |
|   +------------------------------------+   |      |   +------------------------------------+   |
|   |      ElevenLabs (TTS Engine)       |   |      |   |  ImageFX / Midjourney (Image Gen)  |   |
|   +-----------------+------------------+   |      |   +-----------------+------------------+   |
|                     |                      |      |                     |                      |
|                     v                      |      |                     v                      |
|   +------------------------------------+   |      |   +------------------------------------+   |
|   |             Voiceover Audio File (.mp3)|   |  |   |      Static Stick Figure Asset     |   |
|   +-----------------+------------------+   |      |   +-----------------+------------------+   |
|                     |                      |      |                     |                      |
|                     |                      |      |                     v                      |
|                     |                      |      |   +------------------------------------+   |
|                     |                      |      |   |    Kling AI / Hailuo AI (Video Gen)|   |
|                     |                      |      |   +-----------------+------------------+   |
|                     |                      |      |                     |                      |
|                     |                      |      |                     v                      |
|                     |                      |      |   +------------------------------------+   |
|                     |                      |      |   |        Animated Video Clip (.mp4)  |   |
|                     |                      |      |   +-----------------+------------------+   |
+---------------------|----------------------+      +---------------------|----------------------+

                      |                                                   |
                      +-------------------------+-------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------+

| 4. VIDEO EDITING & SYNCHRONIZATION                                     |
|                                                                       |
|   +-------------------+                 +-------------------------+   |
|   |   Audio Track     | --------------> |      Video Editor       |   |
|   +-------------------+                 | (CapCut / Premiere Pro) |   |
|                                         +------------+------------+   |
|   +-------------------+                              ^                |
|   | Animated Clips    | -----------------------------+                |
|   +-------------------+                                               |
+------------------------------------------------------|----------------+
                                                       |
                                                       v
                                          +-------------------------+

                                          |   FINAL EXPLAINER VIDEO  |
                                          |         (.mp4)          |
                                          +-------------------------+

## System Components

* User Input: Defines the specific financial topic (e.g., hidden credit card fees).
* Core Content Engine: Uses a Large Language Model to turn abstract finance concepts into an ordered, scene-by-scene script.
* Audio Generation Pipeline: Translates the written script into spoken dialogue using Text-to-Speech (TTS).
* Visual Generation Pipeline: A two-stage process. First, it generates consistent static stick figures. Second, it uses an Image-to-Video model to animate them.
* Editing & Synchronization: The final assembly point. It matches the generated clip lengths to the pacing of the audio track.

## Key Data Formats

* Prompts: Text strings sent to the LLM and Image Generator.
* Assets: Static images (.png), audio voiceovers (.mp3), and raw animated clips (.mp4).
* Final Product: A fully synthesized video file ready for publishing.

## Recommended AI tools

- Large language models: content generation for ideas, titles, scripts, tags.
- Text-to-speech: fast voiceover for short videos and captions.
- Video APIs: assemble clips, transitions, text overlays, and motion.
- Analytics tools: performance signals for view growth and engagement.

## Build workflow

1. Collect audience and niche input.
2. Generate video concepts and hooks.
3. Create scripts and short-form copy.
4. Produce video assets and assemble final edits.
5. Generate platform-specific metadata.
6. Review and publish.
7. Track engagement and refine content.

## Platform-specific tips

YouTube
- Use strong hooks in the first 2-3 seconds.
- Optimize title and description for search and watch time.
- Prepare short-form clips for YouTube Shorts.

TikTok
- Focus on authenticity and trends.
- Leverage vertical format and fast pacing.
- Use hashtags and captions that match the niche.

Instagram
- Create Reels and Stories with engaging stickers and text.
- Keep messaging concise with a clear call-to-action.
- Use hashtags to reach discovery.

Threads
- Share short threads or text prompts that drive conversation.
- Link back to videos or clips when relevant.
- Use platform-native language and tags.

X
- Post video announcements with concise commentary.
- Use trending hashtags and relevant mentions.
- Leverage short clips and teasers for engagement.

## Best practices

- Keep videos short, engaging, and platform-appropriate.
- Test multiple variations and track performance.
- Reuse content across platforms with format-specific edits.
- Keep branding consistent while adapting style per network.
- Prioritize quality audio and clear visuals.

## Getting started

1. Install dependencies for AI models and video assembly.
2. Configure API keys for text generation, voice, and video services.
3. Define your niche, audience, and posting cadence.
4. Use the agent to generate ideas and assets.
5. Review generated content before publishing.


## System Prompt

# SYSTEM PROMPT: AUTONOMOUS VIDEO GENERATION AGENT
You are an advanced autonomous DevOps and software automation engineer. Your goal is to build, run, and execute a local Python-based pipeline that automatically generates animated financial stick-figure explainer videos from a single user topic.
## 1. OPERATIONAL COREYou have full access to execute terminal commands, write scripts, handle files, and install necessary packages. Do not just explain how to do it; you must write the scripts, run them, manage error logs, and produce the final `.mp4` video file in the workspace.
## 2. THE SYSTEM ARCHITECTURE TO BUILDYou must write and maintain an integrated Python workflow (`generate_video.py`) that implements this exact multi-stage engine:
1.  **Scripting Engine:** Call the OpenAI API (or Anthropic API) to create a 3-scene video blueprint returned as a strict JSON structure containing `narration_text` and `visual_prompt` strings.
2.  **Audio Engine:** Pass the narration strings to the ElevenLabs API to download separate scene `.mp3` voiceover files.3.  **Image Generator:** Use Stability AI (or similar REST API) to generate static 16:9 minimalist stick figures. Enforce strict black-and-white vector aesthetics via negative prompting.4.  **Animation Engine:** Send the generated static images to an Image-to-Video API (like Luma Dream Machine or Kling AI) to create short animated video clips.
5.  **Composition Engine:** Programmatically stitch the audio and animated clips together using the `MoviePy` Python library, matching video scene lengths perfectly to the voiceover audio length.
## 3. YOUR EXECUTION STEPSWhen the user gives you a video topic, you must execute these steps sequentially without further prompting:
### Step 1: Environment SetupCheck for required Python dependencies (`openai`, `requests`, `moviepy`, `pydantic`). If missing, run the appropriate `pip install` commands in the environment. Verify that the required environment variables are active (`OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `STABILITY_KEY`, `LUMA_API_KEY`). If any are missing, alert the user immediately.
### Step 2: Write the Automation CodeWrite a robust Python script named `generate_video.py` matching the system architecture. Include full error handling, API polling loops for the video generator, and automatic folder management (`./workspace/audio`, `./workspace/images`, `./workspace/videos`).
### Step 3: Run and Monitor ExecutionExecute the script using the user's provided topic. Monitor the terminal outputs. If an API call fails or a library throws a compilation error (e.g., a `MoviePy` binary glitch), capture the stack trace, patch the code autonomously, and re-run.
### Step 4: Final VerificationConfirm the output file `final_explainer.mp4` has been successfully compiled and saved to disk. Present a summary of the generated scenes to the user.
## 4. CONSTRAINTS & BEHAVIOR*   **Be Direct:** Do not output long textual tutorials. Create files, run commands, and report status.*   **Idempotency:** Cache completed steps so that if a video animation API takes too long or errors out, you can resume execution without re-billing the user for already-generated images or audio clips.
*   **Stick Figure Quality:** Programmatically append style keywords like `"clean black line art stick figure, isolated on pure white background, whiteboard style"` to every visual prompt sent to the image engine.
## 5. INITIALIZATIONAcknowledge this prompt by checking the system's current directory, listing any missing API keys, and asking the user for their first video topic.

------------------------------
## How to use this in your agentic workspace

   1. For Claude Code: Save the markdown block above as video_agent_prompt.md. Start your terminal session and initialize it by running:
   
   claude "Read video_agent_prompt.md and initialize yourself with these instructions. Tell me what API keys you need."
   
   2. For OpenInterpreter / OpenCode: Paste the prompt directly into your system profile settings or load it at launch:
   
   interpreter --system_message "$(cat video_agent_prompt.md)"
   
   
Once initialized, you can simply type: "Generate a stick figure video about 'Why high-interest credit cards are a blindspot'", and the agent will handle everything from code writing to video compiling.
Would you like me to help you set up a .env file template so your agent can safely access your API keys without exposing them in your terminal history?


## Notes

This README is a guide for building a social media video generation agent. Implementation details depend on the chosen AI services, content strategy, and publishing tools.



