import sys
import os
import re
import shutil
from pathlib import Path


import certifi
import yt_dlp


from PySide6.QtCore import (Qt, QThread, Signal, QUrl)
from PySide6.QtGui import (QFont, QDesktopServices)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QCheckBox,
)


os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())



APP_NAME = "VideoGrab"



WHATSAPP_NUMBER = "213795065655"
WHATSAPP_MESSAGE = "Hello, I have a question about VideoGrab"



DEFAULT_DOWNLOAD_DIR = (
    Path.home()
    / "Videos"
    / "VideoGrab"
)



SUPPORTED_PLATFORMS = {
    "Auto Detect": None,
    "YouTube": "youtube",
    "Facebook": "facebook",
    "Instagram": "instagram",
    "LinkedIn": "linkedin",
    "Pinterest": "pinterest",
}



class DownloadWorker(QThread):


    progress = Signal(float)
    status = Signal(str)
    finished_download = Signal(str)
    error = Signal(str)


    def __init__(self, url, output_dir, ffmpeg_path, download_playlist=False):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.ffmpeg_path = ffmpeg_path
        self.download_playlist = download_playlist
        self._cancelled = False
        self._playlist_count = 0
        self._current_index = 0


    def cancel(self):
        self._cancelled = True


    def format_bytes(self, value):
        if not value:
            return "0 B"


        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(value)


        for unit in units:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024


        return f"{size:.1f} PB"


    def progress_hook(self, data):
        if self._cancelled:
            raise Exception("Download cancelled")


        status = data.get("status")


        if status == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = (
                data.get("total_bytes")
                or data.get("total_bytes_estimate")
                or 0
            )
            speed = data.get("speed")
            eta = data.get("eta")


            if total:
                percent = (downloaded / total) * 100
                self.progress.emit(min(percent, 100))


            speed_text = (
                self.format_bytes(speed) + "/s" if speed else "--"
            )


            if eta is not None:
                eta_int = int(eta)
                minutes = eta_int // 60
                seconds = eta_int % 60
                eta_text = f"{minutes:02d}:{seconds:02d}"
            else:
                eta_text = "--:--"


            downloaded_text = self.format_bytes(downloaded)
            total_text = self.format_bytes(total) if total else "--"


      
            prefix = ""
            if self._playlist_count > 1:
                prefix = f"[{self._current_index}/{self._playlist_count}]  "

            self.status.emit(
                f"{prefix}{downloaded_text} / {total_text}  •  "
                f"{speed_text}  •  ETA {eta_text}"
            )


        elif status == "finished":
            self.progress.emit(100)
            self.status.emit("Processing video...")


    def run(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)


            
            if self.download_playlist:
                outtmpl = str(
                    self.output_dir
                    / "%(playlist_title).150s"
                    / "%(playlist_index)03d - %(title).150s.%(ext)s"
                )
            else:
                outtmpl = str(self.output_dir / "%(title).200s.%(ext)s")


            ydl_options = {
                "format": "b",
                "outtmpl": outtmpl,
                "progress_hooks": [self.progress_hook],
                "overwrites": True,
                "continuedl": True,
                "retries": 5,
                "fragment_retries": 5,
                "socket_timeout": 30,
            
                "noplaylist": not self.download_playlist,
                "quiet": True,
                "no_warnings": True,
                "windowsfilenames": True,
                "writethumbnail": False,
                "writesubtitles": False,
                "restrictfilenames": False,
                "concurrent_fragment_downloads": 5,
                "nocheckcertificate": False,
            }


            if self.ffmpeg_path:
                ydl_options["ffmpeg_location"] = self.ffmpeg_path


            self.status.emit("Analyzing video...")


            with yt_dlp.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(self.url, download=False)


                if not info:
                    raise Exception("Unable to retrieve video information.")

                if "entries" in info and info.get("entries") is not None:
                    entries = [e for e in info["entries"] if e]
                    self._playlist_count = len(entries)
                    title = info.get("title", "Playlist")
                    self.status.emit(
                        f"Downloading playlist: {title} ({self._playlist_count} videos)"
                    )
                else:
                    self._playlist_count = 1
                    title = info.get("title", "Video")
                    self.status.emit(f"Downloading: {title}")


                self._current_index = 1


                ydl.download([self.url])


                self.finished_download.emit(title)


        except Exception as e:
            if not self._cancelled:
                message = str(e)


                lowered = message.lower()
                if "certificate" in lowered or "ssl" in lowered or "timed out" in lowered:
                    message = (
                        "Network/SSL error: unable to securely connect to the "
                        "server. Check your internet connection, disable any VPN/"
                        "proxy temporarily, or update the app. "
                        f"(details: {message[:200]})"
                    )


                if len(message) > 500:
                    message = message[:500] + "..."
                self.error.emit(message)



