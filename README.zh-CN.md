# Diablo Helper (DiabloClicker)

基于 PySide6 的 Windows 桌面辅助工具。提供简单的 GUI 用于监控与截图，并包含
OCR 与窗口捕获的早期基础框架。

语言：简体中文 | [English](README.md)

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
- Miniconda/Conda（建议）
- Python 3.12（开发环境）
- 依赖：
  - `PySide6`
  - `qt-material`
  - `pywin32`
  - `paddleocr`（可选，仅用于 `test_ocr.py`）

## Python 环境说明
- 本项目开发时使用 **Miniconda** 创建的 Python 环境。
- 我会在不同电脑上开发，因此每台电脑的 conda env 目录/路径都可能不同。
- Python 可执行文件 **不在 PATH** 中，请在激活 conda 环境后运行命令，或使用 `conda run -n <env> ...`。

## 安装
```bash
conda create -n diablohelper python=3.12
conda activate diablohelper
pip install PySide6 qt-material pywin32
```

可选方案（venv）：
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

如果不想激活环境，也可以：
```bash
conda run -n diablohelper python launch.py
```

## 说明
- `ui_main_window.py` 由 `main_window.ui` 生成。修改 UI 后请用 Qt 工具重新生成
  （例如 `pyside6-uic`）。
- OCR 演示会将输出写入 `output/` 目录。


启动 designer 方法

```bash
pyside6-designer
```
或
```bash
qt6-tools designer
```