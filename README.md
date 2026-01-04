# 流转卡系统

## 项目简介

流转卡系统是一个基于Web的生产流程管理系统，用于跟踪和管理生产流转卡的创建、审批、流转等全生命周期。

## 技术栈

### 后端
- Python 3.9+
- Flask (Web框架)
- MySQL 8.0 (数据库)
- JWT (身份认证)
- Docker (容器化部署)

### 前端
- HTML5 + CSS3 + JavaScript
- http-server (开发服务器)
- Docker (容器化部署)

### 基础设施
- Docker & Docker Compose
- Git (版本控制)

## 快速开始

### 本地开发环境

#### 前置要求
- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Git

#### 1. 克隆项目
```bash
git clone <你的Git仓库地址>
cd 流转卡
```

#### 2. 配置后端
```bash
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 配置数据库连接
cp config/config.json.example config/config.json
# 编辑 config/config.json，设置数据库连接信息

# 初始化数据库
python init_db.py

# 启动后端服务
python app.py
```

后端将在 http://localhost:5000 启动

#### 3. 配置前端
```bash
cd frontend

# 安装依赖
npm install

# 启动前端服务
npm start
```

前端将在 http://localhost:8080 启动

#### 4. 访问系统
- 前端地址: http://localhost:8080
- 后端API: http://localhost:5000

### Docker部署（推荐）

#### 首次部署

1. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，设置生产环境配置
# 必须修改的配置项：
# - MYSQL_ROOT_PASSWORD: MySQL root密码
# - MYSQL_PASSWORD: 应用数据库密码
# - JWT_SECRET_KEY: JWT密钥（32位以上随机字符串）
```

2. **配置数据库连接**
```bash
# 编辑后端配置
vim backend/config/config.json
```

确保配置与.env文件一致：
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

3. **启动服务**
```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

4. **访问系统**
- 前端地址: http://localhost
- 后端API: http://localhost:5000

#### 使用部署脚本（Linux服务器）

详细部署指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

**快速部署：**
```bash
# 赋予执行权限（Linux）
chmod +x deploy.sh

# 执行部署
sudo ./deploy.sh
```

## 系统功能

### 核心功能
- **流转卡管理**: 创建、编辑、删除流转卡
- **流转审批**: 多级审批流程
- **部门管理**: 组织架构管理
- **用户管理**: 用户权限管理
- **字段配置**: 动态字段配置
- **模板管理**: 流转卡模板管理

### 工作流程
1. 创建流转卡模板
2. 配置审批流程
3. 创建流转卡实例
4. 提交审批
5. 各部门审批流转
6. 完成流转

## OTA更新

系统支持在线更新，无需停机维护。

### 更新步骤

```bash
# 执行OTA更新脚本
sudo ./ota-update.sh
```

更新过程会自动：
- 备份当前版本
- 拉取最新代码
- 更新Docker镜像
- 重启服务
- 执行健康检查
- 如果失败，自动提示回滚

详细更新指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 版本回滚

如果更新后出现问题，可以快速回滚到之前版本。

### 回滚步骤

```bash
# 查看可用备份
sudo ./rollback.sh

# 选择要回滚的版本
sudo ./rollback.sh <备份时间戳>
```

详细回滚指南请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 日常维护

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 备份数据库
```bash
docker-compose exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} transfer_card > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 停止服务
```bash
docker-compose down
```

## 项目结构

```
流转卡/
├── backend/                 # 后端代码
│   ├── app.py              # 主应用入口
│   ├── flow_api.py         # 流转卡API
│   ├── config/             # 配置文件
│   ├── requirements.txt    # Python依赖
│   └── ...
├── frontend/               # 前端代码
│   ├── index.html          # 主页面
│   ├── css/                # 样式文件
│   ├── js/                 # JavaScript文件
│   └── package.json       # 前端依赖
├── database/              # 数据库脚本
│   ├── schema.sql         # 数据库结构
│   └── schema_update.sql  # 数据库更新
├── docker-compose.yml     # Docker编排文件
├── Dockerfile.backend     # 后端Dockerfile
├── Dockerfile.frontend    # 前端Dockerfile
├── deploy.sh             # 部署脚本
├── ota-update.sh         # OTA更新脚本
├── rollback.sh           # 回滚脚本
├── .env.example          # 环境变量模板
├── .version             # 版本号
├── DEPLOYMENT.md         # 部署文档
└── README.md            # 本文件
```

## 配置说明

### 环境变量 (.env)
```env
# MySQL数据库配置
MYSQL_ROOT_PASSWORD=root123456
MYSQL_DATABASE=transfer_card
MYSQL_USER=transfer_user
MYSQL_PASSWORD=transfer123

# JWT密钥
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# 应用环境
FLASK_ENV=production
```

### 后端配置 (backend/config/config.json)
```json
{
  "mysql": {
    "host": "mysql",
    "port": 3306,
    "user": "transfer_user",
    "password": "transfer123",
    "database": "transfer_card"
  }
}
```

## 安全建议

1. **修改默认密码**: 生产环境必须修改所有默认密码
2. **使用HTTPS**: 配置SSL证书，启用HTTPS
3. **配置防火墙**: 只开放必要的端口
4. **定期备份**: 设置数据库自动备份
5. **监控日志**: 定期检查系统日志
6. **及时更新**: 保持系统和依赖包最新

## 常见问题

### 1. 端口被占用
修改docker-compose.yml中的端口映射

### 2. 数据库连接失败
- 检查MySQL容器是否正常启动
- 检查数据库配置是否正确
- 等待MySQL完全启动

### 3. 前端无法访问后端
- 检查后端容器是否正常启动
- 检查API地址配置
- 查看浏览器控制台错误信息

### 4. Docker容器启动失败
```bash
# 查看详细日志
docker-compose logs

# 重新构建镜像
docker-compose build

# 清理并重新启动
docker-compose down
docker-compose up -d
```

更多问题请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

## 文档

- [部署文档](DEPLOYMENT.md) - 详细的部署、更新、回滚指南
- [API文档](API.md) - API接口文档（待完善）
- [用户手册](USER_MANUAL.md) - 用户使用手册（待完善）

## 贡献指南

欢迎提交Issue和Pull Request。

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目地址: https://github.com/your-repo/transfer-card
- 问题反馈: https://github.com/your-repo/transfer-card/issues
- 邮箱: support@example.com

## 版本历史

- **v1.0.0** - 初始版本
  - 基础流转卡管理功能
  - 用户权限管理
  - 部门管理
  - Docker部署支持
  - OTA更新支持

---

**注意**: 首次部署前请务必阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解详细的部署流程和安全配置。
