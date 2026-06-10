@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法：把一个【英雄文件夹】拖到这个文件上（文件夹名=英雄名，里面放该英雄的对局截图）。
  pause
  exit /b
)
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 正在批量识别文件夹：%~1 ======
%RUN% -m lol_coach.batch "%~1"
echo.
echo 汇总已存到 data\matches\ 文件夹，复制上面的内容发给对话即可出诊断。
pause
