import logging
from logging.handlers import RotatingFileHandler
from utils.constants import LOG_DIR


def setup_logger() -> None:
    """Configure logging in a writable per-user folder.

    Important: never write to relative paths like ./logs because the user may run
    the app from / on macOS, where the filesystem is read-only.
    """
    log_file = LOG_DIR / "pulse_player.log"
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)
    logging.getLogger(__name__).info("Logs: %s", log_file)
