import sys

from PySide6.QtWidgets import QApplication

from Directree.theme import apply_global_theme
from Directree.app import DirecTreeApp


def main():
    app = QApplication(sys.argv)
    apply_global_theme(app, "dark")

    window = DirecTreeApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
