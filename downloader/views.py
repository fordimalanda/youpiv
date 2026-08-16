import json
import tempfile
import threading
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

# Use system temporary directory so server files never pollute project directory
DOWNLOAD_DIR = Path(getattr(settings, "DOWNLOAD_DIR", tempfile.gettempdir())) / "youpiv_downloads"
DOWNLOADS = {}
DOWNLOADS_LOCK = threading.Lock()

def index(request):
    return render(request, "index.html")

def validate_youtube_url(value):
    try:
        parsed = urlparse(value.strip())
    except (AttributeError, ValueError):
        return False, "URL YouTube invalide."
    if parsed.scheme not in {"http", "https"}:
        return False, "URL YouTube invalide."
    host = (parsed.hostname or "").lower()
    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}:
        return False, "URL YouTube invalide."
    query = parse_qs(parsed.query)
    if "list" in query or parsed.path.rstrip("/") == "/playlist":
        return False, "Les playlists ne sont pas encore prises en charge. Veuillez fournir l’URL d’une vidéo individuelle."
    if host.endswith("youtu.be"):
        return bool(parsed.path.strip("/")), "URL YouTube invalide."
    return bool(query.get("v") or parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/")), "URL YouTube invalide."

def _format_bytes(value):
    if not value:
        return None
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(value)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024

def _format_eta(seconds):
    if seconds is None:
        return None
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

def _set_state(download_id, **values):
    with DOWNLOADS_LOCK:
        if download_id in DOWNLOADS:
            DOWNLOADS[download_id].update(values)

def _download_worker(download_id, url):
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    def hook(data):
        if data.get("status") != "downloading":
            return
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes", 0)
        percent = min(99, round(downloaded * 100 / total)) if total else 0
        _set_state(
            download_id,
            status="downloading",
            progress=percent,
            downloaded=_format_bytes(downloaded),
            total=_format_bytes(total),
            speed=_format_bytes(data.get("speed")),
            eta=_format_eta(data.get("eta"))
        )

    prefix = str(download_id)
    options = {
        "format": "bv*+ba/b",
        "outtmpl": str(DOWNLOAD_DIR / f"{prefix}_%(title).180B.%(ext)s"),
        "windowsfilenames": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        
        files = list(DOWNLOAD_DIR.glob(f"{prefix}_*"))
        if files:
            target_file = files[0]
            filename = target_file.name[len(prefix) + 1:]
            _set_state(
                download_id,
                status="completed",
                progress=100,
                eta="00:00",
                file_path=str(target_file),
                filename=filename
            )
        else:
            _set_state(download_id, status="completed", progress=100, eta="00:00")
    except Exception:
        _set_state(download_id, status="error", error="Impossible de télécharger cette vidéo.")

@require_POST
def start_download(request):
    try:
        url = json.loads(request.body).get("url", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "URL YouTube invalide."}, status=400)
    is_valid, message = validate_youtube_url(url)
    if not is_valid:
        return JsonResponse({"error": message}, status=400)
    download_id = uuid.uuid4()
    with DOWNLOADS_LOCK:
        DOWNLOADS[download_id] = {
            "status": "queued",
            "progress": 0,
            "speed": None,
            "eta": None,
            "downloaded": None,
            "total": None,
            "file_path": None,
            "filename": None
        }
    threading.Thread(target=_download_worker, args=(download_id, url), daemon=True).start()
    return JsonResponse({"download_id": str(download_id)}, status=202)

@require_GET
def progress(request, download_id):
    with DOWNLOADS_LOCK:
        state = dict(DOWNLOADS[download_id]) if download_id in DOWNLOADS else None
    if state is None:
        return JsonResponse({"error": "Téléchargement introuvable."}, status=404)
    res = dict(state)
    if res.get("status") == "completed":
        res["download_url"] = f"/file/{download_id}/"
    return JsonResponse(res)

@require_GET
def download_file(request, download_id):
    with DOWNLOADS_LOCK:
        state = dict(DOWNLOADS[download_id]) if download_id in DOWNLOADS else None
    if not state or state.get("status") != "completed":
        return JsonResponse({"error": "Téléchargement introuvable ou non terminé."}, status=404)
    file_path = state.get("file_path")
    filename = state.get("filename", "video.mp4")
    if not file_path or not Path(file_path).exists():
        return JsonResponse({"error": "Fichier introuvable sur le serveur."}, status=404)
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)
