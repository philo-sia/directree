# DirecTree.pyw
import sys
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QFileDialog, QMessageBox,
    QDialog, QSpinBox, QDialogButtonBox, QFormLayout, QScrollArea,
    QListWidget, QComboBox, QCheckBox
)
from PySide6.QtGui import (
    QFontDatabase, QPixmap, QImage, QColor, QPainter, QFont, QFontMetrics,
    QShortcut, QKeySequence
)
from PySide6.QtCore import Qt, QTimer

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

DEFAULT_FONT_SIZE = 14
IMAGE_PADDING = 20
TEXT_COLOR = "black"
BUNDLED_FONT = "DejaVuSansMono.ttf"

# Maximum pixel dimension used when displaying the preview. Rendering the full
# (potentially huge) image into a QPixmap can freeze the UI, so the preview is
# always scaled down to fit within this box while the saved file keeps its
# native resolution.
MAX_PREVIEW_DIMENSION = 4096

# When a tree is too tall to be saved as a single image that common viewers can
# open, it is split into vertical "pages". Each page is kept at or below this
# height (a safe limit for virtually all image viewers).
MAX_PAGE_HEIGHT = 16384

# ---------------------------------------------------------------------------
# THEME
# ---------------------------------------------------------------------------

DARK_QSS = """
QMainWindow,
QWidget {
    background-color: #1b1e23;
    color: #cdd6f4;
    font-size: 10pt;
}
QLabel {
    background-color: transparent;
    color: #cdd6f4;
}
QPushButton {
    background-color: #2d3139;
    border: 1px solid #3b3f48;
    border-radius: 5px;
    padding: 6px 14px;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #3b404b;
    border-color: #89b4fa;
}
QPushButton:pressed {
    background-color: #1e2128;
}
QPushButton:disabled {
    background-color: #24272e;
    color: #585b70;
    border-color: #2d3139;
}
QPushButton[danger="true"] {
    background-color: #3d2020;
    border-color: #6e3a3a;
    color: #f38ba8;
}
QPushButton[danger="true"]:hover {
    background-color: #4d2828;
    border-color: #a04040;
}
QPushButton[danger="true"]:disabled {
    background-color: #24272e;
    color: #585b70;
    border-color: #2d3139;
}
QPushButton[flat="true"] {
    background-color: transparent;
    border: 1px solid transparent;
    padding: 4px 8px;
    font-size: 12pt;
}
QPushButton[flat="true"]:hover {
    background-color: #3b404b;
    border-color: #3b3f48;
}
QPlainTextEdit {
    background-color: #21242b;
    border: 1px solid #3b3f48;
    border-radius: 5px;
    padding: 8px;
    color: #cdd6f4;
    font-family: monospace;
    selection-background-color: #2e4a6e;
    selection-color: #cdd6f4;
}
QComboBox {
    background-color: #2d3139;
    border: 1px solid #3b3f48;
    border-radius: 5px;
    padding: 4px 10px;
    color: #cdd6f4;
    min-width: 160px;
}
QComboBox:hover {
    border-color: #89b4fa;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #24272e;
    border: 1px solid #3b3f48;
    color: #cdd6f4;
    selection-background-color: #2e4a6e;
    outline: none;
}
QSpinBox {
    background-color: #2d3139;
    border: 1px solid #3b3f48;
    border-radius: 5px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QSpinBox:hover {
    border-color: #89b4fa;
}
QCheckBox {
    background-color: transparent;
    color: #cdd6f4;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3b3f48;
    border-radius: 3px;
    background-color: #2d3139;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    background: #1b1e23;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3b3f48;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #1b1e23;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #3b3f48;
    min-width: 30px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #585b70;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}
QListWidget {
    background-color: #21242b;
    border: 1px solid #3b3f48;
    border-radius: 5px;
    color: #cdd6f4;
    padding: 6px;
    outline: none;
}
QListWidget::item {
    padding: 3px 4px;
}
QListWidget::item:selected {
    background-color: #2e4a6e;
}
QDialog {
    background-color: #1b1e23;
}
QMessageBox {
    background-color: #1b1e23;
}
QMessageBox QLabel {
    color: #cdd6f4;
}
QMessageBox QPushButton {
    min-width: 80px;
}
QToolTip {
    background-color: #2d3139;
    color: #cdd6f4;
    border: 1px solid #3b3f48;
    border-radius: 4px;
    padding: 4px 8px;
}
QTabWidget::pane {
    border: none;
    background-color: #1b1e23;
}
QTabBar::tab {
    background-color: #2d3139;
    color: #cdd6f4;
    border: 1px solid #3b3f48;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 6px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1b1e23;
    color: #cdd6f4;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #3b404b;
}
"""

LIGHT_QSS = """
QMainWindow,
QWidget {
    background-color: #eff1f5;
    color: #1e1e2e;
    font-size: 10pt;
}
QLabel {
    background-color: transparent;
    color: #1e1e2e;
}
QPushButton {
    background-color: #e6e9ef;
    border: 1px solid #ccd0da;
    border-radius: 5px;
    padding: 6px 14px;
    color: #1e1e2e;
}
QPushButton:hover {
    background-color: #dce0e8;
    border-color: #1e66f5;
}
QPushButton:pressed {
    background-color: #ccd0da;
}
QPushButton:disabled {
    background-color: #e6e9ef;
    color: #9ca0b0;
    border-color: #ccd0da;
}
QPushButton[danger="true"] {
    background-color: #fce4e4;
    border-color: #d20f39;
    color: #d20f39;
}
QPushButton[danger="true"]:hover {
    background-color: #f9d0d0;
}
QPushButton[danger="true"]:disabled {
    background-color: #e6e9ef;
    color: #9ca0b0;
    border-color: #ccd0da;
}
QPushButton[flat="true"] {
    background-color: transparent;
    border: 1px solid transparent;
    padding: 4px 8px;
    font-size: 12pt;
}
QPushButton[flat="true"]:hover {
    background-color: #dce0e8;
    border-color: #ccd0da;
}
QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 5px;
    padding: 8px;
    color: #1e1e2e;
    font-family: monospace;
    selection-background-color: #bcc8f0;
    selection-color: #1e1e2e;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 5px;
    padding: 4px 10px;
    color: #1e1e2e;
    min-width: 160px;
}
QComboBox:hover {
    border-color: #1e66f5;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    color: #1e1e2e;
    selection-background-color: #bcc8f0;
    outline: none;
}
QSpinBox {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 5px;
    padding: 4px 8px;
}
QSpinBox:hover {
    border-color: #1e66f5;
}
QCheckBox {
    background-color: transparent;
    color: #1e1e2e;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #ccd0da;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #1e66f5;
    border-color: #1e66f5;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    background: #eff1f5;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #ccd0da;
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #9ca0b0;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #eff1f5;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #ccd0da;
    min-width: 30px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #9ca0b0;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #ccd0da;
    border-radius: 5px;
    color: #1e1e2e;
    padding: 6px;
    outline: none;
}
QListWidget::item {
    padding: 3px 4px;
}
QListWidget::item:selected {
    background-color: #bcc8f0;
}
QDialog {
    background-color: #eff1f5;
}
QMessageBox {
    background-color: #eff1f5;
}
QMessageBox QLabel {
    color: #1e1e2e;
}
QMessageBox QPushButton {
    min-width: 80px;
}
QToolTip {
    background-color: #ffffff;
    color: #1e1e2e;
    border: 1px solid #ccd0da;
    border-radius: 4px;
    padding: 4px 8px;
}
QTabWidget::pane {
    border: none;
    background-color: #eff1f5;
}
QTabBar::tab {
    background-color: #dce0e8;
    color: #1e1e2e;
    border: 1px solid #ccd0da;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 6px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1e1e2e;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #e6e9ef;
}
"""

