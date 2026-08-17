"""Redesigned symbol library with thumbnail previews and better organization."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QSplitter, QGroupBox, QPushButton,
)
from PySide6.QtCore import Signal, Qt, QRectF, QMimeData, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QDrag, QIcon, QPixmap

from src.ui import ICONS
from src.symbols.library import SYMBOL_CATALOG, DISPLAY_NAMES


_SYMBOL_TILE_COLOR = QColor("#eaf2ea")
_SYMBOL_TILE_BORDER = QColor("#7f9c7f")


def _symbol_tile(sym_id):
    """Render a symbol on a light tile so its black strokes are visible in the
    dark side-panel (the raw comp_* icons are black-on-transparent and would
    otherwise vanish against the dark list background)."""
    base = ICONS.get(f"comp_{sym_id.split('_')[0]}")
    tile = QPixmap(52, 52)
    tile.fill(_SYMBOL_TILE_COLOR)
    p = QPainter(tile)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(_SYMBOL_TILE_BORDER, 1))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(0.5, 0.5, 51, 51), 6, 6)
    if base:
        base.paint(p, 2, 2, 48, 48)
    p.end()
    return QIcon(tile)


def _domain_button_css(mode):
    accent = ("#2e86c1", "#123a5e") if mode == "hydraulic" \
        else ("#2ec18a", "#12413a")
    border, bg = accent
    return f"""
        QPushButton {{
            background: #2b2b2b; color: #bbb;
            border: 1px solid #3d3d3d; border-radius: 4px;
            padding: 4px; font-weight: bold; font-size: 11px;
        }}
        QPushButton:hover {{ background: #3d3d3d; color: #eee; }}
        QPushButton:checked {{ background: {bg}; border-color: {border}; color: #fff; }}
    """


class _SymbolThumbnail(QListWidget):
    """List widget showing symbol thumbnails as icons with labels."""

    symbol_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(48, 48))
        self.setGridSize(QSize(64, 72))
        self.setFlow(QListWidget.TopToBottom)
        self.setResizeMode(QListWidget.Adjust)
        self.setUniformItemSizes(False)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setWordWrap(False)
        self.setStyleSheet("""
            QListWidget {
                background: #1e1e1e; color: #cccccc;
                border: 1px solid #3d3d3d; border-radius: 4px;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background: #2d4a6f;
            }
            QListWidget::item:selected {
                background: #1a5276;
                color: #ffffff;
            }
        """)
        self.currentItemChanged.connect(self._on_item_changed)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.DragOnly)

    def _on_item_changed(self, current, previous):
        if current is not None:
            sym_id = current.data(Qt.UserRole)
            if sym_id:
                self.symbol_selected.emit(sym_id)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return
        sym_id = item.data(Qt.UserRole)
        if not sym_id:
            return
        mime = QMimeData()
        mime.setText(str(sym_id))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(supportedActions)


class SymbolLibrary(QWidget):
    """Modern symbol library with icon thumbnails, search, and mode-aware filtering."""

    symbol_selected = Signal(str)
    mode_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "hydraulic"
        self._current_category = None
        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)

        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #aaa; font-size: 11px;")
        search_layout.addWidget(search_label)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter symbols...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        self._search.setStyleSheet("""
            QLineEdit {
                background: #1e1e1e; color: #ddd; border: 1px solid #444;
                border-radius: 3px; padding: 3px 8px;
            }
            QLineEdit:focus { border-color: #2e86c1; }
        """)
        search_layout.addWidget(self._search)
        layout.addLayout(search_layout)

        # Domain switch — the two distinct parts: Hydraulic / Pneumatic
        self._domain_layout = QHBoxLayout()
        self._domain_layout.setContentsMargins(0, 0, 0, 0)
        self._domain_layout.setSpacing(4)
        self._domain_buttons = {}
        for mode in ("hydraulic", "pneumatic"):
            btn = QPushButton("Hydraulic" if mode == "hydraulic" else "Pneumatic")
            btn.setCheckable(True)
            btn.setStyleSheet(_domain_button_css(mode))
            btn.clicked.connect(lambda checked, m=mode: self._request_mode(m))
            self._domain_buttons[mode] = btn
            self._domain_layout.addWidget(btn, 1)
        layout.addLayout(self._domain_layout)
        self._sync_domain_buttons()

        # Category tabs
        self._cat_layout = QHBoxLayout()
        self._cat_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_layout.setSpacing(2)
        layout.addLayout(self._cat_layout)

        self._category_buttons = {}
        layout.addStretch()

        # Symbol list with thumbnails
        self._list = _SymbolThumbnail()
        self._list.symbol_selected.connect(lambda sid: self.symbol_selected.emit(sid))
        layout.addWidget(self._list)

    def _populate(self):
        """Populate the library for the current mode."""
        self._list.clear()
        self._clear_category_buttons()

        # Capitalize mode to match catalog keys (e.g., "hydraulic" -> "Hydraulic")
        catalog_key = self._mode.capitalize()
        catalog = SYMBOL_CATALOG.get(catalog_key, {})
        all_symbols = []

        for cat_name, symbol_ids in sorted(catalog.items()):
            # Add category button
            btn = QPushButton(cat_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=cat_name: self._filter_category(c))
            btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d; color: #aaa; border: 1px solid #3d3d3d;
                    border-radius: 3px; padding: 3px 8px; font-size: 10px;
                }
                QPushButton:hover { background: #3d3d3d; color: #ddd; }
                QPushButton:checked { background: #1a5276; color: #fff; border-color: #2e86c1; }
            """)
            self._cat_layout.addWidget(btn)
            self._category_buttons[cat_name] = btn

            for sym_id in symbol_ids:
                name = DISPLAY_NAMES.get(sym_id, sym_id)
                item = QListWidgetItem(_symbol_tile(sym_id), name)
                item.setData(Qt.UserRole, sym_id)
                item.setToolTip(name)
                self._list.addItem(item)
                all_symbols.append((sym_id, name))

        # Select first category by default
        if self._category_buttons:
            first_cat = next(iter(self._category_buttons))
            self._filter_category(first_cat)

    def _filter_category(self, cat_name):
        """Show only symbols from the selected category."""
        # Update button states
        for cat, btn in self._category_buttons.items():
            btn.setChecked(cat == cat_name)

        text = self._search.text().lower().strip()
        # Capitalize mode to match catalog keys
        catalog_key = self._mode.capitalize()
        catalog = SYMBOL_CATALOG.get(catalog_key, {})
        symbols = catalog.get(cat_name, [])

        self._list.clear()
        for sym_id in symbols:
            name = DISPLAY_NAMES.get(sym_id, sym_id)
            if text and text not in name.lower():
                continue
            item = QListWidgetItem(_symbol_tile(sym_id), name)
            item.setData(Qt.UserRole, sym_id)
            item.setToolTip(name)
            self._list.addItem(item)

    def _on_search(self, text):
        """Re-apply search filter. Global search across all categories."""
        text = text.lower().strip()
        if not text:
            # Reset to first category
            if self._category_buttons:
                first_cat = next(iter(self._category_buttons))
                self._filter_category(first_cat)
            return
        # Global search: scan ALL categories, show matching symbols
        catalog_key = self._mode.capitalize()
        catalog = SYMBOL_CATALOG.get(catalog_key, {})
        matched = []
        for cat_name, symbol_ids in catalog.items():
            for sym_id in symbol_ids:
                name = DISPLAY_NAMES.get(sym_id, sym_id)
                if text in name.lower():
                    matched.append((sym_id, name))
        self._list.clear()
        # Uncheck all category buttons during global search
        for btn in self._category_buttons.values():
            btn.setChecked(False)
        for sym_id, name in matched:
            item = QListWidgetItem(_symbol_tile(sym_id), name)
            item.setData(Qt.UserRole, sym_id)
            item.setToolTip(name)
            self._list.addItem(item)

    def _clear_category_buttons(self):
        while self._cat_layout.count():
            item = self._cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._category_buttons.clear()

    def _request_mode(self, mode):
        self.set_mode(mode)
        self.mode_requested.emit(mode)

    def _sync_domain_buttons(self):
        for mode, btn in self._domain_buttons.items():
            btn.setChecked(mode == self._mode)

    def set_mode(self, mode):
        """Switch between hydraulic/pneumatic modes."""
        if mode == self._mode:
            return
        self._mode = mode
        self._populate()
        self._sync_domain_buttons()
