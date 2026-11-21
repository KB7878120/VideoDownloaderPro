@echo off
setlocal
py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --windowed --name VideoDownloaderPro --collect-all yt_dlp main.py
echo.
echo Build complete: dist\VideoDownloaderPro\VideoDownloaderPro.exe
pause
