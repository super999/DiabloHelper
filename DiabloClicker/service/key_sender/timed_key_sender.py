# -*- coding: utf-8 -*-
"""定时按键发送（与 UI 解耦）。

你可以把它理解成三层：
1) 配置层：从 config.json 读取目标窗口标题
2) 系统层：通过 win32 API 找到窗口句柄(hwnd)，并向窗口发送按键消息
3) 调度层：使用 QThread 在后台按 interval 周期调度多个按键

注意：
- 该实现使用 win32gui.PostMessage 发送 WM_KEYDOWN/WM_KEYUP。
- 部分游戏/程序可能屏蔽 PostMessage，此时需要改用 SendInput 等更底层方式。
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Optional

from PySide6.QtCore import QThread, Signal

import win32con  # type: ignore
import win32gui  # type: ignore

from DiabloClicker.service.db_op.desktop_op import DesktopService


@dataclass(frozen=True)
class KeyConfig:
    """一条按键配置。

    字段解释：
    - hotkey: 要发送的按键（当前支持：0-9、A-Z、F1-F24、SPACE/ENTER/TAB/ESC）
    - enabled: 是否启用
    - interval: 发送间隔（秒），支持小数
    - description: 仅用于 UI 展示/备注，不参与逻辑
    """

    hotkey: str
    enabled: bool
    interval: float
    description: str


# 固定配置文件位置：以“项目启动路径(cwd)”为根目录的 config.json
# 你说的项目启动路径，就是进程启动时的当前工作目录 (current working directory)。
# 例如你在项目根目录运行 `python launch.py`，那么 cwd 通常就是项目根。
PROJECT_ROOT: Final[Path] = Path.cwd()
CONFIG_PATH: Final[Path] = PROJECT_ROOT / "config.json"


# ===== 按键发送重试策略（可按需调整） =====
# 有些窗口/游戏可能偶发丢消息，所以这里默认每次按键发送 3 遍。
# 每遍之间留 200ms 间隔，避免“同一帧”或过于密集导致被忽略。
KEY_SEND_REPEAT_TIMES: Final[int] = 3
KEY_SEND_REPEAT_INTERVAL_SECONDS: Final[float] = 0.2


def load_target_window_title(default_title: str) -> str:
    """读取目标窗口标题。

    读取顺序：
    1) 根目录 config.json 的 target_window_title
    2) 如果读取失败/缺失，则返回 default_title

    这样做的好处：
    - 你可以在 config.json 里随时改目标窗口，不用改代码。
    """

    # 固定读取：<项目根目录>/config.json
    if not CONFIG_PATH.exists():
        return default_title

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        title = data.get("target_window_title")
        if isinstance(title, str) and title.strip():
            return title
    except Exception:
        logging.exception("读取 config.json 失败")

    return default_title


def get_hwnd_by_title(target_title: str) -> Optional[int]:
    """根据窗口标题找到 hwnd。

    实现策略：
    - 先 EnumWindows 枚举所有可见窗口，生成 {hwnd: title}
    - 先做“精确匹配”
    - 再做“包含匹配”（有些窗口标题会带额外状态信息）

    返回：
    - 找到则返回 hwnd（int），找不到返回 None
    """

    DesktopService.clear_all_title()
    win32gui.EnumWindows(DesktopService().get_all_hwnd, 0)

    # 1) 精确匹配
    for hwnd, title in DesktopService().hwnd_title.items():
        if title == target_title:
            return hwnd

    # 2) 包含匹配（更宽松）
    for hwnd, title in DesktopService().hwnd_title.items():
        if target_title in title:
            return hwnd

    return None


def hotkey_to_vk(hotkey: str) -> Optional[int]:
    """把“人类可读的按键字符串”转换为 Windows 虚拟键码 VK。

    目前支持：
    - 单字符：0-9、A-Z
    - 功能键：F1-F24
    - 少量常用键：SPACE/ENTER/TAB/ESC

    如果不支持，返回 None。
    """

    key = (hotkey or "").strip().upper()
    if not key:
        return None

    # 单字符：数字/字母
    if len(key) == 1:
        ch = key[0]
        if "0" <= ch <= "9" or "A" <= ch <= "Z":
            return ord(ch)
        return None

    # F1-F24
    if key.startswith("F") and key[1:].isdigit():
        n = int(key[1:])
        if 1 <= n <= 24:
            return getattr(win32con, f"VK_F{n}")

    mapping = {
        "SPACE": win32con.VK_SPACE,
        "ENTER": win32con.VK_RETURN,
        "TAB": win32con.VK_TAB,
        "ESC": win32con.VK_ESCAPE,
        "ESCAPE": win32con.VK_ESCAPE,
    }
    return mapping.get(key)


def send_key_to_hwnd(
    hwnd: int,
    hotkey: str,
    *,
    repeat_times: int = KEY_SEND_REPEAT_TIMES,
    repeat_interval_seconds: float = KEY_SEND_REPEAT_INTERVAL_SECONDS,
    should_stop: Optional[Callable[[], bool]] = None,
) -> None:
    """向指定 hwnd 发送按键（按下+抬起），并支持重试。

    说明：
    - 这里使用 PostMessage 给目标窗口投递键盘消息。
    - 为了提高接收概率，会尝试 SetForegroundWindow（失败也无所谓）。
    - 为了降低丢消息概率：同一个按键会发送 repeat_times 遍，每遍间隔 repeat_interval_seconds。

    常见坑：
    - 某些游戏/程序不处理 PostMessage 的键盘消息，此时需要更底层的输入注入。
    """

    vk = hotkey_to_vk(hotkey)
    if vk is None:
        logging.warning(f"不支持的按键: {hotkey}")
        return

    if repeat_times <= 0:
        repeat_times = 1
    if repeat_interval_seconds < 0:
        repeat_interval_seconds = 0.0

    # 让目标窗口尽量成为前台窗口（可能会失败，比如权限/焦点限制）
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass

    for attempt in range(1, repeat_times + 1):
        if should_stop and should_stop():
            return
        try:
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)
        except Exception:
            logging.exception(f"发送按键失败（第 {attempt}/{repeat_times} 次）")

        # 最后一遍不需要 sleep
        if attempt != repeat_times and repeat_interval_seconds > 0:
            # 这里不做长 sleep，保持对 stop 的响应
            slept = 0.0
            while slept < repeat_interval_seconds:
                if should_stop and should_stop():
                    return
                step = min(0.02, repeat_interval_seconds - slept)
                time.sleep(step)
                slept += step


class TimedKeySenderThread(QThread):
    """后台线程：按多条配置定时发送按键。

    为什么用线程：
    - UI 主线程要保持响应，不能被 time.sleep 阻塞。

    工作方式（核心思想）：
    - 只在启动时解析/过滤一次配置
    - 为每条配置维护一个 next_run 时间点
    - 循环中检查哪些“到点了”，到点就发一次，然后更新 next_run

    停止方式：
    - UI 调用 stop() 设置标志位
    - run() 循环检测到标志位后自然退出
    """

    # 向 UI 通知：某个 hotkey 的“下一次触发时间点”(time.monotonic) 更新了。
    # UI 拿到 next_due 后，就可以自己用 QTimer 去计算“剩余时间 = next_due - time.monotonic()”。
    next_due_changed = Signal(str, float)

    def __init__(self, configs: list[KeyConfig], target_window_title: str):
        super().__init__()
        self._configs = configs
        self._target_window_title = target_window_title
        self._stop = False

        # UI 线程可能会在运行中请求“重置某个按键的剩余时间”。
        # 这里用一个锁保护共享数据，避免并发读写 next_run 时出问题。
        self._override_lock = threading.Lock()
        self._override_next_due: dict[str, float] = {}

    def stop(self) -> None:
        """请求停止线程（非强杀）。"""

        self._stop = True

    def request_next_due_in(self, hotkey: str, seconds: float) -> None:
        """请求把某个 hotkey 的下一次触发时间改为“seconds 秒后”。

        这个函数会从 UI 线程调用，所以：
        - 这里只做“记录请求”，不直接操作 run() 里的 next_run
        - run() 循环会定期读取这些请求并应用

        参数：
        - hotkey: 哪个按键要重置
        - seconds: 希望多少秒后触发（例如 1.0 表示 1 秒后）
        """

        hotkey = (hotkey or "").strip()
        if not hotkey:
            return
        if seconds <= 0:
            seconds = 0.0

        next_due = time.monotonic() + seconds
        with self._override_lock:
            self._override_next_due[hotkey] = next_due

    def run(self) -> None:
        """线程入口：查窗口、过滤配置、循环调度。"""

        hwnd = get_hwnd_by_title(self._target_window_title)
        if not hwnd:
            logging.warning(f"未找到目标窗口: {self._target_window_title}")
            return

        enabled_configs: list[KeyConfig] = [
            c for c in self._configs if c.enabled and c.interval and c.interval > 0
        ]
        if not enabled_configs:
            logging.info("没有启用的按键配置，线程直接退出")
            return

        # ===== 启动后的“第一次发送”策略（按你的需求定制） =====
        # 1) 所有技能默认先等待 2 秒（给游戏/窗口一个准备时间）
        # 2) 第一次发送不要挤在同一帧：按顺序错峰发送
        #    - 第 1 个：20ms
        #    - 第 2 个：40ms
        #    - 第 3 个：60ms
        #    ...
        # 3) 每个按键的下一次触发时间，从它“首次发送的那一刻”开始计算：send_time + interval

        initial_wait_seconds = 2.0
        stagger_step_seconds = 0.02

        start_at = time.monotonic()
        # 如果 stop 在等待期间被点了，尽快退出
        while not self._stop and (time.monotonic() - start_at) < initial_wait_seconds:
            time.sleep(0.02)
        if self._stop:
            return

        # 用 hotkey 作为 key，便于 UI 侧按 hotkey 找到对应行。
        next_run: dict[str, float] = {}

        base = time.monotonic()
        for index, cfg in enumerate(enabled_configs, start=1):
            if self._stop:
                return

            # 让第 index 个按键在 base + index*20ms 时刻发送
            desired = base + (index * stagger_step_seconds)
            while not self._stop:
                now = time.monotonic()
                remaining = desired - now
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 0.02))
            if self._stop:
                return

            send_key_to_hwnd(hwnd, cfg.hotkey, should_stop=lambda: self._stop)
            send_time = time.monotonic()
            logging.info(
                f"(首次错峰) 发送按键 {cfg.hotkey} 到窗口 {self._target_window_title} (hwnd={hwnd})"
            )

            # 从“本次发送的时间点”开始计时下一次
            next_due = send_time + cfg.interval
            next_run[cfg.hotkey] = next_due
            self.next_due_changed.emit(cfg.hotkey, next_due)

        # 主循环：每 20ms 检查一次是否有按键到点
        while not self._stop:
            # 先应用 UI 侧发来的“重置 next_due”请求
            with self._override_lock:
                overrides = dict(self._override_next_due)
                self._override_next_due.clear()
            for hotkey, next_due in overrides.items():
                # 只有线程管理的按键才处理（避免 UI 传入无效 hotkey）
                if hotkey in next_run:
                    next_run[hotkey] = next_due
                    self.next_due_changed.emit(hotkey, next_due)

            now = time.monotonic()
            for cfg in enabled_configs:
                due = next_run.get(cfg.hotkey, now)
                if now >= due:
                    send_key_to_hwnd(hwnd, cfg.hotkey, should_stop=lambda: self._stop)
                    logging.info(f"发送按键 {cfg.hotkey} 到窗口 {self._target_window_title} (hwnd={hwnd})")
                    next_due = now + cfg.interval
                    next_run[cfg.hotkey] = next_due
                    self.next_due_changed.emit(cfg.hotkey, next_due)

            time.sleep(0.02)
