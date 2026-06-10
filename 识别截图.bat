@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法:把一张结算/对位截图直接拖到这个文件上。
  pause
  exit /b
)
echo ============================================
echo  正在识别:%~1
echo ============================================
python -m lol_coach.extract "%~1"
echo.
echo 上面的 JSON 已同时存到 data\matches\ 文件夹。
echo 把这段 JSON 复制发给对话,就能得到诊断。
pause
