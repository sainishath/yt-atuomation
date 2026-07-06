import os
import json
import random
import subprocess
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_DIR = "./data"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds/active")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PIPER_EXE = "C:/path/to/piper.exe"  # UPDATE THIS
PIPER_MODEL = "C:/path/to/en_US-lessac-medium.onnx" # UPDATE THIS

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_random_background():
    videos = [v for v in os.listdir(BACKGROUNDS_DIR) if v.endswith('.mp4')]
    if not videos:
        raise FileNotFoundError(f"No background videos found in {BACKGROUNDS_DIR}")
    return os.path.join(BACKGROUNDS_DIR, random.choice(videos))

@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        data = request.json
        script = data.get('script', '')
        hook = data.get('hook', '')
        cta = data.get('cta', '')
        video_id = data.get('video_id', f"vid_{int(datetime.now().timestamp())}")
        
        full_text = f"{hook}. {script}. {cta}"
        audio_path = os.path.join(OUTPUT_DIR, f"{video_id}.wav")
        video_output_path = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
        
        # 1. Generate TTS (Piper)
        # Command: echo "text" | piper --model model.onnx --output_file out.wav
        print(f"[*] Generating TTS for: {video_id}")
        piper_cmd = f'echo "{full_text}" | "{PIPER_EXE}" --model "{PIPER_MODEL}" --output_file "{audio_path}"'
        subprocess.run(piper_cmd, shell=True, check=True)

        # 2. Select Background
        bg_video = get_random_background()
        
        # 3. Simple FFmpeg Assembly (Background + Audio)
        # Note: This is a basic version. We can add complex captions/Whisper timing next.
        print(f"[*] Assembling video: {video_id}")
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1', '-i', bg_video,
            '-i', audio_path,
            '-shortest',
            '-map', '0:v:0', '-map', '1:a:0',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '192k',
            video_output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        return jsonify({
            "status": "success",
            "video_path": video_output_path,
            "video_id": video_id
        })

    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/upload_youtube', methods=['POST'])
def upload_youtube():
    # Placeholder for YouTube API Upload Logic
    # We will implement the actual Google API call in the next iteration
    data = request.json
    print(f"[*] Simulating YouTube Upload for: {data.get('video_path')}")
    return jsonify({
        "status": "success",
        "url": "https://youtube.com/shorts/placeholder",
        "message": "Video uploaded (simulated)"
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
