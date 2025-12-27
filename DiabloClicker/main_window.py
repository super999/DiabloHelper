import logging
import os
from typing import Dict, Optional

from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox

from DiabloClicker.ui.ui_main_window import Ui_MainWindow



class DiabloClickerMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.checkBoxStartMonitor.stateChanged.connect(self.on_start_monitor_changed)
        self.pushButton_screenshot.clicked.connect(self.on_screenshot_clicked)  
   
    # show事件
    def showEvent(self, event):
        super().showEvent(event)
        # 在窗口显示时执行的代码
        logging.info("Main window is shown")
    
    def apply_theme(self, theme_name):
        from qt_material import apply_stylesheet
        app = QApplication.instance()
        if app:
            apply_stylesheet(app, theme=theme_name)

    def on_start_monitor_changed(self, state):
        if state == 2:  # 选中状态
            logging.info("Started monitoring")
        else:
            logging.info("Stopped monitoring")
    
    def on_screenshot_clicked(self):
        logging.info("Screenshot button clicked")
        QMessageBox.information(self, "Screenshot", "Screenshot taken!")
