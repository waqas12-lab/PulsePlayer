from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class MediaItem:
    path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration_ms: int = 0
    artwork: Optional[str] = None
    thumbnail: Optional[str] = None

    @classmethod
    def from_path(cls, path: str):
        p = Path(path)
        return cls(path=str(p), title=p.stem)
