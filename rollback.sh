#!/bin/bash

# 流转卡系统回滚脚本
# 用途：将系统回滚到指定的备份版本

set -e

echo "=========================================="
echo "流转卡系统 - 版本回滚"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="/tmp/transfer-card-backup"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用root用户运行此脚本${NC}"
    exit 1
fi

# 显示可用的备份
echo -e "${BLUE}可用的备份版本：${NC}"
echo ""
if [ -d "$BACKUP_DIR" ]; then
    BACKUP_COUNT=$(ls -1 $BACKUP_DIR | grep "^backup_" | wc -l)
    
    if [ $BACKUP_COUNT -eq 0 ]; then
        echo -e "${RED}没有找到可用的备份${NC}"
        exit 1
    fi
    
    # 列出所有备份
    ls -1 $BACKUP_DIR | grep "^backup_" | nl
    echo ""
    
    # 如果指定了备份时间，直接使用
    if [ -n "$1" ]; then
        BACKUP_TIME=$1
    else
        # 让用户选择备份
        read -p "请输入要回滚的备份编号: " BACKUP_NUM
        
        if ! [[ "$BACKUP_NUM" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}无效的编号${NC}"
            exit 1
        fi
        
        BACKUP_TIME=$(ls -1 $BACKUP_DIR | grep "^backup_" | nl | grep "^$BACKUP_NUM" | awk '{print $2}')
        
        if [ -z "$BACKUP_TIME" ]; then
            echo -e "${RED}无效的备份编号${NC}"
            exit 1
        fi
    fi
    
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_TIME"
    
    if [ ! -d "$BACKUP_PATH" ]; then
        echo -e "${RED}备份不存在: $BACKUP_PATH${NC}"
        exit 1
    fi
    
    # 显示备份信息
    echo -e "${YELLOW}=========================================="
    echo -e "${YELLOW}备份信息"
    echo -e "${YELLOW}=========================================="
    echo -e "备份时间: $BACKUP_TIME"
    echo -e "备份路径: $BACKUP_PATH"
    
    if [ -f "$BACKUP_DIR/.version" ]; then
        BACKUP_VERSION=$(cat $BACKUP_DIR/.version)
        echo -e "备份版本: $BACKUP_VERSION"
    fi
    
    if [ -f "$BACKUP_PATH/database_backup_"*.sql ]; then
        echo -e "数据库备份: ✓"
    else
        echo -e "数据库备份: ✗"
    fi
    echo ""
    
    # 确认回滚
    read -p "确认回滚到此版本？(yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        echo -e "${RED}回滚已取消${NC}"
        exit 0
    fi
    
    # 停止服务
    echo ""
    echo -e "${YELLOW}停止服务...${NC}"
    docker-compose down
    
    # 恢复配置文件
    echo -e "${YELLOW}恢复配置文件...${NC}"
    if [ -d "$BACKUP_PATH/backend/config" ]; then
        rm -rf backend/config
        cp -r $BACKUP_PATH/backend/config .
        echo -e "${GREEN}✓ 配置文件已恢复${NC}"
    fi
    
    if [ -f "$BACKUP_PATH/.env" ]; then
        cp $BACKUP_PATH/.env .
        echo -e "${GREEN}✓ 环境变量已恢复${NC}"
    fi
    
    # 恢复版本号
    if [ -f "$BACKUP_DIR/.version" ]; then
        cp $BACKUP_DIR/.version .version
        echo -e "${GREEN}✓ 版本号已恢复${NC}"
    fi
    
    # 恢复数据库（可选）
    if [ -f "$BACKUP_PATH/database_backup_"*.sql ]; then
        read -p "是否恢复数据库？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}恢复数据库...${NC}"
            SQL_FILE=$(ls $BACKUP_PATH/database_backup_*.sql)
            
            # 启动数据库容器
            docker-compose up -d mysql
            sleep 5
            
            # 恢复数据库
            docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD:-root123456} ${MYSQL_DATABASE:-transfer_card} < $SQL_FILE
            
            echo -e "${GREEN}✓ 数据库已恢复${NC}"
        fi
    fi
    
    # 重新构建并启动服务
    echo ""
    echo -e "${YELLOW}重新构建并启动服务...${NC}"
    docker-compose up -d --build
    
    # 等待服务启动
    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 15
    
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
    
    # 回滚完成
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "${GREEN}回滚完成！"
    echo -e "${GREEN}=========================================="
    echo ""
    
    if [ -f "$BACKUP_DIR/.version" ]; then
        echo "当前版本: $(cat $BACKUP_DIR/.version)"
    fi
    echo ""
    echo "查看日志: docker-compose logs -f"
    
else
    echo -e "${RED}备份目录不存在: $BACKUP_DIR${NC}"
    exit 1
fi
