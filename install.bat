@echo off
chcp 65001 >nul
title 衔音令 一键安装
cd /d "%~dp0"

echo.
echo   🎤 Voice Input 安装工具
echo   ========================
echo.

echo   [1/3] 正在安装 Python 依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo   ❌ 安装失败！请检查是否已安装 Python
    echo   下载地址：https://www.python.org/downloads/
    echo   安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo   [2/3] 正在安装模型下载工具...
pip install modelscope -q

echo   [3/3] 正在下载语音模型（约3GB，请耐心等待）...
echo.
echo   如果下载失败，请关闭后重新运行本脚本，会自动续传。
echo.
modelscope download --model keepitsimple/faster-whisper-large-v3 --local_dir models
if %errorlevel% neq 0 (
    echo.
    echo   ⚠️ 模型下载失败。可以重新运行本脚本重试。
    pause
    exit /b 1
)

echo.
echo   ✅ 安装完成！
echo.
echo   现在可以双击 "voice_input_launcher.bat" 启动了
echo.
pause
