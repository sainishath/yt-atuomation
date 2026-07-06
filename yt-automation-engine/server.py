# -*- coding: utf-8 -*-
"""
server.py
---------
API Backend server bridging n8n automation requests to the upgraded media_engine pipeline.
Exposes /tts, /get-video, and /upload_youtube endpoints.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_file

# Ensure we can import from current directory
_DIR = Path(__file__).parent.resolve()
sys.path.append(str(_DIR))

from media_engine import (
    generate_voiceover,
    generate_subtitles,
    pick_background,
    assemble_video,
    CFG
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
TEMP_DIR = Path(CFG["temp_dir"])
OUTPUT_DIR = Path(CFG["output_dir"])
FINAL_VIDEO_PATH = OUTPUT_DIR / "final.mp4"

@app.route('/tts', methods=['POST'])
def tts():
    """
    Generate video from script and title.
    Expected payload:
    {
        "text": "full script text",
        "title": "on screen title",
        "category": "Weird Science" | "Productivity & stoicism" | "Human Behavior" | "Tech",
        "voice": "en-US-BrianNeural"
    }
    """
    try:
        data = request.json or {}
        text = data.get('text', '')
        title = data.get('title', 'MIND HACK')
        category = data.get('category', 'Tech')
        voice = data.get('voice', 'en-US-BrianNeural')

        if not text:
            return jsonify({"status": "error", "error": "No script text provided"}), 400

        logger.info(f"🎬 Starting video generation for title: '{title}'")
        logger.info(f"Category: {category} | Voice: {voice}")

        # 1. Generate voiceover (charismatic viral voice default)
        audio_raw = str(TEMP_DIR / "final_voice.wav")
        audio_path = generate_voiceover(text, audio_raw, voice=voice)

        # 2. Transcribe voiceover to get timing and duration
        subtitle_data = generate_subtitles(audio_path)

        # 3. Select background video clip
        bg_path = pick_background(required_duration=subtitle_data["duration"])

        # 4. Assemble final video with sidechain compression and bouncing subtitles
        assemble_video(bg_path, audio_path, subtitle_data, str(FINAL_VIDEO_PATH), category)

        logger.info(f"✓ Video generation complete: {FINAL_VIDEO_PATH}")
        return jsonify({
            "status": "success",
            "video_path": str(FINAL_VIDEO_PATH),
            "duration": subtitle_data["duration"]
        })

    except Exception as e:
        logger.error(f"✗ Video generation failed: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/get-video', methods=['GET'])
def get_video():
    """Serves the generated video file as binary download to n8n."""
    if not FINAL_VIDEO_PATH.exists():
        logger.error(f"✗ Video file not found: {FINAL_VIDEO_PATH}")
        return jsonify({"status": "error", "error": "Video file not found"}), 404
    return send_file(FINAL_VIDEO_PATH, mimetype='video/mp4', as_attachment=True, download_name="final.mp4")

@app.route('/upload_youtube', methods=['POST'])
def upload_youtube():
    """
    Exposes YouTube upload functionality.
    Expected payload:
    {
        "video_path": "/path/to/video.mp4" (optional),
        "title": "Video Title",
        "description": "Video Description",
        "tags": ["shorts", "trending"],
        "category_id": "27"
    }
    """
    try:
        data = request.json or {}
        video_path = data.get('video_path', str(FINAL_VIDEO_PATH))
        title = data.get('title', 'New Short')
        description = data.get('description', '#shorts')
        tags = data.get('tags', [])
        category_id = data.get('category_id', '27')

        from uploader import upload_to_youtube
        result = upload_to_youtube(video_path, title, description, tags, category_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"✗ YouTube upload failed: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """System health check endpoint."""
    return jsonify({
        "status": "ok",
        "ffmpeg_available": True,
        "backgrounds_dir_exists": Path(CFG["backgrounds_dir"]).exists(),
        "final_video_exists": FINAL_VIDEO_PATH.exists()
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    logger.info(f"🚀 Flask Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
