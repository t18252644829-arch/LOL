@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  正在安装 OCR 依赖(只需第一次,需联网)
echo ============================================
python -m pip install -r requirements.txt
echo.
echo 安装完成。以后识别截图:把截图拖到「识别截图.bat」上即可。
pause
