@echo off
chcp 65001 >nul
echo ==========================================
echo 流转卡系统 - 数据库初始化
echo ==========================================

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python未安装
    pause
    exit /b 1
)

echo.
echo 正在初始化数据库...
python init_database.py

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo 数据库初始化成功！
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo 数据库初始化失败！
    echo ==========================================
)

pause
