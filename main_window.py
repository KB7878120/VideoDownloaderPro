import os, sqlite3, subprocess, sys
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import *
from core.downloader import DownloadWorker, DEFAULT_DIR

DARK = """
QWidget { background:#171a21; color:#edf0f6; font-family:'Segoe UI'; font-size:10pt; }
QLineEdit,QComboBox,QTextEdit { background:#242936; border:1px solid #3b4353; border-radius:8px; padding:9px; }
QPushButton { background:#30394a; border:0; border-radius:8px; padding:10px 16px; }
QPushButton:hover { background:#43516a; }
QPushButton#primary { background:#3978e8; font-weight:600; padding:13px; }
QProgressBar { border:0; background:#30394a; border-radius:6px; height:13px; text-align:center; }
QProgressBar::chunk { background:#3978e8; border-radius:6px; }
QGroupBox { border:1px solid #343c4b; border-radius:10px; margin-top:12px; padding:12px; font-weight:600; }
"""
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader Pro")
        self.resize(900, 720)
        self.folder = DEFAULT_DIR
        self.worker = None
        self.history_db = os.path.join(os.path.expanduser("~"), ".video_downloader_pro.db")
        self.init_db()
        self.build_ui()
        self.setStyleSheet(DARK)

    def init_db(self):
        with sqlite3.connect(self.history_db) as db:
            db.execute("CREATE TABLE IF NOT EXISTS history (title TEXT, url TEXT, path TEXT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)")

    def build_ui(self):
        w = QWidget(); self.setCentralWidget(w)
        layout = QVBoxLayout(w); layout.setContentsMargins(28,24,28,24); layout.setSpacing(14)
        head = QHBoxLayout()
        title = QLabel("Video Downloader Pro"); title.setStyleSheet("font-size:24pt;font-weight:700")
        subtitle = QLabel("Paste a link. Choose your format. Download.")
        v = QVBoxLayout(); v.addWidget(title); v.addWidget(subtitle)
        head.addLayout(v); head.addStretch()
        self.version = QLabel("Powered by yt-dlp"); head.addWidget(self.version)
        layout.addLayout(head)

        urlbox = QGroupBox("VIDEO URLS")
        ul = QVBoxLayout(urlbox)
        self.urls = QTextEdit(); self.urls.setPlaceholderText("Paste one or more video URLs — one per line"); self.urls.setFixedHeight(90)
        row = QHBoxLayout()
        paste = QPushButton("Paste"); paste.clicked.connect(lambda:self.urls.setPlainText(QApplication.clipboard().text()))
        clear = QPushButton("Clear"); clear.clicked.connect(self.urls.clear)
        row.addWidget(paste); row.addWidget(clear); row.addStretch()
        ul.addWidget(self.urls); ul.addLayout(row); layout.addWidget(urlbox)

        options = QGroupBox("DOWNLOAD OPTIONS"); grid = QGridLayout(options)
        self.quality = QComboBox(); self.quality.addItems(["Best available","2160p (4K)","1440p","1080p","720p","480p","360p"])
        self.format = QComboBox(); self.format.addItems(["MP4","MKV","WebM","Original/best available"])
        self.mode = QComboBox(); self.mode.addItems(["Video","Audio only","Playlist"])
        self.audio = QComboBox(); self.audio.addItems(["MP3","M4A","WAV","FLAC"])
        grid.addWidget(QLabel("Video quality"),0,0); grid.addWidget(self.quality,0,1)
        grid.addWidget(QLabel("Video format"),0,2); grid.addWidget(self.format,0,3)
        grid.addWidget(QLabel("Download type"),1,0); grid.addWidget(self.mode,1,1)
        grid.addWidget(QLabel("Audio format"),1,2); grid.addWidget(self.audio,1,3)
        layout.addWidget(options)

        dest = QGroupBox("DOWNLOAD LOCATION"); dl = QHBoxLayout(dest)
        self.path_label = QLabel(self.folder); self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        browse = QPushButton("Browse"); browse.clicked.connect(self.browse)
        restore = QPushButton("Restore default"); restore.clicked.connect(self.restore)
        openf = QPushButton("Open folder"); openf.clicked.connect(self.open_folder)
        dl.addWidget(self.path_label,1); dl.addWidget(browse); dl.addWidget(restore); dl.addWidget(openf)
        layout.addWidget(dest)

        self.start_btn = QPushButton("DOWNLOAD"); self.start_btn.setObjectName("primary"); self.start_btn.clicked.connect(self.start_download)
        layout.addWidget(self.start_btn)
        statusbox = QGroupBox("DOWNLOAD STATUS"); sl = QVBoxLayout(statusbox)
        self.status = QLabel("Ready — waiting for a URL")
        self.progress = QProgressBar(); self.progress.setValue(0)
        self.details = QLabel("")
        sl.addWidget(self.status); sl.addWidget(self.progress); sl.addWidget(self.details)
        layout.addWidget(statusbox)

        hist = QGroupBox("RECENT DOWNLOADS"); hl = QVBoxLayout(hist)
        self.history = QListWidget(); self.history.setMaximumHeight(130); hl.addWidget(self.history)
        layout.addWidget(hist)
        self.load_history()

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self,"Choose download folder",self.folder)
        if folder: self.folder=folder; self.path_label.setText(folder)

    def restore(self):
        self.folder=DEFAULT_DIR; self.path_label.setText(self.folder)

    def open_folder(self):
        Path(self.folder).mkdir(parents=True,exist_ok=True)
        if sys.platform == "win32": os.startfile(self.folder)
        else: subprocess.Popen(["xdg-open",self.folder])

    def start_download(self):
        urls=[x.strip() for x in self.urls.toPlainText().splitlines() if x.strip()]
        if not urls:
            QMessageBox.warning(self,"URL required","Paste at least one video URL first."); return
        if len(urls)>1:
            QMessageBox.information(self,"Multiple URLs","This starter build processes one URL at a time. Download each URL separately."); urls=urls[:1]
        if self.worker and self.worker.is_alive():
            QMessageBox.information(self,"Busy","A download is already running."); return
        url=urls[0]
        if not url.startswith(("http://","https://")):
            QMessageBox.warning(self,"Invalid URL","Please enter a complete URL beginning with http:// or https://"); return
        callbacks={"progress":self.on_progress,"status":self.status.setText,"done":self.on_done}
        self.progress.setValue(0); self.details.setText(""); self.status.setText("Starting download…")
        self.start_btn.setEnabled(False)
        self.worker=DownloadWorker(url,self.folder,self.quality.currentText(),self.mode.currentText(),
                                   self.audio.currentText() if self.mode.currentText()=="Audio only" else self.format.currentText(),callbacks)
        self.worker.start()

    def on_progress(self,pct,speed,eta):
        QTimer.singleShot(0,lambda:(self.progress.setValue(pct),self.details.setText(f"{speed}  •  ETA {eta}")))
    def on_done(self,ok,result):
        def update():
            self.start_btn.setEnabled(True)
            self.status.setText(("Completed: " if ok else "Download failed: ")+result)
            if ok:
                with sqlite3.connect(self.history_db) as db:
                    db.execute("INSERT INTO history(title,url,path,status) VALUES(?,?,?,?)",(result,"",self.folder,"Completed"))
                self.load_history()
                QMessageBox.information(self,"Download complete",f"{result}\\n\\nSaved in:\\n{self.folder}")
            else:
                QMessageBox.warning(self,"Download error",result[:1200])
        QTimer.singleShot(0,update)

    def load_history(self):
        self.history.clear()
        try:
            with sqlite3.connect(self.history_db) as db:
                for title,path,status in db.execute("SELECT title,path,status FROM history ORDER BY created DESC LIMIT 20"):
                    self.history.addItem(f"{title}  —  {status}  —  {path}")
        except Exception: pass
