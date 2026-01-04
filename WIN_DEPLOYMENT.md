# 流转卡系统 - Windows Server 部署指南

## 目录
- [系统要求](#系统要求)
- [首次部署](#首次部署)
- [远程更新](#远程更新)
- [版本回滚](#版本回滚)
- [服务管理](#服务管理)
- [日常维护](#日常维护)
- [常见问题](#常见问题)

---

## 系统要求

### 硬件要求
- CPU: 2核及以上
- 内存: 4GB及以上
- 磁盘: 20GB及以上（用于数据存储）

### 软件要求
- 操作系统: Windows Server 2019/2022
- Python: 3.8+
- Node.js: 14.0+
- MySQL: 8.0+
- Git: 2.0+
- IIS (可选，用于前端部署)

### 网络要求
- 80端口: 前端访问
- 5000端口: 后端API
- 3306端口: MySQL数据库（建议内网访问）

---

## 首次部署

### 1. 准备工作

#### 1.1 安装必要软件

##### 安装Python
```powershell
# 下载并安装Python 3.8+
# 访问: https://www.python.org/downloads/
# 安装时勾选 "Add Python to PATH"

# 验证安装
python --version
pip --version
```

##### 安装Node.js
```powershell
# 下载并安装Node.js 14.0+
# 访问: https://nodejs.org/

# 验证安装
node --version
npm --version
```

##### 安装MySQL
```powershell
# 下载并安装MySQL 8.0+
# 访问: https://dev.mysql.com/downloads/mysql/
# 安装时设置root密码

# 验证安装
mysql --version
```

##### 安装Git
```powershell
# 下载并安装Git
# 访问: https://git-scm.com/download/win

# 验证安装
git --version
```

#### 1.2 创建项目目录
```powershell
# 创建项目目录
mkdir C:\transfer-card
cd C:\transfer-card
```

#### 1.3 克隆代码
```powershell
# 克隆项目（使用HTTPS）
git clone https://github.com/你的用户名/study.git .

# 或者使用SSH（需要配置SSH密钥）
git clone git@github.com:你的用户名/study.git .
```

#### 1.4 配置环境变量
```powershell
# 复制环境变量模板
copy .env.example .env

# 编辑配置文件
notepad .env
```

**重要配置项：**
```env
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_ROOT_PASSWORD=你的root密码（建议使用强密码）
MYSQL_DATABASE=transfer_card
MYSQL_USER=transfer_user
MYSQL_PASSWORD=你的数据库密码（建议使用强密码）

# JWT密钥（必须修改为强随机字符串）
JWT_SECRET_KEY=生产环境请使用32位以上随机字符串

# 应用环境
FLASK_ENV=production
```

#### 1.5 配置后端数据库连接
```powershell
# 编辑后端配置
notepad backend\config\config.json
```

确保配置与.env文件中的数据库配置一致：
```json
{
  "mysql": {
    "host": "localhost",
    "port": 3306,
    "user": "transfer_user",
    "password": "你的数据库密码",
    "database": "transfer_card"
  }
}
```

### 2. 配置数据库

#### 2.1 创建数据库和用户
```powershell
# 登录MySQL
mysql -u root -p

# 执行以下SQL命令
```

```sql
-- 创建数据库
CREATE DATABASE transfer_card CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'transfer_user'@'localhost' IDENTIFIED BY '你的数据库密码';

-- 授予权限
GRANT ALL PRIVILEGES ON transfer_card.* TO 'transfer_user'@'localhost';
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

#### 2.2 初始化数据库结构
```powershell
# 导入数据库结构
mysql -u transfer_user -p transfer_card < database\schema.sql
```

### 3. 安装依赖

#### 3.1 安装后端依赖
```powershell
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 返回项目根目录
cd ..
```

#### 3.2 安装前端依赖
```powershell
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 返回项目根目录
cd ..
```

### 4. 配置Windows服务

#### 4.1 安装NSSM（用于管理Windows服务）
```powershell
# 下载NSSM
# 访问: https://nssm.cc/download
# 解压到 C:\nssm

# 添加到系统PATH（可选）
setx PATH "%PATH%;C:\nssm" /M
```

#### 4.2 注册后端服务
```powershell
# 使用NSSM创建后端服务
C:\nssm\nssm install TransferCardBackend

# 配置服务参数
C:\nssm\nssm set TransferCardBackend Application C:\transfer-card\backend\venv\Scripts\python.exe
C:\nssm\nssm set TransferCardBackend AppParameters C:\transfer-card\backend\app.py
C:\nssm\nssm set TransferCardBackend AppDirectory C:\transfer-card\backend
C:\nssm\nssm set TransferCardBackend DisplayName "流转卡后端服务"
C:\nssm\nssm set TransferCardBackend Description "流转卡系统后端API服务"
C:\nssm\nssm set TransferCardBackend Start SERVICE_AUTO_START

# 设置环境变量（可选，或使用.env文件）
C:\nssm\nssm set TransferCardBackend AppEnvironmentExtra "FLASK_ENV=production"
```

#### 4.3 配置前端（使用IIS或直接运行）

##### 方式1: 使用IIS（推荐生产环境）
```powershell
# 安装IIS
# 控制面板 -> 程序 -> 启用或关闭Windows功能
# 启用以下功能：
# - Internet Information Services
# - 万维网服务
# - 应用程序开发功能 -> CGI

# 配置IIS站点
# 1. 打开IIS管理器
# 2. 创建新站点，指向 C:\transfer-card\frontend
# 3. 配置端口80
# 4. 启用静态文件支持
```

##### 方式2: 使用Node.js直接运行（开发/简单部署）
```powershell
# 使用NSSM创建前端服务
C:\nssm\nssm install TransferCardFrontend

# 配置服务参数
C:\nssm\nssm set TransferCardFrontend Application C:\Program Files\nodejs\node.exe
C:\nssm\nssm set TransferCardFrontend AppParameters C:\transfer-card\frontend\node_modules\http-server\bin\http-server C:\transfer-card\frontend -p 80
C:\nssm\nssm set TransferCardFrontend AppDirectory C:\transfer-card\frontend
C:\nssm\nssm set TransferCardFrontend DisplayName "流转卡前端服务"
C:\nssm\nssm set TransferCardFrontend Description "流转卡系统前端服务"
C:\nssm\nssm set TransferCardFrontend Start SERVICE_AUTO_START
```

### 5. 启动服务

#### 5.1 启动服务
```powershell
# 启动后端服务
net start TransferCardBackend

# 启动前端服务（如果使用Node.js方式）
net start TransferCardFrontend

# 或者使用NSSM
C:\nssm\nssm start TransferCardBackend
C:\nssm\nssm start TransferCardFrontend
```

#### 5.2 验证部署
```powershell
# 检查服务状态
sc query TransferCardBackend
sc query TransferCardFrontend

# 测试后端API
curl http://localhost:5000/api/health

# 测试前端
curl http://localhost
```

### 6. 初始化系统

#### 6.1 访问系统
- 前端地址: `http://服务器IP`
- 后端API: `http://服务器IP:5000`

#### 6.2 创建初始管理员
```powershell
# 进入后端目录
cd C:\transfer-card\backend

# 激活虚拟环境
.\venv\Scripts\activate

# 使用Python脚本创建管理员（需要提前准备）
python create_admin.py

# 或者通过API创建
curl -X POST http://localhost:5000/api/admin/create -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"your_password\"}"
```

#### 6.3 首次登录
1. 访问 `http://服务器IP`
2. 使用管理员账号登录
3. 创建部门、用户等基础数据

---

## 远程更新

### 更新机制

系统使用Git进行版本控制和远程更新：
1. 本地开发环境提交代码到Git仓库
2. 服务器拉取最新代码
3. 自动执行更新脚本
4. 重启服务

### 配置Git远程仓库

#### 1. 配置Git凭证（HTTPS方式）
```powershell
# 配置Git凭证管理器
git config --global credential.helper manager-core

# 第一次pull时输入用户名和密码，会自动保存
```

#### 2. 配置SSH密钥（推荐）
```powershell
# 生成SSH密钥
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 查看公钥
cat C:\Users\你的用户名\.ssh\id_rsa.pub

# 将公钥添加到GitHub/GitLab账户设置中

# 测试连接
ssh -T git@github.com
```

### 自动化更新脚本

#### 1. 创建更新日志目录
```powershell
mkdir C:\transfer-card\logs
```

#### 2. 执行更新（使用deploy-windows.bat）
```powershell
cd C:\transfer-card
deploy-windows.bat
```

更新脚本会自动：
- 停止服务
- 备份当前版本（配置文件、数据库）
- 拉取最新代码
- 更新依赖（如有变化）
- 重启服务
- 执行健康检查
- 记录更新日志

#### 3. 验证更新
```powershell
# 查看当前版本
type .version

# 查看更新日志
type logs\update_YYYYMMDD_HHMMSS.log

# 测试功能
curl http://localhost
curl http://localhost:5000/api/health
```

### 定时自动更新

#### 使用Windows任务计划程序
```powershell
# 打开任务计划程序
# 任务计划程序 -> 创建任务

# 常规选项卡：
# - 名称: TransferCard Auto Update
# - 选择: 不管用户是否登录都要运行
# - 勾选: 使用最高权限运行

# 触发器选项卡：
# - 新建触发器 -> 每天凌晨2点
# - 或: 每周日凌晨3点

# 操作选项卡：
# - 新建操作
# - 程序/脚本: C:\transfer-card\deploy-windows.bat
# - 起始于: C:\transfer-card

# 条件选项卡：
# - 勾选: 只有在计算机使用交流电源时才启动
# - 勾选: 如果计算机使用电池则停止

# 设置选项卡：
# - 如果任务失败，每隔5分钟重新启动
# - 最多重试次数: 3
```

### 手动推送更新

#### 在本地开发环境
```bash
# 1. 修改代码
git add .
git commit -m "更新描述"
git push origin main
```

#### 在服务器
```powershell
# 2. 拉取更新
cd C:\transfer-card
deploy-windows.bat
```

---

## 版本回滚

### 回滚场景
- 更新后发现严重Bug
- 新版本功能不兼容
- 性能问题
- 数据库迁移失败

### 使用Git回滚

#### 1. 查看版本历史
```powershell
cd C:\transfer-card
git log --oneline --graph --all
```

#### 2. 回滚到指定版本
```powershell
# 停止服务
net stop TransferCardBackend
net stop TransferCardFrontend

# 回滚到上一个版本（保留本地修改）
git reset --hard HEAD~1

# 或回滚到指定版本
git reset --hard <commit-hash>

# 重新启动服务
net start TransferCardBackend
net start TransferCardFrontend
```

#### 3. 查看回滚结果
```powershell
# 查看当前版本
git log --oneline -1

# 查看服务状态
sc query TransferCardBackend
```

### 数据库回滚

#### 1. 查看备份
```powershell
# 列出所有数据库备份
dir C:\transfer-card\backups\database
```

#### 2. 恢复数据库
```powershell
# 停止后端服务
net stop TransferCardBackend

# 恢复指定备份
mysql -u transfer_user -p transfer_card < C:\transfer-card\backups\database\backup_YYYYMMDD_HHMMSS.sql

# 重启服务
net start TransferCardBackend
```

### 完整回滚（使用rollback-windows.bat）
```powershell
cd C:\transfer-card
rollback-windows.bat
```

---

## 服务管理

### 查看服务状态
```powershell
# 查看所有相关服务
sc query | findstr "TransferCard"

# 查看特定服务
sc query TransferCardBackend
sc query TransferCardFrontend
```

### 启动服务
```powershell
# 启动后端
net start TransferCardBackend

# 启动前端
net start TransferCardFrontend

# 或使用NSSM
C:\nssm\nssm start TransferCardBackend
C:\nssm\nssm start TransferCardFrontend
```

### 停止服务
```powershell
# 停止后端
net stop TransferCardBackend

# 停止前端
net stop TransferCardFrontend

# 或使用NSSM
C:\nssm\nssm stop TransferCardBackend
C:\nssm\nssm stop TransferCardFrontend
```

### 重启服务
```powershell
# 重启后端
net stop TransferCardBackend
net start TransferCardBackend

# 重启前端
net stop TransferCardFrontend
net start TransferCardFrontend
```

### 查看服务日志
```powershell
# Windows事件查看器
eventvwr

# 或直接查看应用日志
type C:\transfer-card\logs\backend.log
type C:\transfer-card\logs\frontend.log
```

### 卸载服务
```powershell
# 停止服务
net stop TransferCardBackend
net stop TransferCardFrontend

# 删除服务
C:\nssm\nssm remove TransferCardBackend confirm
C:\nssm\nssm remove TransferCardFrontend confirm
```

---

## 日常维护

### 数据库维护

#### 备份数据库
```powershell
# 创建备份目录
mkdir C:\transfer-card\backups\database -ErrorAction SilentlyContinue

# 备份数据库（包含时间戳）
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
mysqldump -u transfer_user -p transfer_card > C:\transfer-card\backups\database\backup_$timestamp.sql
```

#### 定期自动备份
```powershell
# 创建备份脚本backup-db.ps1
# 添加到任务计划程序，每天执行一次

# 备份保留策略：保留最近30天的备份
Get-ChildItem C:\transfer-card\backups\database | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
    Remove-Item
```

#### 恢复数据库
```powershell
# 从备份恢复
mysql -u transfer_user -p transfer_card < C:\transfer-card\backups\database\backup_YYYYMMDD_HHMMSS.sql
```

#### 优化数据库
```powershell
# 登录MySQL
mysql -u root -p

# 执行优化
```

```sql
-- 分析表
ANALYZE TABLE cards, users, departments, flow_logs;

-- 优化表
OPTIMIZE TABLE cards, users, departments, flow_logs;

-- 检查表
CHECK TABLE cards, users, departments, flow_logs;
```

### 日志管理

#### 查看日志
```powershell
# 查看后端日志
Get-Content C:\transfer-card\logs\backend.log -Tail 50 -Wait

# 查看前端日志
Get-Content C:\transfer-card\logs\frontend.log -Tail 50 -Wait

# 查看更新日志
Get-Content C:\transfer-card\logs\update_*.log -Tail 100
```

#### 清理日志
```powershell
# 删除30天前的日志
Get-ChildItem C:\transfer-card\logs | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
    Remove-Item
```

### 磁盘空间管理

#### 查看磁盘使用
```powershell
# 查看所有磁盘
Get-PSDrive -PSProvider FileSystem

# 查看目录大小
Get-ChildItem C:\transfer-card -Recurse | 
    Measure-Object -Property Length -Sum | 
    Select-Object Count, @{Name='Size(MB)';Expression={[math]::Round($_.Sum / 1MB, 2)}}
```

#### 清理旧备份
```powershell
# 只保留最近30天的备份
Get-ChildItem C:\transfer-card\backups -Recurse | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
    Remove-Item -Recurse
```

### 监控服务

#### 健康检查
```powershell
# 检查后端API
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 5
    Write-Host "后端服务: 正常" -ForegroundColor Green
} catch {
    Write-Host "后端服务: 异常" -ForegroundColor Red
}

# 检查前端
try {
    $response = Invoke-WebRequest -Uri "http://localhost" -TimeoutSec 5
    Write-Host "前端服务: 正常" -ForegroundColor Green
} catch {
    Write-Host "前端服务: 异常" -ForegroundColor Red
}
```

#### 监控资源使用
```powershell
# 查看进程资源占用
Get-Process | Where-Object {$_.Name -like "python*"} | 
    Format-Table Id, Name, CPU, WorkingSet

Get-Process | Where-Object {$_.Name -like "node*"} | 
    Format-Table Id, Name, CPU, WorkingSet
```

---

## 常见问题

### 1. 服务启动失败

**问题：后端服务启动失败**
```
解决方案：
1. 检查Python环境
2. 查看事件查看器日志：eventvwr
3. 手动运行测试：C:\transfer-card\backend\venv\Scripts\python.exe C:\transfer-card\backend\app.py
4. 检查配置文件：.env 和 backend\config\config.json
5. 检查数据库连接
```

**问题：前端服务启动失败**
```
解决方案：
1. 检查Node.js环境
2. 查看事件查看器日志
3. 检查端口占用：netstat -ano | findstr :80
4. 如果使用IIS，检查IIS配置
```

### 2. 数据库连接失败

**问题：无法连接数据库**
```
解决方案：
1. 检查MySQL服务状态：sc query MySQL
2. 启动MySQL服务：net start MySQL
3. 测试连接：mysql -u transfer_user -p
4. 检查配置文件中的数据库连接信息
5. 检查防火墙设置
```

### 3. 端口被占用

**问题：端口80或5000被占用**
```powershell
# 查找占用端口的进程
netstat -ano | findstr :80
netstat -ano | findstr :5000

# 结束占用端口的进程（根据PID）
taskkill /PID <进程ID> /F

# 或修改配置文件使用其他端口
```

### 4. 更新失败

**问题：Git拉取失败**
```
解决方案：
1. 检查网络连接
2. 检查Git凭证：git config --list
3. 手动测试：git pull origin main
4. 检查SSH密钥配置（如果使用SSH）
```

**问题：依赖安装失败**
```
解决方案：
1. 检查网络连接
2. 更新pip：python -m pip install --upgrade pip
3. 使用国内镜像：pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
4. 更新npm：npm install -g npm
5. 清理npm缓存：npm cache clean --force
```

### 5. 权限问题

**问题：权限不足**
```
解决方案：
1. 以管理员身份运行PowerShell
2. 检查文件夹权限
3. 给服务账户分配适当的权限
```

### 6. 性能问题

**问题：系统响应慢**
```
解决方案：
1. 检查CPU和内存使用
2. 优化数据库索引
3. 清理旧数据
4. 增加服务器资源
5. 检查慢查询日志
```

---

## 安全建议

1. **定期更新系统**
   - 安装Windows更新
   - 更新Python和Node.js版本
   - 更新MySQL版本

2. **强化密码安全**
   - 使用强密码
   - 定期更换密码
   - 不要在代码中硬编码密码

3. **配置防火墙**
   - 只开放必要的端口
   - 使用Windows防火墙高级安全
   - 限制远程访问IP

4. **启用HTTPS**
   - 配置SSL证书
   - 使用IIS配置HTTPS
   - 强制使用HTTPS

5. **定期备份**
   - 数据库自动备份
   - 配置文件备份
   - 保留多个备份版本

6. **监控日志**
   - 定期查看系统日志
   - 设置日志告警
   - 异常行为监控

7. **限制访问**
   - 使用强密码策略
   - 定期审计用户权限
   - 禁用不必要的服务

---

## 附录

### 快捷命令

```powershell
# 启动所有服务
Start-Service TransferCardBackend, TransferCardFrontend

# 停止所有服务
Stop-Service TransferCardBackend, TransferCardFrontend

# 重启所有服务
Restart-Service TransferCardBackend, TransferCardFrontend

# 查看所有服务状态
Get-Service TransferCard*

# 备份数据库
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
mysqldump -u transfer_user -p transfer_card > C:\transfer-card\backups\database\backup_$timestamp.sql

# 更新系统
cd C:\transfer-card
deploy-windows.bat
```

### 联系支持

如遇到无法解决的问题，请联系：
- 技术支持邮箱: support@example.com
- 项目地址: https://github.com/your-repo/transfer-card
- 问题反馈: https://github.com/your-repo/transfer-card/issues

---

## 版本历史

- v1.0.0 - 初始版本（Windows Server支持）