_CURRENT_THEME = "dark"


def apply_global_theme(app: QApplication, theme: str = "dark") -> None:
    global _CURRENT_THEME
    _CURRENT_THEME = theme
    app.setStyleSheet(DARK_QSS if theme == "dark" else LIGHT_QSS)


def toggle_global_theme(app: QApplication) -> str:
    new_theme = "light" if _CURRENT_THEME == "dark" else "dark"
    apply_global_theme(app, new_theme)
    return new_theme

FALLBACK_FONTS = [
    "Consolas",
    "Courier New",
    "Menlo",
    "Monaco",
    "DejaVu Sans Mono",
    "monospace",
]

SUPPORTED_FONTS = [
    "DejaVu Sans Mono",
    "Consolas",
    "Courier New",
    "Menlo",
    "Monaco",
    "Arial",
    "Times New Roman",
]

FONT_FILENAME_MAP = {
    "consolas": "consola.ttf",
    "courier new": "cour.ttf",
    "arial": "arial.ttf",
    "times new roman": "times.ttf",
}

SKIP_DIRECTORIES = {
    "__pycache__", "node_modules", ".git", ".svn", ".hg",
    "venv", "env", ".venv", "dist", "build", ".eggs",
    ".idea", ".vscode", ".vs", "bin", "obj", ".tox",
    "eggs", ".mypy_cache", ".pytest_cache", ".coverage",
    "htmlcov", ".sass-cache", "bower_components"
}

COMMON_EXTENSIONLESS_FILES = {
    "Makefile", "Dockerfile", "LICENSE", "LICENCE", "README", "CHANGELOG",
    "Procfile", "Gemfile", "Rakefile", "Vagrantfile", "CODEOWNERS",
    "AUTHORS", "MANIFEST", "Brewfile", "Justfile", "CMakeLists",
    "COPYING", "NOTICE", ".gitignore", ".gitattributes", ".dockerignore",
    ".editorconfig", ".env", ".env.example", ".npmrc", ".nvmrc",
    ".python-version",
}

COMMON_HIDDEN_DIRS = {
    ".github", ".gitlab", ".vscode", ".idea", ".config", ".cache", ".venv",
    ".git",
}

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

TREE_SKIP_RE = re.compile(
    r"^(folder path listing|volume serial number|directory path listing|"
    r"\d+\s+directories?,\s+\d+\s+files?|"
    r"\d+\s+dirs?,\s+\d+\s+files?|"
    r"[-\s]+)$",
    re.IGNORECASE,
)

TREE_BRANCH_RE = re.compile(
    r"(?P<branch>(?:├|└|╞|╘|╠|╚)[─═-]{2,}|(?:\+|\\|`|\|)-{2,3})"
)

# Reference annotations that can trail an item name in pasted trees. Everything
# from the first marker to end-of-line is display-only metadata, not part of the
# file/folder name (e.g. "SKILL.md  ← always loaded: core rules + routing").
ANNOTATION_MARKERS = ("←", "→", "<-", "->", "#")


def strip_tree_annotations(name: str) -> str:
    positions = [name.find(marker) for marker in ANNOTATION_MARKERS]
    positions = [pos for pos in positions if pos != -1]
    if positions:
        name = name[: min(positions)]
    return name.strip()


def clean_tree_text(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        indent = line[: len(line) - len(line.lstrip(" "))]
        content = strip_tree_annotations(line[len(indent):])
        cleaned_lines.append(indent + content)
    return "\n".join(cleaned_lines)


# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------

@dataclass
class ParsedLine:
    line_no: int
    raw: str
    depth: int
    name: str
    has_branch: bool


@dataclass
class OperationResult:
    created_files: list[str] = field(default_factory=list)
    created_dirs: list[str] = field(default_factory=list)
    deleted_files: list[str] = field(default_factory=list)
    deleted_dirs: list[str] = field(default_factory=list)
    renamed: list[tuple[str, str, bool]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_created(self) -> int:
        return len(self.created_files) + len(self.created_dirs)

    @property
    def total_deleted(self) -> int:
        return len(self.deleted_files) + len(self.deleted_dirs)

    @property
    def total_renamed(self) -> int:
        return len(self.renamed)

    @property
    def total_changed(self) -> int:
        return self.total_created + self.total_deleted + self.total_renamed

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


# ---------------------------------------------------------------------------
# GENERAL HELPERS
# ---------------------------------------------------------------------------

def app_base_dir() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text).replace("\ufeff", "")


def sanitize_name(name: str) -> tuple[str, bool, list[str], str | None]:
    warnings: list[str] = []

    original = name.strip()
    explicit_dir = original.endswith(("/", "\\"))

    if explicit_dir:
        original = original.rstrip("/\\").rstrip()

    if not original:
        return "", explicit_dir, warnings, "Empty item name."

    if original in {".", ".."}:
        return "", explicit_dir, warnings, f"Unsafe path component {original!r} is not allowed."

    if os.path.isabs(original) or re.match(r"^[A-Za-z]:[\\/]", original):
        return "", explicit_dir, warnings, f"Absolute paths are not allowed: {original!r}"

    sanitized = INVALID_CHARS_RE.sub("_", original).strip()

    if sanitized != original:
        warnings.append(
            f"Renamed {original!r} to {sanitized!r} because it contained invalid filename characters."
        )

    if not sanitized:
        return "", explicit_dir, warnings, f"Item {name!r} became empty after sanitization."

    if sanitized in {".", ".."}:
        return "", explicit_dir, warnings, f"Unsafe path component {sanitized!r} is not allowed."

    stem = sanitized.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED_NAMES:
        old = sanitized
        sanitized = f"{sanitized}_"
        warnings.append(
            f"Renamed reserved Windows filename {old!r} to {sanitized!r}."
        )

    if sys.platform == "win32":
        stripped = sanitized.rstrip(". ")
        if stripped != sanitized:
            warnings.append(
                f"Trimmed trailing spaces/periods from {sanitized!r} for Windows compatibility."
            )
            sanitized = stripped

        if not sanitized:
            return "", explicit_dir, warnings, f"Item {name!r} became empty after Windows trimming."

    return sanitized, explicit_dir, warnings, None


def safe_join_under_root(root: str, parent: str, name: str) -> tuple[str | None, str | None]:
    root_abs = os.path.abspath(root)
    full_path = os.path.abspath(os.path.join(parent, name))

    try:
        common = os.path.commonpath([root_abs, full_path])
    except ValueError:
        return None, "Path escapes root or is on another drive."

    if common != root_abs:
        return None, f"Path escapes selected root: {full_path}"

    return full_path, None


def safe_resolve_relative_path(root: str, rel_path: str) -> tuple[str | None, list[str], str | None]:
    warnings: list[str] = []
    parts = [part for part in rel_path.replace("\\", "/").split("/") if part]

    if not parts:
        return None, warnings, "Empty relative path."

    root_abs = os.path.abspath(root)
    current_parent = root_abs

    for part in parts:
        clean, _explicit_dir, part_warnings, error = sanitize_name(part)
        warnings.extend(part_warnings)

        if error:
            return None, warnings, error

        full_path, path_error = safe_join_under_root(root_abs, current_parent, clean)
        if path_error or full_path is None:
            return None, warnings, path_error

        current_parent = full_path

    return current_parent, warnings, None


# ---------------------------------------------------------------------------
# IMAGE GENERATION  (rendered natively with Qt's QPainter)
#
# This replaces the previous Pillow pipeline. Drawing text directly onto a
# QImage with QPainter avoids per-render font-file loading and lets the same
# native render path serve both the live preview and the saved file.
# ---------------------------------------------------------------------------

_MONOSPACE_FONTS = {
    "DejaVu Sans Mono", "Consolas", "Courier New", "Menlo", "Monaco",
}


def _qt_color(name: str, fallback: str) -> QColor:
    color = QColor(name)
    if not color.isValid():
        color = QColor(fallback)
    return color


def _build_tree_font(font_name: str, scale: float) -> QFont:
    size = max(1, int(DEFAULT_FONT_SIZE * scale))
    font = QFont(font_name)
    font.setPixelSize(size)

    if font_name in _MONOSPACE_FONTS:
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)

    return font


