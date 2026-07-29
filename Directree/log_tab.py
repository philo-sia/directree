from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton


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
