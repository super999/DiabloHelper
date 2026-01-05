@echo on
setlocal enabledelayedexpansion

REM 说明：
REM - 保持 onefile 打包方式不变
REM - 打包完成后把 res\sounds 复制到 dist\res\sounds
REM - 请在项目根目录运行，或直接双击本脚本

cd /d "%~dp0.."

set APP_NAME=DiabloHelper
set SRC_SOUNDS=res\sounds
set DST_SOUNDS=dist\res\sounds

echo Building %APP_NAME% with PyInstaller...
echo SRC_SOUNDS: %SRC_SOUNDS%
echo DST_SOUNDS: %DST_SOUNDS%

echo [1/2] PyInstaller building...
pyinstaller --onefile --windowed launch.py --console --name="%APP_NAME%"
if errorlevel 1 ( 
  echo PyInstaller failed.
  exit /b 1
)

echo [2/2] Copying sounds: "%SRC_SOUNDS%" -> "%DST_SOUNDS%"
if not exist "%SRC_SOUNDS%" (
  echo Source folder not found: %SRC_SOUNDS%
  exit /b 1
)

if not exist "%DST_SOUNDS%" (
  echo ready to create destination folder: %DST_SOUNDS%
  mkdir "%DST_SOUNDS%" >nul 2>nul
)

echo copy from "%SRC_SOUNDS%" to "%DST_SOUNDS%"
xcopy /E /I /Y "%SRC_SOUNDS%\*" "%DST_SOUNDS%\" >nul
if errorlevel 1 (
  echo Copy sounds failed.
  exit /b 1
)

echo Done.
