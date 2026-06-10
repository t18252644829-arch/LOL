@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法：把某个英雄周期的 _汇总.json 拖到这个文件上。
  pause
  exit /b
)
set /p RANK=请输入你的段位(如 黄金/铂金): 
set /p LANE=请输入位置(top/jungle/mid/adc/support): 
set /p VER=国服客户端版本号(如 26.10,不知道就直接回车): 
py -3.12 --version
if errorlevel 1 (
  set RUN=python
) else (
  set RUN=py -3.12
)
set VERARG=
if not "%VER%"=="" set VERARG=--version %VER%
echo ====== 生成分析简报(含版本数值/补丁说明) ======
%RUN% -m lol_coach.learn.brief "%~1" --rank "%RANK%" --lane "%LANE%" %VERARG% --patch
echo.
echo 把上面整段简报发给对话;meta(tier/胜率/出装)由我用搜索补上,你只要告诉我英雄和位置即可。
pause
