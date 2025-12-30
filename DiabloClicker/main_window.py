import logging
from typing import Dict

from PySide6.QtWidgets import QMainWindow, QWidget

from DiabloClicker.service.hotkey.win_global_hotkey import (
    WM_HOTKEY,
    HotkeySpec,
    load_timed_key_toggle_hotkey,
    register_hotkey,
    unregister_hotkey,
)
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

        # ===== 全局快捷键（Windows） =====
        # 需求：按下 Ctrl+Num0（可在 config.json 修改）切换“定时按键”的启动/停止。
        # 注意：RegisterHotKey 需要窗口句柄，放到 showEvent 里注册更稳。
        self._hotkeys_registered = False
        self._hotkey_toggle_timed_key_id = 0xA001
        self._hotkey_toggle_timed_key_spec: HotkeySpec = load_timed_key_toggle_hotkey(
            default_hotkey="Ctrl+Num0"
        )
   
    # show事件
    def showEvent(self, event):
        super().showEvent(event)
        # 在窗口显示时执行的代码
        logging.info("Main window is shown")

        # 第一次 show 时注册全局热键
        if not self._hotkeys_registered:
            self._register_hotkeys()
    
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

    def _get_or_open_timed_key_tab(self) -> TabTimedKey:
        tab_name = "Timed Key"
        widget = self.opened_tabs.get(tab_name)
        if isinstance(widget, TabTimedKey):
            return widget
        self.open_timed_key_tab()
        widget2 = self.opened_tabs.get(tab_name)
        assert isinstance(widget2, TabTimedKey)
        return widget2

    def _toggle_timed_key_from_hotkey(self) -> None:
        """全局热键触发：切换定时按键启动/停止。"""

        try:
            tab = self._get_or_open_timed_key_tab()
            tab.on_start_clicked()
        except Exception:
            logging.exception("处理全局热键失败：切换定时按键")
    
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

        # 如果关闭的是“定时按键”tab，先停线程，避免后台残留
        if isinstance(widget, TabTimedKey):
            try:
                widget._stop_sender_thread()
            except Exception:
                logging.exception("关闭定时按键 tab 时停止线程失败")

        if tab_name in self.opened_tabs:
            del self.opened_tabs[tab_name]
        self.tabWidget.removeTab(index)
        widget.deleteLater()    

    def _register_hotkeys(self) -> None:
        """注册全局热键（Windows）。"""

        try:
            hwnd = int(self.winId())
        except Exception:
            logging.exception("获取窗口句柄失败，无法注册全局热键")
            return

        ok = register_hotkey(hwnd, self._hotkey_toggle_timed_key_id, self._hotkey_toggle_timed_key_spec)
        if ok:
            self._hotkeys_registered = True
            logging.info(
                "已注册全局热键：%s（用于切换定时按键）",
                self._hotkey_toggle_timed_key_spec.display,
            )
        else:
            logging.warning(
                "全局热键注册失败：%s（可能已被占用）",
                self._hotkey_toggle_timed_key_spec.display,
            )

    def _unregister_hotkeys(self) -> None:
        if not self._hotkeys_registered:
            return
        try:
            hwnd = int(self.winId())
            unregister_hotkey(hwnd, self._hotkey_toggle_timed_key_id)
        finally:
            self._hotkeys_registered = False

    def nativeEvent(self, eventType, message):
        """接收 Windows 消息（用于 WM_HOTKEY）。"""

        try:
            if eventType == "windows_generic_MSG":
                # message 是指向 MSG 结构体的指针
                import ctypes
                from ctypes import wintypes

                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY:
                    hotkey_id = int(msg.wParam)
                    if hotkey_id == self._hotkey_toggle_timed_key_id:
                        self._toggle_timed_key_from_hotkey()
                        return True, 0
        except Exception:
            logging.exception("nativeEvent 处理失败")

        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        # 退出时注销全局热键
        self._unregister_hotkeys()
        super().closeEvent(event)

