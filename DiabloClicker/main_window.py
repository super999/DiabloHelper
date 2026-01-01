import logging
from typing import Callable, Dict

from PySide6.QtWidgets import QMainWindow, QWidget

from DiabloClicker.service.hotkey.win_global_hotkey import (
    WM_HOTKEY,
    HotkeySpec,
    load_timed_key_toggle_hotkey,
    load_timed_key_reset_hotkeys,
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
        # 需求：按下 Ctrl+Num0（可在 config.json 修改）根据“当前激活的 tab”切换启动/停止，
        # 同时直接关闭另一个 tab 来避免冲突：
        # - 当前是 TabTimedKey：切换定时按键启动/停止，并关闭 SmartKey tab
        # - 当前是 TabSmartKey：切换智能按键监控，并关闭 TimedKey tab
        # 注意：RegisterHotKey 需要窗口句柄，放到 showEvent 里注册更稳。
        self._hotkeys_registered = False
        # hotkey_id -> handler
        self._hotkey_handlers: dict[int, Callable[[], None]] = {}
        self._registered_hotkey_ids: set[int] = set()

        self._hotkey_toggle_timed_key_id = 0xA001
        self._hotkey_toggle_timed_key_spec: HotkeySpec = load_timed_key_toggle_hotkey(default_hotkey="Ctrl+Num0")
   
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

    def _get_open_timed_key_tab(self) -> TabTimedKey | None:
        tab_name = "Timed Key"
        widget = self.opened_tabs.get(tab_name)
        return widget if isinstance(widget, TabTimedKey) else None

    def _get_open_smart_key_tab(self) -> TabSmartKey | None:
        tab_name = "Smart Key"
        widget = self.opened_tabs.get(tab_name)
        return widget if isinstance(widget, TabSmartKey) else None

    def _close_other_tab_for_mutex(self, active: QWidget | None) -> None:
        """互斥：按快捷键启动某个 tab 前，直接关闭另一个 tab（并停止其后台功能）。"""

        try:
            if isinstance(active, TabTimedKey):
                other = self._get_open_smart_key_tab()
                if other is None:
                    return
                idx = self.tabWidget.indexOf(other)
                if idx >= 0:
                    self.on_close_tab(idx)
                return

            if isinstance(active, TabSmartKey):
                other2 = self._get_open_timed_key_tab()
                if other2 is None:
                    return
                idx2 = self.tabWidget.indexOf(other2)
                if idx2 >= 0:
                    self.on_close_tab(idx2)
                return
        except Exception:
            logging.exception("互斥关闭另一个 tab 失败")

    def _toggle_key_feature_from_hotkey(self) -> None:
        """全局热键触发：根据当前激活 tab 切换启动/停止，并关闭另一个 tab。"""

        try:
            active = self.tabWidget.currentWidget()
            self._close_other_tab_for_mutex(active)

            if isinstance(active, TabSmartKey):
                active.toggle_monitor_from_external()
                return

            if isinstance(active, TabTimedKey):
                active.on_start_clicked()
                return

            # 如果当前激活的不是这两个 tab，就不做任何动作（避免热键误打开 tab）
            logging.info("全局热键触发：当前 tab 不是 Timed/Smart，忽略")
        except Exception:
            logging.exception("处理全局热键失败：切换按键功能")

    def _reset_single_skill_from_hotkey(self, skill_hotkey: str) -> None:
        """全局热键触发：重置某个技能（等价于点击该行的“重置”按钮）。"""

        try:
            tab = self._get_open_timed_key_tab()
            if tab is None:
                logging.info("技能重置热键触发但 TimedKey tab 未打开，忽略：%s", skill_hotkey)
                return
            tab.trigger_reset_by_hotkey(skill_hotkey)
        except Exception:
            logging.exception("处理全局热键失败：重置技能 %s", skill_hotkey)
    
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

        # 如果关闭的是“智能按键”tab，先停监控，避免后台残留
        if isinstance(widget, TabSmartKey):
            try:
                widget.stop_monitor_from_external()
            except Exception:
                logging.exception("关闭智能按键 tab 时停止监控失败")

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

        # 先清理一次（防御：避免重复注册导致 UnregisterHotKey 漏掉）
        self._unregister_hotkeys()

        # 1) 切换定时按键启动/停止
        ok = register_hotkey(hwnd, self._hotkey_toggle_timed_key_id, self._hotkey_toggle_timed_key_spec)
        if ok:
            self._registered_hotkey_ids.add(self._hotkey_toggle_timed_key_id)
            self._hotkey_handlers[self._hotkey_toggle_timed_key_id] = self._toggle_key_feature_from_hotkey
            logging.info(
                "已注册全局热键：%s（用于切换按键功能）",
                self._hotkey_toggle_timed_key_spec.display,
            )
        else:
            logging.warning(
                "全局热键注册失败：%s（可能已被占用）",
                self._hotkey_toggle_timed_key_spec.display,
            )

        # 2) 单技能重置热键：从 timed_key.keys[*].toggle_reset_key 读取
        reset_specs = load_timed_key_reset_hotkeys()
        base_id = 0xA100
        for idx, (skill_hotkey, spec) in enumerate(reset_specs):
            hotkey_id = base_id + idx
            ok2 = register_hotkey(hwnd, hotkey_id, spec)
            if not ok2:
                logging.warning(
                    "技能重置热键注册失败：skill=%s hotkey=%s",
                    skill_hotkey,
                    spec.display,
                )
                continue

            self._registered_hotkey_ids.add(hotkey_id)
            self._hotkey_handlers[hotkey_id] = (lambda hk=skill_hotkey: self._reset_single_skill_from_hotkey(hk))
            logging.info(
                "已注册技能重置热键：skill=%s hotkey=%s",
                skill_hotkey,
                spec.display,
            )

        self._hotkeys_registered = len(self._registered_hotkey_ids) > 0

    def _unregister_hotkeys(self) -> None:
        if not self._registered_hotkey_ids:
            self._hotkeys_registered = False
            self._hotkey_handlers.clear()
            return

        try:
            hwnd = int(self.winId())
        except Exception:
            # 没 hwnd 也无法注销，但这里至少清理本地状态
            self._registered_hotkey_ids.clear()
            self._hotkey_handlers.clear()
            self._hotkeys_registered = False
            return

        for hotkey_id in list(self._registered_hotkey_ids):
            try:
                unregister_hotkey(hwnd, hotkey_id)
            except Exception:
                logging.exception("注销全局热键失败：id=%s", hotkey_id)

        self._registered_hotkey_ids.clear()
        self._hotkey_handlers.clear()
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
                    handler = self._hotkey_handlers.get(hotkey_id)
                    if handler is not None:
                        handler()
                        return True, 0
        except Exception:
            logging.exception("nativeEvent 处理失败")

        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        # 退出时注销全局热键
        self._unregister_hotkeys()
        super().closeEvent(event)

