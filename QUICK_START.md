# 流转卡系统 - Windows Server 快速部署指南

> 本指南帮助您在10分钟内完成Windows Server 2022上的部署

## 前置准备

### 1. 系统要求检查
```powershell
# 检查Windows版本
systeminfo | findstr /B /C:"OS Name"

# 应显示: Windows Server 2019 或 Windows Server 2022
```

### 2. 安装必要软件

#### 安装Python 3.8+
1. 访问 https://www.python.org/downloads/
2. 下载并安装Python 3.8或更高版本
3. **重要**: 安装时勾选 "Add Python to PATH"
4. 验证: `python --version`

#### 安装Node.js 14.0+
1. 访问 https://nodejs.org/
2. 下载LTS版本并安装
3. 验证: `node --version` 和 `npm --version`

#### 安装MySQL 8.0+
1. 访问 https://dev.mysql.com/downloads/mysql/
2. 下载MySQL Installer for Windows
3. 安装MySQL Server，设置root密码（请记住！）
4. 验证: `mysql --version`

#### 安装Git
1. 访问 https://git-scm.com/download/win
2. 下载并安装
3. 验证: `git --version`

## 快速部署（5分钟）

### 步骤1: 准备项目（2分钟）

```powershell
# 创建项目目录
mkdir C:\transfer-card
cd C:\transfer-card

# 克隆代码（使用HTTPS）
git clone https://github.com/你的用户名/study.git .

# 或者使用SSH（推荐）
git clone git@github.com:你的用户名/study.git .
```

### 步骤2: 配置环境变量（1分钟）

```powershell
# 复制环境变量模板
copy .env.example .env

# 编辑配置文件
notepad .env
```

**必须修改的配置项：**
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_ROOT_PASSWORD=你的MySQL root密码
MYSQL_DATABASE=transfer_card
MYSQL_USER=transfer_user
MYSQL_PASSWORD=设置一个强密码
JWT_SECRET_KEY=设置一个32位以上的随机字符串
FLASK_ENV=production
```

### 步骤3: 配置数据库（1分钟）

```powershell
# 登录MySQL
mysql -u root -p

# 执行以下SQL命令
```

```sql
CREATE DATABASE transfer_card CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'transfer_user'@'localhost' IDENTIFIED BY '你在.env中设置的密码';
GRANT ALL PRIVILEGES ON transfer_card.* TO 'transfer_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```powershell
# 导入数据库结构
mysql -u transfer_user -p transfer_card < database\schema.sql
```

### 步骤4: 安装依赖（1分钟）

```powershell
# 后端依赖
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
deactivate
cd ..

# 前端依赖
cd frontend
npm install
cd ..
```

### 步骤5: 注册Windows服务（2分钟）

#### 5.1 安装NSSM
1. 访问 https://nssm.cc/download
2. 下载并解压到 `C:\nssm`

#### 5.2 注册后端服务

```powershell
# 注册服务
C:\nssm\nssm install TransferCardBackend

# 配置服务
C:\nssm\nssm set TransferCardBackend Application C:\transfer-card\backend\venv\Scripts\python.exe
C:\nssm\nssm set TransferCardBackend AppParameters C:\transfer-card\backend\app.py
C:\nssm\nssm set TransferCardBackend AppDirectory C:\transfer-card\backend
C:\nssm\nssm set TransferCardBackend DisplayName "流转卡后端服务"
C:\nssm\nssm set TransferCardBackend Description "流转卡系统后端API服务"
C:\nssm\nssm set TransferCardBackend Start SERVICE_AUTO_START
```

#### 5.3 配置前端（选择一种方式）

**方式A: 使用IIS（推荐生产环境）**
1. 打开"服务器管理器" -> "管理" -> "添加角色和功能"
2. 添加"Web服务器(IIS)"角色
3. 打开IIS管理器
4. 添加网站:
   - 网站名称: TransferCardFrontend
   - 物理路径: C:\transfer-card\frontend
   - 端口: 80

**方式B: 使用Node.js（简单部署）**
```powershell
# 安装http-server
cd frontend
npm install -g http-server

