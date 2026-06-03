from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton

class SettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Pulse Player Settings")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("General"))
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(settings.get("theme", "dark"))
        self.resume = QCheckBox("Auto resume playback")
        self.resume.setChecked(settings.get("resume_playback", True))
        layout.addWidget(QLabel("Theme"))
        layout.addWidget(self.theme)
        layout.addWidget(self.resume)
        layout.addWidget(QLabel("Playback, Audio, Video, Subtitle and Cache options can be extended here."))
        save = QPushButton("Save Settings")
        save.clicked.connect(self.save)
        layout.addWidget(save)

    def save(self):
        self.settings.set("theme", self.theme.currentText())
        self.settings.set("resume_playback", self.resume.isChecked())
        self.accept()
