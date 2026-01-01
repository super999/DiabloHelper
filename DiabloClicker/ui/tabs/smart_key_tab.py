import logging
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import queue
import threading
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QWidget,
)

from DiabloClicker.service.capture.cap_service import CapService
from DiabloClicker.service.img_ctrl.image_shop import ImageShop
from DiabloClicker.ui.ui_tab_advance_image import Ui_TabAdvanceImage

import cv2
import numpy as np  # type: ignore
from DiabloClicker.service.key_sender.timed_key_sender import send_key_to_hwnd

@dataclass(frozen=True)
class _SmallPicRegion:
    x: int
    y: int
    width: int
    height: int
    ref_screen_width: Optional[int] = None
    ref_screen_height: Optional[int] = None


@dataclass(frozen=True)
class _SkillArea:
    index: int
    name: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class _SkillIcon:
    index: int
    name: str
    icon_path: Path


class TabSmartKey(QWidget, Ui_TabAdvanceImage):
    TAB_NAME = "智能按键"

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.bind_events()

        # 记录最后一次全屏截图（用于裁剪多个区域）
        self._full_image: Optional[QImage] = None

        # 记录最后一次用于展示的图片（用于窗口尺寸变化时重新缩放显示）
        self._last_image: Optional[QImage] = None

        # small_pic_region：程序启动时读取一次并缓存。
        # 这样点击“裁剪”按钮时不会频繁读磁盘/解析 JSON。
        self._small_pic_region: Optional[_SmallPicRegion] = self._load_small_pic_region_from_config()

        # skill_area：程序启动时读取一次并缓存。
        # 用于“截图识别”时裁剪多个技能区域。
        self._skill_areas: list[_SkillArea] = self._load_skill_areas_from_config()
        # 裁剪后的技能区域缓存：index -> QImage
        self._skill_area_images: dict[int, QImage] = {}

        # skill_key_config：index -> hotkey（用于日志展示/后续扩展）
        self._skill_key_by_index: dict[int, str] = self._load_skill_key_config_from_config()

        # skill_icon：index -> icon 配置（用于图片匹配）
        self._skill_icons_by_index: dict[int, _SkillIcon] = {
            icon.index: icon for icon in self._load_skill_icons_from_config()
        }

        # 最近一次图片匹配结果：index -> score
        self._last_match_score: dict[int, float] = {}

        # 保持图片比例：不要让 QLabel 自动拉伸填满（会变形）
        self.labelImageShow.setScaledContents(False)
        self.labelImageShow.setAlignment(Qt.AlignCenter)

        # 让 QLabel 在布局中尽量占满空间，否则 label.size() 可能本身就不大
        self.labelImageShow.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ===== 监控相关（截图/裁剪在 UI 线程；SAT 判断+发键在后台线程） =====
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._on_monitor_timer_tick)
        self._monitor_stop_event: Optional[threading.Event] = None
        self._monitor_worker_thread: Optional[threading.Thread] = None
        self._monitor_queue: Optional[queue.Queue] = None
        self._monitor_last_enabled: dict[int, bool] = {}
        self._monitor_hwnd: Optional[int] = None
        self._monitor_hwnd_title: str = ""
        self._monitor_settings = self._load_smart_key_monitor_settings_from_config()

        # 裁剪缓存与 worker 共享，做一个锁避免竞态
        self._skill_area_lock = threading.Lock()

        # ===== smart_key 表格（从 config.json smart_key.keys 回填） =====
        self._smart_key_row_defaults: dict[int, float] = {}
        self._setup_smart_key_table_ui()
        self._load_smart_key_table_from_config_or_default()
        
    def showEvent(self, event) -> None:
        super().showEvent(event)
        # 在 tab 页显示时执行的代码
        logging.info("Smart Key tab is shown")
        
    def bind_events(self) -> None:
        # 绑定 UI 事件处理函数
        self.pushButton_screenshot.clicked.connect(self.on_screenshot_clicked)
        self.pushButton_smart_pic_cut.clicked.connect(self.on_smart_pic_cut_clicked)
        self.pushButton_pic_match.clicked.connect(self.on_pic_match_clicked)
        self.pushButton_test.clicked.connect(self.on_pic_test_clicked)
        self.checkBoxStartMonitor.stateChanged.connect(self.on_checkbox_start_monitor_changed)
        self.btn_save_config.clicked.connect(self.on_save_smart_key_config_clicked)

    def _setup_smart_key_table_ui(self) -> None:
        """初始化 smart_key 的 tableWidget 外观/列。"""

        # 0 启用热键 | 1 启用 | 2 发送热键 | 3 扫描间隔时间 | 4 操作 | 5 说明（可选）
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels([
            "启用热键",
            "启用",
            "发送热键",
            "扫描间隔时间",
            "操作",
            "说明（选项）",
        ])

        self.tableWidget.setColumnWidth(0, 150)
        self.tableWidget.setColumnWidth(1, 80)
        self.tableWidget.setColumnWidth(2, 120)
        self.tableWidget.setColumnWidth(3, 120)
        self.tableWidget.setColumnWidth(4, 100)
        self.tableWidget.setColumnWidth(5, 220)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

    def _read_config_json(self) -> dict:
        config_path = Path.cwd() / "config.json"
        if not config_path.exists():
            return {}
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("读取 config.json 失败")
            return {}

    def _write_config_json(self, data: dict) -> None:
        config_path = Path.cwd() / "config.json"
        try:
            config_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )
        except Exception:
            logging.exception("写入 config.json 失败")

    def _load_smart_key_configs_from_config(self) -> list[dict]:
        data = self._read_config_json()
        root = data.get("smart_key")
        if not isinstance(root, dict):
            return []
        items = root.get("keys")
        if not isinstance(items, list):
            return []
        out: list[dict] = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            enable_hotkey = str(raw.get("enable_hotkey") or "").strip()
            send_hotkey = str(raw.get("hotkey") or "").strip()
            if not enable_hotkey and not send_hotkey:
                continue
            enabled = bool(raw.get("enabled", True))
            desc = str(raw.get("description") or "").strip()
            interval_raw = raw.get("scan_interval_seconds", 0.2)
            try:
                interval = float(interval_raw)
            except Exception:
                interval = 0.2
            if interval <= 0:
                interval = 0.2
            out.append({
                "enable_hotkey": enable_hotkey,
                "hotkey": send_hotkey,
                "enabled": enabled,
                "description": desc,
                "scan_interval_seconds": float(interval),
            })
        return out

    def _default_smart_key_configs(self) -> list[dict]:
        # 没配 smart_key 时给一个最小默认：6 行
        # - enable_hotkey: Alt+Num{i}（切换该行启用）
        # - hotkey: {i}（真正发送给游戏窗口的热键）
        return [
            {
                "enable_hotkey": f"Alt+Num{i}",
                "hotkey": str(i),
                "enabled": True,
                "description": f"技能{i}",
                "scan_interval_seconds": 0.2,
            }
            for i in range(1, 7)
        ]

    def _load_smart_key_table_from_config_or_default(self) -> None:
        self.tableWidget.setRowCount(0)
        self._smart_key_row_defaults.clear()

        configs = self._load_smart_key_configs_from_config()
        if not configs:
            configs = self._default_smart_key_configs()

        for cfg in configs:
            self._add_smart_key_row(
                enable_hotkey=str(cfg.get("enable_hotkey") or ""),
                send_hotkey=str(cfg.get("hotkey") or ""),
                enabled=bool(cfg.get("enabled", True)),
                scan_interval_seconds=float(cfg.get("scan_interval_seconds", 0.2)),
                description=str(cfg.get("description") or ""),
            )

    def _add_smart_key_row(
        self,
        enable_hotkey: str,
        send_hotkey: str,
        enabled: bool,
        scan_interval_seconds: float,
        description: str,
    ) -> None:
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)

        # 0 启用热键
        enable_hotkey_item = QTableWidgetItem(enable_hotkey)
        self.tableWidget.setItem(row, 0, enable_hotkey_item)

        # 1 启用
        enabled_item = QTableWidgetItem("启用")
        enabled_item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        self.tableWidget.setItem(row, 1, enabled_item)

        # 2 发送热键
        send_hotkey_item = QTableWidgetItem(send_hotkey)
        self.tableWidget.setItem(row, 2, send_hotkey_item)

        # 3 扫描间隔（秒）
        interval_combo = QComboBox(self.tableWidget)
        interval_combo.setEditable(True)
        # 常用值；也允许手动输入
        interval_combo.addItems(["0.05", "0.1", "0.15", "0.2", "0.25", "0.3", "0.5", "1.0"])
        interval_combo.setCurrentText(str(scan_interval_seconds))
        self.tableWidget.setCellWidget(row, 3, interval_combo)

        # 4 操作（重置：把扫描间隔恢复到初始值）
        op_widget = QWidget(self.tableWidget)
        op_layout = QHBoxLayout(op_widget)
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(8)
        btn_reset = QPushButton("重置", op_widget)
        btn_reset.setProperty("row", int(row))
        btn_reset.setProperty("default_interval", float(scan_interval_seconds))
        btn_reset.clicked.connect(self._on_smart_key_reset_clicked)
        op_layout.addWidget(btn_reset)
        op_layout.addStretch(1)
        self.tableWidget.setCellWidget(row, 4, op_widget)

        # 5 描述
        desc_item = QTableWidgetItem(description)
        self.tableWidget.setItem(row, 5, desc_item)

        self._smart_key_row_defaults[row] = float(scan_interval_seconds)

    def _on_smart_key_reset_clicked(self) -> None:
        btn = self.sender()
        if btn is None:
            return
        try:
            row = int(btn.property("row"))
        except Exception:
            row = -1
        try:
            default_interval = float(btn.property("default_interval"))
        except Exception:
            default_interval = float(self._smart_key_row_defaults.get(row, 0.2))

        if row < 0 or row >= self.tableWidget.rowCount():
            return
        w = self.tableWidget.cellWidget(row, 3)
        if isinstance(w, QComboBox):
            w.setCurrentText(str(default_interval))

    def _collect_smart_key_configs_from_table(self) -> list[dict]:
        configs: list[dict] = []
        for row in range(self.tableWidget.rowCount()):
            enable_hotkey_item = self.tableWidget.item(row, 0)
            enabled_item = self.tableWidget.item(row, 1)
            send_hotkey_item = self.tableWidget.item(row, 2)
            interval_widget = self.tableWidget.cellWidget(row, 3)
            desc_item = self.tableWidget.item(row, 5)

            enable_hotkey = enable_hotkey_item.text().strip() if enable_hotkey_item else ""
            send_hotkey = send_hotkey_item.text().strip() if send_hotkey_item else ""
            if not enable_hotkey and not send_hotkey:
                continue
            enabled = bool(enabled_item and enabled_item.checkState() == Qt.Checked)

            interval_text = ""
            if isinstance(interval_widget, QComboBox):
                interval_text = interval_widget.currentText().strip()
            try:
                interval = float(interval_text)
            except Exception:
                interval = 0.2
            if interval <= 0:
                interval = 0.2

            desc = desc_item.text().strip() if desc_item else ""

            configs.append({
                "enable_hotkey": enable_hotkey,
                "hotkey": send_hotkey,
                "enabled": bool(enabled),
                "description": desc,
                "scan_interval_seconds": float(interval),
            })
        return configs

    def on_save_smart_key_config_clicked(self) -> None:
        configs = self._collect_smart_key_configs_from_table()
        data = self._read_config_json()
        if "smart_key" not in data or not isinstance(data.get("smart_key"), dict):
            data["smart_key"] = {}
        root = data["smart_key"]
        if isinstance(root, dict):
            root["keys"] = configs
        self._write_config_json(data)
        logging.info("已保存 smart_key 配置到 config.json，共 %s 条", len(configs))
        # QToolButton 是 checkable 的，保存完把它按回去（避免 UI 一直处于按下状态）
        try:
            self.btn_save_config.setChecked(False)
        except Exception:
            pass

    def _update_image_view(self) -> None:
        """按当前 QLabel 可用区域，等比最大化显示最后一张截图。"""

        if self._last_image is None or self._last_image.isNull():
            return

        # 用 contentsRect 更准确（会扣掉边框/内边距），比 size() 更接近“真正可显示的区域”
        target_size = self.labelImageShow.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        pixmap = QPixmap.fromImage(self._last_image)
        if pixmap.isNull():
            return

        # KeepAspectRatio：等比缩放到“尽量大且不超出”的尺寸
        pixmap = pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.labelImageShow.setPixmap(pixmap)

    def _load_small_pic_region_from_config(self) -> Optional[_SmallPicRegion]:
        """从 config.json 读取 small_pic_region（仅用于启动时加载/刷新缓存）。

        期望结构（见根目录 config.json）：
        {
          "screenshot": {
                        "small_pic_region": {
                            "x": 527, "y": 125, "width": 721, "height": 451,
                            "ref_screen_width": 3840, "ref_screen_height": 2160
                        }
          }
        }

        返回：
        - _SmallPicRegion 或 None
        """

        config_path = Path.cwd() / "config.json"
        if not config_path.exists():
            logging.warning("找不到 config.json，无法读取 small_pic_region")
            return None

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("读取 config.json 失败")
            return None

        screenshot = data.get("screenshot")
        if not isinstance(screenshot, dict):
            return None
        region = screenshot.get("small_pic_region")
        if not isinstance(region, dict):
            return None

        try:
            x = int(region.get("x", 0))
            y = int(region.get("y", 0))
            w = int(region.get("width", 0))
            h = int(region.get("height", 0))
        except Exception:
            logging.warning("small_pic_region 字段类型不正确")
            return None

        ref_w_raw = region.get("ref_screen_width")
        ref_h_raw = region.get("ref_screen_height")
        ref_w: Optional[int]
        ref_h: Optional[int]
        try:
            ref_w = int(ref_w_raw) if ref_w_raw is not None else None
            ref_h = int(ref_h_raw) if ref_h_raw is not None else None
        except Exception:
            logging.warning("small_pic_region 的 ref_screen_width/ref_screen_height 字段类型不正确，将忽略缩放")
            ref_w, ref_h = None, None

        if ref_w is not None and ref_w <= 0:
            ref_w = None
        if ref_h is not None and ref_h <= 0:
            ref_h = None

        if w <= 0 or h <= 0:
            logging.warning("small_pic_region 的 width/height 必须 > 0")
            return None

        return _SmallPicRegion(
            x=x,
            y=y,
            width=w,
            height=h,
            ref_screen_width=ref_w,
            ref_screen_height=ref_h,
        )

    def _load_skill_areas_from_config(self) -> list[_SkillArea]:
        """从 config.json 读取 screenshot.skill_area。

        期望结构：
        {
          "screenshot": {
            "skill_area": [
              {"index": 1, "name": "技能1", "x": 1548, "y": 1957, "width": 115, "height": 107},
              ...
            ]
          }
        }

        返回：
        - _SkillArea 列表（可能为空）
        """

        config_path = Path.cwd() / "config.json"
        if not config_path.exists():
            return []

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("读取 config.json 失败：无法读取 skill_area")
            return []

        screenshot = data.get("screenshot")
        if not isinstance(screenshot, dict):
            return []

        raw_list = screenshot.get("skill_area")
        if not isinstance(raw_list, list):
            return []

        areas: list[_SkillArea] = []
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            try:
                idx = int(raw.get("index", 0))
                name = str(raw.get("name") or "").strip() or f"skill_{idx}"
                x = int(raw.get("x", 0))
                y = int(raw.get("y", 0))
                w = int(raw.get("width", 0))
                h = int(raw.get("height", 0))
            except Exception:
                continue

            if idx <= 0 or w <= 0 or h <= 0:
                continue

            areas.append(_SkillArea(index=idx, name=name, x=x, y=y, width=w, height=h))

        # 按 index 排序，保证稳定
        areas.sort(key=lambda a: a.index)
        return areas

    def _load_skill_key_config_from_config(self) -> dict[int, str]:
        """从 config.json 读取 screenshot.skill_key_config。

        期望结构：
        {
          "screenshot": {
            "skill_key_config": {
              "skill_1_key": "1",
              "skill_2_key": "2",
              ...
            }
          }
        }

        返回：
        - {index: hotkey_str}
        """

        config_path = Path.cwd() / "config.json"
        if not config_path.exists():
            return {}

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("读取 config.json 失败：无法读取 skill_key_config")
            return {}

        screenshot = data.get("screenshot")
        if not isinstance(screenshot, dict):
            return {}

        raw = screenshot.get("skill_key_config")
        if not isinstance(raw, dict):
            return {}

        out: dict[int, str] = {}
        for k, v in raw.items():
            if not isinstance(k, str):
                continue
            # 期望 key 形如 skill_1_key
            digits = "".join(ch for ch in k if ch.isdigit())
            if not digits:
                continue
            try:
                idx = int(digits)
            except Exception:
                continue
            if idx <= 0:
                continue
            hotkey = str(v).strip()
            if not hotkey:
                continue
            out[idx] = hotkey

        return out

    def _load_skill_icons_from_config(self) -> list[_SkillIcon]:
        """从 config.json 读取 screenshot.skill_icon。

        期望结构：
        {
          "screenshot": {
            "skill_icon": [
              {"index": 1, "name": "xxx", "icon_path": "res/icons/skill/xxx.png"},
              ...
            ]
          }
        }

        返回：
        - _SkillIcon 列表（可能为空）
        """

        config_path = Path.cwd() / "config.json"
        if not config_path.exists():
            return []

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("读取 config.json 失败：无法读取 skill_icon")
            return []

        screenshot = data.get("screenshot")
        if not isinstance(screenshot, dict):
            return []

        raw_list = screenshot.get("skill_icon")
        if not isinstance(raw_list, list):
            return []

        icons: list[_SkillIcon] = []
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            try:
                idx = int(raw.get("index", 0))
                name = str(raw.get("name") or "").strip() or f"skill_{idx}"
                icon_path_str = str(raw.get("icon_path") or "").strip()
            except Exception:
                continue

            if idx <= 0 or not icon_path_str:
                continue

            icon_path = Path(icon_path_str)
            if not icon_path.is_absolute():
                icon_path = Path.cwd() / icon_path

            icons.append(_SkillIcon(index=idx, name=name, icon_path=icon_path))

        icons.sort(key=lambda i: i.index)
        return icons

    def _load_smart_key_monitor_settings_from_config(self) -> dict[str, object]:
        """读取智能按键监控相关配置。

        目前支持：
        - screenshot.smart_key_monitor_interval: float，监控间隔（秒），默认 0.1
        - screenshot.smart_key_monitor_save_debug: bool，是否写入技能小图到 screen_shoot/skill_{i}.png，默认 True

        注意：这些字段缺失不影响运行（走默认）。
        """

        defaults: dict[str, object] = {
            "interval_seconds": 0.1,
            "save_debug": True,
        }

        config_path = Path.cwd() / "config.json"
        if not config_path.exists():
            return defaults

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("读取 config.json 失败：无法读取 smart_key_monitor 配置")
            return defaults

        screenshot = data.get("screenshot")
        if not isinstance(screenshot, dict):
            return defaults

        interval_raw = screenshot.get("smart_key_monitor_interval")
        save_debug_raw = screenshot.get("smart_key_monitor_save_debug")

        interval = defaults["interval_seconds"]
        try:
            if interval_raw is not None:
                interval = float(interval_raw)
        except Exception:
            interval = defaults["interval_seconds"]

        if not isinstance(interval, (int, float)) or interval <= 0:
            interval = defaults["interval_seconds"]

        save_debug = defaults["save_debug"]
        if isinstance(save_debug_raw, bool):
            save_debug = save_debug_raw

        return {
            "interval_seconds": float(interval),
            "save_debug": bool(save_debug),
        }

    def _capture_full_screen_qimage(self) -> Optional[QImage]:
        """在 UI 线程抓全屏截图。"""

        screen = QApplication.primaryScreen()
        if screen is None:
            return None
        img: QImage = screen.grabWindow(0).toImage()
        if img is None or img.isNull():
            return None
        return img

    def _cut_skill_areas_from_image(
        self,
        full_img: QImage,
        *,
        max_count: int = 6,
        save_debug: bool = True,
    ) -> dict[int, QImage]:
        """从给定全屏图中裁剪技能区域并返回 index->QImage。"""

        if full_img is None or full_img.isNull() or not self._skill_areas:
            return {}

        ref_w = self._small_pic_region.ref_screen_width if self._small_pic_region else None
        ref_h = self._small_pic_region.ref_screen_height if self._small_pic_region else None

        img_w = full_img.width()
        img_h = full_img.height()

        scale_x = 1.0
        scale_y = 1.0
        if ref_w and ref_h:
            scale_x = img_w / float(ref_w)
            scale_y = img_h / float(ref_h)

        out: dict[int, QImage] = {}

        for area in self._skill_areas[:max_count]:
            x = area.x
            y = area.y
            w = area.width
            h = area.height

            if ref_w and ref_h:
                x = int(round(x * scale_x))
                y = int(round(y * scale_y))
                w = int(round(w * scale_x))
                h = int(round(h * scale_y))

            x = max(0, x)
            y = max(0, y)
            x2 = min(img_w, x + w)
            y2 = min(img_h, y + h)
            w2 = max(0, x2 - x)
            h2 = max(0, y2 - y)
            if w2 <= 0 or h2 <= 0:
                continue

            cut = full_img.copy(x, y, w2, h2)
            if cut.isNull():
                continue

            out[area.index] = cut
            if save_debug:
                ImageShop.save_skill_area(full_img, x, y, w2, h2, area.index)

        return out

    def _resolve_monitor_keys_1_to_6(self) -> dict[int, str]:
        """解析监控要发的按键：优先读 timed_key 的 1-6，fallback 到 screenshot.skill_key_config。"""

        keys: dict[int, str] = {}

        try:
            from DiabloClicker.service.key_sender.timed_key_config_store import (
                load_timed_key_configs,
            )
        except Exception:
            load_timed_key_configs = None  # type: ignore[assignment]

        if load_timed_key_configs is not None:
            try:
                for cfg in load_timed_key_configs():
                    hk = (cfg.hotkey or "").strip()
                    if hk in {"1", "2", "3", "4", "5", "6"} and cfg.enabled:
                        keys[int(hk)] = hk
            except Exception:
                logging.exception("读取 timed_key.keys 失败，回退到 screenshot.skill_key_config")

        # fallback
        for idx in range(1, 7):
            if idx not in keys:
                hk = (self._skill_key_by_index.get(idx) or "").strip()
                if hk:
                    keys[idx] = hk

        return keys

    def _get_smart_key_table_snapshot_by_index(self, *, max_count: int = 6) -> dict[int, dict[str, object]]:
        """从 smart_key 表格读取当前勾选/热键（UI 线程调用）。

        约定：
        - 第 1 行对应 skill 1，第 2 行对应 skill 2 ...
        - enabled=False 时：worker 不做灰度检测，也不发键
        """

        out: dict[int, dict[str, object]] = {}
        try:
            rows = int(self.tableWidget.rowCount())
        except Exception:
            return out

        for row in range(min(rows, max_count)):
            idx = row + 1
            send_hotkey_item = self.tableWidget.item(row, 2)
            enabled_item = self.tableWidget.item(row, 1)
            send_hotkey = send_hotkey_item.text().strip() if send_hotkey_item else ""
            enabled = bool(enabled_item and enabled_item.checkState() == Qt.Checked)
            out[idx] = {"send_hotkey": send_hotkey, "enabled": enabled}
        return out

    def _ensure_monitor_hwnd(self) -> Optional[int]:
        """确保已解析到目标窗口 hwnd。"""

        if self._monitor_hwnd:
            return self._monitor_hwnd

        try:
            from DiabloClicker.service.key_sender.timed_key_sender import (
                get_hwnd_by_title,
                load_target_window_title,
            )
        except Exception:
            logging.exception("缺少依赖：无法导入 timed_key_sender")
            return None

        title = load_target_window_title("暗黑破坏神IV")
        hwnd = get_hwnd_by_title(title)
        self._monitor_hwnd = hwnd
        self._monitor_hwnd_title = title
        if hwnd is None:
            logging.warning("未找到目标窗口句柄：title=%s", title)
        else:
            logging.info("监控目标窗口句柄：hwnd=%s title=%s", hwnd, title)
        return hwnd

    def _monitor_worker_main(self) -> None:
        """后台 worker：从队列拿到技能小图，做 SAT 判断并发键。"""


        stop_event = self._monitor_stop_event
        q = self._monitor_queue
        if stop_event is None or q is None:
            return

        sat_disable_threshold = 50.0
        keys_by_index = self._resolve_monitor_keys_1_to_6()

        while not stop_event.is_set():
            try:
                item = q.get(timeout=0.2)
            except queue.Empty:
                continue

            if item is None:
                continue

            # item: (cuts, table_snapshot)
            try:
                skill_images, table_snapshot = item
            except Exception:
                continue

            hwnd = self._ensure_monitor_hwnd()
            if hwnd is None:
                continue

            for idx in sorted(skill_images.keys()):
                if stop_event.is_set():
                    break

                # 表格“启用”未勾选：不做灰度检测，也不发键
                enabled_cfg = None
                try:
                    enabled_cfg = table_snapshot.get(idx) if isinstance(table_snapshot, dict) else None
                except Exception:
                    enabled_cfg = None
                if isinstance(enabled_cfg, dict):
                    if not bool(enabled_cfg.get("enabled", True)):
                        continue

                # 优先用表格的热键，其次 fallback 到原逻辑解析到的 1-6
                hotkey = ""
                if isinstance(enabled_cfg, dict):
                    hotkey = str(enabled_cfg.get("send_hotkey") or "").strip()
                if not hotkey:
                    hotkey = (keys_by_index.get(idx) or "").strip()
                if not hotkey:
                    continue

                img_qt = skill_images[idx]
                try:
                    bgr = self._qimage_to_cv_bgr(img_qt)
                except Exception:
                    continue

                mean_sat: float | None
                try:
                    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
                    mean_sat = float(hsv[:, :, 1].mean())
                except Exception:
                    mean_sat = None

                enabled_now = bool(mean_sat is not None and mean_sat >= sat_disable_threshold)

                # 你的需求：只要当前帧判定为“可用（非灰色）”，就发送按键
                if enabled_now:
                    logging.info(
                        "监控触发：skill=%s hotkey=%s sat=%s hwnd=%s",
                        idx,
                        hotkey,
                        f"{mean_sat:.1f}" if mean_sat is not None else "None",
                        hwnd,
                    )
                    try:
                        send_key_to_hwnd(
                            hwnd,
                            hotkey,
                            repeat_times=1,
                            repeat_interval_seconds=0.0,
                            should_stop=stop_event.is_set,
                        )
                    except Exception:
                        logging.exception("发送按键失败：skill=%s hotkey=%s", idx, hotkey)
                

    def _on_monitor_timer_tick(self) -> None:
        """UI 线程：抓屏并裁剪，把 1-6 技能小图投递到 worker。"""

        if self._monitor_queue is None or self._monitor_stop_event is None:
            return
        if self._monitor_stop_event.is_set():
            return

        full_img = self._capture_full_screen_qimage()
        if full_img is None or full_img.isNull():
            return

        # 更新缓存（供你调试/后续 UI 复用）
        self._full_image = full_img

        save_debug = bool(self._monitor_settings.get("save_debug", True))
        cuts = self._cut_skill_areas_from_image(full_img, max_count=6, save_debug=save_debug)
        if not cuts:
            return

        # UI 线程读取 table 勾选状态快照（worker 线程不可直接读 Qt 控件）
        table_snapshot = self._get_smart_key_table_snapshot_by_index(max_count=6)

        with self._skill_area_lock:
            self._skill_area_images = dict(cuts)

        # 队列只保留最新一帧，避免 worker 堵塞导致延迟累积
        try:
            while True:
                self._monitor_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            self._monitor_queue.put_nowait((cuts, table_snapshot))
        except queue.Full:
            pass

    def _qimage_to_cv_bgr(self, img: QImage):
        """把 QImage 转成 OpenCV 的 BGR numpy 数组。"""

        if img.format() != QImage.Format.Format_RGBA8888:
            img = img.convertToFormat(QImage.Format.Format_RGBA8888)

        width = img.width()
        height = img.height()
        bytes_per_line = img.bytesPerLine()

        # PySide6: QImage.bits() 通常返回 memoryview（没有 setsize）。
        # PyQt/SIP: 可能返回支持 setsize() 的指针对象。
        ptr = img.bits()
        size = int(img.sizeInBytes())
        if hasattr(ptr, "setsize"):
            # 兼容 PyQt
            ptr.setsize(size)  # type: ignore[attr-defined]

        # 统一拿到一个长度正确的 buffer（尽量零拷贝；必要时切片）
        buf = ptr
        if isinstance(buf, memoryview):
            buf = buf[:size]
        else:
            try:
                buf = memoryview(buf)[:size]
            except TypeError:
                # 极端情况下退化为 bytes（会拷贝，但保证可用）
                buf = bytes(ptr)[:size]

        # QImage 每行可能按 32bit 对齐，bytesPerLine 可能 > width*4。
        # 先按 stride 读出，再裁剪到有效像素区域。
        arr = np.frombuffer(buf, dtype=np.uint8)
        arr = arr.reshape((height, bytes_per_line))
        arr = arr[:, : width * 4]
        arr = arr.reshape((height, width, 4))
        # RGBA -> BGR
        bgr = arr[:, :, [2, 1, 0]].copy()
        return bgr

    def _cv2_imread_unicode(self, path: Path):
        """兼容 Windows Unicode 路径的图片读取。

        OpenCV 在部分环境下对含中文/Unicode 的路径支持不稳定，
        这里用 Python 侧读 bytes，再用 cv2.imdecode 解码。
        """

        import cv2  # type: ignore
        import numpy as np  # type: ignore

        try:
            data = np.fromfile(str(path), dtype=np.uint8)
        except Exception:
            return None

        if data.size == 0:
            return None

        try:
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            return None

        return img

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # 窗口/控件大小变化时，重新等比缩放，让宽/高尽量贴边
        self._update_image_view()
        
    def on_screenshot_clicked(self) -> None:
        logging.info("Screenshot button clicked")
        service = CapService()
        service.cap_full_screen()

        # 显示截图：cap_full_window_img 是 QImage，需要转换为 QPixmap 才能 setPixmap
        img = service.cap_full_window_img
        if img is None or img.isNull():
            logging.warning("截图失败：cap_full_window_img 为空")
            return

        # 缓存全图（用于裁剪），并默认展示全图
        self._full_image = img
        self._last_image = img
        self._update_image_view()
        
    def on_smart_pic_cut_clicked(self) -> None:
        logging.info("Smart Pic Cut button clicked")
        # 根据当前截图，裁剪出智能按键区域 + 技能区域并保存
        if self._full_image is None or self._full_image.isNull():
            logging.warning("无法裁剪：没有有效全屏截图")
            return

        # 直接使用启动时缓存的配置（不在点击时读配置文件）
        region = self._small_pic_region
        if region is None:
            logging.warning("无法裁剪：启动时未读取到有效的 small_pic_region")
            return

        # 如果配置提供了参考分辨率，则按当前截图尺寸等比例缩放裁剪区域。
        img_w = self._full_image.width()
        img_h = self._full_image.height()
        x = region.x
        y = region.y
        w = region.width
        h = region.height

        if region.ref_screen_width and region.ref_screen_height:
            scale_x = img_w / float(region.ref_screen_width)
            scale_y = img_h / float(region.ref_screen_height)
            x = int(round(x * scale_x))
            y = int(round(y * scale_y))
            w = int(round(w * scale_x))
            h = int(round(h * scale_y))
            logging.info(
                "裁剪区域已按参考分辨率缩放：ref=%sx%s img=%sx%s scale=%.4f/%.4f",
                region.ref_screen_width,
                region.ref_screen_height,
                img_w,
                img_h,
                scale_x,
                scale_y,
            )

        # ===== 边界保护 =====
        # QImage.copy(x, y, w, h) 如果越界可能返回空图，这里手动裁剪到有效范围。
        x = max(0, x)
        y = max(0, y)

        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)
        w2 = max(0, x2 - x)
        h2 = max(0, y2 - y)

        if w2 <= 0 or h2 <= 0:
            logging.warning(
                f"裁剪区域越界或无效：region=({x},{y},{w},{h}) image=({img_w}x{img_h})"
            )
            return

        # ===== 裁剪并保存 =====
        img_small = self._full_image.copy(x, y, w2, h2)
        if img_small.isNull():
            logging.warning("裁剪失败：得到的图片为空")
            return

        # 保存到固定路径（ImageShop.tmp_cut_save_path）
        ImageShop.save_small_pic(self._full_image, x, y, w2, h2)
        logging.info(f"已裁剪并保存 small_pic：x={x}, y={y}, w={w2}, h={h2}")

        # ===== 裁剪 skill_area（前 5 个）并保存+缓存 =====
        self._cut_and_cache_skill_areas(max_count=6)

        # ===== UI 回显 =====
        # 让用户立刻看到裁剪结果：用裁剪后的图替换当前显示
        self._last_image = img_small
        self._update_image_view()

    def _cut_and_cache_skill_areas(self, max_count: int = 5) -> None:
        """从全屏截图里裁剪 skill_area 列表中的前 max_count 个区域。

        - 每个区域保存为：screen_shoot/skill_{index}.png
        - 同时缓存到 self._skill_area_images[index]
        """

        if self._full_image is None or self._full_image.isNull():
            return

        if not self._skill_areas:
            logging.warning("未配置 skill_area，跳过技能区域裁剪")
            return

        # 参考分辨率（优先用 small_pic_region 的 ref）
        ref_w = self._small_pic_region.ref_screen_width if self._small_pic_region else None
        ref_h = self._small_pic_region.ref_screen_height if self._small_pic_region else None

        img_w = self._full_image.width()
        img_h = self._full_image.height()

        scale_x = 1.0
        scale_y = 1.0
        if ref_w and ref_h:
            scale_x = img_w / float(ref_w)
            scale_y = img_h / float(ref_h)

        self._skill_area_images.clear()

        for area in self._skill_areas[:max_count]:
            x = area.x
            y = area.y
            w = area.width
            h = area.height

            # 若有参考分辨率则缩放
            if ref_w and ref_h:
                x = int(round(x * scale_x))
                y = int(round(y * scale_y))
                w = int(round(w * scale_x))
                h = int(round(h * scale_y))

            # 边界保护
            x = max(0, x)
            y = max(0, y)
            x2 = min(img_w, x + w)
            y2 = min(img_h, y + h)
            w2 = max(0, x2 - x)
            h2 = max(0, y2 - y)
            if w2 <= 0 or h2 <= 0:
                logging.warning(
                    "技能区域越界或无效：index=%s name=%s region=(%s,%s,%s,%s) image=(%sx%s)",
                    area.index,
                    area.name,
                    x,
                    y,
                    w,
                    h,
                    img_w,
                    img_h,
                )
                continue

            img_cut = self._full_image.copy(x, y, w2, h2)
            if img_cut.isNull():
                logging.warning("技能区域裁剪失败：index=%s name=%s", area.index, area.name)
                continue

            self._skill_area_images[area.index] = img_cut
            ImageShop.save_skill_area(self._full_image, x, y, w2, h2, area.index)
            logging.info(
                "已裁剪技能区域：index=%s name=%s x=%s y=%s w=%s h=%s",
                area.index,
                area.name,
                x,
                y,
                w2,
                h2,
            )
        
    def on_pic_match_clicked(self) -> None:
        logging.info("Pic Match button clicked")

        # 需要先有截图；如果还没裁剪过，自动裁剪一次（前 5 个）
        if self._full_image is None or self._full_image.isNull():
            logging.warning("无法图片匹配：没有有效全屏截图，请先点击‘截图’")
            self.statusLabel.setText("当前状态：请先截图")
            return

        if not self._skill_area_images:
            self._cut_and_cache_skill_areas(max_count=6)

        if not self._skill_area_images:
            logging.warning("无法图片匹配：没有可用的技能区域截图（skill_area_images 为空）")
            self.statusLabel.setText("当前状态：没有技能截图")
            return

        # OpenCV 模板匹配（参考你之前的 cmp_single_pic 实现）
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception:
            logging.exception("缺少依赖：图片匹配需要安装 opencv-python 与 numpy")
            self.statusLabel.setText("当前状态：缺少 opencv/numpy")
            return

        threshold = 0.89
        sat_disable_threshold = 50.0
        # 你的模板原图是 128x128，但技能区域截图约 115x115。
        # 你测试发现：把“技能图标缩放到 114x114 作为 image(target)”，
        # 把“截图裁剪图作为 template（必要时再缩小一点点）”时分数更高。
        icon_target_size = 114
        ok_count = 0
        total = 0
        self._last_match_score.clear()

        for idx in sorted(self._skill_area_images.keys()):
            total += 1
            img_qt = self._skill_area_images[idx]
            icon = self._skill_icons_by_index.get(idx)
            hotkey = self._skill_key_by_index.get(idx, "")

            if icon is None:
                logging.warning("技能 %s 没有配置 skill_icon，跳过匹配", idx)
                continue

            templ_path = str(icon.icon_path)
            if not icon.icon_path.exists():
                logging.warning("技能 %s 模板图不存在：%s", idx, templ_path)
                continue

            try:
                target_bgr = self._qimage_to_cv_bgr(img_qt)
            except Exception:
                logging.exception("技能 %s：QImage 转 OpenCV 失败", idx)
                continue

            # 先判断“灰色（禁用）态”：sat 低于阈值则直接判定禁用，不做任何匹配
            mean_sat: float | None = None
            try:
                hsv = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2HSV)
                mean_sat = float(hsv[:, :, 1].mean())
            except Exception:
                mean_sat = None

            if mean_sat is not None and mean_sat < sat_disable_threshold:
                hk = f" key={hotkey}" if hotkey else ""
                logging.info(
                    "技能状态：index=%s name=%s%s 灰色（禁用） sat=%.1f",
                    idx,
                    icon.name,
                    hk,
                    mean_sat,
                )
                continue

            # Windows 下中文路径可能导致 cv2.imread 失败，优先用 imdecode 方式读取
            icon_bgr = self._cv2_imread_unicode(icon.icon_path)
            logging.info(
                f'技能 {idx}：技能图标路径={templ_path}，尺寸={icon_bgr.shape if icon_bgr is not None else "None"}'
            )
            if icon_bgr is None:
                icon_bgr = cv2.imread(templ_path)
            if icon_bgr is None:
                logging.warning("技能 %s：读取技能图标失败：%s", idx, templ_path)
                continue

            # ===== 下面开始做“模板匹配” =====
            # 这里优先用“彩色匹配”（BGR 三通道）而不是灰度匹配。
            # 注意：这段代码不会修改原始截图/模板文件，只是创建用于匹配的临时数组。
            #
            # 你的需求：
            # - 把“技能图标（缩放到 114x114）”作为 matchTemplate 的 image(target)
            # - 把“截图裁剪出来的技能格子”作为 matchTemplate 的 template
            # 这样你实测 max_val 能更高。
            target_for_match = icon_bgr
            templ_for_match = target_bgr
            try:
                # 先把技能图标（原 128x128）统一缩放到 114x114，便于 1:1 匹配
                target_for_match = cv2.resize(
                    target_for_match,
                    (icon_target_size, icon_target_size),
                    interpolation=cv2.INTER_AREA,
                )

                th, tw = templ_for_match.shape[:2]
                ih, iw = target_for_match.shape[:2]

                # matchTemplate 要求：template 尺寸不能大于 image
                if th > ih or tw > iw:
                    scale = min(iw / float(tw), ih / float(th))
                    if scale <= 0:
                        logging.warning("技能 %s：模板图尺寸无效，跳过", idx)
                        continue
                    new_w = max(1, int(round(tw * scale)))
                    new_h = max(1, int(round(th * scale)))
                    templ_for_match = cv2.resize(
                        templ_for_match,
                        (new_w, new_h),
                        interpolation=cv2.INTER_AREA,
                    )

                # 开始做模板匹配，result 是相似度热力图；取 max_val 作为本次匹配得分
                result = cv2.matchTemplate(
                    target_for_match,
                    templ_for_match,
                    cv2.TM_CCORR_NORMED,
                )
                _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
                logging.info(
                    f'技能 {idx}：模板匹配 max_val={max_val} max_loc={max_loc}， '
                    f'min_val={_min_val}, min_loc={_min_loc} '
                    f'| icon(target)={target_for_match.shape} screenshot(template)={templ_for_match.shape} result={result.shape}'
                )
            except Exception:
                logging.exception("技能 %s：彩色 matchTemplate 失败", idx)
                continue

            score = float(max_val)
            self._last_match_score[idx] = score
            passed = score >= threshold
            if passed:
                ok_count += 1

            name = icon.name
            hk = f" key={hotkey}" if hotkey else ""
            sat_str = f" sat={mean_sat:.1f}" if mean_sat is not None else ""
            logging.info(
                "技能匹配：index=%s name=%s%s score=%.4f passed=%s loc=%s%s",
                idx,
                name,
                hk,
                score,
                passed,
                max_loc,
                sat_str,
            )

        self.statusLabel.setText(f"当前状态：匹配 {ok_count}/{total} (阈值={threshold})")

    def test_match(
        self,
        target_icon_path: str | Path,
        template_icon_path: str | Path,
        *,
        method: int | None = None,
    ) -> float | None:
        """调试用：给两张图的路径，跑一次模板匹配并打印关键指标。

        参数：
        - target_icon_path: “截图里裁剪出来的技能图标/技能格子”图片路径（目标图）
        - template_icon_path: “技能模板图标”图片路径（模板图）
        - method: OpenCV matchTemplate 的方法；默认用当前线上同款 TM_CCORR_NORMED

        返回：
        - 本次匹配得分 max_val（失败返回 None）
        """

        try:
            import cv2  # type: ignore
        except Exception:
            logging.exception("缺少依赖：test_match 需要安装 opencv-python")
            return None

        # 默认使用线上同款方法，便于对齐你现在看到的日志
        if method is None:
            method = cv2.TM_CCORR_NORMED

        target_path = Path(target_icon_path)
        templ_path = Path(template_icon_path)
        if not target_path.is_absolute():
            target_path = Path.cwd() / target_path
        if not templ_path.is_absolute():
            templ_path = Path.cwd() / templ_path

        if not target_path.exists():
            logging.warning("test_match：目标图不存在：%s", target_path)
            return None
        if not templ_path.exists():
            logging.warning("test_match：模板图不存在：%s", templ_path)
            return None

        # 读取图片（优先 Unicode 安全方式；失败再 fallback 到 cv2.imread）
        target_bgr = self._cv2_imread_unicode(target_path)
        if target_bgr is None:
            target_bgr = cv2.imread(str(target_path))
        templ_bgr = self._cv2_imread_unicode(templ_path)
        if templ_bgr is None:
            templ_bgr = cv2.imread(str(templ_path))

        if target_bgr is None:
            logging.warning("test_match：读取目标图失败：%s", target_path)
            return None
        if templ_bgr is None:
            logging.warning("test_match：读取模板图失败：%s", templ_path)
            return None

        # 计算目标图饱和度均值（用于你分析“灰色/彩色”的状态）
        mean_sat: float | None
        try:
            hsv = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2HSV)
            mean_sat = float(hsv[:, :, 1].mean())
        except Exception:
            mean_sat = None

        logging.info(
            "test_match：target=%s shape=%s | templ=%s shape=%s | mean_sat=%s | method=%s",
            str(target_path),
            getattr(target_bgr, "shape", None),
            str(templ_path),
            getattr(templ_bgr, "shape", None),
            f"{mean_sat:.1f}" if mean_sat is not None else "None",
            int(method),
        )

        target_for_match = target_bgr
        templ_for_match = templ_bgr

        try:
            th, tw = templ_for_match.shape[:2]
            ih, iw = target_for_match.shape[:2]

            # matchTemplate 要求模板不大于目标图：必要时按比例缩小模板
            if th > ih or tw > iw:
                scale = min(iw / float(tw), ih / float(th))
                if scale <= 0:
                    logging.warning("test_match：模板图尺寸无效，跳过")
                    return None
                new_w = max(1, int(round(tw * scale)))
                new_h = max(1, int(round(th * scale)))
                logging.info(
                    "test_match：模板缩放：(%sx%s) -> (%sx%s) scale=%.4f",
                    tw,
                    th,
                    new_w,
                    new_h,
                    scale,
                )
                templ_for_match = cv2.resize(
                    templ_for_match,
                    (new_w, new_h),
                    interpolation=cv2.INTER_AREA,
                )

            result = cv2.matchTemplate(target_for_match, templ_for_match, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        except Exception:
            logging.exception("test_match：matchTemplate 失败")
            return None

        logging.info(
            "test_match：min_val=%.6f min_loc=%s | max_val=%.6f max_loc=%s | result_shape=%s",
            float(min_val),
            min_loc,
            float(max_val),
            max_loc,
            getattr(result, "shape", None),
        )

        return float(max_val)
    
    def on_pic_test_clicked(self) -> None:
        self.test_match(
            target_icon_path="res/icons/skill/坠天星落-114.png",
            template_icon_path="screen_shoot/skill_1.png",
        )
        self.test_match(
            target_icon_path="res/icons/skill/正义仲裁官-114.png",
            template_icon_path="screen_shoot/skill_2.png",
        )
        
    def on_checkbox_start_monitor_changed(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            logging.info("Start Monitor checkbox checked")

            # 刷新配置（允许你改 config.json 后直接生效）
            self._monitor_settings = self._load_smart_key_monitor_settings_from_config()
            interval_seconds = float(self._monitor_settings.get("interval_seconds", 0.1))
            interval_ms = max(1, int(round(interval_seconds * 1000)))

            # 如果已经在跑，避免重复启动
            if self._monitor_timer.isActive() or self._monitor_worker_thread is not None:
                self.statusLabel.setText(f"当前状态：监控已在运行（{interval_seconds:.3f}s）")
                return

            self._monitor_stop_event = threading.Event()
            self._monitor_queue = queue.Queue(maxsize=1)
            self._monitor_last_enabled = {}
            self._monitor_hwnd = None
            self._monitor_hwnd_title = ""

            self._monitor_worker_thread = threading.Thread(
                target=self._monitor_worker_main,
                name="smart_key_monitor_worker",
                daemon=True,
            )
            self._monitor_worker_thread.start()

            self._monitor_timer.setInterval(interval_ms)
            self._monitor_timer.start()

            self.statusLabel.setText(f"当前状态：监控已启动（{interval_seconds:.3f}s）")
        else:
            logging.info("Start Monitor checkbox unchecked")

            if self._monitor_timer.isActive():
                self._monitor_timer.stop()

            if self._monitor_stop_event is not None:
                self._monitor_stop_event.set()

            if self._monitor_queue is not None:
                try:
                    self._monitor_queue.put_nowait(None)
                except Exception:
                    pass

            if self._monitor_worker_thread is not None:
                self._monitor_worker_thread.join(timeout=1.0)

            self._monitor_worker_thread = None
            self._monitor_queue = None
            self._monitor_stop_event = None
            self._monitor_hwnd = None

            self.statusLabel.setText("当前状态：监控已停止")

    def stop_monitor_from_external(self) -> None:
        """供外部（例如全局热键/主窗口）强制停止监控。

        说明：
        - 通过取消勾选触发 on_checkbox_start_monitor_changed 的停止分支
        - 不做“切换”，只做停止（避免误启动）
        """

        try:
            if self.checkBoxStartMonitor.isChecked():
                self.checkBoxStartMonitor.setChecked(False)
        except Exception:
            pass

    def toggle_monitor_from_external(self) -> None:
        """供外部（例如全局热键）切换监控启停。"""

        try:
            self.checkBoxStartMonitor.toggle()
        except Exception:
            pass

    def toggle_row_enabled_by_index(self, index: int) -> None:
        """切换表格中某一行（按技能序号 1..N）的“启用”勾选状态。"""

        try:
            idx = int(index)
        except Exception:
            return
        if idx <= 0:
            return

        row = idx - 1
        if row < 0 or row >= self.tableWidget.rowCount():
            return

        enabled_item = self.tableWidget.item(row, 1)
        if enabled_item is None:
            enabled_item = QTableWidgetItem("启用")
            enabled_item.setCheckState(Qt.Unchecked)
            self.tableWidget.setItem(row, 1, enabled_item)

        enabled_item.setCheckState(Qt.Unchecked if enabled_item.checkState() == Qt.Checked else Qt.Checked)