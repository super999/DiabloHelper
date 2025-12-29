from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHeaderView, QTableWidgetItem
from DiabloClicker.ui.ui_tab_timed_key import Ui_TabTimedKey
from PySide6.QtWidgets import QComboBox


class KeyConfig:
    def __init__(self, hotkey: str, enabled: bool, interval: int, description: str):
        self.hotkey = hotkey
        self.enabled = enabled
        self.interval = interval
        self.description = description


class TabTimedKey(QWidget, Ui_TabTimedKey):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.key_configs = []
        self.key_status: bool = False
        self.setup_ui()

    def setup_ui(self):
        super().setupUi(self)
        # tableWidget 控件
        # 设置每个列的宽度
        self.tableWidget.setColumnWidth(0, 150)  #
        self.tableWidget.setColumnWidth(1, 100)  #
        self.tableWidget.setColumnWidth(2, 100)  #
        self.tableWidget.setColumnWidth(3, 100)  #
        # 1,2 列固定，3 列自适应宽度
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # 添加 一行
        self.add_row('1', False, 6.12,  '坠天星落')
        self.add_row('2', True, 50.21,  '正义仲裁官')
        self.add_row('3', True, 13.12,  '奉献')
        self.add_row('4', True, 10.94,  '狂信光环')
        self.add_row('5', True, 14.58,  '抗争光环')
        self.add_row('6', True, 13.85,  '庇护')
        # 
        self.bind_events()
        self.check_btn_status()
        
    def add_row(self, hotkey: str, enabled: bool, interval: int, description: str):
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
        # 这里示例提供 1~5 的间隔选项（可按需改成你自己的列表）
        interval_combo.addItems([str(i) for i in range(1, 6)])
        interval_combo.setCurrentText(str(interval))

        self.tableWidget.setCellWidget(row_position, 2, interval_combo)

        # 描述 列
        description_item = QTableWidgetItem(description)
        self.tableWidget.setItem(row_position, 3, description_item)
        key_config = KeyConfig(hotkey, enabled, interval, description)
        self.key_configs.append(key_config)
    
    def bind_events(self):
        self.btn_start.clicked.connect(self.on_start_clicked)
        
    def on_start_clicked(self):
        self.key_status = not self.key_status
        self.btn_start.setChecked(self.key_status)
        self.check_btn_status()
        
            
    def check_btn_status(self):
        if not self.key_status:
            self.btn_start.setText("已停止")
        else:
            self.btn_start.setText("启动中")