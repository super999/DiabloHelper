# -*- coding: utf-8 -*-
import logging
import os
from DiabloClicker.helper.singleton_def import Singleton
from PySide6.QtGui import QImage

class ImageShop(metaclass=Singleton):
    id_next = 0
    tmp_save_path = "screen_shoot/screenshot_tmp.png"
    tmp_cut_save_path = "screen_shoot/screenshot_small.png"

    def __init__(self):
        self.id_images = {}
        # 检查 目录是否存在，不存在则创建
        dir_path = os.path.dirname(self.tmp_save_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    @classmethod
    def inc_id(cls):
        cls.id_next += 1

    def add_img_pot(self, img: QImage):
        self.id_images[self.id_next] = img
        ret_id = self.id_next
        self.inc_id()
        return ret_id

    @classmethod
    def save_to_screen_shoot_dir(cls, img: QImage):
        img.save(cls.tmp_save_path)
        logging.warning(f'img has save to {cls.tmp_save_path}')

    @classmethod
    def save_small_pic(cls, img: QImage, x: int, y: int, w: int, h: int):
        img_small = img.copy(x, y, w, h)
        img_small.save(cls.tmp_cut_save_path)
