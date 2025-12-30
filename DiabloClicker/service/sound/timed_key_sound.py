import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect


@dataclass(frozen=True)
class TimedKeySoundConfig:
    start_sound_path: Optional[str]
    stop_sound_path: Optional[str]
    reset_sound_path: Optional[str] = None
    volume: float = 1.0


def load_timed_key_sound_config() -> TimedKeySoundConfig:
    """从 cwd/config.json 读取定时按键的启动/停止提示音配置。

    建议结构：
    {
      "sounds": {
        "timed_key": {
          "start": "res/sounds/timed_key_start.wav",
          "stop": "res/sounds/timed_key_stop.wav",
          "volume": 0.8
        }
      }
    }

    - 路径支持相对路径（相对 cwd）或绝对路径。
    - 未配置/读取失败：返回 start/stop 为 None（不播放）。
    """

    config_path = Path.cwd() / "config.json"
    if not config_path.exists():
        return TimedKeySoundConfig(start_sound_path=None, stop_sound_path=None, volume=1.0)

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("读取 config.json 失败：无法加载 sounds.timed_key")
        return TimedKeySoundConfig(start_sound_path=None, stop_sound_path=None, volume=1.0)

    sounds = data.get("sounds")
    if not isinstance(sounds, dict):
        return TimedKeySoundConfig(start_sound_path=None, stop_sound_path=None, volume=1.0)

    timed_key = sounds.get("timed_key")
    if not isinstance(timed_key, dict):
        return TimedKeySoundConfig(start_sound_path=None, stop_sound_path=None, volume=1.0)

    start = timed_key.get("start")
    stop = timed_key.get("stop")
    reset = timed_key.get("reset")
    volume_raw = timed_key.get("volume", 1.0)

    start_path = str(start).strip() if isinstance(start, str) and start.strip() else None
    stop_path = str(stop).strip() if isinstance(stop, str) and stop.strip() else None
    reset_path = str(reset).strip() if isinstance(reset, str) and reset.strip() else None

    try:
        volume = float(volume_raw)
    except Exception:
        volume = 1.0

    # 约束到 [0, 1]
    if volume < 0:
        volume = 0.0
    if volume > 1:
        volume = 1.0

    return TimedKeySoundConfig(
        start_sound_path=start_path,
        stop_sound_path=stop_path,
        reset_sound_path=reset_path,
        volume=volume,
    )


class TimedKeySoundPlayer:
    """定时按键启动/停止提示音播放器。

    设计点：
    - 使用 QSoundEffect：非阻塞、实现简单。
    - QSoundEffect 对象必须保活（否则可能播不出来），所以做成类成员。
    """

    def __init__(self, config: Optional[TimedKeySoundConfig] = None) -> None:
        self._config = config or load_timed_key_sound_config()

        self._start_effect = QSoundEffect()
        self._stop_effect = QSoundEffect()
        self._reset_effect = QSoundEffect()

        self._apply_config()

    def reload_from_config(self) -> None:
        self._config = load_timed_key_sound_config()
        self._apply_config()

    def _apply_config(self) -> None:
        # volume 需要先设置好
        self._start_effect.setVolume(self._config.volume)
        self._stop_effect.setVolume(self._config.volume)
        self._reset_effect.setVolume(self._config.volume)

        self._set_effect_source(self._start_effect, self._config.start_sound_path)
        self._set_effect_source(self._stop_effect, self._config.stop_sound_path)

        # reset 音效：优先使用单独配置；若未配置，则回退为 start/stop（确保重置有声音）
        reset_path = self._config.reset_sound_path
        if not reset_path:
            reset_path = self._config.start_sound_path or self._config.stop_sound_path
        self._set_effect_source(self._reset_effect, reset_path)

    @staticmethod
    def _set_effect_source(effect: QSoundEffect, path_str: Optional[str]) -> None:
        if not path_str:
            effect.setSource(QUrl())
            return

        path = Path(path_str)
        if not path.is_absolute():
            path = Path.cwd() / path

        if not path.exists():
            logging.warning("音效文件不存在：%s", str(path))
            effect.setSource(QUrl())
            return

        effect.setSource(QUrl.fromLocalFile(str(path)))

    def play_start(self) -> None:
        if self._start_effect.source().isEmpty():
            return
        self._start_effect.play()

    def play_stop(self) -> None:
        if self._stop_effect.source().isEmpty():
            return
        self._stop_effect.play()

    def play_reset(self) -> None:
        if self._reset_effect.source().isEmpty():
            return
        self._reset_effect.play()
