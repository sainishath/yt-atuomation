---
name: youtube-automator
description: Generates and uploads vertical YouTube Shorts using local Python scripts.
---
## How to use it
You are responsible for writing the implementation logic for a YouTube Shorts automation pipeline. Follow these strict technical requirements:

1. **Tech Stack:** - Voice generation: `Piper TTS`
   - Subtitle generation & timestamps: `Whisper`
   - Video/Audio compilation: `FFmpeg` wrapper in Python

2. **Media Pipeline (`media_engine.py`):**
   - Accept a text script as input.
   - Generate audio via Piper.
   - Run the audio through Whisper to extract word-level timestamps.
   - Use FFmpeg to overlay the generated audio and burn the subtitles onto a background video. 
   - Ensure the FFmpeg command restricts subtitles to the middle 50% of the 9:16 frame (the "safe zone").

3. **Upload Logic (`uploader.py`):**
   - Handle the final payload for YouTube.
   - **Crucial Rule:** When configuring the YouTube upload node or API payload, you must require hashtags specifically (e.g., `#DeepLearning #Automation`) in the description and tag arrays, rather than using generic, comma-separated keywords.

4. **Orchestration (`main.py`):**
   - Read API keys and paths from `config.json`.
   - Execute the pipeline sequentially.
