import os
from typing import Dict, Optional

from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox

from DiabloClicker.ui.ui_main_window import Ui_MainWindow



class DiabloClickerMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
   

    
    def apply_theme(self, theme_name):
        from qt_material import apply_stylesheet
        app = QApplication.instance()
        if app:
            apply_stylesheet(app, theme=theme_name)

    