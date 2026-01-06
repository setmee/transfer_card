#!/bin/bash

# 恢复流转卡系统数据库

echo "=========================================="
echo "恢复流转卡系统数据库"
echo "=========================================="

# 读取数据库配置
echo ""
echo "正在读取数据库配置..."
DB_USER=$(python3 -c "import json; config=json.load(open('backend/config/config.json')); print(config['database']['user'])")
DB_PASS=$(python3 -c "import json; config=json.load(open('backend/config/config.json')); print(config['database']['password'])")
DB_NAME=$(python3 -c "import json; config=json.load(open('backend/config/config.json')); print(config['database']['database'])")

echo ""
echo "数据库配置:"
echo "  用户名: $DB_USER"
echo "  数据库名: $DB_NAME"

# 检查MySQL服务
echo ""
echo "检查MySQL服务..."
if ! command -v mysql &> /dev/null; then
    echo "错误: MySQL未安装或未添加到PATH"
    exit 1
fi

# 检查MySQL连接
if ! mysql -u "$DB_USER" -p"$DB_PASS" -e "SELECT 1" &> /dev/null; then
    echo "错误: 无法连接到MySQL服务器"
    echo "请检查用户名和密码"
    exit 1
fi

echo ""
echo "开始恢复数据库..."
