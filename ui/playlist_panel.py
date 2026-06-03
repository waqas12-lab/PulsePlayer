from pathlib import Path
from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QAbstractItemView, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QMenu
)
from PySide6.QtCore import Signal, Qt, QSize, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
from models.media_item import MediaItem
from utils.constants import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS


class PlaylistRow(QWidget):
    """Clean VLC-inspired playlist row with strong readable text and thumbnails."""

    def __init__(self, number: int, item: MediaItem):
        super().__init__()
        self.number = number
        self.item = item
        self.playing = False
        self.selected = False
        self.hovered = False
        self.setObjectName("PlaylistRow")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        root = QHBoxLayout(self)
        root.setContentsMargins(9, 6, 9, 6)
        root.setSpacing(9)

        self.play_icon = QLabel("")
        self.play_icon.setObjectName("PlaylistPlayingIcon")
        self.play_icon.setFixedWidth(18)
        self.play_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cover = QLabel()
        self.cover.setObjectName("PlaylistCover")
        self.cover.setFixedSize(32, 32)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_thumbnail()

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        title = (item.title or Path(item.path).stem).strip()
        self.title_label = QLabel(f"{number}. {title}")
        self.title_label.setObjectName("PlaylistTitle")
        self.title_label.setWordWrap(False)
        self.title_label.setToolTip(title)

        suffix = Path(item.path).suffix.upper().replace('.', '') or 'FILE'
        info_parts = []
        if item.artist:
            info_parts.append(item.artist)
        if item.album:
            info_parts.append(item.album)
        if not info_parts:
            info_parts.append("Local media")
        info_parts.append(suffix)
        self.info_label = QLabel("  •  ".join(info_parts))
        self.info_label.setObjectName("PlaylistInfo")
        self.info_label.setWordWrap(False)

        file_name = Path(item.path).name
        self.path_label = QLabel(file_name)
        self.path_label.setObjectName("PlaylistPath")
        self.path_label.setWordWrap(False)
        self.path_label.setToolTip(item.path)

        text_col.addWidget(self.title_label)
        text_col.addWidget(self.info_label)
        text_col.addWidget(self.path_label)
        root.addWidget(self.play_icon)
        root.addWidget(self.cover)
        root.addLayout(text_col, 1)

    def _load_thumbnail(self):
        suffix = Path(self.item.path).suffix.lower()
        thumb = self.item.thumbnail or self.item.artwork
        if thumb and Path(thumb).exists():
            pix = QPixmap(thumb)
            if not pix.isNull():
                self.cover.setPixmap(pix.scaled(
                    32, 32,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                ))
                self.cover.setText("")
                return
        self.cover.setPixmap(QPixmap())
        self.cover.setText("♪" if suffix in AUDIO_EXTENSIONS else "▣" if suffix in VIDEO_EXTENSIONS else "●")

    def set_number(self, number: int):
        self.number = number
        title = self.item.title or Path(self.item.path).stem
        self.title_label.setText(f"{number}. {title}")

    def set_playing(self, playing: bool):
        self.playing = bool(playing)
        self.play_icon.setText("▶" if self.playing else "")
        self._refresh_state()

    def set_selected_state(self, selected: bool):
        self.selected = bool(selected)
        self._refresh_state()

    def enterEvent(self, event):
        self.hovered = True
        self._refresh_state()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self._refresh_state()
        super().leaveEvent(event)

    def _refresh_state(self):
        self.setProperty("playing", self.playing)
        self.setProperty("selected", self.selected)
        self.setProperty("hovered", self.hovered)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class PlaylistPanel(QListWidget):
    play_requested = Signal(int)
    remove_requested = Signal(int)
    clear_requested = Signal()
    properties_requested = Signal(int)

    def __init__(self):
        super().__init__()
        self.items_data = []
        self.playing_row = -1
        self.setObjectName("PlaylistPanel")
        self.setMinimumWidth(390)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAlternatingRowColors(False)
        self.setIconSize(QSize(32, 32))
        self.setUniformItemSizes(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemDoubleClicked.connect(lambda _: self.play_requested.emit(self.currentRow()))
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.model().rowsMoved.connect(self._sync_after_drag)
        self.itemSelectionChanged.connect(self._update_selected_rows)

    def add_media(self, item: MediaItem):
        self.items_data.append(item)
        row_number = len(self.items_data)
        list_item = QListWidgetItem()
        list_item.setData(Qt.ItemDataRole.UserRole, item.path)
        list_item.setToolTip(item.path)
        list_item.setSizeHint(QSize(360, 66))
        self.addItem(list_item)
        self.setItemWidget(list_item, PlaylistRow(row_number, item))

    def clear_all(self):
        self.items_data.clear()
        self.playing_row = -1
        self.clear()

    def current_item(self):
        row = self.currentRow()
        return self.items_data[row] if 0 <= row < len(self.items_data) else None

    def remove_selected(self):
        self.remove_row(self.currentRow())

    def remove_row(self, row: int):
        if 0 <= row < len(self.items_data):
            self.items_data.pop(row)
            self.takeItem(row)
            if row == self.playing_row:
                self.playing_row = -1
            elif row < self.playing_row:
                self.playing_row -= 1
            self.renumber()
            self.set_playing_row(self.playing_row)
            self._update_selected_rows()

    def renumber(self):
        for i in range(self.count()):
            widget = self.itemWidget(self.item(i))
            if isinstance(widget, PlaylistRow):
                widget.set_number(i + 1)

    def set_playing_row(self, row: int):
        self.playing_row = row
        for i in range(self.count()):
            widget = self.itemWidget(self.item(i))
            if isinstance(widget, PlaylistRow):
                widget.set_playing(i == row)

    def _update_selected_rows(self):
        selected_rows = {index.row() for index in self.selectedIndexes()}
        for i in range(self.count()):
            widget = self.itemWidget(self.item(i))
            if isinstance(widget, PlaylistRow):
                widget.set_selected_state(i in selected_rows)

    def _show_context_menu(self, pos):
        row = self.indexAt(pos).row()
        if row >= 0:
            self.setCurrentRow(row)
        menu = QMenu(self)
        play = menu.addAction("▶ Play")
        remove = menu.addAction("Remove")
        clear = menu.addAction("Remove All")
        menu.addSeparator()
        open_location = menu.addAction("Open Location")
        properties = menu.addAction("Properties")

        has_item = row >= 0
        play.setEnabled(has_item)
        remove.setEnabled(has_item)
        open_location.setEnabled(has_item)
        properties.setEnabled(has_item)

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if not action:
            return
        if action == play:
            self.play_requested.emit(row)
        elif action == remove:
            self.remove_requested.emit(row)
        elif action == clear:
            self.clear_requested.emit()
        elif action == open_location and has_item:
            p = Path(self.items_data[row].path)
            if p.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.parent)))
        elif action == properties and has_item:
            self.properties_requested.emit(row)

    def _sync_after_drag(self, *args):
        old_current_path = None
        if 0 <= self.playing_row < len(self.items_data):
            old_current_path = self.items_data[self.playing_row].path
        path_to_item = {m.path: m for m in self.items_data}
        ordered = []
        for i in range(self.count()):
            p = self.item(i).data(Qt.ItemDataRole.UserRole) or self.item(i).toolTip()
            if p in path_to_item:
                ordered.append(path_to_item[p])
        if len(ordered) == len(self.items_data):
            self.items_data = ordered
            self.renumber()
            if old_current_path:
                self.playing_row = next((i for i, m in enumerate(self.items_data) if m.path == old_current_path), -1)
                self.set_playing_row(self.playing_row)
            self._update_selected_rows()
