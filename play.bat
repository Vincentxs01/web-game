@echo off
title 憤怒鳥 Python 精緻重製版
echo 正在啟動憤怒鳥...
"%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe" main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [錯誤] 遊戲異常退出。
    pause
)
