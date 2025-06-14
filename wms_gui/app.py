import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
# Ensure correct import path if main_window is in the same directory
# For a package structure, it should be from .main_window
from .main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # It's good practice to instantiate translator once if possible,
    # but MainWindow handles its own instance for now.
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
