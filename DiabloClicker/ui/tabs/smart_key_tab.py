import logging
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

from DiabloClicker.service.capture.cap_service import CapService
from DiabloClicker.service.img_ctrl.image_shop import ImageShop
from DiabloClicker.ui.ui_tab_advance_image import Ui_TabAdvanceImage


@dataclass(frozen=True)
class _SmallPicRegion:
    x: int
    y: int
    width: int
    height: int
    ref_screen_width: Optional[int] = None
    ref_screen_height: Optional[int] = None


class TabSmartKey(QWidget, Ui_TabAdvanceImage):
    TAB_NAME = "智能按键"

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.bind_events()

        # 记录最后一次截图（用于窗口尺寸变化时重新缩放显示）
        self._last_image: Optional[QImage] = None

        # small_pic_region：程序启动时读取一次并缓存。
        # 这样点击“裁剪”按钮时不会频繁读磁盘/解析 JSON。
        self._small_pic_region: Optional[_SmallPicRegion] = self._load_small_pic_region_from_config()

        # 保持图片比例：不要让 QLabel 自动拉伸填满（会变形）
        self.labelImageShow.setScaledContents(False)
        self.labelImageShow.setAlignment(Qt.AlignCenter)

        # 让 QLabel 在布局中尽量占满空间，否则 label.size() 可能本身就不大
        self.labelImageShow.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def showEvent(self, event) -> None:
        super().showEvent(event)
        # 在 tab 页显示时执行的代码
        logging.info("Smart Key tab is shown")
        
    def bind_events(self) -> None:
        # 绑定 UI 事件处理函数
        self.pushButton_screenshot.clicked.connect(self.on_screenshot_clicked)
        self.pushButton_smart_pic_cut.clicked.connect(self.on_smart_pic_cut_clicked)

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

        # 先缓存原图，再统一走“等比最大化显示”逻辑
        self._last_image = img
        self._update_image_view()
        
    def on_smart_pic_cut_clicked(self) -> None:
        logging.info("Smart Pic Cut button clicked")
        # 根据当前截图，裁剪出智能按键区域并保存
        if self._last_image is None or self._last_image.isNull():
            logging.warning("无法裁剪智能按键区域：没有有效截图")
            return

        # 直接使用启动时缓存的配置（不在点击时读配置文件）
        region = self._small_pic_region
        if region is None:
            logging.warning("无法裁剪：启动时未读取到有效的 small_pic_region")
            return

        # 如果配置提供了参考分辨率，则按当前截图尺寸等比例缩放裁剪区域。
        img_w = self._last_image.width()
        img_h = self._last_image.height()
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
        img_small = self._last_image.copy(x, y, w2, h2)
        if img_small.isNull():
            logging.warning("裁剪失败：得到的图片为空")
            return

        # 保存到固定路径（ImageShop.tmp_cut_save_path）
        ImageShop.save_small_pic(self._last_image, x, y, w2, h2)
        logging.info(f"已裁剪并保存 small_pic：x={x}, y={y}, w={w2}, h={h2}")

        # ===== UI 回显 =====
        # 让用户立刻看到裁剪结果：用裁剪后的图替换当前显示
        self._last_image = img_small
        self._update_image_view()
        