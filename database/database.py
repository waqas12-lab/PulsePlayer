import sqlite3
import logging
from utils.constants import DB_PATH

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS media(
    path TEXT PRIMARY KEY,
    title TEXT,
    artist TEXT,
    album TEXT,
    duration_ms INTEGER DEFAULT 0,
    size INTEGER DEFAULT 0,
    date_added INTEGER DEFAULT 0,
    artwork TEXT
);
CREATE TABLE IF NOT EXISTS playlists(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS playlist_items(
    playlist_id INTEGER,
    path TEXT,
    position INTEGER,
    PRIMARY KEY(playlist_id, path)
);
"""

class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        log.info("Database: %s", DB_PATH)

    def upsert_media(self, item):
        self.conn.execute(
            """INSERT INTO media(path,title,artist,album,duration_ms,size,date_added,artwork)
               VALUES(?,?,?,?,?,?,strftime('%s','now'),?)
               ON CONFLICT(path) DO UPDATE SET title=excluded.title, artist=excluded.artist,
               album=excluded.album, duration_ms=excluded.duration_ms, artwork=excluded.artwork""",
            (item.path, item.title, item.artist, item.album, item.duration_ms, 0, item.artwork)
        )
        self.conn.commit()

    def all_media(self):
        return self.conn.execute("SELECT path,title,artist,album,duration_ms,artwork FROM media ORDER BY title").fetchall()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
