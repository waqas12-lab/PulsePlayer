from dataclasses import dataclass, field
from .media_item import MediaItem

@dataclass
class Playlist:
    name: str = "Now Playing"
    items: list[MediaItem] = field(default_factory=list)
    current_index: int = -1
