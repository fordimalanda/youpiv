import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from . import views

class DownloaderTests(TestCase):
    def setUp(self):
        views.DOWNLOADS.clear()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "YouTube Downloader")

    def test_invalid_url_is_rejected(self):
        response = self.client.post("/download/", data=json.dumps({"url": "https://example.com/video"}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "URL YouTube invalide.")

    def test_playlist_is_rejected(self):
        response = self.client.post("/download/", data=json.dumps({"url": "https://youtube.com/watch?v=abc&list=xyz"}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("playlists", response.json()["error"])

    @patch("downloader.views.threading.Thread")
    def test_valid_url_creates_download(self, thread):
        response = self.client.post("/download/", data=json.dumps({"url": "https://youtu.be/abc123"}), content_type="application/json")
        self.assertEqual(response.status_code, 202)
        download_id = response.json()["download_id"]
        self.assertEqual(views.DOWNLOADS[uuid.UUID(download_id)]["status"], "queued")
        thread.return_value.start.assert_called_once()

    def test_progress_state(self):
        download_id = uuid.uuid4()
        views.DOWNLOADS[download_id] = {
            "status": "downloading",
            "progress": 42,
            "speed": "1.0 MB",
            "eta": "00:10",
            "downloaded": "42 MB",
            "total": "100 MB"
        }
        response = self.client.get(f"/progress/{download_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["progress"], 42)

    def test_download_file_endpoint(self):
        download_id = uuid.uuid4()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"dummy video content")
            tmp_path = tmp.name

        try:
            views.DOWNLOADS[download_id] = {
                "status": "completed",
                "progress": 100,
                "file_path": tmp_path,
                "filename": "sample_video.mp4"
            }
            # Verify progress endpoint includes download_url
            progress_resp = self.client.get(f"/progress/{download_id}/")
            self.assertEqual(progress_resp.status_code, 200)
            self.assertEqual(progress_resp.json()["download_url"], f"/file/{download_id}/")

            # Verify file download endpoint returns the file
            response = self.client.get(f"/file/{download_id}/")
            self.assertEqual(response.status_code, 200)
            self.assertIn("sample_video.mp4", response.headers["Content-Disposition"])
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_download_file_not_found(self):
        # Non existent UUID
        response = self.client.get(f"/file/{uuid.uuid4()}/")
        self.assertEqual(response.status_code, 404)

        # Incomplete download
        download_id = uuid.uuid4()
        views.DOWNLOADS[download_id] = {"status": "downloading", "progress": 50}
        response = self.client.get(f"/file/{download_id}/")
        self.assertEqual(response.status_code, 404)

    @patch("downloader.views.yt_dlp.YoutubeDL")
    def test_download_error_is_sanitized(self, ydl):
        ydl.return_value.__enter__.return_value.download.side_effect = RuntimeError("technical detail")
        download_id = uuid.uuid4()
        views.DOWNLOADS[download_id] = {"status": "queued", "progress": 0}
        with patch.object(views, "DOWNLOAD_DIR") as directory:
            views._download_worker(download_id, "https://youtu.be/abc123")
        self.assertEqual(views.DOWNLOADS[download_id]["error"], "Impossible de télécharger cette vidéo.")
