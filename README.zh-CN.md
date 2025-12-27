# Diablo Helper (DiabloClicker)

基于 PySide6 的 Windows 桌面辅助工具。提供简单的 GUI 用于监控与截图，并包含
OCR 与窗口捕获的早期基础框架。

## 功能
- PySide6 GUI（Qt Designer UI 文件）
- 启动/停止监控开关与基础动作
- 通过 Win32 API 枚举窗口
- 可选 OCR 演示（见 `test_ocr.py`）

## 目录结构
- `launch.py`: 入口
- `DiabloClicker/main.py`: 应用启动
- `DiabloClicker/main_window.py`: 主窗口逻辑
- `DiabloClicker/ui/main_window.ui`: Qt Designer 源文件
- `DiabloClicker/ui/ui_main_window.py`: 生成的 UI 文件（不要手改）
- `DiabloClicker/service/`: 捕获与桌面服务

## 环境要求
- Windows
- Python 3.9+（建议）
- 依赖：
  - `PySide6`
  - `qt-material`
  - `pywin32`
  - `paddleocr`（可选，仅用于 `test_ocr.py`）

## 安装
```bash
python -m venv .venv
.venv\Scripts\activate
pip install PySide6 qt-material pywin32
```

可选 OCR：
```bash
pip install paddleocr
```

## 运行
```bash
python launch.py
```

## 说明
- `ui_main_window.py` 由 `main_window.ui` 生成。修改 UI 后请用 Qt 工具重新生成
  （例如 `pyside6-uic`）。
- OCR 演示会将输出写入 `output/` 目录。
