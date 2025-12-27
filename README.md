# Diablo Helper (DiabloClicker)

Windows desktop helper built with PySide6. It provides a simple GUI for
monitoring and screenshots, and includes early scaffolding for OCR and
window capture.

Language: English | [简体中文](README.zh-CN.md)

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
- Miniconda/Conda (recommended)
- Python 3.12 (development environment)
- Dependencies:
  - `PySide6`
  - `qt-material`
  - `pywin32`
  - `paddleocr` (optional, only for `test_ocr.py`)

## Python Environment Notes
- This project is developed using a Python environment created in **Miniconda**.
- I develop on multiple computers, so the conda environment directory/path may differ on each machine.
- The Python executable is **not added to PATH**. Always run commands from an activated conda environment, or use `conda run -n <env> ...`.

## Setup
```bash
conda create -n diablohelper python=3.12
conda activate diablohelper
pip install PySide6 qt-material pywin32
```

Alternative (venv):
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

If you do not activate the environment, you can also run:
```bash
conda run -n diablohelper python launch.py
```

## Notes
- `ui_main_window.py` is generated from `main_window.ui`. Rebuild it after UI
  edits using Qt tools (e.g., `pyside6-uic`).
- The OCR demo writes outputs to the `output/` directory.
