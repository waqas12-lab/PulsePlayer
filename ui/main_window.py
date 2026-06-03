from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QMessageBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout as DialogVBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QThreadPool
from PySide6.QtGui import QAction, QActionGroup, QShortcut, QKeySequence
from utils.constants import APP_NAME, MEDIA_EXTENSIONS, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, THEME_DIR
from settings.settings_manager import SettingsManager
from database.database import Database
from player.vlc_player import VlcPlayer
from services.media_scanner import FolderScanWorker
from services.playlist_service import PlaylistService
from services.metadata_service import MetadataService
from notifications.tray_service import TrayService
from ui.video_widget import VideoWidget
from ui.player_controls import PlayerControls
from ui.playlist_panel import PlaylistPanel
from ui.settings_dialog import SettingsDialog
from models.media_item import MediaItem

class PulsePlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pulse Player – Feel Every Beat, Watch Every Moment.")
        self.resize(1280, 760)
        self.setAcceptDrops(True)
        self.settings = SettingsManager()
        self.db = Database()
        self.playlist_service = PlaylistService()
        self.metadata = MetadataService()
        self.thread_pool = QThreadPool.globalInstance()
        self.current_index = -1
        self.current_path = None
        self.shuffle_enabled = bool(self.settings.get("shuffle", False))
        self.repeat_mode = str(self.settings.get("repeat_mode", "off"))  # off, all, one
        self._end_handled = False

        self.video = VideoWidget()
        self.controls = PlayerControls()
        self.playlist = PlaylistPanel()
        self.player = VlcPlayer(self.video)
        self.tray = TrayService(self)

        self._build_ui()
        self._build_menus()
        self._build_shortcuts()
        self._connect()
        self._load_theme()

        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(5000)
        self.hide_timer.timeout.connect(self.hide_fullscreen_ui)
        QTimer.singleShot(400, self.offer_resume_last_media)

    def _build_ui(self):
        splitter = QSplitter()
        left = QWidget()
        v = QVBoxLayout(left)
        v.setContentsMargins(14,14,14,8)
        v.addWidget(self.video, 1)
        v.addWidget(self.controls)
        splitter.addWidget(left)
        splitter.addWidget(self.playlist)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([920, 340])
        self.splitter = splitter
        self.setCentralWidget(splitter)

    def _build_menus(self):
        m = self.menuBar()
        media = m.addMenu("Media")
        playback = m.addMenu("Playback")
        audio = m.addMenu("Audio")
        self.audio_menu = audio
        self.audio_track_group = QActionGroup(self)
        self.audio_track_group.setExclusive(True)
        video = m.addMenu("Video")
        subtitle = m.addMenu("Subtitle")
        playlist = m.addMenu("Playlist")
        tools = m.addMenu("Tools")
        view = m.addMenu("View")
        helpm = m.addMenu("Help")

        self._act(media, "Open File", self.open_file, "Ctrl+O")
        self._act(media, "Open Multiple Files", self.open_files)
        self._act(media, "Open Folder", self.open_folder, "Ctrl+Shift+O")
        self._act(media, "Quit", self.close, "Ctrl+Q")
        self._act(playback, "Play/Pause", self.toggle_play, "Space")
        self._act(playback, "Stop", self.stop)
        self._act(playback, "Previous", self.previous_media, "Shift+P")
        self._act(playback, "Next", self.next_media, "Shift+N")
        self._act(playback, "Shuffle", self.toggle_shuffle, "S")
        self._act(playback, "Repeat / Loop", self.cycle_repeat_mode, "L")
        self.audio_tracks_menu = audio.addMenu("Audio Track")
        no_audio = QAction("No audio track loaded", self)
        no_audio.setEnabled(False)
        self.audio_tracks_menu.addAction(no_audio)
        self._act(subtitle, "Load External Subtitle", self.load_subtitle)
        self._act(playlist, "Import M3U", self.import_m3u, "Ctrl+P")
        self._act(playlist, "Export M3U", self.export_m3u)
        self._act(playlist, "Clear Playlist", self.playlist.clear_all)
        self._act(tools, "Settings", self.open_settings)
        self._act(view, "Fullscreen", self.toggle_fullscreen, "F")
        self._act(view, "Mini Mode / Always On Top", self.toggle_mini_mode)
        self._act(helpm, "About", self.about)

    def _act(self, menu, text, callback, shortcut=None):
        a = QAction(text, self)
        if shortcut: a.setShortcut(shortcut)
        a.triggered.connect(callback)
        menu.addAction(a)
        return a

    def _build_shortcuts(self):
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.exit_fullscreen)
        QShortcut(QKeySequence("M"), self).activated.connect(self.toggle_mute)
        QShortcut(QKeySequence("Shift+P"), self).activated.connect(self.previous_media)
        QShortcut(QKeySequence("Shift+N"), self).activated.connect(self.next_media)
        QShortcut(QKeySequence("S"), self).activated.connect(self.toggle_shuffle)
        QShortcut(QKeySequence("L"), self).activated.connect(self.cycle_repeat_mode)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self).activated.connect(lambda: self.player.seek_relative(-10000))
        QShortcut(QKeySequence(Qt.Key.Key_Right), self).activated.connect(lambda: self.player.seek_relative(10000))
        QShortcut(QKeySequence(Qt.Key.Key_Up), self).activated.connect(lambda: self.controls.vol.setValue(min(200, self.controls.vol.value()+5)))
        QShortcut(QKeySequence(Qt.Key.Key_Down), self).activated.connect(lambda: self.controls.vol.setValue(max(0, self.controls.vol.value()-5)))

    def _connect(self):
        self.controls.play_clicked.connect(self.toggle_play)
        self.controls.stop_clicked.connect(self.stop)
        self.controls.prev_clicked.connect(self.previous_media)
        self.controls.next_clicked.connect(self.next_media)
        self.controls.shuffle_clicked.connect(self.toggle_shuffle)
        self.controls.repeat_clicked.connect(self.cycle_repeat_mode)
        self.controls.set_shuffle(self.shuffle_enabled)
        self.controls.set_repeat_mode(self.repeat_mode)
        self.controls.mute_clicked.connect(self.toggle_mute)
        self.controls.fullscreen_clicked.connect(self.toggle_fullscreen)
        self.controls.screenshot_clicked.connect(self.take_screenshot)
        self.controls.volume_changed.connect(self.player.set_volume)
        saved_volume = int(self.settings.get("volume", 80))
        self.controls.set_volume_value(saved_volume)
        self.player.set_volume(saved_volume)
        self.controls.speed_changed.connect(self.player.set_rate)
        self.controls.seek_requested.connect(self.seek_from_slider)
        self.playlist.play_requested.connect(self.play_index)
        self.playlist.remove_requested.connect(self.remove_playlist_row)
        self.playlist.clear_requested.connect(self.clear_playlist)
        self.playlist.properties_requested.connect(self.show_media_properties)
        self.player.position_changed.connect(self.on_position)
        self.player.state_changed.connect(lambda s: self.controls.set_playing(s == "playing"))
        self.player.media_ended.connect(self.on_media_ended)
        self.player.error.connect(lambda e: QMessageBox.warning(self, "Playback Error", e))

    def _load_theme(self):
        theme = self.settings.get("theme", "dark")
        p = THEME_DIR / f"{theme}.qss"
        if p.exists():
            self.setStyleSheet(p.read_text(encoding="utf-8"))

    def add_paths(self, paths, autoplay: bool = False):
        """Add local media files to the playlist smoothly.

        Network stream support was intentionally removed. Only real local files/folders
        are accepted, which keeps Pulse Player focused and simpler like you requested.
        """
        first_added_index = None
        self.playlist.setUpdatesEnabled(False)
        try:
            for path in paths:
                if not path:
                    continue
                path_obj = Path(path)
                if not path_obj.exists() or not path_obj.is_file():
                    continue
                suffix = path_obj.suffix.lower()
                if suffix in MEDIA_EXTENSIONS:
                    item = self.metadata.read(str(path_obj))
                    self.playlist.add_media(item)
                    self.db.upsert_media(item)
                    if first_added_index is None:
                        first_added_index = len(self.playlist.items_data) - 1
        finally:
            self.playlist.setUpdatesEnabled(True)
            self.playlist.viewport().update()
        if first_added_index is not None and (autoplay or self.current_index == -1):
            self.play_index(first_added_index)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Media")
        if path:
            self.add_paths([path], autoplay=True)

    def open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open Media Files")
        self.add_paths(paths, autoplay=True)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not folder: return
        worker = FolderScanWorker(folder)
        worker.signals.found.connect(self._add_scanned_item)
        worker.signals.finished.connect(lambda n: self.tray.notify("Pulse Player", f"Added {n} media files"))
        self.thread_pool.start(worker)


    def _add_scanned_item(self, item):
        self.playlist.add_media(item)
        self.db.upsert_media(item)

    def play_index(self, index):
        if not (0 <= index < len(self.playlist.items_data)): return
        if self.current_path:
            self.settings.save_position(self.current_path, self.player.get_time())
        self.current_index = index
        self.playlist.setCurrentRow(index)
        self.playlist.set_playing_row(index)
        item = self.playlist.items_data[index]
        self.current_path = item.path
        self.settings.set("last_media", item.path)
        suffix = Path(item.path).suffix.lower()
        if suffix in AUDIO_EXTENSIONS:
            details = " • ".join(x for x in (item.artist, item.album) if x)
            self.video.show_audio_artwork(item.artwork, item.title, details or "Audio")
        else:
            self.video.hide_audio_artwork()
        start = 0
        saved_pos = self.settings.get_position(item.path) if self.settings.get("resume_playback", True) else 0
        if saved_pos > 15000 and self.settings.get("ask_resume", True):
            start = self.ask_resume_position(item, saved_pos)
        self._end_handled = False
        self.player.open(item.path, start, volume=self.controls.vol.value())
        QTimer.singleShot(900, self.refresh_audio_tracks_menu)
        self.settings.add_recent(item.path)
        self.tray.notify("Now Playing", item.title)

    def toggle_play(self): self.player.toggle()
    def stop(self): self.player.stop()
    def next_media(self):
        if not self.playlist.items_data:
            return
        if self.shuffle_enabled and len(self.playlist.items_data) > 1:
            import random
            choices = [i for i in range(len(self.playlist.items_data)) if i != self.current_index]
            self.play_index(random.choice(choices))
        else:
            next_index = self.current_index + 1
            if next_index >= len(self.playlist.items_data):
                if self.repeat_mode == "all":
                    next_index = 0
                else:
                    return
            self.play_index(next_index)

    def previous_media(self):
        if not self.playlist.items_data:
            return
        prev_index = self.current_index - 1
        if prev_index < 0:
            prev_index = len(self.playlist.items_data) - 1 if self.repeat_mode == "all" else 0
        self.play_index(prev_index)

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        self.settings.set("shuffle", self.shuffle_enabled)
        self.controls.set_shuffle(self.shuffle_enabled)

    def cycle_repeat_mode(self):
        order = ["off", "all", "one"]
        try:
            idx = order.index(self.repeat_mode)
        except ValueError:
            idx = 0
        self.repeat_mode = order[(idx + 1) % len(order)]
        self.settings.set("repeat_mode", self.repeat_mode)
        self.controls.set_repeat_mode(self.repeat_mode)
        self.tray.notify("Repeat Mode", {"off": "Repeat off", "all": "Repeat all", "one": "Repeat one"}[self.repeat_mode])

    def on_media_ended(self):
        # Prevent repeated VLC Ended events from triggering multiple skips.
        if self._end_handled:
            return
        self._end_handled = True
        if self.repeat_mode == "one":
            self.player.set_position_ms(0)
            self.player.play()
            QTimer.singleShot(700, lambda: setattr(self, "_end_handled", False))
            return
        if self.current_index < len(self.playlist.items_data) - 1 or self.repeat_mode == "all" or self.shuffle_enabled:
            self.next_media()

    def toggle_mute(self):
        muted = self.player.toggle_mute()
        self.controls.set_muted(bool(muted))

    def refresh_audio_tracks_menu(self):
        """Build VLC-like Audio > Audio Track menu for the current media."""
        self.audio_tracks_menu.clear()
        tracks = self.player.get_audio_tracks()
        self.audio_track_group = QActionGroup(self)
        self.audio_track_group.setExclusive(True)
        if not tracks:
            a = QAction("No audio track found", self)
            a.setEnabled(False)
            self.audio_tracks_menu.addAction(a)
            return
        current = self.player.get_current_audio_track()
        for track_id, name in tracks:
            label = name or f"Track {track_id}"
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(track_id == current)
            action.setToolTip(f"Switch audio to {label}")
            action.triggered.connect(lambda checked=False, tid=track_id: self.player.set_audio_track(tid))
            self.audio_track_group.addAction(action)
            self.audio_tracks_menu.addAction(action)

    def seek_from_slider(self, value):
        length = self.player.get_length()
        if length > 0:
            self.player.set_position_ms(int(value / 1000 * length))

    def on_position(self, current, total):
        self.controls.update_position(current, total)
        vol = self.player.volume()
        if vol >= 0 and not self.controls.vol.isSliderDown():
            self.controls.vol_label.setText(f"{vol}%")


    def is_current_audio(self) -> bool:
        """Return True when the current item is an audio/music file.

        In audio fullscreen mode Pulse Player should behave like a music player:
        keep album art, playlist, controls, progress bar, volume, shuffle/repeat,
        and other features visible. Only video fullscreen auto-hides controls.
        """
        if not self.current_path:
            return False
        return Path(self.current_path).suffix.lower() in AUDIO_EXTENSIONS

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.showFullScreen()
            self.show_fullscreen_ui()
            # Audio/music fullscreen keeps all controls and features visible.
            # Video fullscreen keeps VLC-like auto-hide behavior.
            if self.is_current_audio():
                self.hide_timer.stop()
            else:
                self.hide_timer.start()

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.show_fullscreen_ui()
            self.hide_timer.stop()

    def hide_fullscreen_ui(self):
        """Hide UI only for video fullscreen.

        For audio/music fullscreen, all player features must remain visible:
        album art, playlist, progress bar, control buttons, volume, speed,
        shuffle/repeat, menus, and tooltips.
        """
        if self.isFullScreen() and not self.is_current_audio():
            self.menuBar().hide()
            self.controls.hide()
            self.playlist.hide()

    def show_fullscreen_ui(self):
        self.menuBar().show()
        self.controls.show()
        self.playlist.show()

    def mouseMoveEvent(self, event):
        if self.isFullScreen():
            self.show_fullscreen_ui()
            if self.is_current_audio():
                self.hide_timer.stop()
            else:
                self.hide_timer.start()
        super().mouseMoveEvent(event)

    def toggle_mini_mode(self):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, not bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        self.resize(460, 300)
        self.show()

    def take_screenshot(self):
        pics = Path.home() / "Pictures"
        pics.mkdir(parents=True, exist_ok=True)
        out = str(pics / "pulse_screenshot.png")
        result = self.player.screenshot(out)
        if result == 0:
            self.tray.notify("Screenshot saved", out)
        else:
            QMessageBox.warning(self, "Screenshot", "Could not capture screenshot. Play a video first.")

    def load_subtitle(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Subtitle", filter="Subtitle (*.srt *.ass *.ssa)")
        if path: self.player.add_subtitle(path)

    def import_m3u(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import M3U", filter="M3U Playlist (*.m3u *.m3u8)")
        if path:
            for item in self.playlist_service.import_m3u(path):
                self.playlist.add_media(item)

    def export_m3u(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export M3U", filter="M3U Playlist (*.m3u)")
        if path:
            self.playlist_service.export_m3u(path, self.playlist.items_data)

    def open_settings(self):
        dlg = SettingsDialog(self.settings)
        if dlg.exec():
            self._load_theme()

    def about(self):
        QMessageBox.information(self, "About Pulse Player", "Pulse Player\nFeel Every Beat, Watch Every Moment.\n\nModern desktop media player powered by PySide6 and VLC.")

    def ask_resume_position(self, item, saved_ms: int) -> int:
        """VLC-style prompt: continue previous playback or restart from beginning."""
        seconds = saved_ms // 1000
        minutes = seconds // 60
        rem = seconds % 60
        title = item.title or Path(item.path).stem
        box = QMessageBox(self)
        box.setWindowTitle("Continue playback?")
        box.setIcon(QMessageBox.Icon.Question)
        box.setText(f"Continue playing previous file?\n\n{title}\nLast position: {minutes:02d}:{rem:02d}")
        continue_btn = box.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
        restart_btn = box.addButton("Restart", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == continue_btn:
            return saved_ms
        if clicked == restart_btn:
            return 0
        return 0

    def offer_resume_last_media(self):
        last = self.settings.get("last_media", "")
        if not last or self.playlist.items_data or not Path(last).exists():
            return
        saved = self.settings.get_position(last)
        if saved <= 15000:
            return
        box = QMessageBox(self)
        box.setWindowTitle("Pulse Player")
        box.setIcon(QMessageBox.Icon.Question)
        box.setText(f"Continue where you left off?\n\n{Path(last).name}")
        open_btn = box.addButton("Continue", QMessageBox.ButtonRole.AcceptRole)
        restart_btn = box.addButton("Open from Start", QMessageBox.ButtonRole.ActionRole)
        box.addButton("No", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == open_btn:
            self.add_paths([last], autoplay=True)
        elif clicked == restart_btn:
            self.settings.save_position(last, 0)
            self.add_paths([last], autoplay=True)

    def remove_playlist_row(self, row: int):
        was_current = row == self.current_index
        self.playlist.remove_row(row)
        if was_current:
            self.stop()
            self.current_index = -1
            self.current_path = None
        elif row < self.current_index:
            self.current_index -= 1
            self.playlist.set_playing_row(self.current_index)

    def clear_playlist(self):
        self.stop()
        self.current_index = -1
        self.current_path = None
        self.playlist.clear_all()
        self.video.show_audio_artwork(None, "Pulse Player", "Ready")

    def show_media_properties(self, row: int):
        if not (0 <= row < len(self.playlist.items_data)):
            return
        item = self.playlist.items_data[row]
        p = Path(item.path)
        size = f"{p.stat().st_size / (1024*1024):.2f} MB" if p.exists() else "Unknown"
        text = (
            f"Title: {item.title or p.stem}\n"
            f"Artist: {item.artist or '-'}\n"
            f"Album: {item.album or '-'}\n"
            f"Type: {p.suffix.upper().replace('.', '') or 'FILE'}\n"
            f"Size: {size}\n"
            f"Path: {item.path}"
        )
        QMessageBox.information(self, "Media Properties", text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()], autoplay=True)

    def closeEvent(self, event):
        if self.current_path:
            self.settings.save_position(self.current_path, self.player.get_time())
            self.settings.set("last_media", self.current_path)
        event.accept()
