# Diablo Helper (DiabloClicker)

Windows desktop helper built with PySide6. It provides a simple GUI for
monitoring and screenshots, and includes early scaffolding for OCR and
window capture.

中文版请看 `README.zh-CN.md`.

## Features
- PySide6 GUI with Qt Designer UI files
- Start/stop monitor toggle and basic actions
- Window enumeration via Win32 APIs
- Optional OCR demo via PaddleOCR (see `test_ocr.py`)

## Project Layout
- `launch.py`: entrypoint
- `DiabloClicker/main.py`: app bootstrap
- `DiabloClicker/main_window.py`: main window logic
- `DiabloClicker/ui/main_window.ui`: Qt Designer source
- `DiabloClicker/ui/ui_main_window.py`: generated UI (do not edit)
- `DiabloClicker/service/`: capture and desktop services

## Requirements
- Windows
- Python 3.9+ (recommended)
- Dependencies:
  - `PySide6`
  - `qt-material`
  - `pywin32`
  - `paddleocr` (optional, only for `test_ocr.py`)

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install PySide6 qt-material pywin32
```

Optional OCR:
```bash
pip install paddleocr
```

## Run
```bash
python launch.py
```

## Notes
- `ui_main_window.py` is generated from `main_window.ui`. Rebuild it after UI
  edits using Qt tools (e.g., `pyside6-uic`).
- The OCR demo writes outputs to the `output/` directory.
