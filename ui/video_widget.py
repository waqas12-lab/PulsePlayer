from pathlib import Path
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QFont


class VideoWidget(QWidget):
    """Native VLC video surface with an album-art overlay for audio files.

    VLC renders video directly on this widget. For audio-only playback there is no video
    frame, so we show a centered artwork card similar to VLC's audio view.
    """

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("VideoWidget")

        self.art_container = QWidget(self)
        self.art_container.setObjectName("AudioArtworkOverlay")
        self.art_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self.art_container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        self.cover = QLabel()
        self.cover.setObjectName("AudioCover")
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setFixedSize(330, 330)
        self.cover.setScaledContents(False)

        self.title = QLabel("Pulse Player")
        self.title.setObjectName("AudioTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setFont(QFont("Arial", 20, QFont.Weight.Bold))

        self.subtitle = QLabel("Feel Every Beat, Watch Every Moment.")
        self.subtitle.setObjectName("AudioSubtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setWordWrap(True)

        layout.addStretch(1)
        layout.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addStretch(1)

        self.opacity = QGraphicsOpacityEffect(self.art_container)
        self.art_container.setGraphicsEffect(self.opacity)
        self.fade = QPropertyAnimation(self.opacity, b"opacity", self)
        self.fade.setDuration(180)
        self.fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.show_audio_artwork(None, "Pulse Player", "Ready")

    def resizeEvent(self, event):
        self.art_container.setGeometry(self.rect())
        super().resizeEvent(event)

    def show_audio_artwork(self, artwork_path: str | None, title: str = "", subtitle: str = ""):
        self.art_container.show()
        self.art_container.raise_()
        self.title.setText(title or "Unknown Title")
        self.subtitle.setText(subtitle or "")

        pixmap = None
        if artwork_path and Path(artwork_path).exists():
            pixmap = QPixmap(artwork_path)
        if pixmap and not pixmap.isNull():
            self.cover.setPixmap(pixmap.scaled(
                QSize(320, 320),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
            self.cover.setText("")
        else:
            self.cover.setPixmap(QPixmap())
            self.cover.setText("♪")

        self.fade.stop()
        self.fade.setStartValue(self.opacity.opacity())
        self.fade.setEndValue(1.0)
        self.fade.start()

    def hide_audio_artwork(self):
        self.fade.stop()
        self.fade.setStartValue(self.opacity.opacity())
        self.fade.setEndValue(0.0)
        self.fade.start()
