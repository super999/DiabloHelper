from typing import Optional
import logging
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem, QPushButton, QHBoxLayout
from DiabloClicker.ui.ui_tab_timed_key import Ui_TabTimedKey
from PySide6.QtWidgets import QComboBox

from DiabloClicker.service.key_sender.timed_key_sender import (
    KeyConfig,
    TimedKeySenderThread,
    load_target_window_title,
)

from DiabloClicker.service.key_sender.timed_key_config_store import (
    load_timed_key_configs,
    save_timed_key_configs,
)


class TabTimedKey(QWidget, Ui_TabTimedKey):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.key_configs = []
        self.key_status: bool = False
        self._sender_thread: Optional[TimedKeySenderThread] = None

        # ====== “剩余时间”显示相关 ======
        # hotkey -> 表格行号，用于快速定位某个按键对应哪一行
        self._hotkey_to_row: dict[str, int] = {}
        # hotkey -> 下一次触发时间点（time.monotonic() 的绝对时间）
        self._next_due_by_hotkey: dict[str, float] = {}
        # UI 定时器：每隔一段时间刷新一次“剩余时间”列
        self._remaining_timer = QTimer(self)
        self._remaining_timer.setInterval(200)
        self._remaining_timer.timeout.connect(self._refresh_remaining_times)

        self.setup_ui()

    def setup_ui(self):
        super().setupUi(self)
        # 如果 .ui 文件还没同步列数，这里强制为 6 列：
        # 0 热键 | 1 启用 | 2 间隔 | 3 剩余时间 | 4 操作 | 5 描述
        self.tableWidget.setColumnCount(6)

        # 显式设置表头文本，避免 .ui 没同步时显示错乱
        self.tableWidget.setHorizontalHeaderLabels([
            "热键",
            "启用",
            "间隔(秒)",
            "剩余时间",
            "操作",
            "描述",
        ])

        # tableWidget 控件：这里主要做 UI 外观/列宽设置
        self.tableWidget.setColumnWidth(0, 150)  # 热键
        self.tableWidget.setColumnWidth(1, 100)  # 启用
        self.tableWidget.setColumnWidth(2, 100)  # 间隔
        self.tableWidget.setColumnWidth(3, 100)  # 剩余时间
        self.tableWidget.setColumnWidth(4, 300)  # 操作（重置，未来更多按钮）
        self.tableWidget.setColumnWidth(5, 300)  # 描述
        # 1,2 列固定，3 列自适应宽度
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # 热键
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # 启用
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)  # 间隔
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # 剩余时间
        self.tableWidget.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 操作
        self.tableWidget.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 描述
        # 启动时：从 config.json 回填表格；若无配置则使用默认值
        self._load_table_from_config_or_default()
        # 
        self.bind_events()
        self.check_btn_status()

    def _load_table_from_config_or_default(self):
        """从配置回填表格。

        逻辑：
        - 如果 config.json 里存在 timed_key.keys：按配置生成表格行
        - 否则：用代码内置的默认行
        """

        self.tableWidget.setRowCount(0)
        self.key_configs.clear()

        configs = load_timed_key_configs()
        if configs:
            for cfg in configs:
                self.add_row(cfg.hotkey, cfg.enabled, cfg.interval, cfg.description)
            return

        # 默认行（第一次使用时没有配置，就走这里）
        self.add_row('1', False, 6.12,  '坠天星落')
        self.add_row('2', True, 52,  '正义仲裁官')
        self.add_row('3', True, 3,  '奉献')
        self.add_row('4', True, 4,  '狂信光环')
        self.add_row('5', True, 12,  '抗争光环')
        self.add_row('6', True, 3,  '庇护')
        
    def add_row(self, hotkey: str, enabled: bool, interval: float, description: str):
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)

        # 热键 列
        hotkey_item = QTableWidgetItem(hotkey)
        self.tableWidget.setItem(row_position, 0, hotkey_item)

        # 启用 列, checkbox
        enabled_item = QTableWidgetItem()
        enabled_item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        # 设置名称
        enabled_item.setText("启用")
        self.tableWidget.setItem(row_position, 1, enabled_item)

        # 间隔 列, 插入 Editable ComboBox
        interval_combo = QComboBox(self.tableWidget)
        interval_combo.setEditable(True)
        # 这里提供 1~60 的间隔选项（你也可以手动输入小数，比如 0.5）
        interval_combo.addItems([str(i) for i in range(1, 61)])
        interval_combo.setCurrentText(str(interval))

        self.tableWidget.setCellWidget(row_position, 2, interval_combo)

        # 剩余时间 列（启动后由 QTimer 定时刷新）
        remaining_item = QTableWidgetItem("-")
        remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemIsEditable)
        remaining_item.setTextAlignment(Qt.AlignCenter)
        self.tableWidget.setItem(row_position, 3, remaining_item)

        # 操作 列：用一个 layout 承载按钮，未来你可以继续往里加更多按钮
        op_widget = QWidget(self.tableWidget)
        op_layout = QHBoxLayout(op_widget)
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(8)

        btn_reset = QPushButton("重置", op_widget)
        # 用属性把 hotkey 绑在按钮上，点击时就知道要重置哪一行
        btn_reset.setProperty("hotkey", hotkey)
        btn_reset.clicked.connect(self._on_reset_clicked)
        op_layout.addWidget(btn_reset)
        op_layout.addStretch(1)

        self.tableWidget.setCellWidget(row_position, 4, op_widget)

        # 描述 列
        description_item = QTableWidgetItem(description)
        self.tableWidget.setItem(row_position, 5, description_item)
        key_config = KeyConfig(hotkey=hotkey, enabled=enabled, interval=float(interval), description=description)
        self.key_configs.append(key_config)
    
    def bind_events(self):
        # 点击按钮：启动/停止
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_save_config.clicked.connect(self.on_save_config_clicked)

    def on_save_config_clicked(self):
        """点击“保存配置”：把当前表格内容写入 config.json。

        注意：
        - 这里只保存“定时按键表格”相关字段，不影响 config.json 其它设置。
        - 保存的内容来源于 UI 当前值（勾选/间隔/描述）。
        """

        configs = self._collect_configs_from_table()
        save_timed_key_configs(configs)
        logging.info(f"已保存定时按键配置到 config.json，共 {len(configs)} 条")

    def _collect_configs_from_table(self) -> list[KeyConfig]:
        """从表格读取当前配置。

        为什么要从表格读：
        - 用户可能修改了勾选状态或间隔值
        - 所以点击“启动”时要用最新的 UI 数据
        """

        configs: list[KeyConfig] = []
        for row in range(self.tableWidget.rowCount()):
            hotkey_item = self.tableWidget.item(row, 0)
            enabled_item = self.tableWidget.item(row, 1)
            interval_widget = self.tableWidget.cellWidget(row, 2)
            description_item = self.tableWidget.item(row, 5)

            hotkey = hotkey_item.text().strip() if hotkey_item else ""
            enabled = bool(enabled_item and enabled_item.checkState() == Qt.Checked)
            description = description_item.text().strip() if description_item else ""

            interval_text = ""
            if isinstance(interval_widget, QComboBox):
                interval_text = interval_widget.currentText().strip()
            try:
                interval = float(interval_text)
            except Exception:
                interval = 0.0

            configs.append(
                KeyConfig(hotkey=hotkey, enabled=enabled, interval=interval, description=description)
            )
        return configs

    def _on_reset_clicked(self):
        """点击“重置”按钮：把该行的剩余时间强制改为 1 秒。

        需求解释：
        - 只有在线程正在运行时，这个按钮才有意义
        - 点击后：UI 立即显示 1.0s
        - 同时通知线程：把对应 hotkey 的 next_due 改成 now + 1s
          => 1 秒后会触发一次按键
        """

        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return

        hotkey = str(btn.property("hotkey") or "").strip()
        if not hotkey:
            return

        # 如果线程没在跑，就不处理（避免 UI 显示与实际不一致）
        if not (self._sender_thread and self._sender_thread.isRunning()):
            return

        # 1) 先更新 UI：立刻显示 1.0s
        now = time.monotonic()
        next_due = now + 1.0
        self._next_due_by_hotkey[hotkey] = next_due
        row = self._hotkey_to_row.get(hotkey)
        if row is not None:
            self._set_remaining_text(row, 1.0)

        # 2) 通知线程：把 next_due 改为 1 秒后
        self._sender_thread.request_next_due_in(hotkey, 1.0)

    def _rebuild_hotkey_row_index(self):
        """重建 hotkey->row 的索引。

        为什么需要：
        - 线程回调给 UI 的是 hotkey（比如 '1'）
        - UI 更新“剩余时间”时，需要知道 hotkey 在表格哪一行
        """

        self._hotkey_to_row.clear()
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if not item:
                continue
            hotkey = item.text().strip()
            if hotkey:
                self._hotkey_to_row[hotkey] = row

    def _set_remaining_text(self, row: int, remaining_seconds: float) -> None:
        """把某行的“剩余时间”列更新为可读文本。"""

        remaining_item = self.tableWidget.item(row, 3)
        if not remaining_item:
            remaining_item = QTableWidgetItem("-")
            remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemIsEditable)
            remaining_item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 3, remaining_item)

        if remaining_seconds < 0:
            remaining_seconds = 0.0
        remaining_item.setText(f"{remaining_seconds:.1f}s")

    def _refresh_remaining_times(self):
        """定时刷新“剩余时间”列。

        计算方式：
        - 线程会通过 next_due_changed 信号告诉 UI：某个 hotkey 的 next_due(单调时间)
        - UI 每隔 200ms 计算 remaining = next_due - time.monotonic()
        """

        now = time.monotonic()
        for hotkey, next_due in list(self._next_due_by_hotkey.items()):
            row = self._hotkey_to_row.get(hotkey)
            if row is None:
                continue
            remaining = next_due - now
            self._set_remaining_text(row, remaining)

    def _on_next_due_changed(self, hotkey: str, next_due: float):
        """线程回调：某个 hotkey 的 next_due 更新。"""

        self._next_due_by_hotkey[hotkey] = next_due

    def _stop_sender_thread(self):
        """停止后台线程（如果存在）。

        说明：
        - stop() 是“请求停止”（设置标志位）
        - wait(2000) 最多等 2 秒让线程自然退出
        """

        if self._sender_thread and self._sender_thread.isRunning():
            self._sender_thread.stop()
            self._sender_thread.wait(2000)
        self._sender_thread = None

        # 停止后：停止 UI 刷新，并清空剩余时间
        self._remaining_timer.stop()
        self._next_due_by_hotkey.clear()
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 3)
            if item:
                item.setText("-")
        
    def on_start_clicked(self):
        """启动/停止按钮的点击回调。

        行为约定：
        - 当前是“停止”状态：点击 -> 启动线程
        - 当前是“启动”状态：点击 -> 停止线程
        """

        if not self.key_status:
            # 1) 准备启动：读取目标窗口标题 + 读取表格配置
            target_title = load_target_window_title(default_title="暗黑破坏神IV")
            configs = self._collect_configs_from_table()
            logging.info(f"准备启动定时按键发送，目标窗口标题：{target_title}，配置：{configs}")

            # 重建索引，用于后续更新“剩余时间”列
            self._rebuild_hotkey_row_index()

            # 2) 启动前，先确保没有旧线程残留
            self._stop_sender_thread()

            # 3) 创建并启动线程
            self._sender_thread = TimedKeySenderThread(configs=configs, target_window_title=target_title)
            self._sender_thread.finished.connect(self._on_sender_finished)
            self._sender_thread.next_due_changed.connect(self._on_next_due_changed)
            self._sender_thread.start()

            # 4) 开始定时刷新“剩余时间”列
            self._remaining_timer.start()

            self.key_status = True
        else:
            # 停止：请求线程退出并等待
            self._stop_sender_thread()
            self.key_status = False

        self.btn_start.setChecked(self.key_status)
        self.check_btn_status()

    def _on_sender_finished(self):
        """线程自然退出（比如找不到窗口）时，回收 UI 状态。"""

        self._sender_thread = None
        self._remaining_timer.stop()
        if self.key_status:
            self.key_status = False
            self.btn_start.setChecked(False)
            self.check_btn_status()

    def closeEvent(self, event):
        # 窗口关闭时，确保线程退出，避免进程残留
        self._stop_sender_thread()
        super().closeEvent(event)
        
            
    def check_btn_status(self):
        if not self.key_status:
            self.btn_start.setText("已停止")
        else:
            self.btn_start.setText("启动中")