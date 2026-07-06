# -*- coding: utf-8 -*-
"""
main.py
-------
Generates a YouTube Short (video + thumbnail).
YOU upload it manually.

Usage:
    python main.py
    python main.py --topic "Why you yawn" --category "Weird Science"

Categories:
    "Weird Science"
    "Productivity & stoicism"
    "Human Behavior"
"""

import argparse
import json
import sys
import io
from pathlib import Path

# Force UTF-8 output so emoji/box-drawing print on Windows terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# -- config -------------------------------------------------------------------
_DIR      = Path(__file__).parent
with open(_DIR / "config.json", "r") as f:
    CFG = json.load(f)

OUTPUT_DIR = Path(CFG["output_dir"])
TEMP_DIR   = Path(CFG["temp_dir"])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

from media_engine import (
    generate_script,
    generate_voiceover,
    generate_subtitles,
    pick_background,
    assemble_video,
)
import requests

def check_ollama() -> bool:
    """Return True if Ollama is reachable."""
    try:
        r = requests.get(CFG.get("ollama_url", "http://localhost:11434") + "/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False



# =============================================================================
def _next_number() -> int:
    """Return the next Short number by scanning the videos folder."""
    existing = list(OUTPUT_DIR.glob("Short_*.mp4"))
    if not existing:
        return 1
    nums = []
    for p in existing:
        try:
            nums.append(int(p.stem.split("_")[1]))
        except (IndexError, ValueError):
            pass
    return max(nums) + 1 if nums else 1


# =============================================================================
def run_pipeline(topic: str, category: str, script_file: str = None, script_text: str = None, audio_file: str = None, voice: str = "en-US-BrianNeural") -> dict:
    """
    Full media pipeline. No uploading - that's your job.
    """
    num       = _next_number()
    label     = f"Short_{num:03d}"        # Short_001, Short_002 ...
    audio_raw = str(TEMP_DIR / f"{label}.wav")
    video_out = str(OUTPUT_DIR / f"{label}.mp4")
    thumb_out = str(OUTPUT_DIR / f"{label}_thumb.jpg")

    print("\n" + "=" * 60)
    print(f"  Topic    : {topic}")
    print(f"  Category : {category}")
    print(f"  Label    : {label}")
    print("=" * 60 + "\n")

    # 1/2. Generate or Load Script
    if script_file and Path(script_file).exists():
        with open(script_file, "r", encoding="utf-8") as f:
            full_text = f.read()
        hook = " ".join(full_text.split()[:4]) if full_text else "My Hook"
        body = full_text
        cta = ""
        print(f"[Manual Script] Loaded from {script_file}")
    elif script_text:
        full_text = script_text
        hook = " ".join(full_text.split()[:4]) if full_text else "My Hook"
        body = full_text
        cta = ""
        print("[Manual Script] Provided directly.")
    else:
        # Check Ollama
        if not check_ollama():
            print("[ERROR] Ollama is not running.")
            print("        Open a terminal and run:  ollama serve")
            sys.exit(1)

        # Generate script via Ollama
        script = generate_script(topic, category)
        hook, body, cta = script["hook"], script["body"], script["cta"]
        title = script.get("title", f"{hook} #Shorts")
        full_text = f"{hook} {body} {cta}"

    print(f"  HOOK : {hook}")
    print(f"  BODY : {body[:70]}...")
    print(f"  CTA  : {cta}\n")

    # 3. Audio / TTS
    if audio_file and Path(audio_file).exists():
        audio_path = str(Path(audio_file).absolute())
        print(f"[Manual Audio] Using provided audio file: {audio_path}")
    else:
        # Text -> speech (Google TTS + FFmpeg speed)
        audio_path = generate_voiceover(full_text, audio_raw, voice=voice)

    # 4. Speech -> word timestamps (Whisper)
    subtitle_data = generate_subtitles(audio_path)

    # 5. Pick background (random or sequential clip from long source)
    bg_path = pick_background(required_duration=subtitle_data["duration"])

    # 6. Assemble final 9:16 MP4 with burned subtitles
    assemble_video(bg_path, audio_path, subtitle_data, video_out, category)

    # -- Done -----------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  VIDEO READY")
    print(f"  Video     : {video_out}")
    print()
    print(f"  Label     : {label}")
    print(f"  Title     : {title}")
    print("=" * 60 + "\n")

    return {
        "video":  video_out,
        "title":  title,
        "script": {"hook": hook, "body": body, "cta": cta},
    }


# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Shorts video generator")
    parser.add_argument(
        "--topic",
        default="Why your brain forgets things on purpose",
        help="Topic for the Short",
    )
    parser.add_argument(
        "--category",
        default="Tech",
        choices=["Weird Science", "Productivity & stoicism", "Human Behavior", "Tech"],
        help="Content category",
    )
    parser.add_argument("--script_file", default=None, help="Path to manual script text file (skips Ollama)")
    parser.add_argument("--script_text", default=None, help="Manual script text string (skips Ollama)")
    parser.add_argument("--audio_file", default=None, help="Path to pre-generated audio file (skips TTS)")
    parser.add_argument("--voice", default="en-US-BrianNeural", help="Edge TTS voice to use")
    
    args = parser.parse_args()

    run_pipeline(
        topic=args.topic, 
        category=args.category,
        script_file=args.script_file,
        script_text=args.script_text,
        audio_file=args.audio_file,
        voice=args.voice
    )
