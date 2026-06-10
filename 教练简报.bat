@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 教练状态包(档案+任务+最近对局) ======
%RUN% -m lol_coach.profile digest
echo.
echo 把上面整段复制发给对话,我就能接上你的训练进度。
pause
