import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QComboBox, QCheckBox,
)
from PySide6.QtGui import QFontDatabase

from Directree.constants import SUPPORTED_FONTS


class EditTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)

        tb = QHBoxLayout()

        import_btn = QPushButton("\u21e9 Import Folder")
        import_btn.setToolTip("Scan an existing directory (Ctrl+Shift+O)")
        import_btn.clicked.connect(self._on_import)

        clear_btn = QPushButton("\u2716 Clear")
        clear_btn.clicked.connect(self._on_clear)

        copy_btn = QPushButton("\u2398 Copy")
        copy_btn.clicked.connect(self._on_copy)

        tb.addWidget(import_btn)
        tb.addWidget(clear_btn)
        tb.addWidget(copy_btn)
        tb.addStretch()

        self.mode_label = QLabel("")
        self.mode_label.setStyleSheet("QLabel { color: #89b4fa; font-weight: bold; }")
        tb.addWidget(self.mode_label)

        layout.addLayout(tb)

        self.edit = QPlainTextEdit()
        self.edit.setPlaceholderText("Paste or scan a directory tree here \u2026")
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(11)
        self.edit.setFont(font)
        layout.addWidget(self.edit, 1)

        opts = QHBoxLayout()

        self.include_root_check = QCheckBox("Include first tree root line as folder")
        self.include_root_check.setChecked(False)
        self.include_root_check.setToolTip(
            "Unchecked: a leading tree header like '.' or 'project/' is treated "
            "as display-only."
        )

        self.kind_combo = QComboBox()
        self.kind_combo.addItems([
            "Smart detection",
            "Extensionless items are folders",
            "Extensionless items are files",
        ])

        opts.addWidget(self.include_root_check)
        opts.addWidget(QLabel("Extensionless names:"))
        opts.addWidget(self.kind_combo)
        opts.addStretch()
        layout.addLayout(opts)

        root_row = QHBoxLayout()

        root_btn = QPushButton("\U0001f4c1 Select Root Directory")
        root_btn.clicked.connect(self._on_pick_root)

        self.root_lbl = QLabel()
        self.root_lbl.setWordWrap(True)

        root_row.addWidget(root_btn)
        root_row.addWidget(self.root_lbl, 1)
        layout.addLayout(root_row)

        actions = QHBoxLayout()

        self.preview_btn = QPushButton("\U0001f50d Preview Plan")
        self.preview_btn.clicked.connect(self._on_preview)

        self.create_btn = QPushButton("\u25b6 Create Structure")
        self.create_btn.clicked.connect(self._on_create)

        self.sync_btn = QPushButton("\U0001f504 Sync Changes")
        self.sync_btn.clicked.connect(self._on_sync)
        self.sync_btn.setVisible(False)

        self.cancel_sync_btn = QPushButton("\u2716 Cancel Sync")
        self.cancel_sync_btn.setVisible(False)
        self.cancel_sync_btn.clicked.connect(self._on_cancel_sync)

        actions.addWidget(self.preview_btn)
        actions.addWidget(self.create_btn, 1)
        actions.addWidget(self.sync_btn, 1)
        actions.addWidget(self.cancel_sync_btn)
        actions.addStretch()

        self.undo_btn = QPushButton("\u21a9 Undo Last Creation")
        self.undo_btn.clicked.connect(self._on_undo)
        self.undo_btn.setEnabled(False)
        self.undo_btn.setProperty("danger", True)
        actions.addWidget(self.undo_btn)

        layout.addLayout(actions)

    def _on_clear(self):
        self.window().clear_input()

    def _on_copy(self):
        self.window().copy_to_clipboard()

    def _on_import(self):
        self.window()._open_scan_tab()

    def _on_pick_root(self):
        self.window().pick_root()

    def _on_preview(self):
        self.window().preview_create_plan()

    def _on_create(self):
        self.window().create_dirs()

    def _on_sync(self):
        self.window().sync_changes()

    def _on_cancel_sync(self):
        self.window().cancel_sync()

    def _on_undo(self):
        self.window().undo_last()

    def enter_sync_mode(self, root_name: str):
        self.create_btn.setVisible(False)
        self.preview_btn.setVisible(False)
        self.sync_btn.setVisible(True)
        self.cancel_sync_btn.setVisible(True)
        self.mode_label.setText(f"SYNC  \u2014  {root_name}")

    def leave_sync_mode(self):
        self.create_btn.setVisible(True)
        self.preview_btn.setVisible(True)
        self.sync_btn.setVisible(False)
        self.cancel_sync_btn.setVisible(False)
        self.mode_label.setText("")

    def set_undo_enabled(self, enabled: bool):
        self.undo_btn.setEnabled(enabled)

    def refresh_root_lbl(self, path: str):
        self.root_lbl.setText(f"Root: {os.path.abspath(path)}")



