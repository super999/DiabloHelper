# -*- coding: utf-8 -*-
import logging
import win32gui  # type: ignore
from DiabloClicker.helper.singleton_def import Singleton

class DesktopService(metaclass=Singleton):
    hwnd_title = dict()

    @classmethod
    def clear_all_title(cls):
        cls.hwnd_title.clear()

    @classmethod
    def get_all_hwnd(cls, hwnd, lparam):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            if window_text:
                cls.hwnd_title.update({hwnd: window_text})
                logging.info(f'windows title: [{window_text}], hwnd: [{hwnd}]')
