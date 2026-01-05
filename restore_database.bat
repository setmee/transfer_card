@echo off
chcp 65001 >nul
echo ==========================================
echo 恢复流转卡系统数据库
echo ==========================================

REM 读取数据库配置
echo 正在读取数据库配置...
powershell -Command "$config = Get-Content 'backend\config\config.json' | ConvertFrom-Json; Write-Host $config.database.user" > %TEMP%\db_config.txt
set /p DB_USER=<%TEMP%\db_config.txt
powershell -Command "$config = Get-Content 'backend\config\config.json' | ConvertFrom-Json; Write-Host $config.database.password" > %TEMP%\db_config.txt
set /p DB_PASS=<%TEMP%\db_config.txt
powershell -Command "$config = Get-Content 'backend\config\config.json' | ConvertFrom-Json; Write-Host $config.database.database" > %TEMP%\db_config.txt
set /p DB_NAME=<%TEMP%\db_config.txt

echo.
echo 数据库配置:
echo   用户名: %DB_USER%
echo   数据库名: %DB_NAME%
echo.

REM 检查MySQL服务
echo 检查MySQL服务...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: MySQL未安装或未添加到PATH
    pause
    exit /b 1
)

echo.
echo 开始恢复数据库...
echo 这将删除现有数据库并重新创建所有表
echo.
set /p confirm="确认继续？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 操作已取消
    pause
    exit /b 0
)

echo.
echo 正在创建数据库结构...
mysql -u %DB_USER% -p%DB_PASS% < database\schema.sql
if %errorlevel% neq 0 (
    echo.
    echo ❌ 数据库恢复失败！
    echo 请检查：
    echo   1. 数据库配置是否正确
    echo   2. MySQL服务是否运行
    echo   3. database/schema.sql文件是否存在
    pause
    exit /b 1
)

echo.
echo ✅ 数据库恢复成功！
echo.
echo 数据库: %DB_NAME%
echo 已恢复的表: 15个（包括1个视图）
echo.
echo 下一步：
echo   1. 启动后端服务: cd backend ^&^& python app.py
echo   2. 访问系统: http://localhost:8080
echo.
pause
