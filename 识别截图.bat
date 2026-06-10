@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法：把一张结算/对位截图直接拖到这个文件上。
  pause
  exit /b
)
where python
if errorlevel 1 (
  echo [错误] 没找到 Python，请先运行 安装依赖.bat。
  pause
  exit /b
)
echo ====== 正在识别：%~1 ======
python -m lol_coach.extract "%~1"
echo.
echo 上面的 JSON 已存到 data\matches\ 文件夹，复制发给对话即可。
pause