def _tree_geometry(
    lines: list[str],
    scale: float,
    bottom_padding_px: int,
    font_name: str,
):
    font = _build_tree_font(font_name, scale)
    metrics = QFontMetrics(font)

    line_height = max(1, metrics.height())
    line_spacing = max(1, int(4 * scale))
    pad = max(0, int(IMAGE_PADDING * scale))
    extra_bottom = max(0, int(bottom_padding_px * scale))

    max_width = 1
    for line in lines:
        width = metrics.horizontalAdvance(line or " ")
        if width > max_width:
            max_width = width

    width = max(1, int(max_width) + 2 * pad)

    return font, metrics, line_height, line_spacing, pad, extra_bottom, width


def _page_ranges(
    line_count: int,
    line_height: int,
    line_spacing: int,
    pad: int,
    extra_bottom: int,
    max_page_height: int,
) -> list[tuple[int, int]]:
    if line_count == 0:
        return [(0, 0)]

    limit = max_page_height - 2 * pad - extra_bottom
    limit = max(line_height, limit)

    ranges: list[tuple[int, int]] = []
    start = 0
    current_height = 0
    count = 0

    for i in range(line_count):
        add = line_height + (line_spacing if count > 0 else 0)

        if count > 0 and current_height + add > limit:
            ranges.append((start, i))
            start = i
            current_height = line_height
            count = 1
        else:
            current_height += add
            count += 1

    ranges.append((start, line_count))
    return ranges


def _render_pages(
    lines: list[str],
    font: QFont,
    metrics: QFontMetrics,
    line_height: int,
    line_spacing: int,
    pad: int,
    extra_bottom: int,
    width: int,
    ranges: list[tuple[int, int]],
    bg: QColor,
    fg: QColor,
) -> list[QImage]:
    pages: list[QImage] = []

    for index, (s, e) in enumerate(ranges):
        n = e - s
        height = max(
            1,
            n * line_height
            + max(0, n - 1) * line_spacing
            + 2 * pad
            + (extra_bottom if index == len(ranges) - 1 else 0),
        )

        img = QImage(width, height, QImage.Format.Format_RGB32)
        img.fill(bg)

        painter = QPainter(img)
        painter.setFont(font)
        painter.setPen(fg)

        y = pad + metrics.ascent()
        for i in range(s, e):
            painter.drawText(pad, y, lines[i] or "")
            y += line_height + line_spacing

        painter.end()
        pages.append(img)

    return pages


def render_tree_qimages(
    text: str,
    scale: float,
    bottom_padding_px: int,
    font_name: str,
    bg_color: str,
    text_color: str = TEXT_COLOR,
    max_page_height: int = MAX_PAGE_HEIGHT,
) -> list[QImage]:
    """Render the tree into one or more QImage pages (tiled when too tall)."""
    lines = text.splitlines() or [""]

    font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
        lines, scale, bottom_padding_px, font_name
    )

    # Bound the WIDTH as well as the height. A single very long line (e.g. a
    # deeply nested path) can make the image extremely wide, producing an
    # un-saveable giant image where QImage.save() silently fails. Scale the
    # whole render down so it always stays within the safe limit.
    if width > max_page_height:
        scale *= max_page_height / width
        font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
            lines, scale, bottom_padding_px, font_name
        )

    ranges = _page_ranges(len(lines), line_height, line_spacing, pad, extra_bottom, max_page_height)

    bg = _qt_color(bg_color, "white")
    fg = _qt_color(text_color, "black")

    return _render_pages(
        lines, font, metrics, line_height, line_spacing, pad, extra_bottom, width, ranges, bg, fg
    )


def render_tree_qimage_full(
    text: str,
    scale: float,
    bottom_padding_px: int,
    font_name: str,
    bg_color: str,
    text_color: str = TEXT_COLOR,
    max_height: int = MAX_PAGE_HEIGHT,
) -> QImage:
    """Render the entire tree into a single QImage, downscaling internally if
    the native height would exceed ``max_height`` (used for the preview)."""
    lines = text.splitlines() or [""]

    font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
        lines, scale, bottom_padding_px, font_name
    )

    n = len(lines)
    native_height = max(1, n * line_height + max(0, n - 1) * line_spacing + 2 * pad + extra_bottom)

    if native_height > max_height:
        reduced_scale = scale * (max_height / native_height)
        font, metrics, line_height, line_spacing, pad, extra_bottom, width = _tree_geometry(
            lines, reduced_scale, bottom_padding_px, font_name
        )

    bg = _qt_color(bg_color, "white")
    fg = _qt_color(text_color, "black")

    return _render_pages(
        lines, font, metrics, line_height, line_spacing, pad, extra_bottom, width,
        [(0, len(lines))], bg, fg,
    )[0]


# ---------------------------------------------------------------------------
# TREE PARSING
# ---------------------------------------------------------------------------

def parse_tree_line(raw_line: str, line_no: int) -> ParsedLine | None:
    line = strip_ansi(raw_line).rstrip()

    if not line.strip():
        return None

    stripped = line.strip()

    if stripped.startswith("#"):
        return None

    if TREE_SKIP_RE.match(stripped):
        return None

    branch_match = TREE_BRANCH_RE.search(line)

    if branch_match:
        prefix = line[:branch_match.start()].expandtabs(4)
        depth = len(prefix) // 4
        name = strip_tree_annotations(line[branch_match.end():])

        if not name:
            return None

        if name.startswith("(") and name.endswith(")"):
            return None

        return ParsedLine(
            line_no=line_no,
            raw=raw_line,
            depth=depth,
            name=name,
            has_branch=True,
        )

    expanded = line.expandtabs(4)
    leading_spaces = len(expanded) - len(expanded.lstrip(" "))
    depth = leading_spaces // 4
    name = strip_tree_annotations(expanded.strip())

    if not name:
        return None

    if name.startswith("(") and name.endswith(")"):
        return None

    return ParsedLine(
        line_no=line_no,
        raw=raw_line,
        depth=depth,
        name=name,
        has_branch=False,
    )


