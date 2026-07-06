# 🚀 COMPLETE SETUP GUIDE: YouTube Shorts Automation Pipeline

## Overview
Your final system:
- **Input:** Google Sheets (topics)
- **Processing:** n8n (orchestration) → Gemini (scripts) → Piper (audio) → Flask (video)
- **Output:** YouTube Shorts (automated upload)
- **Updates:** Results logged back to Sheets

---

## ✅ PRE-SETUP CHECKLIST

Before you start, verify you have:

```
[ ] Piper TTS installed locally
    Run: piper --help
    If not: pip install piper-tts

[ ] FFmpeg installed and in PATH
    Run: ffmpeg -version
    If not: Download from ffmpeg.org or brew install ffmpeg

[ ] Faster Whisper installed
    Run: pip install faster-whisper
    
[ ] Python 3.9+ installed
    Run: python --version

[ ] n8n running (local or cloud)
    Run: npm install -g n8n && n8n start

[ ] YouTube API credentials (you said you have this)
    File: youtube_credentials.json (in your project root)

[ ] Google Sheets API credentials
    Create in Google Cloud Console if not done
```

---

## 📋 STEP 1: Prepare Your Directories

```bash
# Create folder structure
mkdir -p D:\piper\assets\backgrounds\active
mkdir -p D:\piper\assets\backgrounds\archive
mkdir -p D:\piper\output
mkdir -p D:\piper\temp

# Download 3-5 background videos and place in:
# D:\piper\assets\backgrounds\active\
# 
# Good sources:
# - Subway Surfers (TikTok/YouTube clips)
# - GTA V gameplay
# - Nature scenes
# - ASMR content
# - Minecraft parkour
#
# Make sure they're at least 60 seconds long
```

