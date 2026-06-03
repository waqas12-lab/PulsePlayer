import sys
import logging
from PySide6.QtCore import QObject, Signal, QTimer

try:
    import vlc
except Exception as exc:
    vlc = None
    VLC_IMPORT_ERROR = exc
else:
    VLC_IMPORT_ERROR = None

log = logging.getLogger(__name__)

class VlcPlayer(QObject):
    position_changed = Signal(int, int)
    state_changed = Signal(str)
    media_ended = Signal()
    error = Signal(str)

    def __init__(self, video_widget):
        super().__init__()
        self.video_widget = video_widget
        self.instance = None
        self.player = None
        self._volume = 80
        self._muted = False
        if vlc is None:
            self.error.emit(f"VLC is not available: {VLC_IMPORT_ERROR}")
            return
        try:
            # Keep audio enabled and let VLC choose the correct macOS/Windows/Linux output.
            self.instance = vlc.Instance(
                "--no-video-title-show",
                "--avcodec-hw=any",
                "--aout=any",
                "--quiet",
            )
            self.player = self.instance.media_player_new()
            self._set_video_output()
            self.player.audio_set_mute(False)
            self.player.audio_set_volume(self._volume)
        except Exception as exc:
            log.exception("Could not initialize VLC")
            self.error.emit(f"Could not initialize VLC. Install VLC first. Details: {exc}")
        self.timer = QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _ready(self):
        if self.player is None:
            self.error.emit("VLC player is not ready. Install VLC and python-vlc.")
            return False
        return True

    def _set_video_output(self):
        if not self._ready():
            return
        wid = int(self.video_widget.winId())
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(wid)
        elif sys.platform == "win32":
            self.player.set_hwnd(wid)
        elif sys.platform == "darwin":
            self.player.set_nsobject(wid)

    def open(self, path: str, start_ms: int = 0, volume: int | None = None):
        if not self._ready():
            return
        try:
            media = self.instance.media_new(path)
            self.player.set_media(media)
            self._set_video_output()
            if volume is not None:
                self._volume = max(0, min(200, int(volume)))
            self.player.audio_set_mute(False)
            self.player.audio_set_volume(self._volume)
            self.play()
            # VLC needs a short delay after play() before audio/video properties are always accepted.
            QTimer.singleShot(250, lambda: self.player and self.player.audio_set_volume(self._volume))
            if start_ms > 0:
                QTimer.singleShot(900, lambda: self.player and self.player.set_time(max(0, int(start_ms))))
        except Exception as exc:
            log.exception("Cannot open media")
            self.error.emit(str(exc))

    def play(self):
        if self._ready():
            result = self.player.play()
            if result == -1:
                self.error.emit("VLC could not start playback. Try another file or install/update VLC.")
            else:
                self.player.audio_set_volume(self._volume)
                self.state_changed.emit("playing")

    def pause(self):
        if self._ready():
            self.player.pause()
            self.state_changed.emit("paused")

    def stop(self):
        if self._ready():
            self.player.stop()
            self.state_changed.emit("stopped")

    def toggle(self):
        if self._ready():
            self.pause() if self.player.is_playing() else self.play()

    def get_time(self) -> int:
        return int(self.player.get_time()) if self.player else 0

    def get_length(self) -> int:
        return int(self.player.get_length()) if self.player else 0

    def set_position_ms(self, ms: int):
        if self._ready():
            length = self.get_length()
            target = max(0, int(ms))
            if length > 0:
                target = min(target, length - 1)
            self.player.set_time(target)

    def seek_relative(self, delta_ms: int):
        if self._ready():
            self.set_position_ms(self.player.get_time() + int(delta_ms))

    def set_volume(self, value: int):
        if self._ready():
            self._volume = max(0, min(200, int(value)))
            self.player.audio_set_volume(self._volume)
            if self._volume > 0:
                self.player.audio_set_mute(False)
                self._muted = False

    def volume(self):
        if not self.player:
            return self._volume
        try:
            v = int(self.player.audio_get_volume())
            return v if v >= 0 else self._volume
        except Exception:
            return self._volume

    def toggle_mute(self):
        if self._ready():
            self.player.audio_toggle_mute()
            self._muted = bool(self.player.audio_get_mute())
            return self._muted
        return False


    def get_audio_tracks(self):
        """Return available VLC audio tracks as [(track_id, name), ...]."""
        if not self.player:
            return []
        tracks = []
        try:
            desc = self.player.audio_get_track_description()
            if not desc:
                return []
            for track_id, name in desc:
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="replace")
                tracks.append((int(track_id), str(name)))
        except Exception:
            log.exception("Could not read audio tracks")
        return tracks

    def get_current_audio_track(self) -> int:
        if not self.player:
            return -1
        try:
            return int(self.player.audio_get_track())
        except Exception:
            return -1

    def set_audio_track(self, track_id: int):
        if self._ready():
            try:
                self.player.audio_set_track(int(track_id))
            except Exception as exc:
                self.error.emit(f"Audio track change failed: {exc}")

    def set_rate(self, rate: float):
        if self._ready():
            try:
                self.player.set_rate(float(rate))
            except Exception as exc:
                self.error.emit(f"Playback speed failed: {exc}")

    def screenshot(self, path: str):
        if self._ready():
            return self.player.video_take_snapshot(0, path, 0, 0)
        return -1

    def add_subtitle(self, path: str):
        if self._ready():
            return self.player.video_set_subtitle_file(path)
        return False

    def _tick(self):
        if not self.player:
            return
        try:
            self.position_changed.emit(max(0, self.player.get_time()), max(0, self.player.get_length()))
            if vlc is not None and self.player.get_state() == vlc.State.Ended:
                self.media_ended.emit()
        except Exception:
            pass
