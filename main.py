# main.py

from PySide6.QtWidgets import QApplication
from gui import CalculatorGUI
import sys

def main():
    app = QApplication(sys.argv)
    window = CalculatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