# 注册为服务
C:\nssm\nssm install TransferCardFrontend
C:\nssm\nssm set TransferCardFrontend Application C:\Program Files\nodejs\node.exe
C:\nssm\nssm set TransferCardFrontend AppParameters C:\transfer-card\frontend\node_modules\http-server\bin\http-server C:\transfer-card\frontend -p 80
C:\nssm\nssm set TransferCardFrontend AppDirectory C:\transfer-card\frontend
C:\nssm\nssm set TransferCardFrontend DisplayName "流转卡前端服务"
C:\nssm\nssm set TransferCardFrontend Start SERVICE_AUTO_START
```

### 步骤6: 启动服务（30秒）

```powershell
# 启动服务
net start TransferCardBackend
net start TransferCardFrontend  # 如果使用Node.js方式

# 验证服务
sc query TransferCardBackend
```

### 步骤7: 验证部署（30秒）

```powershell
# 测试后端
curl http://localhost:5000/api/health

# 测试前端
curl http://localhost

# 或在浏览器访问
# http://localhost
# http://localhost:5000/api/health
```

## 常用命令

### 服务管理
```powershell
# 启动服务
manage-services.bat start

# 停止服务
manage-services.bat stop

# 重启服务
manage-services.bat restart

# 查看状态
manage-services.bat status

# 健康检查
manage-services.bat health

# 查看日志
manage-services.bat logs
```

### 更新系统
```powershell
# 远程推送更新（从本地开发环境）
git add .
git commit -m "更新描述"
git push origin main

# 服务器拉取更新（在服务器上执行）
deploy-windows.bat
```

### 备份和恢复
```powershell
# 备份数据
backup-windows.bat

# 回滚版本
rollback-windows.bat
```

## 定时自动更新

### 设置每天凌晨2点自动更新

1. 打开"任务计划程序"
2. 点击"创建基本任务"
3. 名称: `TransferCard Auto Update`
4. 触发器: 每天，凌晨2:00
5. 操作: 启动程序
   - 程序: `C:\transfer-card\deploy-windows.bat`
   - 起始于: `C:\transfer-card`
6. 勾选"打开任务属性对话框"
7. 在"常规"选项卡中:
   - 选择"不管用户是否登录都要运行"
   - 勾选"使用最高权限运行"
8. 保存

## 故障排除

### 问题1: 服务启动失败
```powershell
# 查看服务日志
eventvwr

# 手动测试后端
cd C:\transfer-card\backend
.\venv\Scripts\python.exe app.py
```

### 问题2: 数据库连接失败
```powershell
# 测试数据库连接
mysql -u transfer_user -p transfer_card

# 检查MySQL服务
sc query MySQL80
net start MySQL80
```

### 问题3: 端口被占用
```powershell
# 查看端口占用
netstat -ano | findstr :80
netstat -ano | findstr :5000

# 结束占用进程
taskkill /PID <进程ID> /F
```

### 问题4: Git拉取失败
```powershell
# 检查网络连接
ping github.com

# 配置Git凭证
git config --global credential.helper manager-core

# 或使用SSH密钥
ssh-keygen -t rsa -b 4096
# 将公钥添加到GitHub
```

## 安全建议

1. **修改默认密码**: 更改所有默认密码（数据库、管理员账户）
2. **配置防火墙**: 只开放必要端口（80, 5000）
3. **启用HTTPS**: 配置SSL证书
4. **定期备份**: 设置定时自动备份
5. **定期更新**: 保持系统和依赖最新
6. **监控日志**: 定期检查日志文件

## 部署完成后的检查清单

- [ ] 后端服务运行正常
- [ ] 前端服务运行正常
- [ ] 可以访问 http://localhost
- [ ] 可以访问 http://localhost:5000/api/health
- [ ] 数据库连接正常
- [ ] 已修改所有默认密码
- [ ] 已配置防火墙
- [ ] 已设置定时备份
- [ ] 已测试更新和回滚流程

## 下一步

1. 阅读完整部署文档: `WIN_DEPLOYMENT.md`
2. 配置HTTPS和SSL证书
3. 设置监控和告警
4. 配置域名解析
5. 性能优化

## 获取帮助

- 完整文档: `WIN_DEPLOYMENT.md`
- 常见问题: 查看 `WIN_DEPLOYMENT.md` 的"常见问题"章节
- 项目地址: https://github.com/你的用户名/study

---

**部署完成后，系统将运行在:**
- 前端: http://服务器IP
- 后端API: http://服务器IP:5000
