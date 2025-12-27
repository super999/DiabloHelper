

from DiabloClicker.service.db_op.desktop_op import DesktopService


class CapService:
    
    _instance = None
    
    target_hwmd = None
    target_program_title = 'Legend of Merchant'

    def get_target_hwnd(self):
        for hwnd, title in DesktopService().hwnd_title.items():
            if title == self.target_program_title:
                return hwnd
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CapService, cls).__new__(cls)
        return cls._instance
    
    def get_target_hwnd(self):
        # 返回目标窗口句柄的逻辑
        pass