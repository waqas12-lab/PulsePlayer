import hashlib
from pathlib import Path
from typing import Optional
from mutagen import File
from models.media_item import MediaItem
from utils.constants import CACHE_DIR, VIDEO_EXTENSIONS
from services.thumbnail_service import ThumbnailService

ART_DIR = CACHE_DIR / "artwork"
ART_DIR.mkdir(parents=True, exist_ok=True)

class MetadataService:
    def __init__(self):
        self.thumbnails = ThumbnailService()

    def read(self, path: str) -> MediaItem:
        item = MediaItem.from_path(path)
        try:
            audio = File(path, easy=True)
            if audio:
                item.title = first(audio.get("title")) or item.title
                item.artist = first(audio.get("artist")) or ""
                item.album = first(audio.get("album")) or ""
                if audio.info and getattr(audio.info, "length", None):
                    item.duration_ms = int(audio.info.length * 1000)
        except Exception:
            pass
        item.artwork = self.extract_embedded_art(path) or self.find_folder_art(path)
        if Path(path).suffix.lower() in VIDEO_EXTENSIONS:
            item.thumbnail = self.thumbnails.thumbnail_for_video(path)
        else:
            item.thumbnail = item.artwork
        return item

    def extract_embedded_art(self, path: str) -> Optional[str]:
        try:
            tagged = File(path)
            if not tagged:
                return None
            data = None
            mime = "image/jpeg"
            # MP3 ID3 APIC frames
            if getattr(tagged, "tags", None):
                for key, value in tagged.tags.items():
                    if key.startswith("APIC"):
                        data = value.data
                        mime = getattr(value, "mime", "image/jpeg") or "image/jpeg"
                        break
                # FLAC/Vorbis pictures
                pics = getattr(tagged, "pictures", None)
                if not data and pics:
                    data = pics[0].data
                    mime = getattr(pics[0], "mime", "image/jpeg") or "image/jpeg"
                # MP4 cover atoms
                if not data and "covr" in tagged.tags:
                    cover = tagged.tags["covr"][0]
                    data = bytes(cover)
                    mime = "image/png" if getattr(cover, "imageformat", None) == 14 else "image/jpeg"
            if not data:
                return None
            ext = ".png" if "png" in mime.lower() else ".jpg"
            out = ART_DIR / (hashlib.sha1(str(path).encode("utf-8")).hexdigest() + ext)
            if not out.exists():
                out.write_bytes(data)
            return str(out)
        except Exception:
            return None

    def find_folder_art(self, path: str) -> Optional[str]:
        folder = Path(path).parent
        for name in ("cover.jpg", "cover.png", "folder.jpg", "folder.png", "Cover.jpg", "Folder.jpg"):
            p = folder / name
            if p.exists():
                return str(p)
        return None

def first(v):
    return v[0] if isinstance(v, list) and v else None
