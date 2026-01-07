@echo off
chcp 65001 >nul
echo ==========================================
echo 启动流转卡系统...
echo ==========================================

REM 检查MySQL服务
echo 检查MySQL服务...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: MySQL未安装
    pause
    exit /b 1
)

echo.
echo 启动后端服务...
cd backend
start "Backend Server" python app.py
echo Backend started successfully
echo Backend URL: http://localhost:5000

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 测试后端连接
echo 测试后端连接...
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务运行正常
) else (
    echo ❌ 后端服务启动失败
    pause
    exit /b 1
)

echo.
echo 启动前端服务...
cd ..\frontend
start "Frontend Server" npm start
echo 前端服务已启动
echo 前端地址: http://localhost:8080 或 http://服务器IP:8080

echo.
echo ==========================================
echo 系统启动完成！
echo ==========================================
echo 前端: http://localhost:8080 (本地) 或 http://服务器IP:8080 (外部)
echo 后端: http://localhost:5000
echo 后端健康检查: http://localhost:5000/health
echo.
echo 本地访问: 请在浏览器中访问 http://localhost:8080
echo 外部访问: 请在浏览器中访问 http://服务器IP:8080
echo ==========================================
pause
