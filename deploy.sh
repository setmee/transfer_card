#!/bin/bash

# 流转卡系统部署脚本
# 用途：在服务器上首次部署或重新部署整个系统

set -e

echo "=========================================="
echo "流转卡系统 - 开始部署"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用root用户运行此脚本${NC}"
    exit 1
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker安装完成${NC}"
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose未安装，正在安装...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose安装完成${NC}"
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env文件不存在，正在创建...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}请编辑.env文件，设置生产环境的配置${NC}"
    read -p "是否现在编辑.env文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        vi .env
    fi
fi

# 停止现有容器（如果存在）
echo -e "${YELLOW}停止现有容器...${NC}"
docker-compose down 2>/dev/null || true

# 拉取最新代码（如果使用Git）
if [ -d .git ]; then
    echo -e "${YELLOW}拉取最新代码...${NC}"
    git pull origin main
fi

# 构建并启动容器
echo -e "${YELLOW}构建并启动容器...${NC}"
docker-compose up -d --build

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
docker-compose ps

# 查看日志
echo ""
echo -e "${GREEN}=========================================="
echo -e "${GREEN}部署完成！"
echo -e "${GREEN}=========================================="
echo ""
echo "前端访问地址: http://$(hostname -I | awk '{print $1}')"
echo "后端API地址: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
echo ""
echo -e "${YELLOW}首次部署后，请访问以下URL初始化数据库：${NC}"
echo -e "${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
echo ""
