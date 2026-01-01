import json
import logging
import re
import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ctypes import wintypes


# Win32 constants
WM_HOTKEY = 0x0312

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

VK_NUMPAD0 = 0x60
VK_NUMPAD1 = 0x61
VK_NUMPAD2 = 0x62
VK_NUMPAD3 = 0x63
VK_NUMPAD4 = 0x64
VK_NUMPAD5 = 0x65
VK_NUMPAD6 = 0x66
VK_NUMPAD7 = 0x67
VK_NUMPAD8 = 0x68
VK_NUMPAD9 = 0x69

_user32 = ctypes.windll.user32


@dataclass(frozen=True)
class HotkeySpec:
    modifiers: int
    vk: int
    display: str


def _normalize_hotkey_text(text: str) -> str:
    # 允许配置里写："Ctrl+Num 0" / "CTRL+NUM0" / "Ctrl + Numpad0" 等
    # 统一：去掉多余空白，分隔符统一用 +，并转大写
    text = text.strip()
    # 把各种分隔符都当成 +
    text = re.sub(r"[\s]+", "", text)
    return text.upper()


def _parse_key_token(token: str) -> Optional[int]:
    # token 已经是大写且无空格
    # 支持：NUM0/NUMPAD0/NUM_0/NUM 0（在 normalize 后都会变成 NUM0 或 NUMPAD0）
    token = token.replace("_", "")

    # NUM0 ~ NUM9
    m = re.fullmatch(r"NUM(PAD)?([0-9])", token)
    if m:
        digit = int(m.group(2))
        return VK_NUMPAD0 + digit

    # 直接数字：0-9（主键盘）
    if re.fullmatch(r"[0-9]", token):
        return ord(token)

    # A-Z
    if re.fullmatch(r"[A-Z]", token):
        return ord(token)

    # F1-F24
    m = re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", token)
    if m:
        n = int(m.group(1))
        return 0x70 + (n - 1)  # VK_F1 = 0x70

    # 常见命名
    aliases = {
        "ESC": 0x1B,
        "ESCAPE": 0x1B,
        "ENTER": 0x0D,
        "RETURN": 0x0D,
        "TAB": 0x09,
        "SPACE": 0x20,
    }
    return aliases.get(token)


def parse_hotkey_spec(hotkey_text: str) -> Optional[HotkeySpec]:
    """把配置字符串解析成 Win32 RegisterHotKey 所需的 modifiers + vk。

    期望格式：
    - "Ctrl+Num0"（默认）
    - "Ctrl+Numpad0" / "Alt+Shift+F1" / "Win+Z" 等

    返回：HotkeySpec 或 None。
    """

    if not hotkey_text or not str(hotkey_text).strip():
        return None

    text = _normalize_hotkey_text(str(hotkey_text))
    parts = [p for p in text.split("+") if p]
    if len(parts) < 2:
        return None

    modifiers = 0
    key_token = parts[-1]
    for token in parts[:-1]:
        if token in {"CTRL", "CONTROL"}:
            modifiers |= MOD_CONTROL
        elif token == "ALT":
            modifiers |= MOD_ALT
        elif token == "SHIFT":
            modifiers |= MOD_SHIFT
        elif token in {"WIN", "META"}:
            modifiers |= MOD_WIN
        else:
            # 允许用户把 key 放前面（不推荐），这种情况先跳过
            pass

    vk = _parse_key_token(key_token)
    if vk is None:
        return None

    return HotkeySpec(modifiers=modifiers, vk=vk, display=hotkey_text)


def load_timed_key_toggle_hotkey(default_hotkey: str = "Ctrl+Num0") -> HotkeySpec:
    """从 cwd/config.json 读取定时按键的启动/停止切换热键。

    建议配置结构：
    {
      "hotkeys": {
        "toggle_timed_key": "Ctrl+Num0"
      }
    }

    若读取/解析失败，则回退到默认值。
    """

    config_path = Path.cwd() / "config.json"
    hotkey_text = default_hotkey

    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            hotkeys = data.get("hotkeys")
            if isinstance(hotkeys, dict):
                raw = hotkeys.get("toggle_timed_key")
                if isinstance(raw, str) and raw.strip():
                    hotkey_text = raw.strip()
        except Exception:
            logging.exception("读取 config.json 的 hotkeys.toggle_timed_key 失败，使用默认热键")

    spec = parse_hotkey_spec(hotkey_text)
    if spec is None:
        logging.warning("热键配置解析失败：%s，使用默认热键：%s", hotkey_text, default_hotkey)
        spec = parse_hotkey_spec(default_hotkey)

    # 理论上默认热键必须可解析
    assert spec is not None
    return spec


