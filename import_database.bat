@echo off
REM 直接导入数据库SQL文件

echo ============================================================
echo 流转卡系统 - 数据库导入
echo ============================================================
echo.

REM 读取配置
python -c "import json; config=json.load(open('backend\config\config.json')); print(config['database']['database'])" > tmp_dbname.txt
set /p DB_NAME=<tmp_dbname.txt

python -c "import json; config=json.load(open('backend\config\config.json')); print(config['database']['host'])" > tmp_dbhost.txt
set /p DB_HOST=<tmp_dbhost.txt

python -c "import json; config=json.load(open('backend\config\config.json')); print(config['database']['port'])" > tmp_dbport.txt
set /p DB_PORT=<tmp_dbport.txt

python -c "import json; config=json.load(open('backend\config\config.json')); print(config['database']['user'])" > tmp_dbuser.txt
set /p DB_USER=<tmp_dbuser.txt

python -c "import json; config=json.load(open('backend\config\config.json')); print(config['database']['password'])" > tmp_dbpass.txt
set /p DB_PASS=<tmp_dbpass.txt

del tmp_*.txt

echo ℹ️  目标数据库: %DB_NAME%
echo.

REM 检查SQL文件是否存在
if not exist "database\transfer_card_system.sql" (
    echo ❌ SQL文件不存在: database\transfer_card_system.sql
    pause
    exit /b 1
)

echo ℹ️  正在导入数据库: database\transfer_card_system.sql
echo.

REM 导入数据库
mysql -h %DB_HOST% -P %DB_PORT% -u %DB_USER% -p%DB_PASS% %DB_NAME% < database\transfer_card_system.sql

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo ✅ 数据库导入成功！
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo ❌ 数据库导入失败！
    echo ============================================================
    pause
    exit /b 1
)
