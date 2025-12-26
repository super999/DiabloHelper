@echo off
REM 切换到脚本所在目录，保证相对路径正确
cd /d "%~dp0"

REM 批量编译 ui 目录下所有 .ui 文件，只保留 ui_ 前缀命名
for %%f in (*.ui) do (
  echo 正在编译 %%f ...
  if exist "%%~nf_ui.py" del "%%~nf_ui.py"
  pyside6-uic "%%~f" -o "ui_%%~nf.py"
)

echo 编译完成！
