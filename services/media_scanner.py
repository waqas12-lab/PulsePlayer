from pathlib import Path
import logging
from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from utils.helpers import is_media_file
from services.metadata_service import MetadataService

log = logging.getLogger(__name__)

class ScanSignals(QObject):
    found = Signal(object)
    finished = Signal(int)

class FolderScanWorker(QRunnable):
    def __init__(self, folder: str):
        super().__init__()
        self.folder = folder
        self.signals = ScanSignals()
        self.meta = MetadataService()

    @Slot()
    def run(self):
        count = 0
        try:
            iterator = Path(self.folder).rglob("*")
            for p in iterator:
                try:
                    if p.is_file() and is_media_file(str(p)):
                        item = self.meta.read(str(p))
                        self.signals.found.emit(item)
                        count += 1
                except PermissionError:
                    log.warning("Permission denied while scanning: %s", p)
                except Exception as exc:
                    log.warning("Skipping media scan item %s: %s", p, exc)
        except Exception as exc:
            log.warning("Folder scan failed for %s: %s", self.folder, exc)
        finally:
            self.signals.finished.emit(count)
