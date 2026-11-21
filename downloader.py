import os, re, threading
from pathlib import Path
from yt_dlp import YoutubeDL

DEFAULT_DIR = r"C:\Users\Kevin\Downloads"

class DownloadWorker(threading.Thread):
    def __init__(self, url, folder, quality, mode, fmt, callbacks):
        super().__init__(daemon=True)
        self.url, self.folder, self.quality = url, folder, quality
        self.mode, self.fmt, self.cb = mode, fmt, callbacks
        self.cancelled = False

    def run(self):
        try:
            Path(self.folder).mkdir(parents=True, exist_ok=True)
            if not os.access(self.folder, os.W_OK):
                raise PermissionError("The selected download folder is not writable.")
            def hook(d):
                if self.cancelled:
                    raise Exception("Download cancelled by user.")
                if d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    pct = int(d.get("downloaded_bytes", 0) * 100 / total) if total else 0
                    self.cb["progress"](pct, d.get("_speed_str", ""), d.get("_eta_str", ""))
                elif d.get("status") == "finished":
                    self.cb["status"]("Processing media…")
            if self.mode == "Audio only":
                fmt = "bestaudio/best"
                post = [{"key":"FFmpegExtractAudio","preferredcodec":self.fmt.lower(),"preferredquality":"192"}]
            else:
                height = {"Best available":None,"2160p (4K)":2160,"1440p":1440,"1080p":1080,
                          "720p":720,"480p":480,"360p":360}.get(self.quality)
                selector = "bv*+ba/b" if height is None else f"bv*[height<={height}]+ba/b[height<={height}]"
                fmt = selector
                post = []
                if self.fmt != "Original/best available":
                    post.append({"key":"FFmpegVideoConvertor","preferedformat":self.fmt.lower()})
            opts = {
                "format": fmt, "outtmpl": os.path.join(self.folder, "%(title)s.%(ext)s"),
                "paths":{"home":self.folder,"temp":os.path.join(self.folder,".vdp_temp")},
                "progress_hooks":[hook], "noplaylist": self.mode != "Playlist",
                "ignoreerrors":False, "windowsfilenames":True, "overwrites":False,
                "quiet":True, "no_warnings":True, "postprocessors":post,
                "retries":3, "fragment_retries":3
            }
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
            title = info.get("title", "Download") if info else "Download"
            self.cb["done"](True, title)
        except Exception as e:
            self.cb["done"](False, str(e))
