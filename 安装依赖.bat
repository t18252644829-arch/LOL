@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python
if errorlevel 1 (
  echo [错误] 没找到 Python，请先安装 Python 并勾选 Add Python to PATH。
  pause
  exit /b
)
echo ====== 正在安装 OCR 依赖（只需第一次，需联网） ======
python -m pip install -r requirements.txt
echo.
echo 安装完成。以后把截图拖到「识别截图.bat」上即可。
pause
