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


def verify_activation_code():
    """验证激活码"""
    import os
    from PySide6.QtWidgets import QMessageBox, QWidget
    file_path = os.path.join(os.getcwd(), 'activation_codes.dat')
    if not os.path.exists(file_path):
        QMessageBox.warning(QWidget(), "提示", f"未找到激活码文件{file_path}，请联系管理员。")
        sys.exit(0)
    from bt_register.service.register.register_service import RegisterService
    success = RegisterService().verify_activation_code(file_path)
    if not success:
        QMessageBox.warning(QWidget(), '警告', '激活码验证失败')
        sys.exit(0)
    expiry_date = RegisterService().get_expiry_date()
    logging.info(f'激活码验证成功,有效期至：{expiry_date}')
    # QMessageBox.information(None, '提示', f'激活码验证成功,有效期至：{expiry_date}')
    if RegisterService().is_expired():
        QMessageBox.warning(QWidget(), '警告', '激活码已过期，请联系管理员。')
        sys.exit(0)


def main():
    # 初始化日志
    logging_utils.init_logging()
    logging.info("Diablo Clicker started")
    # 初始化全局服务
    # init_services()
    # 启动主窗口
    app = QApplication(sys.argv)
    print(list_themes())
    verify_activation_code()
    # 套用“dark_teal.xml”深色主题
    apply_stylesheet(app, theme='dark_cyan.xml')
    window = DiabloClickerMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
