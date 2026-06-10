@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 当前激活的成长任务 ======
%RUN% -m lol_coach.tasks list
echo.
echo 完成某项: 在此窗口输入  %RUN% -m lol_coach.tasks done 编号
pause
