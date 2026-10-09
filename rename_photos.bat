@echo off
if "%~1"=="" (
    echo Drag photo files onto this file to rename them to N.1, N.2, ...
    pause
    exit /b 1
)
chcp 65001 >nul
python "%~dp0rename_photos.py" %*
pause
