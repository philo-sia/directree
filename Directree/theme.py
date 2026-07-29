from PySide6.QtWidgets import QApplication

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
