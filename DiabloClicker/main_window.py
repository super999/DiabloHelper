import logging
from typing import Dict

from PySide6.QtWidgets import QMainWindow, QWidget

from DiabloClicker.ui.tabs.smart_key_tab import TabSmartKey
from DiabloClicker.ui.tabs.timed_key_tab import TabTimedKey
from DiabloClicker.ui.ui_main_window import Ui_MainWindow


class DiabloClickerMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 定时按键按钮
        self.btn_timed_key.clicked.connect(self.open_timed_key_tab)
        # 智能按键按钮
        self.btn_smart_key.clicked.connect(self.open_smart_key_tab)
        # tabWidget 控件
        self.tabWidget.tabCloseRequested.connect(self.on_close_tab)
        # 初始化 tab 页
        self.init_tabs()
   
    # show事件
    def showEvent(self, event):
        super().showEvent(event)
        # 在窗口显示时执行的代码
        logging.info("Main window is shown")
    
    def init_tabs(self):
        self.opened_tabs: Dict[str, QWidget] = {}
        # 清空现有的 tab 页
        self.tabWidget.clear()
        # 打开 定时按键 tab 页
        self.open_timed_key_tab()
        self.open_smart_key_tab()
        
    def open_timed_key_tab(self):
        tab_name = "Timed Key"
        if tab_name in self.opened_tabs:
            index = self.tabWidget.indexOf(self.opened_tabs[tab_name])
            self.tabWidget.setCurrentIndex(index)
            return

        timed_key_tab = TabTimedKey()
        self.tabWidget.addTab(timed_key_tab, tab_name)
        self.tabWidget.setCurrentWidget(timed_key_tab)
        self.opened_tabs[tab_name] = timed_key_tab
    
    def open_smart_key_tab(self):
        tab_name = "Smart Key"
        if tab_name in self.opened_tabs:
            index = self.tabWidget.indexOf(self.opened_tabs[tab_name])
            self.tabWidget.setCurrentIndex(index)
            return

        smart_key_tab = TabSmartKey(self.tabWidget)
        self.tabWidget.addTab(smart_key_tab, tab_name)
        self.tabWidget.setCurrentWidget(smart_key_tab)
        self.opened_tabs[tab_name] = smart_key_tab
    
    def on_close_tab(self, index):
        widget = self.tabWidget.widget(index)
        tab_name = self.tabWidget.tabText(index)
        if tab_name in self.opened_tabs:
            del self.opened_tabs[tab_name]
        self.tabWidget.removeTab(index)
        widget.deleteLater()    

