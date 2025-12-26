#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/28 15:21
# @Author  : ChenXiaWen
# @File    : main.py.py
# @Path    : MuseLog/main.py


import logging
import sys
from PySide6.QtWidgets import QApplication
from qt_material import list_themes, apply_stylesheet

from DiabloClicker import logging_utils
from DiabloClicker.main_window import DiabloClickerMainWindow



def main():
    # 初始化日志
    logging_utils.init_logging()
    logging.info("Meta Story Board started")
    # 初始化全局服务
    # init_services()
    # 启动主窗口
    app = QApplication(sys.argv)
    print(list_themes())
    # 套用“dark_teal.xml”深色主题
    apply_stylesheet(app, theme='dark_cyan.xml')
    window = DiabloClickerMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