def parse_all_tree_lines(text_or_lines) -> list[ParsedLine]:
    if isinstance(text_or_lines, str):
        lines = text_or_lines.splitlines()
    else:
        lines = text_or_lines

    parsed: list[ParsedLine] = []

    for index, line in enumerate(lines, start=1):
        item = parse_tree_line(line, index)
        if item is not None:
            parsed.append(item)

    return parsed


def parse_creation_lines(lines: list[str], include_first_root: bool) -> tuple[list[ParsedLine], list[str]]:
    warnings: list[str] = []
    parsed = parse_all_tree_lines(lines)

    if not parsed:
        return [], warnings

    first = parsed[0]
    first_name = first.name.strip()

    if first_name in {".", "./"}:
        warnings.append(
            f"Line {first.line_no}: skipped root marker {first_name!r}; selected root directory is used instead."
        )
        return parsed[1:], warnings

    looks_like_tree_root = (
        len(parsed) > 1
        and not first.has_branch
        and parsed[1].has_branch
        and parsed[1].depth == 0
    )

    if looks_like_tree_root:
        if include_first_root:
            for item in parsed[1:]:
                item.depth += 1
            warnings.append(f"Line {first.line_no}: using {first.name!r} as top-level folder.")
        else:
            warnings.append(
                f"Line {first.line_no}: skipped apparent tree root header {first.name!r}."
            )
            parsed = parsed[1:]

    return parsed, warnings


def infer_is_directory(clean_name: str, explicit_dir: bool, has_children: bool, policy: str) -> bool:
    if explicit_dir:
        return True

    if has_children:
        return True

    lower = clean_name.lower()

    if lower in {item.lower() for item in COMMON_HIDDEN_DIRS}:
        return True

    if lower in {item.lower() for item in COMMON_EXTENSIONLESS_FILES}:
        return False

    _, extension = os.path.splitext(clean_name)

    if extension:
        return False

    if policy == "Extensionless items are files":
        return False

    return True


def parse_tree_to_paths(tree_text: str) -> tuple[str, set[tuple[str, bool]], list[str]]:
    warnings: list[str] = []
    parsed = parse_all_tree_lines(tree_text)

    if not parsed:
        return "", set(), ["No parseable tree lines found."]

    root_name = parsed[0].name.rstrip("/\\").strip()
    nodes = parsed[1:]

    paths: set[tuple[str, bool]] = set()
    stack: list[tuple[int, str]] = []

    for index, item in enumerate(nodes):
        has_children = index + 1 < len(nodes) and nodes[index + 1].depth > item.depth

        raw_name = item.name.strip()
        explicit_dir = raw_name.endswith(("/", "\\"))
        raw_name = raw_name.rstrip("/\\").strip()

        if not raw_name:
            warnings.append(f"Line {item.line_no}: skipped empty item.")
            continue

        while stack and item.depth <= stack[-1][0]:
            stack.pop()

        rel_parts = [part for _, part in stack] + [raw_name]
        rel_path = "/".join(rel_parts)

        is_dir = explicit_dir or has_children

        paths.add((rel_path, is_dir))

        if is_dir:
            stack.append((item.depth, raw_name))

    return root_name, paths, warnings


def compare_trees(original_tree: str, edited_tree: str) -> dict:
    original_root, original_paths, original_warnings = parse_tree_to_paths(original_tree)
    edited_root, edited_paths, edited_warnings = parse_tree_to_paths(edited_tree)

    warnings = original_warnings + edited_warnings

    if original_root and edited_root and original_root != edited_root:
        warnings.append(
            f"Root rename detected: {original_root!r} -> {edited_root!r}. "
            "Sync keeps the original scanned directory path and does not rename the root folder."
        )

    raw_removed = original_paths - edited_paths
    raw_added = edited_paths - original_paths
    unchanged = original_paths & edited_paths

    removed, added, renames = detect_renames(raw_removed, raw_added)

    if renames:
        warnings.append(
            f"Detected {len(renames)} rename(s). "
            "Sync will move these rather than delete and recreate."
        )

    return {
        "original_root": original_root,
        "edited_root": edited_root,
        "root_changed": bool(original_root and edited_root and original_root != edited_root),
        "added": sorted(added, key=lambda item: item[0]),
        "removed": sorted(removed, key=lambda item: item[0]),
        "renamed": renames,
        "unchanged": sorted(unchanged, key=lambda item: item[0]),
        "warnings": warnings,
    }


def detect_renames(removed: set, added: set) -> tuple[set, set, list]:
    renames = []
    still_removed = set(removed)
    still_added = set(added)

    removed_by_key = {}
    for path, is_dir in removed:
        parent = "/".join(path.split("/")[:-1])
        key = (parent, is_dir)
        removed_by_key.setdefault(key, []).append(path)

    added_by_key = {}
    for path, is_dir in added:
        parent = "/".join(path.split("/")[:-1])
        key = (parent, is_dir)
        added_by_key.setdefault(key, []).append(path)

    for key, removed_paths in removed_by_key.items():
        if key not in added_by_key:
            continue
        added_paths = added_by_key[key]
        for old_path, new_path in zip(sorted(removed_paths), sorted(added_paths)):
            renames.append((old_path, new_path, key[1]))
            still_removed.discard((old_path, key[1]))
            still_added.discard((new_path, key[1]))

    return still_removed, still_added, renames


# ---------------------------------------------------------------------------
# DIRECTORY SCANNING
# ---------------------------------------------------------------------------

def scan_directory_to_tree(root_path: str, show_hidden: bool = False, max_depth: int | None = None):
    lines: list[str] = []
    warnings: list[str] = []

    root_path = os.path.abspath(root_path)
    root_name = os.path.basename(root_path) or root_path
    lines.append(f"{root_name}/")

    stats = {
        "directories": 1,
        "files": 0,
        "skipped": 0,
        "warnings": 0,
    }

    def should_skip(name: str, hidden: bool) -> bool:
        if name in SKIP_DIRECTORIES:
            return True

        if hidden and not show_hidden:
            return True

        return False

    def scan_recursive(path: str, prefix: str = "", depth: int = 0):
        if max_depth is not None and depth >= max_depth:
            return

        try:
            entries = list(os.scandir(path))
        except PermissionError:
            warnings.append(f"Permission denied: {path}")
            stats["warnings"] += 1
            return
        except OSError as exc:
            warnings.append(f"Could not read {path}: {exc}")
            stats["warnings"] += 1
            return

        dirs = []
        files = []

        for entry in sorted(entries, key=lambda item: item.name.lower()):
            hidden = entry.name.startswith(".")

            if should_skip(entry.name, hidden):
                stats["skipped"] += 1
                continue

            if entry.is_symlink():
                warnings.append(f"Skipped symlink: {entry.path}")
                stats["skipped"] += 1
                continue

            try:
                if entry.is_dir(follow_symlinks=False):
                    dirs.append(entry)
                else:
                    files.append(entry)
            except OSError as exc:
                warnings.append(f"Skipped unreadable entry {entry.path}: {exc}")
                stats["skipped"] += 1

        all_entries = dirs + files

        for index, entry in enumerate(all_entries):
            is_last = index == len(all_entries) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            is_dir = entry in dirs
            display_name = f"{entry.name}/" if is_dir else entry.name
            lines.append(f"{prefix}{connector}{display_name}")

            if is_dir:
                stats["directories"] += 1
                scan_recursive(entry.path, prefix + extension, depth + 1)
            else:
                stats["files"] += 1

    scan_recursive(root_path)

    return "\n".join(lines), stats, warnings


