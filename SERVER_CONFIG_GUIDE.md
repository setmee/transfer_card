# 服务器配置指南

> 本指南说明如何在开发环境和服务器环境配置前后端地址

## 📋 配置说明

### 当前配置状态

系统已经实现了**前后端自动适配**，一般情况下**无需修改配置**。

#### 前端API配置（自动适配）

前端使用动态API地址，会自动根据访问地址配置：

```javascript
// frontend/js/api.js
const API_BASE_URL = (() => {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    // 使用主机的5000端口作为后端API地址
    return `${protocol}//${hostname}:5000/api`;
})();
```

**工作原理：**
- 如果您访问 `http://192.168.1.100`，后端API会自动指向 `http://192.168.1.100:5000/api`
- 如果您访问 `http://localhost`，后端API会自动指向 `http://localhost:5000/api`
- 如果您访问 `http://your-domain.com`，后端API会自动指向 `http://your-domain.com:5000/api`

**优势：**
✅ 开发环境和生产环境无需修改代码
✅ 支持多IP/域名访问
✅ 自动适配HTTP/HTTPS

#### 后端配置

后端主要配置在 `.env` 文件中：

```env
# MySQL数据库配置
MYSQL_ROOT_PASSWORD=root123456
MYSQL_DATABASE=transfer_card
MYSQL_USER=transfer_user
MYSQL_PASSWORD=transfer123

# JWT密钥（生产环境必须修改）
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# 应用环境
FLASK_ENV=production
```

## 🔧 配置步骤

### 场景1：开发环境与服务器IP不同（推荐，无需修改）

**开发环境：**
- 访问：`http://localhost` 或 `http://127.0.0.1`
- 前端自动连接：`http://localhost:5000/api`

**服务器环境：**
- 访问：`http://192.168.1.100`（服务器IP）
- 前端自动连接：`http://192.168.1.100:5000/api`

**无需任何修改！** ✅

### 场景2：开发环境和服务器使用固定域名

如果您的开发环境和服务器使用不同的域名，例如：
- 开发环境：`dev.yourdomain.com`
- 服务器：`prod.yourdomain.com`

同样**无需修改**，系统会自动适配。

### 场景3：需要指定固定的后端地址（不推荐）

**警告：** 除非有特殊需求，否则不建议修改。修改后系统将失去自动适配能力。

如果确实需要指定固定的后端地址，按以下步骤操作：

#### 修改前端API地址

**步骤1：编辑 frontend/js/api.js**

找到这段代码：
```javascript
const API_BASE_URL = (() => {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:5000/api`;
})();
```

**方式A：指定开发环境后端地址**
```javascript
// 开发环境使用固定地址
const API_BASE_URL = 'http://192.168.1.50:5000/api'; // 替换为您的开发环境后端地址
```

**方式B：根据环境变量配置**
```javascript
// 根据环境变量配置
const API_BASE_URL = process.env.API_BASE_URL || (() => {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:5000/api`;
})();
```

**方式C：使用条件判断**
```javascript
// 根据域名或IP判断
const API_BASE_URL = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // 开发环境
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://192.168.1.50:5000/api'; // 开发环境后端地址
    }
    
    // 服务器环境
    if (hostname === '192.168.1.100') {
        return 'http://192.168.1.100:5000/api'; // 服务器后端地址
    }
    
    // 默认：自动适配
    return `${protocol}//${hostname}:5000/api`;
})();
```

#### 修改后端监听地址（如需要）

默认情况下，后端监听所有网络接口（`0.0.0.0`），可以接受来自任何IP的请求。

**如果需要限制访问IP：**

**步骤1：编辑 backend/app.py**

查找 `app.run()` 相关代码：
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**修改为：**
```python
# 只监听本地（仅允许localhost访问）
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

# 或监听特定IP
if __name__ == '__main__':
    app.run(host='192.168.1.50', port=5000, debug=True)
```

**注意：** Windows服务部署时，监听地址的配置在服务注册时指定。

## 🚀 服务器部署配置

### 第一步：复制环境变量模板

在服务器上执行：
```powershell
cd C:\transfer-card
copy .env.example .env
```

### 第二步：修改 .env 文件

```powershell
notepad .env
```

**必须修改的配置项：**

```env
# MySQL数据库配置
MYSQL_ROOT_PASSWORD=你的MySQL root密码
MYSQL_DATABASE=transfer_card
MYSQL_USER=transfer_user
MYSQL_PASSWORD=设置一个强密码

