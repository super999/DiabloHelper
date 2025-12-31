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
        
    def showEvent(self, event) -> None:
        super().showEvent(event)
        # 在 tab 页显示时执行的代码
        logging.info("Smart Key tab is shown")
        
    def bind_events(self) -> None:
        # 绑定 UI 事件处理函数
        self.pushButton_screenshot.clicked.connect(self.on_screenshot_clicked)
        self.pushButton_smart_pic_cut.clicked.connect(self.on_smart_pic_cut_clicked)
        self.pushButton_pic_match.clicked.connect(self.on_pic_match_clicked)

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

    def _qimage_to_cv_bgr(self, img: QImage):
        """把 QImage 转成 OpenCV 的 BGR numpy 数组。"""

        # 延迟导入：避免环境没装 opencv/numpy 时直接崩
        import numpy as np  # type: ignore

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
        self._cut_and_cache_skill_areas(max_count=5)

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
            self._cut_and_cache_skill_areas(max_count=5)

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

            # Windows 下中文路径可能导致 cv2.imread 失败，优先用 imdecode 方式读取
            templ_bgr = self._cv2_imread_unicode(icon.icon_path)
            if templ_bgr is None:
                templ_bgr = cv2.imread(templ_path)
            if templ_bgr is None:
                logging.warning("技能 %s：读取模板失败：%s", idx, templ_path)
                continue

            # 灰度匹配更稳一些
            target_gray = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2GRAY)
            templ_gray = cv2.cvtColor(templ_bgr, cv2.COLOR_BGR2GRAY)

            th, tw = templ_gray.shape[:2]
            ih, iw = target_gray.shape[:2]

            # matchTemplate 要求 template 不大于 image
            if th > ih or tw > iw:
                scale = min(iw / float(tw), ih / float(th))
                if scale <= 0:
                    logging.warning("技能 %s：模板图尺寸无效，跳过", idx)
                    continue
                new_w = max(1, int(round(tw * scale)))
                new_h = max(1, int(round(th * scale)))
                templ_gray = cv2.resize(templ_gray, (new_w, new_h), interpolation=cv2.INTER_AREA)

            try:
                result = cv2.matchTemplate(target_gray, templ_gray, cv2.TM_CCORR_NORMED)
                _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
            except Exception:
                logging.exception("技能 %s：matchTemplate 失败", idx)
                continue

            score = float(max_val)
            self._last_match_score[idx] = score
            passed = score >= threshold
            if passed:
                ok_count += 1

            name = icon.name
            hk = f" key={hotkey}" if hotkey else ""
            logging.info(
                "技能匹配：index=%s name=%s%s score=%.4f passed=%s loc=%s",
                idx,
                name,
                hk,
                score,
                passed,
                max_loc,
            )

        self.statusLabel.setText(f"当前状态：匹配 {ok_count}/{total} (阈值={threshold})")