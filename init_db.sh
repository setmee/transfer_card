#!/bin/bash

# 流转卡系统 - 数据库初始化

echo "=========================================="
echo "流转卡系统 - 数据库初始化"
echo "=========================================="

# 检查Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误: Python未安装"
    exit 1
fi

# 使用python3或python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo ""
echo "正在初始化数据库..."
$PYTHON_CMD init_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "数据库初始化成功！"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "数据库初始化失败！"
    echo "=========================================="
fi