# JWT密钥（必须修改为32位以上的随机字符串）
JWT_SECRET_KEY=生成一个强随机密钥，例如：abc123def456ghi789jkl012mno345pqr

# 应用环境
FLASK_ENV=production
```

**如何生成JWT密钥：**

```powershell
# 方法1：使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法2：使用在线工具
# 访问 https://www.random.org/strings/ 生成32位随机字符串
```

### 第三步：数据库配置

**如果MySQL在同一台服务器：**
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

**如果MySQL在其他服务器：**
```env
MYSQL_HOST=192.168.1.200  # MySQL服务器IP
MYSQL_PORT=3306
```

### 第四步：配置防火墙

确保以下端口开放：

```powershell
# 开放HTTP端口（前端）
New-NetFirewallRule -DisplayName "TransferCard HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# 开放API端口（后端）
New-NetFirewallRule -DisplayName "TransferCard API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

## 🔍 验证配置

### 验证前端配置

在浏览器中访问前端，打开开发者工具（F12），在Console中输入：

```javascript
console.log(window.TransferCardAPI);
```

检查 `API_BASE_URL` 是否正确。

### 验证后端配置

```powershell
# 测试后端是否正常运行
curl http://localhost:5000/api/health

# 或在浏览器访问
# http://localhost:5000/api/health
```

### 验证前后端连接

1. 打开前端页面
2. 尝试登录
3. 如果成功，说明前后端连接正常

## 📊 配置对比表

| 配置项 | 开发环境 | 服务器环境 | 是否需要修改 |
|--------|---------|-----------|------------|
| 前端API地址 | 自动适配 | 自动适配 | ❌ 不需要 |
| 后端监听地址 | 0.0.0.0 | 0.0.0.0 | ❌ 不需要 |
| 数据库密码 | 本地密码 | 服务器密码 | ✅ 需要修改 |
| JWT密钥 | 本地密钥 | 服务器密钥 | ✅ 需要修改 |
| FLASK_ENV | development | production | ✅ 需要修改 |

## ⚠️ 常见问题

### 问题1：前端无法连接后端

**可能原因：**
- 后端服务未启动
- 防火墙阻止了5000端口
- 后端监听地址配置错误

**解决方案：**
```powershell
# 检查后端服务
sc query TransferCardBackend

# 检查端口监听
netstat -ano | findstr :5000

# 检查防火墙
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*TransferCard*"}
```

### 问题2：数据库连接失败

**可能原因：**
- MySQL服务未运行
- 数据库密码错误
- 数据库未创建

**解决方案：**
```powershell
# 测试数据库连接
mysql -u transfer_user -p

# 检查MySQL服务
sc query MySQL80

# 查看后端日志
type logs\backend.log
```

### 问题3：跨域问题（CORS）

如果遇到跨域错误，确保后端已配置CORS。

**检查 backend/app.py 中是否有：**
```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

## 📝 配置检查清单

部署到服务器前，请确认：

- [ ] 已复制 `.env.example` 为 `.env`
- [ ] 已修改数据库密码
- [ ] 已修改JWT密钥（32位以上随机字符串）
- [ ] 已设置 `FLASK_ENV=production`
- [ ] 数据库已创建并导入schema
- [ ] 后端服务已启动
- [ ] 前端服务已启动
- [ ] 防火墙已配置
- [ ] 前端可以访问（http://服务器IP）
- [ ] 后端API可以访问（http://服务器IP:5000/api/health）
- [ ] 前后端可以正常连接（登录测试通过）

## 🎯 推荐配置

### 最简单配置（推荐）

**开发环境：**
- 前端：http://localhost
- 后端：http://localhost:5000/api
- 配置：保持默认，无需修改

**服务器环境：**
- 前端：http://192.168.1.100（服务器IP）
- 后端：http://192.168.1.100:5000/api
- 配置：只需修改 .env 中的密码和JWT密钥

### 域名配置

**生产环境使用域名：**
- 前端：http://app.yourdomain.com
- 后端：http://api.yourdomain.com
- 需要在前端配置中指定API地址
- 配置HTTPS证书

## 📞 获取帮助

- 部署问题：查看 `WIN_DEPLOYMENT.md` 或 `QUICK_START.md`
- GitHub SSH配置：查看 `GITHUB_SSH_SETUP.md`
- 完整文档：查看项目README.md

---

**总结：** 在大多数情况下，您只需要在服务器的 `.env` 文件中修改数据库密码和JWT密钥，前后端地址会自动适配！✅
