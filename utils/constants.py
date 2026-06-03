from pathlib import Path
from platformdirs import user_data_dir, user_cache_dir, user_log_dir

APP_NAME = "Pulse Player"
APP_AUTHOR = "Pulse Player"
TAGLINE = "Feel Every Beat, Watch Every Moment."

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
SUBTITLE_EXTENSIONS = {".srt", ".ass", ".ssa"}

# Always resolve files from the project folder, not from the terminal's current directory.
ROOT_DIR = Path(__file__).resolve().parents[1]
THEME_DIR = ROOT_DIR / "themes"
ICON_DIR = ROOT_DIR / "icons"
RESOURCE_DIR = ROOT_DIR / "resources"

# Writable application folders. This fixes macOS read-only filesystem errors when launched from '/'.
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
CACHE_DIR = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
LOG_DIR = Path(user_log_dir(APP_NAME, APP_AUTHOR))
SETTINGS_DIR = DATA_DIR / "settings"
DB_PATH = DATA_DIR / "database" / "pulse_player.sqlite3"
THUMBNAIL_CACHE_DIR = CACHE_DIR / "thumbnails"
METADATA_CACHE_DIR = CACHE_DIR / "metadata"

for directory in (DATA_DIR, CACHE_DIR, LOG_DIR, SETTINGS_DIR, DB_PATH.parent, THUMBNAIL_CACHE_DIR, METADATA_CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)
