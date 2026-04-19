from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app.config import AppConfig
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Multimedia Recommender")

    config = AppConfig.from_env()
    window = MainWindow(config=config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
