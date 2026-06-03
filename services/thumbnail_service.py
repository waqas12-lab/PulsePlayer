import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from utils.constants import THUMBNAIL_CACHE_DIR, VIDEO_EXTENSIONS

log = logging.getLogger(__name__)

class ThumbnailService:
    """Small cached thumbnail generator.

    Audio thumbnails come from embedded/folder artwork in MetadataService.
    Video thumbnails are generated with ffmpeg when available. If ffmpeg is not
    installed, the UI gracefully falls back to a video icon, so playback still works.
    """

    def __init__(self):
        THUMBNAIL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def thumbnail_for_video(self, path: str) -> Optional[str]:
        try:
            p = Path(path)
            if not p.exists() or p.suffix.lower() not in VIDEO_EXTENSIONS:
                return None
            out = THUMBNAIL_CACHE_DIR / (hashlib.sha1(str(p).encode('utf-8')).hexdigest() + '.jpg')
            if out.exists() and out.stat().st_size > 500:
                return str(out)
            ffmpeg = shutil.which('ffmpeg')
            if not ffmpeg:
                return None
            cmd = [
                ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
                '-ss', '00:00:03', '-i', str(p),
                '-frames:v', '1', '-vf', 'scale=96:-1', str(out)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            return str(out) if out.exists() and out.stat().st_size > 500 else None
        except Exception as exc:
            log.debug('Video thumbnail failed for %s: %s', path, exc)
            return None