# ---------------------------------------------------------------------------
# SYNC DIALOG  (preserved as a modal diff-before-apply view)
# ---------------------------------------------------------------------------

class SyncDialog(QDialog):
    def __init__(self, changes: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Sync Changes")
        self.setMinimumSize(700, 550)

        layout = QVBoxLayout(self)

        summary = QLabel(
            f"<b>Changes detected:</b><br>"
            f"<span style='color: #a6e3a1;'>Added: {len(changes['added'])}</span><br>"
            f"<span style='color: #f38ba8;'>Removed: {len(changes['removed'])}</span><br>"
            f"<span style='color: #fab387;'>Renamed: {len(changes.get('renamed', []))}</span><br>"
            f"Unchanged: {len(changes['unchanged'])}"
        )
        layout.addWidget(summary)

        if changes.get("warnings"):
            warning_label = QLabel(
                "<b style='color: #fab387;'>Warnings:</b><br>"
                + "<br>".join(changes["warnings"][:10])
            )
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)

        if changes.get("renamed"):
            layout.addWidget(QLabel("<b style='color: #fab387;'>Items to rename (move):</b>"))
            renamed_list = QListWidget()
            for old_path, new_path, is_dir in changes["renamed"]:
                kind = "Folder" if is_dir else "File"
                renamed_list.addItem(f"{kind}: {old_path}  ->  {new_path}")
            renamed_list.setMaximumHeight(120)
            layout.addWidget(renamed_list)

        if changes["added"]:
            layout.addWidget(QLabel("<b style='color: #a6e3a1;'>Items to create:</b>"))
            added_list = QListWidget()
            for path, is_dir in changes["added"]:
                added_list.addItem(f"{'[D]' if is_dir else '[F]'}: {path}")
            added_list.setMaximumHeight(150)
            layout.addWidget(added_list)

        if changes["removed"]:
            layout.addWidget(QLabel("<b style='color: #f38ba8;'>Items to remove:</b>"))
            removed_list = QListWidget()
            for path, is_dir in changes["removed"]:
                removed_list.addItem(f"{'[D]' if is_dir else '[F]'}: {path}")
            removed_list.setMaximumHeight(150)
            layout.addWidget(removed_list)

            warning = QLabel(
                "<b style='color: #f38ba8;'>Warning:</b> Files removed during sync "
                "are permanently deleted. Directories are removed only if empty."
            )
            warning.setWordWrap(True)
            layout.addWidget(warning)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Apply Safe Sync")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)


# =====================================================================
#  TAB 1 — EDIT & CREATE
# =====================================================================

class EditTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)

        # --- toolbar ---
        tb = QHBoxLayout()

        import_btn = QPushButton("\u21e9 Import Folder")
        import_btn.setToolTip("Scan an existing directory (Ctrl+Shift+O)")
        import_btn.clicked.connect(self._on_import)

        clear_btn = QPushButton("\u2716 Clear")
        clear_btn.clicked.connect(self._on_clear)

        copy_btn = QPushButton("\u2398 Copy")
        copy_btn.clicked.connect(self._on_copy)

        cleanup_btn = QPushButton("\U0001f9f9 Cleanup Tree")
        cleanup_btn.setToolTip(
            "Remove reference annotations (e.g. '  \u2190 notes', '# comment') "
            "from the pasted tree so created files/folders get clean names"
        )
        cleanup_btn.clicked.connect(self._on_cleanup)

        tb.addWidget(import_btn)
        tb.addWidget(clear_btn)
        tb.addWidget(copy_btn)
        tb.addWidget(cleanup_btn)
        tb.addStretch()

        self.mode_label = QLabel("")
        self.mode_label.setStyleSheet("QLabel { color: #89b4fa; font-weight: bold; }")
        tb.addWidget(self.mode_label)

        layout.addLayout(tb)

        # --- editor ---
        self.edit = QPlainTextEdit()
        self.edit.setPlaceholderText("Paste or scan a directory tree here …")
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(11)
        self.edit.setFont(font)
        layout.addWidget(self.edit, 1)

        # --- options row ---
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

        # --- root row ---
        root_row = QHBoxLayout()

        root_btn = QPushButton("\U0001f4c1 Select Root Directory")
        root_btn.clicked.connect(self._on_pick_root)

        self.root_lbl = QLabel()
        self.root_lbl.setWordWrap(True)

        root_row.addWidget(root_btn)
        root_row.addWidget(self.root_lbl, 1)
        layout.addLayout(root_row)

        # --- action row ---
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

    # ----- helpers that delegate to the main window -----

    def _on_clear(self):
        self.window().clear_input()

    def _on_copy(self):
        self.window().copy_to_clipboard()

    def _on_cleanup(self):
        self.window().cleanup_tree()

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

    # ----- sync-mode UI updates -----

    def enter_sync_mode(self, root_name: str):
        self.create_btn.setVisible(False)
        self.preview_btn.setVisible(False)
        self.sync_btn.setVisible(True)
        self.cancel_sync_btn.setVisible(True)
        self.mode_label.setText(f"SYNC  —  {root_name}")

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


# =====================================================================
#  TAB 2 — SAVE IMAGE  (replaces the old modal ImagePreviewDialog)
# =====================================================================

class ImageTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page = 0
        self._all_pages: list[QImage] = []
        self._setup_ui()
        self._setup_debounce()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- preview ---
        preview_col = QVBoxLayout()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.preview_lbl = QLabel("Image preview will appear here")
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.preview_lbl)
        preview_col.addWidget(self.scroll, 1)

        # --- page navigator ---
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

        # --- settings ---
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

    # ----- rendering -----

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
            self.preview_lbl.setText("Preview failed — check the tree text")
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

    # ----- save -----

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
                       else f"Saved as {len(saved)} page files (_1, _2, …)")
                QMessageBox.information(self, "Saved", msg)
            if failed:
                QMessageBox.critical(self, "Save Failed",
                    "Some files could not be written:\n" + "\n".join(failed[:10]))

        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))

    # ----- read text from the editor tab -----

    def _get_text(self) -> str:
        try:
            w = self.window()
            return w.edit_tab.edit.toPlainText()
        except Exception:
            return ""


# =====================================================================
#  TAB 3 — SCAN FOLDER  (replaces DirectoryScanDialog)
# =====================================================================

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
        browse_btn = QPushButton("\U0001f4c2 Browse…")
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

            # Push the tree into the editor tab
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

            # auto-switch to editor tab
            w.tabs.setCurrentIndex(0)

        except Exception as exc:
            QMessageBox.critical(self, "Scan Error", str(exc))

    def _copy(self):
        text = self.preview_edit.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            self.copy_btn.setText("Copied!")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))


# =====================================================================
#  TAB 4 — LOG  (replaces show_log dialog)
# =====================================================================

class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        self.log_list = QListWidget()
        layout.addWidget(self.log_list)

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self._clear)
        layout.addWidget(clear_btn)

    def refresh(self):
        self.log_list.clear()
        w = self.window()
        if not w.action_log:
            self.log_list.addItem("(no actions yet)")
        else:
            self.log_list.addItems(w.action_log)
        self.log_list.scrollToBottom()

    def _clear(self):
        w = self.window()
        w.action_log.clear()
        self.log_list.clear()
        self.log_list.addItem("(log cleared)")


