from pathlib import Path
from .constants import MEDIA_EXTENSIONS

def is_media_file(path: str) -> bool:
    return Path(path).suffix.lower() in MEDIA_EXTENSIONS

def format_time(ms: int) -> str:
    if ms is None or ms < 0:
        return "00:00"
    sec = ms // 1000
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
