# 流转卡系统 - 服务器部署指南

## 目录
- [系统要求](#系统要求)
- [首次部署](#首次部署)
- [OTA更新](#ota更新)
- [版本回滚](#版本回滚)
- [日常维护](#日常维护)
- [常见问题](#常见问题)

---

## 系统要求

### 硬件要求
- CPU: 2核及以上
- 内存: 4GB及以上
- 磁盘: 20GB及以上（用于数据存储）

### 软件要求
- 操作系统: Linux (Ubuntu 20.04+ / CentOS 7+)
- Docker: 20.10+
- Docker Compose: 1.29+
- Git: 2.0+

### 网络要求
- 80端口: 前端访问
- 5000端口: 后端API（可选，仅用于开发调试）
- 3306端口: MySQL数据库（可选，建议内网访问）

---

## 首次部署

### 1. 准备工作

#### 1.1 服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget vim
```

#### 1.2 克隆代码
```bash
# 克隆项目到服务器
git clone <你的Git仓库地址> /opt/transfer-card
cd /opt/transfer-card
```

#### 1.3 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**重要配置项：**
```env
# MySQL数据库配置
MYSQL_ROOT_PASSWORD=你的root密码（建议使用强密码）
MYSQL_DATABASE=transfer_card
MYSQL_USER=transfer_user
MYSQL_PASSWORD=你的数据库密码（建议使用强密码）

# JWT密钥（必须修改为强随机字符串）
JWT_SECRET_KEY=生产环境请使用32位以上随机字符串

# 应用环境
FLASK_ENV=production
```

#### 1.4 配置数据库连接
```bash
# 编辑后端配置
vim backend/config/config.json
```

确保配置与.env文件中的数据库配置一致：
```json
{
  "mysql": {
    "host": "mysql",
    "port": 3306,
    "user": "transfer_user",
    "password": "你的数据库密码",
    "database": "transfer_card"
  }
}
```

### 2. 执行部署

#### 2.1 运行部署脚本
```bash
# 赋予执行权限
chmod +x deploy.sh

# 执行部署
sudo ./deploy.sh
```

部署脚本会自动：
- 检查并安装Docker和Docker Compose
- 停止现有容器
- 拉取最新代码
- 构建Docker镜像
- 启动所有服务
- 执行健康检查

#### 2.2 验证部署
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 检查前端
curl http://localhost

# 检查后端
curl http://localhost:5000/api/health
```

### 3. 初始化系统

#### 3.1 访问系统
- 前端地址: `http://服务器IP`
- 默认管理员账号需要通过API创建

#### 3.2 创建初始管理员
```bash
# 进入后端容器
docker-compose exec backend bash

# 使用Python脚本创建管理员（需要提前准备）
python create_admin.py
```

#### 3.3 首次登录
1. 访问 `http://服务器IP`
2. 使用管理员账号登录
3. 创建部门、用户等基础数据

---

## OTA更新

### 更新流程

#### 1. 准备更新
```bash
# 进入项目目录
cd /opt/transfer-card

# 查看当前版本
cat .version

# 查看Git更新日志
git fetch origin
git log HEAD..origin/main --oneline
```

#### 2. 执行OTA更新
```bash
# 赋予执行权限
chmod +x ota-update.sh

# 执行更新
sudo ./ota-update.sh
```

更新过程会自动：
- 备份当前版本（配置文件、数据库）
- 拉取最新代码
- 更新Docker镜像
- 重启服务
- 执行健康检查
- 如果失败，提示是否回滚

#### 3. 验证更新
```bash
# 查看新版本
cat .version

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 测试功能
curl http://localhost
curl http://localhost:5000/api/health
```

### 更新最佳实践

1. **在非高峰期更新**：选择用户访问量少的时间段
2. **先在测试环境验证**：确保新版本在测试环境运行正常
3. **备份数据库**：更新前选择备份选项
4. **检查更新日志**：了解版本变更内容
5. **准备回滚方案**：如果更新失败，可以快速回滚
6. **通知用户**：提前通知用户系统维护时间

---

## 版本回滚

### 回滚场景
- 更新后发现严重Bug
- 新版本功能不兼容
- 性能问题
- 数据库迁移失败

### 回滚步骤

#### 1. 查看可用备份
```bash
# 赋予执行权限
chmod +x rollback.sh

# 列出所有备份
sudo ./rollback.sh
```

#### 2. 选择回滚版本
```bash
# 方式1：通过编号选择
sudo ./rollback.sh

# 方式2：直接指定备份时间
sudo ./rollback.sh 20260104_143022
```

#### 3. 确认回滚
回滚过程会自动：
- 停止当前服务
- 恢复配置文件
- 恢复数据库（可选）
- 重新构建并启动服务
- 执行健康检查

#### 4. 验证回滚
```bash
# 查看当前版本
cat .version

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

## 日常维护

### 服务管理

#### 查看服务状态
```bash
# 查看所有容器状态
docker-compose ps

# 查看特定容器状态
docker-compose ps backend
docker-compose ps frontend
docker-compose ps mysql
```

#### 查看日志
```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql

# 查看最近100行日志
docker-compose logs --tail=100
```

#### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart frontend
docker-compose restart mysql
```

#### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据（危险操作！）
docker-compose down -v
```

#### 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d backend
docker-compose up -d frontend
```

### 数据库维护

#### 备份数据库
```bash
# 备份到文件
docker-compose exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份到指定目录
mkdir -p /backup/transfer-card
docker-compose exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > /backup/transfer-card/backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 恢复数据库
```bash
# 从文件恢复
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < backup_file.sql

# 恢复时选择数据库
docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} < backup_file.sql
```

#### 查看数据库
```bash
# 进入MySQL容器
docker-compose exec mysql bash

# 登录MySQL
mysql -u root -p

# 执行SQL命令
mysql> use transfer_card;
mysql> show tables;
mysql> select * from users;
```

### 磁盘清理

#### 清理Docker镜像
```bash
# 清理未使用的镜像
docker image prune -a

# 清理所有未使用的资源
docker system prune -a --volumes
```

#### 清理日志
```bash
# 清理Docker日志
docker-compose logs --tail=0

# 限制日志大小（在docker-compose.yml中配置）
```

### 监控服务

#### 健康检查
```bash
# 检查前端
curl -f http://localhost

# 检查后端
curl -f http://localhost:5000/api/health

# 检查数据库
docker-compose exec mysql mysqladmin -u root -p ping
```

#### 资源使用
```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

---

## 常见问题

### 1. 部署失败

**问题：Docker容器启动失败**
```
解决方案：
1. 检查Docker和Docker Compose版本
2. 检查端口占用：netstat -tulpn | grep -E ':(80|5000|3306)'
3. 查看日志：docker-compose logs
4. 检查配置文件：.env 和 backend/config/config.json
```

**问题：数据库连接失败**
```
解决方案：
1. 检查MySQL容器状态：docker-compose ps mysql
2. 查看MySQL日志：docker-compose logs mysql
3. 检查数据库配置是否正确
4. 等待MySQL完全启动：docker-compose exec mysql mysqladmin ping
```

### 2. 更新失败

**问题：Git拉取失败**
```
解决方案：
1. 检查网络连接
2. 检查Git仓库地址
3. 检查Git凭证：git config --list
4. 手动拉取：git pull origin main
```

**问题：服务启动失败**
```
解决方案：
1. 立即回滚：sudo ./rollback.sh
2. 查看日志定位问题：docker-compose logs
3. 检查配置文件是否正确
4. 联系开发团队
```

### 3. 性能问题

**问题：系统响应慢**
```
解决方案：
1. 检查资源使用：docker stats
2. 查看数据库性能：
   - 检查慢查询
   - 优化索引
   - 清理旧数据
3. 检查网络延迟
4. 增加服务器资源
```

### 4. 数据丢失

**问题：数据意外丢失**
```
解决方案：
1. 立即停止服务：docker-compose down
2. 检查数据库备份
3. 恢复最近的备份
4. 检查MySQL数据卷：docker volume ls
5. 联系数据库专家
```

### 5. 端口冲突

**问题：端口被占用**
```
解决方案：
1. 查找占用端口的进程：netstat -tulpn | grep 端口号
2. 停止占用端口的进程
3. 或者修改docker-compose.yml中的端口映射
```

---

## 安全建议

1. **定期更新系统**
   - 及时安装安全补丁
   - 更新Docker版本

2. **强化密码安全**
   - 使用强密码
   - 定期更换密码
   - 不要在代码中硬编码密码

3. **配置防火墙**
   - 只开放必要的端口
   - 使用UFW或iptables

4. **启用HTTPS**
   - 配置SSL证书
   - 使用Nginx反向代理

5. **定期备份**
   - 数据库自动备份
   - 配置文件备份
   - 保留多个备份版本

6. **监控日志**
   - 定期查看系统日志
   - 设置告警机制
   - 异常行为监控

---

## 联系支持

如遇到无法解决的问题，请联系：
- 技术支持邮箱: support@example.com
- 项目地址: https://github.com/your-repo/transfer-card
- 问题反馈: https://github.com/your-repo/transfer-card/issues

---

## 附录

### 版本历史
- v1.0.0 - 初始版本

### 更新日志
- 参见 CHANGELOG.md

### 相关文档
- [系统架构文档](ARCHITECTURE.md)
- [API文档](API.md)
- [用户手册](USER_MANUAL.md)
