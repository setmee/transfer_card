#!/bin/bash

# 流转卡系统OTA更新脚本
# 用途：在线更新系统到新版本，支持回滚

set -e

echo "=========================================="
echo "流转卡系统 - OTA更新"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="/tmp/transfer-card-backup"
VERSION_FILE=".version"
BACKUP_VERSION_FILE="$BACKUP_DIR/.version"
CURRENT_VERSION=$(cat $VERSION_FILE 2>/dev/null || echo "1.0.0")

# 显示当前版本
echo -e "${BLUE}当前版本: $CURRENT_VERSION${NC}"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用root用户运行此脚本${NC}"
    exit 1
fi

# 检查是否为Git仓库
if [ ! -d .git ]; then
    echo -e "${RED}错误: 不是Git仓库，无法进行OTA更新${NC}"
    exit 1
fi

# 创建备份目录
echo -e "${YELLOW}创建备份目录...${NC}"
mkdir -p $BACKUP_DIR

# 备份当前版本
echo -e "${YELLOW}备份当前版本...${NC}"
BACKUP_TIME=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIME"

mkdir -p $BACKUP_PATH

# 备份配置文件
cp -r backend/config $BACKUP_PATH/
cp .env $BACKUP_PATH/ 2>/dev/null || true
cp $VERSION_FILE $BACKUP_DIR/.version 2>/dev/null || echo "$CURRENT_VERSION" > $BACKUP_DIR/.version

# 备份数据库（可选）
read -p "是否备份数据库？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}备份数据库...${NC}"
    docker-compose exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD:-root123456} ${MYSQL_DATABASE:-transfer_card} > $BACKUP_PATH/database_backup_$BACKUP_TIME.sql
    echo -e "${GREEN}数据库备份完成${NC}"
fi

echo -e "${GREEN}备份完成，备份路径: $BACKUP_PATH${NC}"

# 拉取最新代码
echo ""
echo -e "${YELLOW}拉取最新代码...${NC}"
git fetch origin
git log HEAD..origin/main --oneline || true

read -p "确认更新到最新版本？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}更新已取消${NC}"
    exit 0
fi

git pull origin main

# 获取新版本号
NEW_VERSION=$(cat $VERSION_FILE 2>/dev/null || echo "unknown")
echo -e "${BLUE}新版本: $NEW_VERSION${NC}"

# 更新Docker镜像
echo ""
echo -e "${YELLOW}更新Docker镜像...${NC}"
docker-compose pull 2>/dev/null || echo "无法拉取预构建镜像，将本地构建"
docker-compose build

# 重启服务
echo ""
echo -e "${YELLOW}重启服务...${NC}"
docker-compose down
docker-compose up -d

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 15

# 检查服务状态
echo ""
echo -e "${YELLOW}检查服务状态...${NC}"
if docker-compose ps | grep -q "Exit"; then
    echo -e "${RED}警告: 某些容器启动失败${NC}"
    docker-compose ps
    read -p "是否回滚到之前版本？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}正在回滚...${NC}"
        git checkout HEAD~1
        docker-compose down
        docker-compose up -d
        echo -e "${GREEN}回滚完成${NC}"
        exit 0
    fi
fi

# 健康检查
echo ""
echo -e "${YELLOW}执行健康检查...${NC}"
sleep 5

# 检查前端
if curl -f -s http://localhost:8080 > /dev/null; then
    echo -e "${GREEN}✓ 前端服务正常${NC}"
else
    echo -e "${RED}✗ 前端服务异常${NC}"
fi

# 检查后端
if curl -f -s http://localhost:5000/api/health > /dev/null; then
    echo -e "${GREEN}✓ 后端服务正常${NC}"
else
    echo -e "${RED}✗ 后端服务异常${NC}"
fi

# 检查数据库
if docker-compose exec -T mysql mysqladmin -u root -p${MYSQL_ROOT_PASSWORD:-root123456} ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 数据库连接正常${NC}"
else
    echo -e "${RED}✗ 数据库连接异常${NC}"
fi

# 更新完成
echo ""
echo -e "${GREEN}=========================================="
echo -e "${GREEN}OTA更新完成！"
echo -e "${GREEN}=========================================="
echo ""
echo "当前版本: $NEW_VERSION"
echo "备份位置: $BACKUP_PATH"
echo ""
echo "查看日志: docker-compose logs -f"
echo "如需回滚，请运行: ./rollback.sh $BACKUP_TIME"
echo ""

# 提示清理旧备份
echo -e "${YELLOW}提示: 可以在7天后清理旧备份${NC}"
echo "清理命令: find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;"