**What to download:** Look for trending short-form videos on TikTok/YouTube that:
- Have good visual movement
- High contrast (not washed out)
- 60+ seconds duration
- 9:16 aspect ratio preferred (we'll crop/pad anyway)

---

## 🔑 STEP 2: Set Up YouTube API (You Have This, But Let's Verify)

1. **Get Credentials File:**
   ```
   Go to: Google Cloud Console
   Project: Create New Project (or use existing)
   APIs: Enable "YouTube Data API v3"
   Credentials: OAuth 2.0 Desktop App
   Download: JSON file → Save as `youtube_credentials.json` in project root
   ```

2. **Place in Project Root:**
   ```
   D:\piper\
   ├── youtube_credentials.json
   ├── server_enhanced.py
   └── ...
   ```

---

## 📊 STEP 3: Set Up Google Sheet

1. **Create New Google Sheet**
   - Go to sheets.google.com
   - Create new spreadsheet
   - Name it: "YouTube Shorts Pipeline"

2. **Set Up Sheet Tabs & Columns**
   
   **Tab 1: "Topics Queue"**
   ```
   A | B                          | C                    | D           | E              | F           | G
   ----------|------|-----|----|----|----|----|---
   Day       | Category             | Topic                | Hook        | Script Status  | Video Status| YouTube URL
   Monday    | Weird Science        | Why we yawn          | (blank)     | (blank)        | (blank)     | (blank)
   Tuesday   | Productivity...      | Morning routine hack | (blank)     | (blank)        | (blank)     | (blank)
   ...
   ```

3. **Get Your Sheet ID:**
   ```
   URL: sheets.google.com/spreadsheets/d/[SHEET_ID]/edit
   Copy: [SHEET_ID] value for n8n configuration
   ```

4. **Share Sheet with Service Account (if using):**
   - Or just use OAuth (simpler for your setup)

---

## 🔧 STEP 4: Install Enhanced Server

1. **Copy server code:**
   ```bash
   # Copy server_enhanced.py to your project
   cp server_enhanced.py D:\piper\server.py
   ```

2. **Install dependencies:**
   ```bash
   pip install flask google-auth-oauthlib google-auth-httplib2 google-api-python-client
   pip install pillow numpy opencv-python
   ```

3. **Test the server:**
   ```bash
   python server.py
   
   # Should see:
   # 🚀 Flask server starting...
   # WARNING in werkzeug: ... Running on http://localhost:5000
   ```

4. **Test health endpoint:**
   ```bash
   curl http://localhost:5000/health
   
   # Should return:
   # {
   #   "status": "ok",
   #   "piper_available": true,
   #   "ffmpeg_available": true,
   #   "backgrounds_available": true
   # }
   ```

---

## 🔗 STEP 5: Set Up n8n Workflow

### 5a. Create Credentials in n8n

**Google Sheets:**
1. n8n Admin → Credentials → New
2. Type: "Google Sheets"
3. Connect your Google account
4. Name: "Google Sheets - YouTube"

**YouTube (OAuth):**
1. Credentials → New
2. Type: "Google OAuth2"
3. Client ID: From youtube_credentials.json
4. Client Secret: From youtube_credentials.json
5. Scopes: `https://www.googleapis.com/auth/youtube.upload`
6. Name: "YouTube Upload"

### 5b. Import Workflow Template

Instead of building from scratch, create these nodes:

**Node 1: Cron Trigger**
- Type: Cron
- Time: Every day at 9:00 AM
- Days: Mon-Fri

**Node 2: Google Sheets (Read)**
- Type: Google Sheets
- Credential: Google Sheets - YouTube
- Operation: Read
- Sheet ID: [Your sheet ID]
- Sheet Name: "Topics Queue"
- Range: A:J
- Read all: Yes

**Node 3: Function (Extract Today's Row)**
```javascript
// Get today's day name
const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });

// Find matching row
const rows = $json;
const todayRow = rows.find(row => row['Day'] === today);

if (!todayRow) {
  return {
    error: `No topic found for ${today}`
  };
}

return {
  day: todayRow['Day'],
  category: todayRow['Category'],
  topic: todayRow['Topic'],
  rowIndex: rows.indexOf(todayRow)
};
```

**Node 4: Switch (Route by Category)**
- Condition 1: `category == "Weird Science"` → Link to Gemini (Weird Science)
- Condition 2: `category == "Productivity & stoicism"` → Link to Gemini (Productivity)
- Condition 3: `category == "Human Behavior"` → Link to Gemini (Behavior)

**Node 5a: Gemini (Weird Science)**
- Type: AI (Gemini)
- Model: gemini-1.5-pro
- Prompt: See gemini_prompts.py (WEIRD_SCIENCE_PROMPT)
- Input: {{$json.topic}}

**Node 5b: Gemini (Productivity)**
- Same as 5a, but use PRODUCTIVITY_STOICISM_PROMPT

**Node 5c: Gemini (Human Behavior)**
- Same as 5a, but use HUMAN_BEHAVIOR_PROMPT

**Node 6: Function (Parse Script)**
```javascript
const script = $json.response;

// Extract sections
const hookMatch = script.match(/\[HOOK\](.*?)\[BODY\]/s);
const bodyMatch = script.match(/\[BODY\](.*?)\[CTA\]/s);
const ctaMatch = script.match(/\[CTA\](.*?)$/s);

return {
  hook: hookMatch ? hookMatch[1].trim() : "",
  body: bodyMatch ? bodyMatch[1].trim() : "",
  cta: ctaMatch ? ctaMatch[1].trim() : "",
  category: $json.category,
  topic: $json.topic
};
```

**Node 7: HTTP Request (Call Flask)**
- Method: POST
- URL: http://localhost:5000/generate_video
- Headers: Content-Type: application/json
- Body:
```json
{
  "script": "{{$json.body}}",
  "hook": "{{$json.hook}}",
  "cta": "{{$json.cta}}",
  "category": "{{$json.category}}",
  "video_id": "video_{{$now.getTime()}}",
  "audio_speed": 1.15
}
```

**Node 8: Wait**
- Wait: 5 minutes (video processing)

**Node 9: HTTP Request (YouTube Upload)**
- Method: POST
- URL: http://localhost:5000/upload_youtube
- Headers: Content-Type: application/json
- Body:
```json
{
  "video_path": "{{$json.body.video_path}}",
  "title": "{{$json.body.hook}} #shorts",
  "description": "{{$json.category}}\n\n{{$json.body.body}}\n\n#psychology #facts #shorts",
  "tags": ["psychology", "facts", "education", "shorts"],
  "category": "27"
}
```

**Node 10: Google Sheets (Update)**
- Type: Google Sheets
- Operation: Update
- Sheet ID: [Your sheet ID]
- Sheet Name: "Topics Queue"
- Update: Column F, G, H with video status and YouTube URL

**Node 11: End**
- Optional Slack notification with video link

---

## 🎬 STEP 6: Manual Test (IMPORTANT)

Before running automation:

1. **Add test topic to Google Sheet:**
   ```
   Monday | Weird Science | Why do we yawn
   ```

2. **Start Flask server:**
   ```bash
   python server.py
   ```

3. **Manually trigger n8n workflow**
   - Click "Execute Workflow"
   - Watch logs for errors
   - Check D:\piper\output\ for video file

4. **Verify output:**
   - Does video.mp4 exist? (Should be ~30-40 seconds)
   - Does it have audio?
   - Does thumbnail exist?

If successful → Move to daily automation

---

## 🔄 STEP 7: Schedule Daily Automation

1. **n8n → Workflow → Activate**
   - Toggle "Active" to ON
   - Set trigger time to 9:00 AM

2. **Weekly refresh backgrounds:**
   - Every Saturday: Download 3-5 new videos
   - Move old videos to `D:\piper\assets\backgrounds\archive\`
   - Put new videos in `D:\piper\assets\backgrounds\active\`

3. **Weekly topic planning:**
   - Every Sunday evening: Add 4 topics to Google Sheet (Mon-Thu)
   - Leave Friday-Sunday empty or batch them

---

## 🐛 TROUBLESHOOTING

### Problem: "Piper not found"
```
Solution: Add to PATH or use full path
Windows: Set environment variable PIPER_PATH=C:\...\piper.exe
```

### Problem: "Flask server crashes with 500 error"
```
Check logs for:
- Background folder empty? Add videos
- Audio generation failed? Check Piper installation
- FFmpeg missing? Install it

Run: python server.py --debug
```

### Problem: "n8n can't reach Flask"
```
Make sure:
1. Flask is running: python server.py
2. Port 5000 is accessible: curl http://localhost:5000/health
3. If running n8n in Docker, use: http://host.docker.internal:5000
```

### Problem: "Video uploads but appears blank on YouTube"
```
- Check video duration is > 15 seconds
- Check if uploaded as private/unlisted first
- Check YouTube processing (might take 15 mins)
- Check YouTube quota isn't exceeded
```

### Problem: "Transcription is slow"
```
Whisper is running on CPU. To speed up:
- Use GPU: Change compute_type="float16" to CUDA if available
- Or: Use smaller model="tiny" (less accurate but faster)
```

### Problem: "Audio is robotic sounding"
```
Try different Piper voices:
- en_US-lessac-medium (more natural)
- en_US-john-medium (different tone)
- en_GB-RP-medium (British accent)

Update in server.py line 280:
"--voice", "en_US-lessac-medium"
```

---

## 📈 MONITORING & OPTIMIZATION

### Weekly Review

1. **Check YouTube Analytics:**
   - Which content type gets most views?
   - What hook patterns work best?
   - Average watch duration by video

2. **Update Content Plan:**
   - Increase frequency of top-performing content
   - Test new hook formats
   - Refine background selection

3. **Monitor Automation:**
   - Check n8n execution logs
   - Verify all videos uploaded successfully
   - Update Google Sheet with view counts

### Monthly Updates

- Change backgrounds (prevents algorithm repetition)
- Refine Gemini prompts based on performance
- Analyze trending topics in your niche
- Update tags/descriptions based on top performers

---

## 🎯 SUCCESS METRICS (First Month)

| Metric | Target | How to Track |
|--------|--------|-------------|
| Upload consistency | 4 videos/week | Google Sheets log |
| Avg views per video | 500-2000 | YouTube Analytics |
| Avg watch % | 40%+ | YouTube Analytics |
| CTR | 3%+ | YouTube Analytics |
| Subscriber growth | 50-100 | YouTube Studio |

If you hit these → Scale to 7-10 videos/week

---

## 🚀 NEXT STEPS (In Order)

1. ✅ Download this complete setup
2. ✅ Create Google Sheet with template
3. ✅ Place videos in backgrounds\active folder
4. ✅ Install dependencies: `pip install -r requirements.txt`
5. ✅ Test Flask server locally
6. ✅ Build n8n workflow
7. ✅ Do ONE manual test run
8. ✅ Fix any errors
9. ✅ Activate automation
10. ✅ Monitor first week's videos
11. ✅ Optimize based on performance

---

## 💡 PRO TIPS

- **Use Discord for notifications:** Add Discord webhook to n8n for upload confirmations
- **Track ideas:** Keep a separate Google Sheet of trending topics
- **Batch topics:** Plan 4 weeks in advance, execute weekly
- **A/B test:** Upload same script with different backgrounds to see what drives views
- **Engage:** Reply to comments with Gemini-generated responses (save time)

---

Need help? Check logs:
- Flask: stdout/stderr of `python server.py`
- n8n: Workflow logs in UI
- YouTube: Check Studio → Videos → Processing status

Good luck! 🎬
