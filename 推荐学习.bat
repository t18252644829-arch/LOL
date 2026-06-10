@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法：把某个英雄周期的 _汇总.json（在 data\matches 里）拖到这个文件上。
  pause
  exit /b
)
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 根据弱点推荐学习视频（B站+YouTube） ======
%RUN% -m lol_coach.learn.recommend "%~1"
echo.
echo 把上面的推荐清单发给对话即可;想总结某个视频,把它链接发我。
pause
