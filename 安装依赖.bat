@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version
if errorlevel 1 (
  echo [提示] 没检测到 Python 3.12，改用默认 python（建议装 Python 3.12）。
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 正在安装 OCR 依赖（只需第一次，需联网） ======
%RUN% -m pip install -r requirements.txt
echo.
echo 安装完成。以后把截图拖到「识别截图.bat」上即可。
pause
