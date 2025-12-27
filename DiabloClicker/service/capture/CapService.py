import logging
import win32gui # type: ignore
from PySide6.QtWidgets import QApplication
from DiabloClicker.helper.singleton_def import Singleton
from DiabloClicker.service.db_op.desktop_op import DesktopService
from DiabloClicker.service.img_ctrl.image_shop import ImageShop


class CapService(metaclass=Singleton):    
    target_hwmd = None
    target_program_title = '暗黑破坏神IV'

    def get_target_hwnd(self):
        logging.warning(f'获取目标窗口句柄,标题为 {self.target_program_title}')
        for hwnd, title in DesktopService().hwnd_title.items():
            if title == self.target_program_title:
                logging.warning(f'找到目标窗口句柄: {hwnd}, 标题为 {title}')
                return hwnd
            else:
                logging.warning(f'当前窗口标题为 {title}，不匹配')
        logging.warning('未找到目标窗口句柄')

    
    def cap_window(self):
        logging.warning('调用截屏')
        logging.warning('先获取窗口名称')
        win32gui.EnumWindows(DesktopService().get_all_hwnd, 0)
        logging.warning(f'call cap window end {DesktopService().hwnd_title}')
        # 获取是否有商人传说进程
        self.target_hwmd = self.get_target_hwnd()
        if not self.target_hwmd:
            return
        screen = QApplication.primaryScreen()
        img = screen.grabWindow(self.target_hwmd).toImage()
        if not img:
            return
        ImageShop().add_img_pot(img)
        ImageShop().save_to_screen_shoot_dir(img=img)
        ImageShop().save_small_pic(img=img, x=527, y=125, w=721, h=451)