def find_ffmpeg():
  
    app_dir = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    )


    local_ffmpeg = app_dir / "bin" / "ffmpeg.exe"


    if local_ffmpeg.exists():
        return str(local_ffmpeg)


    return shutil.which("ffmpeg")



class VideoGrab(QWidget):


    def __init__(self):
        super().__init__()

        self.worker = None
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.ffmpeg_path = find_ffmpeg()

        self.setWindowTitle(APP_NAME)

        self.setFixedSize(460, 600)

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )

        self.setup_ui()
        self.apply_style()


    # -------------------------------------------------
    # UI
    # -------------------------------------------------


    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)


        # Header
        header = QHBoxLayout()


        title = QLabel("VideoGrab")
        title.setObjectName("title")


        subtitle = QLabel("Video Downloader")
        subtitle.setObjectName("subtitle")


        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)


        header.addLayout(title_box)
        header.addStretch()


        main_layout.addLayout(header)


        # URL label
        url_label = QLabel("Video URL")
        url_label.setObjectName("label")
        main_layout.addWidget(url_label)


        # URL input row
        url_layout = QHBoxLayout()
        url_layout.setSpacing(8)


        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video link here...")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self.start_download)
        self.url_input.setMinimumHeight(40)
    
        self.url_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )


        url_layout.addWidget(self.url_input)


        paste_button = QPushButton("Paste")
        paste_button.setObjectName("secondaryButton")
        paste_button.clicked.connect(self.paste_url)
        paste_button.setFixedHeight(40)
        paste_button.setFixedWidth(70)
        paste_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )


        url_layout.addWidget(paste_button)
        main_layout.addLayout(url_layout)


        # Platform
        platform_label = QLabel("Platform")
        platform_label.setObjectName("label")
        main_layout.addWidget(platform_label)


        self.platform_combo = QComboBox()
        self.platform_combo.addItems(SUPPORTED_PLATFORMS.keys())
        self.platform_combo.setMinimumHeight(40)
   
        self.platform_combo.setMinimumContentsLength(14)
        self.platform_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.platform_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        main_layout.addWidget(self.platform_combo)

        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)

        self.playlist_checkbox = QCheckBox("Download full playlist (YouTube)")
        self.playlist_checkbox.setObjectName("playlistCheckbox")
        main_layout.addWidget(self.playlist_checkbox)


        # Save location
        location_layout = QHBoxLayout()
        location_layout.setSpacing(8)


        location_label = QLabel("Save to")
        location_label.setObjectName("label")
        location_layout.addWidget(location_label)
        location_layout.addStretch()


        self.location_button = QPushButton("VideoGrab")
        self.location_button.setObjectName("locationButton")
        self.location_button.setMinimumHeight(32)
        self.location_button.setMaximumWidth(220)
        self.location_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )

        self.location_button.clicked.connect(self.choose_download_folder)


        location_layout.addWidget(self.location_button)
        main_layout.addLayout(location_layout)


        # Download button
        self.download_button = QPushButton("Download Video")
        self.download_button.setObjectName("downloadButton")
        self.download_button.setMinimumHeight(48)
        self.download_button.clicked.connect(self.start_download)


        main_layout.addWidget(self.download_button)



        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(16)


        main_layout.addWidget(self.progress_bar)


        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(30)


        main_layout.addWidget(self.status_label)


        main_layout.addStretch()


        # WhatsApp contact button
        self.whatsapp_button = QPushButton("Contact us on WhatsApp")
        self.whatsapp_button.setObjectName("whatsappButton")
        self.whatsapp_button.setMinimumHeight(40)
        self.whatsapp_button.clicked.connect(self.open_whatsapp)


        main_layout.addWidget(self.whatsapp_button)


        # Footer
        footer = QLabel("Downloads are saved locally on your PC.")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)


        main_layout.addWidget(footer)


    def apply_style(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #F7F8FA;
                color: #1C1E21;
                font-family: "Segoe UI";
                font-size: 13px;
            }


            QLabel#title {
                font-size: 22px;
                font-weight: 700;
                color: #101216;
            }


            QLabel#subtitle {
                font-size: 11px;
                color: #6B7280;
            }


            QLabel#label {
                color: #4B5563;
                font-size: 12px;
                font-weight: 600;
            }


            QLineEdit {
                background: #FFFFFF;
                border: 1px solid #D8DCE3;
                border-radius: 9px;
                padding: 8px 12px;
                color: #101216;
                selection-background-color: #4F7CFF;
            }


            QLineEdit:focus {
                border: 1px solid #4F7CFF;
            }


            QComboBox {
                background: #FFFFFF;
                border: 1px solid #D8DCE3;
                border-radius: 9px;
                padding: 6px 12px;
                color: #101216;
            }


            QComboBox:hover {
                border: 1px solid #B7BEC9;
            }


            QComboBox::drop-down {
                border: none;
                width: 28px;
            }


            QComboBox QAbstractItemView {
                background: #FFFFFF;
                color: #101216;
                border: 1px solid #D8DCE3;
                selection-background-color: #4F7CFF;
                selection-color: #FFFFFF;
                padding: 4px;
            }


            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }


            QPushButton#secondaryButton {
                background: #EEF0F3;
                color: #33383F;
            }


            QPushButton#secondaryButton:hover {
                background: #E3E6EA;
            }


            QPushButton#locationButton {
                background: #EEF0F3;
                color: #4B5563;
                padding: 6px 12px;
                text-align: left;
            }


            QPushButton#locationButton:hover {
                background: #E3E6EA;
            }


            QPushButton#downloadButton {
                background: #4F7CFF;
                color: white;
                font-size: 14px;
                font-weight: 700;
            }


            QPushButton#downloadButton:hover {
                background: #3E68E0;
            }


            QPushButton#downloadButton:disabled {
                background: #C9CED6;
                color: #8A8F98;
            }


            QPushButton#whatsappButton {
                background: #25D366;
                color: white;
                font-size: 13px;
                font-weight: 700;
            }


            QPushButton#whatsappButton:hover {
                background: #1FBE5A;
            }


            QProgressBar {
                background: #EAECEF;
                border: none;
                border-radius: 7px;
                height: 13px;
                text-align: center;
                color: #101216;
            }


            QProgressBar::chunk {
                background: #4F7CFF;
                border-radius: 7px;
            }


            QLabel#status {
                color: #6B7280;
                font-size: 11px;
            }


            QLabel#footer {
                color: #9AA0AA;
                font-size: 10px;
            }


            QCheckBox#playlistCheckbox {
                color: #4B5563;
                font-size: 12px;
                font-weight: 600;
                padding: 2px 0px;
            }


            QCheckBox#playlistCheckbox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #D8DCE3;
                border-radius: 4px;
                background: #FFFFFF;
            }


            QCheckBox#playlistCheckbox::indicator:checked {
                background: #4F7CFF;
                border: 1px solid #4F7CFF;
            }


            QCheckBox#playlistCheckbox:disabled {
                color: #B0B5BD;
            }
            """
        )


    # -------------------------------------------------
    # URL
    # -------------------------------------------------


    def paste_url(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()


        if text:
            self.url_input.setText(text)


    def is_valid_url(self, url):
        pattern = re.compile(r"^https?://", re.IGNORECASE)
        return bool(pattern.match(url))


    
    def on_platform_changed(self, platform_name):
        allowed = platform_name in ("Auto Detect", "YouTube")
        self.playlist_checkbox.setEnabled(allowed)
        if not allowed:
            self.playlist_checkbox.setChecked(False)


    # -------------------------------------------------
    # Download
    # -------------------------------------------------


    def start_download(self):
        if self.worker and self.worker.isRunning():
            return


        url = self.url_input.text().strip()


        if not url:
            self.show_error("Please paste a video URL.")
            return


        if not self.is_valid_url(url):
            self.show_error("Please enter a valid HTTP/HTTPS URL.")
            return


        platform = self.platform_combo.currentText()


        if platform != "Auto Detect":
            domain_map = {
                "YouTube": ["youtube.com", "youtu.be"],
                "Facebook": ["facebook.com", "fb.watch"],
                "Instagram": ["instagram.com"],
                "LinkedIn": ["linkedin.com"],
                "Pinterest": ["pinterest.com", "pin.it"],
            }


            domains = domain_map.get(platform, [])


            if not any(domain in url.lower() for domain in domains):
                self.show_error(
                    f"The URL does not appear to be a {platform} link."
                )
                return


        is_youtube_url = "youtube.com" in url.lower() or "youtu.be" in url.lower()
        download_playlist = (
            self.playlist_checkbox.isChecked()
            and self.playlist_checkbox.isEnabled()
            and is_youtube_url
        )


        self.download_button.setEnabled(False)
        self.url_input.setEnabled(False)
        self.platform_combo.setEnabled(False)
        self.playlist_checkbox.setEnabled(False)


        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)


        self.status_label.setText("Starting...")


        self.worker = DownloadWorker(
            url, self.download_dir, self.ffmpeg_path, download_playlist
        )


        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished_download.connect(self.download_finished)
        self.worker.error.connect(self.download_error)


        self.worker.start()


    def update_progress(self, value):
        self.progress_bar.setValue(int(value))


    def update_status(self, text):
        self.status_label.setText(text)


    def download_finished(self, title):
        self.progress_bar.setValue(100)
        self.status_label.setText("Download completed")


        self.reset_controls()


        QMessageBox.information(
            self,
            "Download Complete",
            f"Video downloaded successfully.\\n\\n{title}",
        )


        self.progress_bar.setVisible(False)


    def download_error(self, message):
        self.status_label.setText("Download failed")


        self.reset_controls()
        self.progress_bar.setVisible(False)


        self.show_error(message)


    def reset_controls(self):
        self.download_button.setEnabled(True)
        self.url_input.setEnabled(True)
        self.platform_combo.setEnabled(True)
       
        self.on_platform_changed(self.platform_combo.currentText())


    def choose_download_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Download Folder", str(self.download_dir)
        )


        if folder:
            self.download_dir = Path(folder)
            self.location_button.setText(
                self.download_dir.name or str(self.download_dir)
            )


    def open_whatsapp(self):
        url = f"https://wa.me/{WHATSAPP_NUMBER}?text={WHATSAPP_MESSAGE}"
        QDesktopServices.openUrl(QUrl(url))



    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)



    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Download in progress",
                "A download is currently running.\\n"
                "Do you want to close the application?",
            )


            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return


            self.worker.cancel()
            self.worker.wait(3000)


        event.accept()



def main():
    app = QApplication(sys.argv)


    app.setApplicationName(APP_NAME)
    app.setOrganizationName("VideoGrab")
    app.setFont(QFont("Segoe UI", 10))


    window = VideoGrab()
    window.show()


    sys.exit(app.exec())



if __name__ == "__main__":
    main()