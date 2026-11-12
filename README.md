# VideoGrab

A lightweight desktop application for downloading videos from social media platforms. Built with Python, PySide6, and yt-dlp, VideoGrab provides a simple interface for pasting a video URL, choosing a download folder, and tracking download progress.

## Features

- **Simple desktop interface** — Paste a link and start downloading.
- **Automatic platform detection** — Let yt-dlp detect the platform from the URL.
- **Platform selection** — Includes options for YouTube, Facebook, Instagram, LinkedIn, and Pinterest.
- **YouTube playlist downloads** — Download a full playlist into an organized folder.
- **Live download information** — View progress, downloaded size, download speed, and estimated time remaining.
- **Custom download folder** — Choose where your videos are saved.
- **Background downloading** — Download tasks run in a separate thread to keep the interface responsive.
- **Windows executable** — Run the packaged application without installing Python.
- **WhatsApp contact button** — Access the developer’s contact channel directly from the application.

> Platform availability depends on yt-dlp support and the accessibility of each video. Private, restricted, or login-required content may not be available.

## Screenshots
<img width="566" height="778" alt="image" src="https://github.com/user-attachments/assets/6835d283-a577-442e-8fc3-ff1bed0d5786" />
<img width="565" height="777" alt="image" src="https://github.com/user-attachments/assets/643d7a9b-48a0-4397-a26a-d26a8379d665" />


## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| PySide6 | Desktop user interface |
| yt-dlp | Video information extraction and downloading |
| certifi | Certificate bundle configuration for HTTPS connections |
| QThread and Qt signals | Background download execution and UI updates |

## Getting Started

### Option 1: Run the Windows Application

1. Download `videoDownloader.exe` from this repository.
2. Launch the executable.
3. Paste a video URL.
4. Select a platform or leave it on **Auto Detect**.
5. Choose a download folder if needed.
6. Click **Download Video**.

Python is not required to run the packaged Windows application.

### Option 2: Run from Source

#### Requirements

- Python with support for the dependencies below.
- An internet connection.
- A graphical desktop environment.

#### Installation

Clone the repository:

```bash
git clone [https://github.com/Ynsaid/Social-Media-Video-Downloder.git](https://github.com/Ynsaid/Social-Media-Video-Downloder.git)
cd Social-Media-Video-Downloder
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install PySide6 yt-dlp certifi
```

Run the application:

```bash
python project.py
```

## How to Use

### Download a Single Video

1. Copy the video link from its platform.
2. Paste it into the **Video URL** field, or click **Paste**.
3. Select the platform, or keep **Auto Detect**.
4. Leave the playlist option unchecked.
5. Choose your destination using the **Save to** button.
6. Click **Download Video**.
7. Wait for the completion message.

### Download a YouTube Playlist

1. Paste a YouTube playlist URL.
2. Select **YouTube** or **Auto Detect**.
3. Enable **Download full playlist (YouTube)**.
4. Click **Download Video**.

Playlist downloads are organized into a folder using the playlist title, with numbered video filenames.

### Default Download Location

Unless you choose another folder, downloads are saved to:

```text
~/Videos/VideoGrab
```

On Windows, this normally corresponds to:

```text
C:\Users\<YourUsername>\Videos\VideoGrab
```

## Download Format

The current configuration uses:

```python
"format": "b"
```

This requests the best available format that already includes both video and audio, avoiding the need to merge separate streams with FFmpeg.

### Format Limitations

- The highest available resolution may require separate video and audio streams and therefore may not be selected.
- Downloads may fail if the source does not provide a suitable combined format.
- The output file extension depends on the format supplied by the platform; MP4 is not guaranteed.

## Repository Contents

```text
Social-Media-Video-Downloder/
├── project.py             # Python application source
├── videoDownloader.exe    # Packaged Windows application
└── README.md              # Project documentation
```

## Troubleshooting

### A Video Fails to Download

- Check that the URL is correct and the video is accessible.
- Try **Auto Detect** if the selected platform does not match the link.
- Check your internet connection.
- If running from source, update yt-dlp:

```bash
python -m pip install --upgrade yt-dlp
```

Changes made by supported platforms can affect video extraction.

### An FFmpeg Merging Error Appears

The current source configuration requests a combined video-and-audio format. If you still receive a merging error, make sure you are running an executable rebuilt from the updated source rather than an older version.

### The Downloaded File Is Not MP4

The application keeps the format provided by the selected download stream. It does not automatically convert every video to MP4.

## Responsible Use

Download only content that you own or have permission to download. Respect copyright, privacy, and the terms of the source platform.

## Developer

Developed by [Ynsaid](https://github.com/Ynsaid).

For questions, use the **Contact us on WhatsApp** button inside the application.
