from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from utils.constants import ICON_DIR

class TrayService:
    def __init__(self, window):
        self.window = window
        icon_path = ICON_DIR / "pulse.svg"
        self.tray = QSystemTrayIcon(QIcon(str(icon_path)) if icon_path.exists() else QIcon(), window)
        menu = QMenu()
        for text, callback in [
            ("Play/Pause", window.toggle_play),
            ("Next", window.next_media),
            ("Previous", window.previous_media),
            ("Stop", window.stop),
            ("Mute", window.toggle_mute),
            ("Open Pulse Player", window.showNormal),
            ("Exit", window.close),
        ]:
            act = QAction(text, window)
            act.triggered.connect(callback)
            menu.addAction(act)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda *_: window.showNormal())
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def notify(self, title, message):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2500)
