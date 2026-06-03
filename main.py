import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from utils.logger import setup_logger
from utils.constants import ICON_DIR, APP_NAME
from ui.main_window import PulsePlayerWindow


def main():
    setup_logger()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    icon_path = ICON_DIR / "pulse.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    try:
        win = PulsePlayerWindow()
        win.show()
        sys.exit(app.exec())
    except Exception as exc:
        QMessageBox.critical(None, "Pulse Player Error", str(exc))
        raise

if __name__ == "__main__":
    main()
