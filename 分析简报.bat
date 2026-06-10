@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法：把某个英雄周期的 _汇总.json 拖到这个文件上。
  pause
  exit /b
)
set /p RANK=请输入你的段位(如 黄金/铂金): 
set /p VER=国服客户端显示的版本号(如 14.10,不知道就直接回车): 
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
echo ====== 生成分析简报 ======
if "%VER%"=="" (
  %RUN% -m lol_coach.learn.brief "%~1" --rank "%RANK%"
) else (
  %RUN% -m lol_coach.learn.brief "%~1" --rank "%RANK%" --version "%VER%"
)
echo.
echo 把上面这段简报整个复制发给对话,我就给你出完整分析。
pause
