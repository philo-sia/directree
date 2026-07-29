import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QFormLayout,
    QScrollArea, QFileDialog, QMessageBox,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer

from Directree.constants import SUPPORTED_FONTS, MAX_PREVIEW_DIMENSION
from Directree.image_renderer import render_tree_qimages


class ImageTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page = 0
        self._all_pages: list = []
        self._setup_ui()
        self._setup_debounce()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        preview_col = QVBoxLayout()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.preview_lbl = QLabel("Image preview will appear here")
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.preview_lbl)
        preview_col.addWidget(self.scroll, 1)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("\u25c0 Prev")
        self.prev_btn.clicked.connect(self._prev_page)
        self.prev_btn.setEnabled(False)

        self.page_lbl = QLabel("")

        self.next_btn = QPushButton("Next \u25b6")
        self.next_btn.clicked.connect(self._next_page)
        self.next_btn.setEnabled(False)

        self.size_lbl = QLabel("")

        nav.addWidget(self.prev_btn)
        nav.addStretch()
        nav.addWidget(self.page_lbl)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        nav.addStretch()
        nav.addWidget(self.size_lbl)
        preview_col.addLayout(nav)

        layout.addLayout(preview_col, 3)

        settings = QFormLayout()

        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(50, 500)
        self.scale_spin.setValue(150)
        self.scale_spin.setSuffix(" %")
        settings.addRow("Scale:", self.scale_spin)

        self.bottom_padding_spin = QSpinBox()
        self.bottom_padding_spin.setRange(0, 500)
        self.bottom_padding_spin.setValue(10)
        self.bottom_padding_spin.setSuffix(" px")
        settings.addRow("Bottom padding:", self.bottom_padding_spin)

        self.font_combo = QComboBox()
        self.font_combo.addItems(SUPPORTED_FONTS)
        self.font_combo.setCurrentText("DejaVu Sans Mono")
        settings.addRow("Font:", self.font_combo)

        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["white", "lightgray", "gray", "black", "navy"])
        self.bg_combo.setCurrentText("white")
        settings.addRow("Background:", self.bg_combo)

        self.text_color_combo = QComboBox()
        self.text_color_combo.addItems(["black", "white", "gray", "blue", "green", "navy"])
        self.text_color_combo.setCurrentText("black")
        settings.addRow("Text color:", self.text_color_combo)

        self.bg_combo.currentTextChanged.connect(self._on_bg_changed)

        save_layout = QHBoxLayout()

        save_png = QPushButton("\U0001f5bc Save PNG")
        save_png.clicked.connect(lambda: self._do_save("PNG"))
        save_jpg = QPushButton("\U0001f5bc Save JPEG")
        save_jpg.clicked.connect(lambda: self._do_save("JPEG"))

        save_layout.addWidget(save_png, 1)
        save_layout.addWidget(save_jpg, 1)

        controls = QVBoxLayout()
        controls.addLayout(settings)
        controls.addStretch()
        controls.addLayout(save_layout)

        layout.addLayout(controls, 1)

    def _setup_debounce(self):
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(150)
        self._preview_timer.timeout.connect(self._render_preview)

        self.scale_spin.valueChanged.connect(self.schedule_preview)
        self.bottom_padding_spin.valueChanged.connect(self.schedule_preview)
        self.font_combo.currentTextChanged.connect(self.schedule_preview)
        self.text_color_combo.currentTextChanged.connect(self.schedule_preview)

    def _on_bg_changed(self):
        bg = self.bg_combo.currentText()
        tc = self.text_color_combo.currentText()
        if bg in {"black", "navy"} and tc == "black":
            self.text_color_combo.setCurrentText("white")
        elif bg in {"white", "lightgray"} and tc == "white":
            self.text_color_combo.setCurrentText("black")
        self.schedule_preview()

    def schedule_preview(self):
        self._preview_timer.start()

    def _render_preview(self):
        self._all_pages = []
        self._current_page = 0

        text = self._get_text()
        if not text.strip():
            self.preview_lbl.setText("No tree text to preview")
            self.page_lbl.setText("")
            self.size_lbl.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        try:
            self._all_pages = render_tree_qimages(
                text,
                self.scale_spin.value() / 100.0,
                self.bottom_padding_spin.value(),
                self.font_combo.currentText(),
                self.bg_combo.currentText(),
                self.text_color_combo.currentText(),
            )
        except Exception:
            self.preview_lbl.setText("Preview failed \u2014 check the tree text")
            return

        self._show_page(0)

    def _show_page(self, index: int):
        if not self._all_pages:
            return

        self._current_page = max(0, min(index, len(self._all_pages) - 1))
        page = self._all_pages[self._current_page]

        pix = QPixmap.fromImage(page)
        if pix.width() > MAX_PREVIEW_DIMENSION or pix.height() > MAX_PREVIEW_DIMENSION:
            pix = pix.scaled(
                MAX_PREVIEW_DIMENSION, MAX_PREVIEW_DIMENSION,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.preview_lbl.setPixmap(pix)
        self.preview_lbl.adjustSize()

        total = len(self._all_pages)
        self.page_lbl.setText("Page 1 of 1" if total == 1 else f"Page {self._current_page + 1} of {total}")
        self.size_lbl.setText(f"{page.width()}\u00d7{page.height()}")
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < total - 1)

    def _prev_page(self):
        self._show_page(self._current_page - 1)

    def _next_page(self):
        self._show_page(self._current_page + 1)

    def _do_save(self, format_name: str):
        if not self._all_pages:
            self._render_preview()
        if not self._all_pages:
            QMessageBox.warning(self, "Empty", "Nothing to save.")
            return

        ext = ".png" if format_name == "PNG" else ".jpg"
        filter_str = f"{format_name} (*{ext})"
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", filter_str)

        if not path:
            return

        if not path.lower().endswith(ext):
            path += ext

        try:
            failed: list[str] = []
            saved: list[str] = []

            if len(self._all_pages) == 1:
                if self._all_pages[0].save(path, format_name) and os.path.exists(path):
                    saved.append(path)
                else:
                    failed.append(path)
            else:
                base, e = os.path.splitext(path)
                if not e:
                    e = ext
                for i, page in enumerate(self._all_pages, 1):
                    pp = f"{base}_{i}{e}"
                    if page.save(pp, format_name) and os.path.exists(pp):
                        saved.append(pp)
                    else:
                        failed.append(pp)

            if saved and not failed:
                msg = (f"Saved to {saved[0]}" if len(saved) == 1
                       else f"Saved as {len(saved)} page files (_1, _2, \u2026)")
                QMessageBox.information(self, "Saved", msg)
            if failed:
                QMessageBox.critical(self, "Save Failed",
                    "Some files could not be written:\n" + "\n".join(failed[:10]))

        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    def _get_text(self) -> str:
        try:
            w = self.window()
            return w.edit_tab.edit.toPlainText()
        except Exception:
            return ""