def load_timed_key_reset_hotkeys() -> list[tuple[str, HotkeySpec]]:
    """从 cwd/config.json 读取每个技能的“重置热键”。

    期望结构：
    {
      "timed_key": {
        "keys": [
          {"hotkey": "1", "toggle_reset_key": "Ctrl+Num1", ...},
          ...
        ]
      }
    }

    返回：
    - [(skill_hotkey, HotkeySpec), ...]
    - 解析失败/缺失则返回 []
    """

    config_path = Path.cwd() / "config.json"
    if not config_path.exists():
        return []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("读取 config.json 失败：无法加载 timed_key.keys[*].toggle_reset_key")
        return []

    timed_key = data.get("timed_key")
    if not isinstance(timed_key, dict):
        return []
    items = timed_key.get("keys")
    if not isinstance(items, list):
        return []

    result: list[tuple[str, HotkeySpec]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue

        skill_hotkey = str(raw.get("hotkey") or "").strip()
        if not skill_hotkey:
            continue

        toggle_reset_key = raw.get("toggle_reset_key")
        if not isinstance(toggle_reset_key, str) or not toggle_reset_key.strip():
            continue

        spec = parse_hotkey_spec(toggle_reset_key.strip())
        if spec is None:
            logging.warning(
                "重置热键解析失败：skill=%s toggle_reset_key=%s",
                skill_hotkey,
                toggle_reset_key,
            )
            continue

        result.append((skill_hotkey, spec))

    return result


def load_smart_key_enable_hotkeys() -> list[tuple[int, HotkeySpec]]:
    """从 cwd/config.json 读取智能按键每行的“启用热键”（enable_hotkey）。

    期望结构：
    {
      "smart_key": {
        "keys": [
          {"enable_hotkey": "Alt+Num1", ...},
          ...
        ]
      }
    }

    返回：
    - [(index, HotkeySpec), ...] 其中 index 从 1 开始，对应表格第 index 行
    - 解析失败/缺失则返回 []
    """

    config_path = Path.cwd() / "config.json"
    if not config_path.exists():
        return []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("读取 config.json 失败：无法加载 smart_key.keys[*].enable_hotkey")
        return []

    smart_key = data.get("smart_key")
    if not isinstance(smart_key, dict):
        return []
    items = smart_key.get("keys")
    if not isinstance(items, list):
        return []

    result: list[tuple[int, HotkeySpec]] = []
    for idx, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            continue
        enable_hotkey = raw.get("enable_hotkey")
        if not isinstance(enable_hotkey, str) or not enable_hotkey.strip():
            continue

        spec = parse_hotkey_spec(enable_hotkey.strip())
        if spec is None:
            logging.warning(
                "启用热键解析失败：index=%s enable_hotkey=%s",
                idx,
                enable_hotkey,
            )
            continue

        result.append((idx, spec))

    return result


def register_hotkey(hwnd: int, hotkey_id: int, spec: HotkeySpec) -> bool:
    """注册全局热键。

    注意：
    - 若已被其它程序占用，会失败。
    - hwnd 传主窗口句柄，这样 WM_HOTKEY 会发到窗口消息循环中。
    """

    try:
        ok = bool(_user32.RegisterHotKey(wintypes.HWND(hwnd), int(hotkey_id), int(spec.modifiers), int(spec.vk)))
        if not ok:
            err = ctypes.get_last_error()
            logging.warning("RegisterHotKey 失败：id=%s hotkey=%s err=%s", hotkey_id, spec.display, err)
        return ok
    except Exception:
        logging.exception("RegisterHotKey 异常：id=%s hotkey=%s", hotkey_id, spec.display)
        return False


def unregister_hotkey(hwnd: int, hotkey_id: int) -> None:
    try:
        _user32.UnregisterHotKey(wintypes.HWND(hwnd), int(hotkey_id))
    except Exception:
        logging.exception("UnregisterHotKey 异常：id=%s", hotkey_id)
