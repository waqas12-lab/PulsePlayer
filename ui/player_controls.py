from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QComboBox
from PySide6.QtCore import Qt, Signal
from utils.helpers import format_time

class PlayerControls(QWidget):
    play_clicked = Signal()
    stop_clicked = Signal()
    prev_clicked = Signal()
    next_clicked = Signal()
    shuffle_clicked = Signal()
    repeat_clicked = Signal()
    mute_clicked = Signal()
    fullscreen_clicked = Signal()
    screenshot_clicked = Signal()
    seek_requested = Signal(int)
    volume_changed = Signal(int)
    speed_changed = Signal(float)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 8)
        root.setSpacing(5)

        # VLC-style: big progress bar on top, compact buttons below.
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        self.time = QLabel("00:00")
        self.time.setMinimumWidth(48)
        self.time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 1000)
        self.seek.setMinimumHeight(20)
        self.seek.setToolTip("Seek / progress bar  — shortcuts: Left / Right")
        self.total = QLabel("00:00")
        self.total.setMinimumWidth(48)
        self.total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_row.addWidget(self.time)
        progress_row.addWidget(self.seek, 1)
        progress_row.addWidget(self.total)

        button_row = QHBoxLayout()
        button_row.setSpacing(6)
        self.prev = QPushButton("⏮")
        self.prev.setToolTip("Previous media  — shortcut: Shift+P")
        self.play = QPushButton("▶")
        self.play.setToolTip("Play / Pause  — shortcut: Space")
        self.stop = QPushButton("⏹")
        self.stop.setToolTip("Stop playback")
        self.next = QPushButton("⏭")
        self.next.setToolTip("Next media  — shortcut: Shift+N")
        self.shuffle = QPushButton("🔀")
        self.shuffle.setCheckable(True)
        self.shuffle.setToolTip("Shuffle playlist  — shortcut: S")
        self.repeat = QPushButton("🔁")
        self.repeat.setToolTip("Repeat mode: Off / Repeat All / Repeat One  — shortcut: L")
        self.speed = QComboBox()
        self.speed.addItems(["0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x", "3x"])
        self.speed.setCurrentText("1x")
        self.speed.setToolTip("Playback speed")
        self.mute = QPushButton("🔈")
        self.mute.setToolTip("Mute / Unmute  — shortcut: M")
        self.vol = QSlider(Qt.Orientation.Horizontal)
        self.vol.setRange(0, 200)
        self.vol.setValue(80)
        self.vol.setFixedWidth(105)
        self.vol.setToolTip("Volume 0–200%  — shortcuts: Up / Down")
        self.vol_label = QLabel("80%")
        self.vol_label.setToolTip("Current volume percentage")
        self.vol_label.setMinimumWidth(42)
        self.shot = QPushButton("📸")
        self.shot.setToolTip("Take video screenshot")
        self.full = QPushButton("⛶")
        self.full.setToolTip("Fullscreen  — shortcut: F / Esc")

        for btn in (self.prev, self.play, self.stop, self.next, self.shuffle, self.repeat, self.mute, self.shot, self.full):
            btn.setFixedSize(34, 30)
        self.play.setFixedSize(42, 32)
        self.speed.setFixedWidth(78)

        button_row.addWidget(self.prev)
        button_row.addWidget(self.play)
        button_row.addWidget(self.stop)
        button_row.addWidget(self.next)
        button_row.addWidget(self.shuffle)
        button_row.addWidget(self.repeat)
        button_row.addSpacing(8)
        button_row.addWidget(QLabel("Speed"))
        button_row.addWidget(self.speed)
        button_row.addStretch(1)
        button_row.addWidget(self.mute)
        button_row.addWidget(self.vol)
        button_row.addWidget(self.vol_label)
        button_row.addWidget(self.shot)
        button_row.addWidget(self.full)

        root.addLayout(progress_row)
        root.addLayout(button_row)

        self.prev.clicked.connect(self.prev_clicked)
        self.play.clicked.connect(self.play_clicked)
        self.stop.clicked.connect(self.stop_clicked)
        self.next.clicked.connect(self.next_clicked)
        self.shuffle.clicked.connect(self.shuffle_clicked)
        self.repeat.clicked.connect(self.repeat_clicked)
        self.mute.clicked.connect(self.mute_clicked)
        self.full.clicked.connect(self.fullscreen_clicked)
        self.shot.clicked.connect(self.screenshot_clicked)
        self.vol.valueChanged.connect(self._on_volume_changed)
        self.seek.sliderReleased.connect(lambda: self.seek_requested.emit(self.seek.value()))
        self.speed.currentTextChanged.connect(lambda s: self.speed_changed.emit(float(s.replace("x", ""))))

    def _on_volume_changed(self, value: int):
        self.vol_label.setText(f"{value}%")
        self.volume_changed.emit(value)

    def set_volume_value(self, value: int):
        self.vol.blockSignals(True)
        self.vol.setValue(max(0, min(200, int(value))))
        self.vol.blockSignals(False)
        self.vol_label.setText(f"{self.vol.value()}%")

    def set_muted(self, muted: bool):
        self.mute.setText("🔇" if muted else "🔈")

    def set_playing(self, playing: bool):
        self.play.setText("⏸" if playing else "▶")

    def update_position(self, current_ms: int, total_ms: int):
        current_ms = max(0, int(current_ms or 0))
        total_ms = max(0, int(total_ms or 0))
        self.time.setText(format_time(current_ms))
        self.total.setText(format_time(total_ms))
        if total_ms > 0 and not self.seek.isSliderDown():
            self.seek.setValue(max(0, min(1000, int(current_ms / total_ms * 1000))))


    def set_shuffle(self, enabled: bool):
        self.shuffle.setChecked(bool(enabled))
        self.shuffle.setText("🔀" if enabled else "🔀")
        self.shuffle.setToolTip(("Shuffle ON" if enabled else "Shuffle OFF") + "  — shortcut: S")

    def set_repeat_mode(self, mode: str):
        # mode values: off, all, one
        icons = {"off": "🔁", "all": "🔁", "one": "🔂"}
        labels = {"off": "Repeat OFF", "all": "Repeat ALL", "one": "Repeat ONE"}
        self.repeat.setText(icons.get(mode, "🔁"))
        self.repeat.setToolTip(f"{labels.get(mode, 'Repeat')}  — shortcut: L")
