@echo off
chcp 65001 >nul
echo ==========================================
echo 重启后端服务...
echo ==========================================

REM 查找并终止现有的python进程
echo 正在停止旧的后端服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend Server*" 2>nul

REM 等待进程完全停止
timeout /t 2 /nobreak >nul

echo.
echo 正在启动新的后端服务...
cd backend
start "Backend Server" python app.py

echo.
echo 等待后端服务启动...
timeout /t 3 /nobreak >nul

REM 测试后端连接
echo 测试后端连接...
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务重启成功
    echo 后端地址: http://localhost:5000
    echo.
    echo 现在可以测试API连接了
) else (
    echo ❌ 后端服务启动失败，请检查错误信息
)

echo.
echo ==========================================
pause
