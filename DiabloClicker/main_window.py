import os
from typing import Dict, Optional

from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox

from MuseLog.explorer import TabExplorerWidget
from MuseLog.explorer.persistence_mixin import PersistenceMixin
from MuseLog.tab_favorites_widget import TabFavoritesWidget
from MuseLog.tab_home_widget import TabHomeWidget
from MuseLog.tab_settings_widget import TabSettingsWidget
from MuseLog.tab_video_gen_ai_widget import TabVideoGenAIWidget
from MuseLog.ui.ui_main_window import Ui_MainWindow
from MuseLog.explorer_signals import signal_manager

class MuseLogMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # 清空设计器默认的tab页，避免tabCloseRequested失效
        self.tabWidget.clear()
        # 连接关闭信号
        self.tabWidget.tabCloseRequested.connect(self.on_tab_close)
        # 连接按钮点击事件
        self.btnHome.clicked.connect(self.open_home_tab)
        self.btnSettings.clicked.connect(self.open_settings_tab)
        # 用于记录已打开的tab页
        self.opened_tabs: Dict[str, QWidget] = {}
        # 默认打开首页
        self.open_home_tab()

        self.btnExplorer = getattr(self, 'btnExplorer', None)
        if self.btnExplorer:
            self.btnExplorer.clicked.connect(lambda: self.open_explorer_tab())

        self.btnFavorites = getattr(self, 'btnFavorites', None)
        if self.btnFavorites:
            self.btnFavorites.clicked.connect(self.open_favorites_tab)

        self.btnVideoGen = getattr(self, 'btnVideoGen', None)
        if self.btnVideoGen:
            self.btnVideoGen.clicked.connect(self.open_video_gen_tab)

        self._restore_explorer_tabs()
        if not any(key.startswith("explorer-") for key in self.opened_tabs):
            self.open_explorer_tab()
        
        # 绑定信号
        self.bind_signals()

    def open_home_tab(self):
        tab_key = 'home'
        widget = self.opened_tabs.get(tab_key)
        if widget is not None:
            index = self.tabWidget.indexOf(widget)
            if index != -1:
                self.tabWidget.setCurrentIndex(index)
            return
        home_widget = TabHomeWidget()
        index = self.tabWidget.addTab(home_widget, "首页")
        self.opened_tabs[tab_key] = home_widget
        self.tabWidget.setCurrentIndex(index)

    def open_settings_tab(self):
        tab_key = 'settings'
        widget = self.opened_tabs.get(tab_key)
        if widget is not None:
            index = self.tabWidget.indexOf(widget)
            if index != -1:
                self.tabWidget.setCurrentIndex(index)
            return
        settings_widget = TabSettingsWidget(theme_apply_callback=self.apply_theme)
        index = self.tabWidget.addTab(settings_widget, "设置")
        self.opened_tabs[tab_key] = settings_widget
        self.tabWidget.setCurrentIndex(index)

    def open_explorer_tab(
        self,
        tab_id: Optional[str] = None,
        *,
        default_path: Optional[str] = None,
        select_path: Optional[str] = None,
    ) -> TabExplorerWidget:
        if isinstance(tab_id, bool):  # 兼容信号传入的 checked 参数
            tab_id = None
        if tab_id is None:
            tab_id = PersistenceMixin.allocate_tab_id()

        existing_widget = self.opened_tabs.get(tab_id)
        if existing_widget is not None and isinstance(existing_widget, TabExplorerWidget):
            index = self.tabWidget.indexOf(existing_widget)
            if index != -1:
                self.tabWidget.setCurrentIndex(index)
            return existing_widget

        try:
            explorer_widget = TabExplorerWidget(
                tab_id=tab_id,
                default_path=default_path,
                default_select_path=select_path,
            )
        except Exception:
            PersistenceMixin.remove_tab_state(tab_id)
            raise
        title = self._format_explorer_title(tab_id)
        index = self.tabWidget.addTab(explorer_widget, title)
        self.opened_tabs[tab_id] = explorer_widget
        self.tabWidget.setCurrentIndex(index)
        return explorer_widget

    def open_favorites_tab(self):
        tab_key = 'favorites'
        widget = self.opened_tabs.get(tab_key)
        if widget is not None:
            index = self.tabWidget.indexOf(widget)
            if index != -1:
                self.tabWidget.setCurrentIndex(index)
            return
        favorites_widget = TabFavoritesWidget()
        index = self.tabWidget.addTab(favorites_widget, "收藏夹")
        self.opened_tabs[tab_key] = favorites_widget
        self.tabWidget.setCurrentIndex(index)

    def open_video_gen_tab(self):
        tab_key = 'video_gen_ai'
        widget = self.opened_tabs.get(tab_key)
        if widget is not None:
            index = self.tabWidget.indexOf(widget)
            if index != -1:
                self.tabWidget.setCurrentIndex(index)
            return
        video_gen_widget = TabVideoGenAIWidget()
        index = self.tabWidget.addTab(video_gen_widget, "视频生成AI")
        self.opened_tabs[tab_key] = video_gen_widget
        self.tabWidget.setCurrentIndex(index)

    def on_tab_close(self, index):
        widget = self.tabWidget.widget(index)
        if widget is None:
            self.tabWidget.removeTab(index)
            return

        key_to_remove: Optional[str] = None
        for key, stored_widget in list(self.opened_tabs.items()):
            if stored_widget is widget:
                key_to_remove = key
                break

        if key_to_remove is not None:
            del self.opened_tabs[key_to_remove]
            if isinstance(widget, TabExplorerWidget):
                PersistenceMixin.remove_tab_state(widget.tab_id)

        self.tabWidget.removeTab(index)
        widget.deleteLater()

    def apply_theme(self, theme_name):
        from qt_material import apply_stylesheet
        app = QApplication.instance()
        if app:
            apply_stylesheet(app, theme=theme_name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _restore_explorer_tabs(self) -> None:
        saved_tabs = PersistenceMixin.get_saved_tabs()
        if not saved_tabs:
            return

        for tab in saved_tabs:
            if not isinstance(tab, dict):
                continue
            tab_id = str(tab.get("tab_id") or "").strip()
            if not tab_id:
                continue
            enter_path = tab.get("enter_last_path")
            select_path = tab.get("select_last_path")
            if enter_path and os.path.isdir(enter_path):
                default_path = enter_path
            elif select_path and os.path.isdir(select_path):
                default_path = select_path
            else:
                default_path = None
            if default_path is None:
                PersistenceMixin.remove_tab_state(tab_id)
                continue
            self.open_explorer_tab(
                tab_id=tab_id,
                default_path=default_path,
                select_path=select_path if isinstance(select_path, str) else None,
            )

    @staticmethod
    def _format_explorer_title(tab_id: str) -> str:
        suffix = tab_id.split("-", 1)[-1]
        return f"资源浏览 {suffix}"

    def bind_signals(self) -> None:
        # 绑定通知 GUI 消息信号
        signal_manager.gui_notify_msg_to_app.connect(self.on_gui_notify_msg_to_app)

    def on_gui_notify_msg_to_app(self, message: str) -> None:
        # 处理通知 GUI 消息
        QMessageBox.information(self, "通知", message, QMessageBox.Ok)