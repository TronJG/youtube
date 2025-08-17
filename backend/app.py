from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp, tempfile, os, threading, uuid

app = FastAPI(title="YouTube Downloader – Jobs + Progress")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Lưu trạng thái job ở RAM
JOBS = {}  # job_id -> {"status": "queued|downloading|postprocessing|done|error",
           #             "progress": float, "speed": str, "eta": int|None,
           #             "file": str, "error": str}

def _progress_hook(job_id):
    def hook(d):
        j = JOBS.get(job_id)
        if not j: return
        st = d.get("status")
        if st == "downloading":
            # _percent_str như " 12.3%"
            p = (d.get("_percent_str") or "").strip().replace("%","")
            try:
                pct = float(p)
            except:
                pct = j.get("progress", 0.0)
            j.update({
                "status": "downloading",
                "progress": round(pct, 2),
                "speed": d.get("_speed_str") or "",
                "eta": d.get("eta") if isinstance(d.get("eta"), int) else None,
            })
        elif st == "finished":
            j["status"] = "postprocessing"
    return hook

def _resolve_output(filename: str):
    """Sau download/merge/postprocess, dò lại file thực tế."""
    base, _ = os.path.splitext(filename)
    candidates = [
        base + ".mp4", base + ".mkv",
        base + ".mp3", base + ".m4a", base + ".webm"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return filename

def _run_download(job_id: str, url: str, kind: str):
    temp_dir = tempfile.mkdtemp(prefix="ytdlp_")
    outtmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

    if kind == "video":
        # Giới hạn ≤1080p
        fmt = "bestvideo[height<=1080][vcodec!=none]+bestaudio[acodec!=none]/best[height<=1080]/best"
        ydl_opts = {
            "format": fmt,
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
            "quiet": True, "no_warnings": True,
            "progress_hooks": [_progress_hook(job_id)],
            # "ffmpeg_location": r"C:\ffmpeg\bin",  # bật nếu không thêm PATH
        }
    else:
        # Audio MP3 192kbps
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True, "no_warnings": True,
            "progress_hooks": [_progress_hook(job_id)],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            # "ffmpeg_location": r"C:\ffmpeg\bin",
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            real_file = _resolve_output(filename)

        JOBS[job_id].update({"status": "done", "progress": 100.0, "file": real_file})
    except Exception as e:
        JOBS[job_id].update({"status": "error", "error": str(e)})

@app.get("/api/start_download")
def start_download(
    url: str = Query(..., description="YouTube URL"),
    kind: str = Query("video", pattern="^(video|audio)$")
):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "queued", "progress": 0.0, "eta": None, "speed": "", "file": "", "error": ""}
    t = threading.Thread(target=_run_download, args=(job_id, url, kind), daemon=True)
    t.start()
    return {"job_id": job_id}

@app.get("/api/progress")
def progress(job_id: str):
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "job not found")
    return JSONResponse(j)

@app.get("/api/fetch")
def fetch(job_id: str):
    j = JOBS.get(job_id)
    if not j or j.get("status") != "done" or not os.path.exists(j.get("file","")):
        raise HTTPException(400, "file not ready")
    path = j["file"]
    return FileResponse(path, filename=os.path.basename(path))
