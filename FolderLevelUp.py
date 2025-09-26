import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from gui import MainWindow
from utils import setup_logging

def main():
    setup_logging()

    app = QApplication(sys.argv)
    app.setFont(QFont("メイリオ", 10))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
