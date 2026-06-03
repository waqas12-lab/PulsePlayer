from pathlib import Path
from models.media_item import MediaItem
from utils.helpers import is_media_file

class PlaylistService:
    def import_m3u(self, path: str):
        base = Path(path).parent
        items = []
        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = Path(line)
            if not p.is_absolute():
                p = base / p
            if p.exists() and is_media_file(str(p)):
                items.append(MediaItem.from_path(str(p)))
        return items

    def export_m3u(self, path: str, items):
        lines = ["#EXTM3U"] + [i.path for i in items]
        Path(path).write_text("\n".join(lines), encoding="utf-8")
