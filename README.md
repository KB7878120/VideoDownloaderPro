# Video Downloader Pro

A Windows desktop GUI for yt-dlp. The configured default destination is:
`C:\Users\Kevin\Downloads`

## Run from source
1. Install Python 3.12 or newer.
2. Open a terminal in this folder and run `python -m pip install -r requirements.txt`.
3. Run `python main.py`.

FFmpeg is recommended for merging separate video/audio streams and converting formats. Install a trusted FFmpeg build and ensure `ffmpeg` is on PATH.

## Build a Windows executable
On Windows, run `build_windows.bat`. The build creates `dist\VideoDownloaderPro\VideoDownloaderPro.exe`.

## Current scope
This is a functional starter release with a GUI, yt-dlp background worker, progress, format/quality selection, destination controls, and local history. Multi-URL batch queue, playlist item selection, pause/resume, dependency auto-install/update UI, thumbnail preview, clipboard monitoring, installer, and full QA are not yet implemented. This project must not be described as a fully tested production release.
Only download content you are authorised to access. It does not bypass DRM, paywalls, or access controls.


## Easiest available Windows build route
See `BUILD_EXE_FOR_ME.txt`. The `.github/workflows/build-windows.yml` workflow
builds the app on a Windows runner and publishes a downloadable ZIP artifact.
