from __future__ import annotations

import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from tankflow.ui.theme import apply_app_theme
from tankflow.ui.main_window import TankFlowMainWindow


def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    try:
        with open("tankflow_crash_log.txt", "w", encoding="utf-8") as f:
            f.write(error_msg)
    except Exception:
        pass

    try:
        if QApplication.instance():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("TankFlow – Fatal Error")
            msg.setText("An unexpected error occurred and the application must close.")
            msg.setInformativeText("A file 'tankflow_crash_log.txt' was generated with details.")
            msg.setDetailedText(error_msg)
            msg.exec()
    except Exception:
        pass

    sys.__excepthook__(exctype, value, tb)
    sys.exit(1)


def main():
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    apply_app_theme(app)

    w = TankFlowMainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
