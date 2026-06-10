@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 长期趋势分析（汇总全部英雄各周期） ======
%RUN% -m lol_coach.trend
echo.
echo 把上面的内容复制发给对话,即可得到长期成长诊断。
pause
