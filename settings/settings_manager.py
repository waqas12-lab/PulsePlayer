import json
import logging
from copy import deepcopy
from utils.constants import SETTINGS_DIR

log = logging.getLogger(__name__)

DEFAULTS = {
    "theme": "dark",
    "resume_playback": True,
    "volume": 80,
    "playback_speed": 1.0,
    "recent_files": [],
    "positions": {},
    "minimize_to_tray": True,
    "last_media": "",
    "ask_resume": True,
}

class SettingsManager:
    def __init__(self):
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.path = SETTINGS_DIR / "config.json"
        self.data = deepcopy(DEFAULTS)
        self.load()

    def load(self):
        if not self.path.exists():
            self.save()
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except Exception as exc:
            log.warning("Could not read settings, recreating defaults: %s", exc)
            self.save()

    def save(self):
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def add_recent(self, path: str):
        items = [p for p in self.data.get("recent_files", []) if p != path]
        items.insert(0, path)
        self.data["recent_files"] = items[:30]
        self.save()

    def save_position(self, path: str, ms: int):
        if not path or not isinstance(ms, int):
            return
        positions = self.data.setdefault("positions", {})
        if ms <= 0:
            positions.pop(path, None)
        else:
            positions[path] = ms
        self.save()

    def get_position(self, path: str) -> int:
        try:
            return int(self.data.get("positions", {}).get(path, 0))
        except Exception:
            return 0
