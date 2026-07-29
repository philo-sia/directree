import os

from PySide6.QtWidgets import (
    QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QCheckBox, QSpinBox,
    QFormLayout, QFileDialog, QMessageBox,
)
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QTimer

from Directree.scanner import scan_directory_to_tree


class ScanTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_path: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        path_row = QHBoxLayout()
        browse_btn = QPushButton("\U0001f4c2 Browse\u2026")
        browse_btn.clicked.connect(self._browse)

        self.path_lbl = QLabel("No directory selected")
        self.path_lbl.setWordWrap(True)

        path_row.addWidget(browse_btn)
        path_row.addWidget(self.path_lbl, 1)
        layout.addLayout(path_row)

        opts = QFormLayout()
        self.hidden_check = QCheckBox()
        self.hidden_check.setToolTip("Include entries whose name starts with '.'")
        opts.addRow("Include hidden:", self.hidden_check)

        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(0, 50)
        self.depth_spin.setValue(0)
        self.depth_spin.setSpecialValueText("Unlimited")
        opts.addRow("Max depth:", self.depth_spin)
        layout.addLayout(opts)

        gen_btn = QPushButton("\u2699 Generate Tree")
        gen_btn.clicked.connect(self._generate)
        layout.addWidget(gen_btn)

        header = QHBoxLayout()
        header.addWidget(QLabel("Preview:"))
        header.addStretch()
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy)
        self.copy_btn.setEnabled(False)
        header.addWidget(self.copy_btn)
        layout.addLayout(header)

        self.preview_edit = QPlainTextEdit()
        self.preview_edit.setReadOnly(True)
        f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        f.setPointSize(10)
        self.preview_edit.setFont(f)
        layout.addWidget(self.preview_edit)

        self.stats_lbl = QLabel("")
        layout.addWidget(self.stats_lbl)

        layout.addStretch()

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if path:
            self._selected_path = os.path.abspath(path)
            self.path_lbl.setText(self._selected_path)
            self.preview_edit.clear()

    def _generate(self):
        if not self._selected_path:
            QMessageBox.warning(self, "No Directory", "Select a directory first.")
            return

        try:
            d = self.depth_spin.value()
            tree, stats, warnings = scan_directory_to_tree(
                self._selected_path,
                show_hidden=self.hidden_check.isChecked(),
                max_depth=None if d == 0 else d,
            )
            self.preview_edit.setPlainText(tree)
            self.copy_btn.setEnabled(True)
            self.stats_lbl.setText(
                f"  Dirs: {stats['directories']}  |  Files: {stats['files']}"
                f"  |  Skipped: {stats['skipped']}  |  Warnings: {len(warnings)}"
            )

            w = self.window()
            w.edit_tab.edit.setPlainText(tree)
            w.original_tree = tree
            w.sync_mode = True
            w.sync_root_path = self._selected_path
            w.sync_root_name = os.path.basename(self._selected_path)
            w.edit_tab.enter_sync_mode(w.sync_root_name)
            w.log("--- Action: Scan Directory ---")
            w.log(f"Scanned: {self._selected_path}")
            w.status_bar.showMessage(f"Scanned {stats['directories']} dirs, {stats['files']} files")

            w.tabs.setCurrentIndex(0)

        except Exception as exc:
            QMessageBox.critical(self, "Scan Error", str(exc))

    def _copy(self):
        text = self.preview_edit.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            self.copy_btn.setText("Copied!")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))



