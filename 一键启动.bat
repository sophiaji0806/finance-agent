@echo off
cd /d "%~dp0"
title 智能财务分析 Agent

echo ============================================
echo   智能财务分析 Agent
echo ============================================
echo.
echo 当前目录：
cd
echo.
echo 服务器启动后，浏览器会自动打开 http://localhost:8000
echo 如果没自动打开，请手动在浏览器地址栏输入： http://localhost:8000
echo.
echo 关闭服务：在这个黑窗口里按 Ctrl + C
echo.

start "" http://localhost:8000
python -m uvicorn app.main:app --reload

echo.
echo ============================================
echo 服务已停止（或启动失败，请把上面的错误信息截图）
echo ============================================
pause
