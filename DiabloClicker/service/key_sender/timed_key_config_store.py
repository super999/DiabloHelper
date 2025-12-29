# -*- coding: utf-8 -*-
"""定时按键 Tab 的配置读写。

目标：
- 启动时：从 config.json 读取定时按键配置，回填表格
- 点击“保存配置”按钮时：把表格内容写回 config.json

设计原则：
- 不破坏 config.json 现有字段（如 target_window_title、logging、ui 等）
- 只在一个固定位置读写：以启动 cwd 为根目录的 config.json
- 文件不存在/字段缺失时，返回空列表，由 UI 决定用默认值
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Final

from DiabloClicker.service.key_sender.timed_key_sender import KeyConfig


CONFIG_PATH: Final[Path] = Path.cwd() / "config.json"

# 在 config.json 里保存的 key
TIMED_KEY_ROOT_KEY: Final[str] = "timed_key"
TIMED_KEY_LIST_KEY: Final[str] = "keys"


def _read_config_json() -> dict[str, Any]:
    """读取 config.json 并返回 dict。

    - 如果文件不存在：返回空 dict
    - 如果 JSON 解析失败：返回空 dict（并记录日志）
    """

    if not CONFIG_PATH.exists():
        return {}

    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("读取 config.json 失败")
        return {}


def _write_config_json(data: dict[str, Any]) -> None:
    """把 dict 写回 config.json（UTF-8，保留中文，带缩进）。"""

    try:
        CONFIG_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
    except Exception:
        logging.exception("写入 config.json 失败")


def load_timed_key_configs() -> list[KeyConfig]:
    """从 config.json 读取定时按键配置。

    期望结构：
    {
      "timed_key": {
        "keys": [
          {"hotkey": "1", "enabled": true, "interval": 6.12, "description": "..."},
          ...
        ]
      }
    }

    返回：
    - 解析到的 KeyConfig 列表；如果没有配置则返回 []
    """

    data = _read_config_json()
    root = data.get(TIMED_KEY_ROOT_KEY)
    if not isinstance(root, dict):
        return []

    items = root.get(TIMED_KEY_LIST_KEY)
    if not isinstance(items, list):
        return []

    configs: list[KeyConfig] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue

        hotkey = str(raw.get("hotkey") or "").strip()
        if not hotkey:
            continue

        enabled = bool(raw.get("enabled", True))

        interval_raw = raw.get("interval", 1)
        try:
            interval = float(interval_raw)
        except Exception:
            interval = 0.0

        description = str(raw.get("description") or "").strip()

        configs.append(
            KeyConfig(
                hotkey=hotkey,
                enabled=enabled,
                interval=interval,
                description=description,
            )
        )

    return configs


def save_timed_key_configs(configs: list[KeyConfig]) -> None:
    """把 KeyConfig 列表保存到 config.json。

    说明：
    - 会保留 config.json 其它字段
    - 只覆盖 timed_key.keys
    """

    data = _read_config_json()

    if TIMED_KEY_ROOT_KEY not in data or not isinstance(data.get(TIMED_KEY_ROOT_KEY), dict):
        data[TIMED_KEY_ROOT_KEY] = {}

    root = data[TIMED_KEY_ROOT_KEY]
    assert isinstance(root, dict)

    root[TIMED_KEY_LIST_KEY] = [
        {
            "hotkey": c.hotkey,
            "enabled": bool(c.enabled),
            "interval": float(c.interval),
            "description": c.description,
        }
        for c in configs
    ]

    _write_config_json(data)
