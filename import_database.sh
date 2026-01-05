#!/bin/bash
# 直接导入数据库SQL文件

echo "============================================================"
echo "流转卡系统 - 数据库导入"
echo "============================================================"
echo ""

# 读取配置
CONFIG_FILE="backend/config/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

DB_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['database']['database'])")
DB_HOST=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['database']['host'])")
DB_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['database']['port'])")
DB_USER=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['database']['user'])")
DB_PASS=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['database']['password'])")

echo "ℹ️  目标数据库: $DB_NAME"
echo ""

# 检查SQL文件是否存在
SQL_FILE="database/transfer_card_system.sql"
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL文件不存在: $SQL_FILE"
    exit 1
fi

echo "ℹ️  正在导入数据库: $SQL_FILE"
echo ""

# 导入数据库
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ 数据库导入成功！"
    echo "============================================================"
else
    echo ""
    echo "============================================================"
    echo "❌ 数据库导入失败！"
    echo "============================================================"
    exit 1
fi