# =====================================================================
#  MAIN APPLICATION WINDOW
# =====================================================================

class DirecTreeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DirecTree — Directory Structure Creator")
        self.setGeometry(100, 100, 1020, 740)

        # --- shared state ---
        self.root_dir = app_base_dir()
        self.undo_stack: list[OperationResult] = []
        self.action_log: list[str] = []
        self.original_tree: str | None = None
        self.sync_mode = False
        self.sync_root_path: str | None = None
        self.sync_root_name: str | None = None

        # --- tabs ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.edit_tab = EditTab()
        self.image_tab = ImageTab()
        self.scan_tab = ScanTab()
        self.log_tab = LogTab()

        self.tabs.addTab(self.edit_tab, "\u270f  Edit & Create")
        self.tabs.addTab(self.image_tab, "\U0001f5bc  Save Image")
        self.tabs.addTab(self.scan_tab, "\U0001f4c2  Scan Folder")
        self.tabs.addTab(self.log_tab, "\U0001f4cb  Log")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Theme toggle in the tab-bar corner
        self.theme_btn = QPushButton("\u263d")
        self.theme_btn.setProperty("flat", True)
        self.theme_btn.setToolTip("Toggle dark / light theme")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.tabs.setCornerWidget(self.theme_btn, Qt.Corner.TopRightCorner)

        # Cross-tab wiring: image tab re-renders when editor text changes
        self.edit_tab.edit.textChanged.connect(self.image_tab.schedule_preview)

        # Initial root label
        self.edit_tab.refresh_root_lbl(self.root_dir)

        # --- status bar ---
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        self.status_lbl = QLabel("Ready")
        self.status_bar.addWidget(self.status_lbl, 1)

        # Status counter widget for real-time stats
        self._stats_lbl = QLabel("")
        self.status_bar.addPermanentWidget(self._stats_lbl)

        # --- keyboard shortcuts ---
        self._setup_shortcuts()

        # --- drag & drop on editor ---
        self._setup_drag_drop()

    # -----------------------------------------------------------------
    #  Keyboard shortcuts
    # -----------------------------------------------------------------

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Return"), self, self.create_dirs)
        QShortcut(QKeySequence("Ctrl+Shift+P"), self, self.preview_create_plan)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self, self._open_image_tab)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self._open_scan_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.undo_last)
        QShortcut(QKeySequence("Ctrl+Shift+L"), self, self._open_log_tab)

    def _open_image_tab(self):
        self.tabs.setCurrentIndex(1)
        self.image_tab.schedule_preview()

    def _open_scan_tab(self):
        self.tabs.setCurrentIndex(2)

    def _open_log_tab(self):
        self.tabs.setCurrentIndex(3)
        self.log_tab.refresh()

    def _toggle_theme(self):
        new = toggle_global_theme(QApplication.instance())
        self.theme_btn.setText("\u2600" if new == "dark" else "\u263d")

    # -----------------------------------------------------------------
    #  Drag & drop
    # -----------------------------------------------------------------

    def _setup_drag_drop(self):
        self.edit_tab.edit.setAcceptDrops(True)

        orig_drag_enter = self.edit_tab.edit.dragEnterEvent
        orig_drop = self.edit_tab.edit.dropEvent

        def on_drag_enter(event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                orig_drag_enter(event)

        def on_drop(event):
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self._scan_and_import(path)
                    return
            orig_drop(event)

        self.edit_tab.edit.dragEnterEvent = on_drag_enter
        self.edit_tab.edit.dropEvent = on_drop

    def _scan_and_import(self, path: str):
        tree, stats, _warnings = scan_directory_to_tree(path)
        self.edit_tab.edit.setPlainText(tree)
        self.original_tree = tree
        self.sync_mode = True
        self.sync_root_path = os.path.abspath(path)
        self.sync_root_name = os.path.basename(self.sync_root_path)
        self.edit_tab.enter_sync_mode(self.sync_root_name)
        self.log("--- Action: Drag-drop scan ---")
        self.log(f"Scanned: {self.sync_root_path}")
        self.status_bar.showMessage(f"Imported {stats['directories']} dirs, {stats['files']} files")

    # -----------------------------------------------------------------
    #  Tab change handler
    # -----------------------------------------------------------------

    def _on_tab_changed(self, index: int):
        if index == 1:  # Image
            self.image_tab.schedule_preview()
        elif index == 3:  # Log
            self.log_tab.refresh()

    # -----------------------------------------------------------------
    #  Core actions  (called by EditTab buttons)
    # -----------------------------------------------------------------

    def clear_input(self):
        if self.edit_tab.edit.toPlainText().strip():
            answer = QMessageBox.question(
                self, "Clear Input",
                "Clear the current input and leave sync mode?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.edit_tab.edit.clear()
        self.original_tree = None
        self.sync_mode = False
        self.sync_root_path = None
        self.sync_root_name = None
        self.edit_tab.leave_sync_mode()
        self.status_bar.showMessage("Input cleared")

    def cancel_sync(self):
        self.original_tree = None
        self.sync_mode = False
        self.sync_root_path = None
        self.sync_root_name = None
        self.edit_tab.leave_sync_mode()
        self.status_bar.showMessage("Sync cancelled")

    def pick_root(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Root Directory", self.root_dir)
        if selected:
            self.root_dir = selected
            self.edit_tab.refresh_root_lbl(self.root_dir)
            self.status_bar.showMessage("Root directory set")

    def copy_to_clipboard(self):
        text = self.edit_tab.edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Empty", "Nothing to copy.")
            return
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Copied to clipboard")

    def cleanup_tree(self):
        text = self.edit_tab.edit.toPlainText()
        cleaned = clean_tree_text(text)
        if cleaned == text:
            self.status_bar.showMessage("Tree is already clean")
            return
        self.edit_tab.edit.setPlainText(cleaned)
        self.log("--- Action: Cleanup Tree ---")
        self.status_bar.showMessage("Tree cleaned")

    # ----- extensionless policy -----

    def current_extensionless_policy(self) -> str:
        text = self.edit_tab.kind_combo.currentText()
        if text == "Extensionless items are folders":
            return text
        if text == "Extensionless items are files":
            return text
        return "Smart detection"

    # ----- create / preview -----

    def preview_create_plan(self):
        text = self.edit_tab.edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Input Empty", "Please provide a directory structure.")
            return

        result = self._process_structure(text.splitlines(), self.root_dir, dry_run=True)
        self.show_result_dialog("Preview Create Plan", result, planned=True)

    def create_dirs(self):
        text = self.edit_tab.edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Input Empty", "Please provide a directory structure.")
            return

        plan = self._process_structure(text.splitlines(), self.root_dir, dry_run=True)

        if plan.has_errors:
            self.show_result_dialog("Validation Errors", plan, planned=True)
            self.status_bar.showMessage("Creation blocked — validation errors")
            return

        if plan.total_created == 0:
            self.show_result_dialog("Nothing New To Create", plan, planned=True)
            self.status_bar.showMessage("Nothing new to create")
            return

        message = (
            f"Create structure under:\n{os.path.abspath(self.root_dir)}\n\n"
            f"New directories: {len(plan.created_dirs)}\n"
            f"New files: {len(plan.created_files)}\n"
            f"Skipped existing: {len(plan.skipped)}\n"
            f"Warnings: {len(plan.warnings)}\n\n"
            "Existing files will not be overwritten.\n"
            "Undo will remove only newly-created items."
        )

        answer = QMessageBox.question(
            self, "Confirm Creation", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("Creation cancelled")
            return

        actual = self._process_structure(text.splitlines(), self.root_dir, dry_run=False)

        if actual.total_created:
            self.undo_stack.append(actual)
            self.edit_tab.set_undo_enabled(True)

        self.log(f"--- Action: Create at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.log_operation(actual)

        if actual.errors:
            self.show_result_dialog("Creation Completed With Errors", actual, planned=False)

        self._update_stats_display(actual)
        self.status_bar.showMessage(
            f"Created {actual.total_created} item(s); skipped {len(actual.skipped)}; errors {len(actual.errors)}"
        )

    def _process_structure(self, lines: list[str], root: str, dry_run: bool) -> OperationResult:
        result = OperationResult()
        root_abs = os.path.abspath(root)

        if not os.path.isdir(root_abs):
            result.errors.append(f"Root directory does not exist: {root_abs}")
            return result

        parsed, warnings = parse_creation_lines(
            lines,
            include_first_root=self.edit_tab.include_root_check.isChecked(),
        )
        result.warnings.extend(warnings)

        if not parsed:
            result.warnings.append("No usable structure lines were found.")
            return result

        policy = self.current_extensionless_policy()

        stack: list[dict[str, object]] = [{"depth": -1, "path": root_abs}]
        planned_dirs: set[str] = set()

        for index, item in enumerate(parsed):
            has_children = index + 1 < len(parsed) and parsed[index + 1].depth > item.depth

            raw_name = item.name.strip()
            if "#" in raw_name:
                raw_name = raw_name.split("#", 1)[0].rstrip()
            clean_name, explicit_dir, name_warnings, error = sanitize_name(raw_name)
            for warn in name_warnings:
                result.warnings.append(f"Line {item.line_no}: {warn}")

            inferred_dir = (
                infer_is_directory(clean_name, explicit_dir, has_children, policy)
                if not error else (has_children or explicit_dir)
            )

            while stack and item.depth <= int(stack[-1]["depth"]):
                stack.pop()
            if not stack:
                stack = [{"depth": -1, "path": root_abs}]

            parent = stack[-1]["path"]

            if error:
                result.errors.append(f"Line {item.line_no}: {error}")
                if inferred_dir:
                    stack.append({"depth": item.depth, "path": None})
                continue

            if parent is None:
                result.skipped.append(f"Line {item.line_no}: skipped {item.name!r} (invalid parent)")
                if inferred_dir:
                    stack.append({"depth": item.depth, "path": None})
                continue

            full_path, path_error = safe_join_under_root(root=root_abs, parent=str(parent), name=clean_name)

            if path_error or full_path is None:
                result.errors.append(f"Line {item.line_no}: {path_error}")
                if inferred_dir:
                    stack.append({"depth": item.depth, "path": None})
                continue

            if inferred_dir:
                self._handle_directory(result, full_path, item, stack, planned_dirs, dry_run)
            else:
                self._handle_file(result, full_path, str(parent), item, planned_dirs, dry_run)

        return result

    def _handle_directory(self, result: OperationResult, full_path: str, item: ParsedLine,
                          stack: list, planned_dirs: set, dry_run: bool):
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                result.skipped.append(f"Line {item.line_no}: already exists: {full_path}")
                stack.append({"depth": item.depth, "path": full_path})
            else:
                result.errors.append(f"Line {item.line_no}: file blocks dir: {full_path}")
                stack.append({"depth": item.depth, "path": None})
            return
        if dry_run:
            result.created_dirs.append(full_path)
            planned_dirs.add(full_path)
            stack.append({"depth": item.depth, "path": full_path})
            return
        try:
            os.mkdir(full_path)
            result.created_dirs.append(full_path)
            stack.append({"depth": item.depth, "path": full_path})
        except OSError as exc:
            result.errors.append(f"Line {item.line_no}: mkdir failed: {full_path}: {exc}")
            stack.append({"depth": item.depth, "path": None})

    def _handle_file(self, result: OperationResult, full_path: str, parent: str,
                     item: ParsedLine, planned_dirs: set, dry_run: bool):
        parent_ready = os.path.isdir(parent) or parent in planned_dirs
        if not parent_ready:
            result.errors.append(f"Line {item.line_no}: parent missing: {parent}")
            return
        if os.path.exists(full_path):
            if os.path.isfile(full_path):
                result.skipped.append(f"Line {item.line_no}: already exists: {full_path}")
            else:
                result.errors.append(f"Line {item.line_no}: dir blocks file: {full_path}")
            return
        if dry_run:
            result.created_files.append(full_path)
            return
        try:
            with open(full_path, "x", encoding="utf-8"):
                pass
            result.created_files.append(full_path)
        except OSError as exc:
            result.errors.append(f"Line {item.line_no}: create file failed: {full_path}: {exc}")

    # ----- sync -----

    def sync_changes(self):
        if not self.sync_mode or not self.original_tree or not self.sync_root_path:
            QMessageBox.warning(self, "Not in Sync Mode",
                "Sync is available after scanning a directory.")
            return

        current_tree = self.edit_tab.edit.toPlainText().strip()
        if not current_tree:
            QMessageBox.warning(self, "Empty Input", "No tree structure to sync.")
            return

        changes = compare_trees(self.original_tree, current_tree)

        if changes["root_changed"]:
            QMessageBox.warning(self, "Root Rename Not Supported",
                "The root line was changed. Sync does not rename the scanned root folder.\n"
                "Restore the original root line or rename the folder manually.")
            return

        if not changes["added"] and not changes["removed"]:
            QMessageBox.information(self, "No Changes", "No changes detected.")
            return

        dialog = SyncDialog(changes, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.status_bar.showMessage("Sync cancelled")
            return

        result = self._apply_sync_changes(changes)

        self.log(f"--- Action: Sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.log_operation(result)

        if result.total_created:
            self.undo_stack.append(result)
            self.edit_tab.set_undo_enabled(True)

        if result.errors or result.warnings:
            self.show_result_dialog("Sync Result", result, planned=False)

        if not result.errors:
            self.original_tree = current_tree
            self.edit_tab.enter_sync_mode(self.sync_root_name or "")

        self._update_stats_display(result)
        self.status_bar.showMessage(
            f"Sync: created {result.total_created}, deleted {result.total_deleted}, "
            f"skipped {len(result.skipped)}, errors {len(result.errors)}"
        )

    def _apply_sync_changes(self, changes: dict) -> OperationResult:
        result = OperationResult()
        if not self.sync_root_path:
            result.errors.append("Internal: missing sync root path")
            return result

        sync_root = os.path.abspath(self.sync_root_path)

        renames_sorted = sorted(
            changes.get("renamed", []),
            key=lambda item: item[0].count("/"),
        )

        for old_rel, new_rel, is_dir in renames_sorted:
            old_full, ow, oe = safe_resolve_relative_path(sync_root, old_rel)
            result.warnings.extend(ow)
            if oe or old_full is None:
                result.errors.append(f"Cannot resolve rename source {old_rel!r}: {oe}")
                continue

            new_full, nw, ne = safe_resolve_relative_path(sync_root, new_rel)
            result.warnings.extend(nw)
            if ne or new_full is None:
                result.errors.append(f"Cannot resolve rename target {new_rel!r}: {ne}")
                continue

            if not os.path.exists(old_full):
                result.skipped.append(f"Rename source already gone: {old_full}")
                continue

            if os.path.exists(new_full):
                result.errors.append(
                    f"Cannot rename {old_full} to {new_full}: target already exists."
                )
                continue

            try:
                shutil.move(old_full, new_full)
                if is_dir:
                    result.created_dirs.append(new_full)
                    result.deleted_dirs.append(old_full)
                else:
                    result.created_files.append(new_full)
                    result.deleted_files.append(old_full)
                result.renamed.append((old_rel, new_rel, is_dir))
            except OSError as exc:
                result.errors.append(f"Failed to rename {old_full} to {new_full}: {exc}")

        for rel_path, is_dir in sorted(changes["removed"], key=lambda x: x[0].count("/"), reverse=True):
            full_path, warnings, error = safe_resolve_relative_path(sync_root, rel_path)
            result.warnings.extend(warnings)
            if error or full_path is None:
                result.errors.append(f"Cannot remove {rel_path!r}: {error}")
                continue
            if not os.path.exists(full_path):
                result.skipped.append(f"Already gone: {full_path}")
                continue
            try:
                if is_dir:
                    if os.path.isdir(full_path):
                        os.rmdir(full_path)
                        result.deleted_dirs.append(full_path)
                    else:
                        result.errors.append(f"Expected dir, found file: {full_path}")
                else:
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                        result.deleted_files.append(full_path)
                    else:
                        result.errors.append(f"Expected file, found dir: {full_path}")
            except OSError as exc:
                result.errors.append(f"Remove failed {full_path}: {exc}")

        for rel_path, is_dir in sorted(changes["added"], key=lambda x: x[0].count("/")):
            full_path, warnings, error = safe_resolve_relative_path(sync_root, rel_path)
            result.warnings.extend(warnings)
            if error or full_path is None:
                result.errors.append(f"Cannot create {rel_path!r}: {error}")
                continue
            if os.path.exists(full_path):
                result.skipped.append(f"Already exists: {full_path}")
                continue
            try:
                if is_dir:
                    os.makedirs(full_path, exist_ok=False)
                    result.created_dirs.append(full_path)
                else:
                    parent = os.path.dirname(full_path)
                    os.makedirs(parent, exist_ok=True)
                    with open(full_path, "x", encoding="utf-8"):
                        pass
                    result.created_files.append(full_path)
            except OSError as exc:
                result.errors.append(f"Create failed {full_path}: {exc}")

        return result

    # ----- undo -----

    def undo_last(self):
        if not self.undo_stack:
            return

        answer = QMessageBox.question(
            self, "Confirm Safe Undo",
            "Undo the last creation?\n\n"
            "Only files created by the last action will be removed.\n"
            "Directories are removed only if empty.\n"
            "Sync-deleted files cannot be restored.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("Undo cancelled")
            return

        op = self.undo_stack.pop()
        rm_files = 0
        rm_dirs = 0
        failures: list[str] = []

        for path in reversed(op.created_files):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    rm_files += 1
            except OSError as exc:
                failures.append(f"File {path}: {exc}")

        for path in reversed(op.created_dirs):
            try:
                if os.path.isdir(path):
                    os.rmdir(path)
                    rm_dirs += 1
            except OSError as exc:
                failures.append(f"Dir {path}: {exc}")

        self.edit_tab.set_undo_enabled(bool(self.undo_stack))
        self.log(f"--- Action: Undo at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.log(f"Removed {rm_dirs} dirs, {rm_files} files")
        for f in failures:
            self.log(f"Undo warning: {f}")

        self.status_bar.showMessage(f"Undo: {rm_dirs} dirs, {rm_files} files removed")
        if failures:
            QMessageBox.warning(self, "Undo With Warnings",
                "\n".join(failures[:20]) + ("\n…" if len(failures) > 20 else ""))

    # ----- stats display -----

    def _update_stats_display(self, result: OperationResult):
        parts = []
        if result.created_dirs:
            parts.append(f"{len(result.created_dirs)} dirs")
        if result.created_files:
            parts.append(f"{len(result.created_files)} files")
        if result.deleted_dirs:
            parts.append(f"{len(result.deleted_dirs)} rm-dirs")
        if result.deleted_files:
            parts.append(f"{len(result.deleted_files)} rm-files")
        if result.skipped:
            parts.append(f"{len(result.skipped)} skipped")
        if result.errors:
            parts.append(f"{len(result.errors)} errors")
        self._stats_lbl.setText("  " + " | ".join(parts) if parts else "")

    # ----- log -----

    def log(self, text: str):
        self.action_log.append(text)

    def log_operation(self, result: OperationResult):
        for w in result.warnings:
            self.log(f"Warning: {w}")
        for s in result.skipped:
            self.log(f"Skipped: {s}")
        for e in result.errors:
            self.log(f"Error: {e}")
        for d in result.created_dirs:
            self.log(f"Created dir: {d}")
        for f in result.created_files:
            self.log(f"Created file: {f}")
        for old_path, new_path, is_dir in result.renamed:
            self.log(f"Renamed ({'folder' if is_dir else 'file'}): {old_path} -> {new_path}")
        for d in result.deleted_dirs:
            self.log(f"Deleted dir: {d}")
        for f in result.deleted_files:
            self.log(f"Deleted file: {f}")

    # ----- result dialog (still a modal — shows create/preview/sync outcomes) -----

    def format_result(self, result: OperationResult, planned: bool) -> str:
        dir_hdr = "Directories that would be created" if planned else "Directories created"
        file_hdr = "Files that would be created" if planned else "Files created"
        title = "Preview Summary" if planned else "Result Summary"

        lines = [
            title, "",
            f"Directories: {len(result.created_dirs)}",
            f"Files: {len(result.created_files)}",
            f"Deleted dirs: {len(result.deleted_dirs)}",
            f"Deleted files: {len(result.deleted_files)}",
            f"Renamed: {len(result.renamed)}",
            f"Skipped: {len(result.skipped)}",
            f"Warnings: {len(result.warnings)}",
            f"Errors: {len(result.errors)}",
            "",
        ]
        for label, vals in [
            (dir_hdr, result.created_dirs),
            (file_hdr, result.created_files),
            ("Directories deleted", result.deleted_dirs),
            ("Files deleted", result.deleted_files),
            ("Renamed", [f"{old} -> {new}" for old, new, _ in result.renamed]),
            ("Skipped", result.skipped),
            ("Warnings", result.warnings),
            ("Errors", result.errors),
        ]:
            if vals:
                lines.append(f"{label}:")
                lines.extend(f"  {v}" for v in vals)
                lines.append("")
        return "\n".join(lines)

    def show_result_dialog(self, title: str, result: OperationResult, planned: bool):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(750, 500)
        lay = QVBoxLayout(dlg)
        ed = QPlainTextEdit()
        ed.setReadOnly(True)
        ed.setPlainText(self.format_result(result, planned))
        f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        f.setPointSize(10)
        ed.setFont(f)
        lay.addWidget(ed)
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn.rejected.connect(dlg.close)
        lay.addWidget(btn)
        dlg.exec()


# =====================================================================
#  ENTRY POINT
# =====================================================================

def main():
    app = QApplication(sys.argv)
    apply_global_theme(app, "dark")

    window = DirecTreeApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
