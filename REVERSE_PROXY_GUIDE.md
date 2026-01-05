# 反向代理配置指南（Windows Server）

> 使用反向代理解决跨域问题，提供统一的访问入口

## 📋 为什么需要反向代理？

### 当前架构的问题

```
用户浏览器
    │
    ├─ 访问 http://服务器IP:80 (前端)
    │   ↓
    │   前端需要跨域访问 http://服务器IP:5000/api (后端)
    │   ⚠️ 跨域问题
    │
    └─ 访问 http://服务器IP:5000/api (后端API)
        ⚠️ 暴露5000端口（安全风险）
```

### 使用反向代理后的架构

```
用户浏览器
    │
    ├─ 访问 http://服务器IP (统一入口)
    │   ↓
    │   反向代理 (80端口)
    │   ├─ / → 转发到前端
    │   └─ /api → 转发到后端API
    │   ✅ 无跨域问题
    │   ✅ 只需暴露80端口
    │   ✅ 支持HTTPS
```

### 反向代理的优势

✅ **解决跨域问题** - 前后端同源访问  
✅ **统一访问入口** - 只需暴露80/443端口  
✅ **提升安全性** - 隐藏后端端口  
✅ **支持HTTPS** - 配置SSL证书  
✅ **负载均衡** - 可扩展多实例  
✅ **缓存加速** - 静态资源缓存  

## 🚀 方案选择

### 方案一：IIS + ARR（推荐Windows Server）

**适用场景：** Windows Server 2019/2022  
**优势：** Windows原生，无需额外安装，管理方便  
**难度：** 中等  

### 方案二：Nginx for Windows

**适用场景：** Windows Server或Windows 10/11  
**优势：** 轻量级，配置简单，性能优秀  
**难度：** 简单  

### 方案三：Caddy

**适用场景：** 需要快速部署和自动HTTPS  
**优势：** 配置最简单，自动HTTPS证书  
**难度：** 最简单  

## 🔧 方案一：IIS + ARR（推荐）

### 步骤1：安装IIS

在Windows Server上打开"服务器管理器"：

```powershell
# 以管理员身份运行PowerShell
Import-Module ServerManager
Install-WindowsFeature Web-Server -IncludeManagementTools

# 安装完成后，打开IIS管理器
inetmgr
```

或通过图形界面：
1. 打开"服务器管理器"
2. 点击"管理" → "添加角色和功能"
3. 勾选"Web服务器(IIS)"
4. 点击"添加功能"
5. 点击"下一步"直到完成

### 步骤2：安装ARR (Application Request Routing)

#### 2.1 下载Web Platform Installer

访问：https://www.microsoft.com/web/downloads/platform.aspx

下载并安装 Microsoft Web Platform Installer

#### 2.2 安装ARR模块

1. 打开 Web Platform Installer
2. 搜索 "Application Request Routing"
3. 点击"添加" → "安装"
4. 等待安装完成

### 步骤3：配置IIS站点

#### 3.1 添加默认网站

1. 打开 IIS 管理器
2. 右键"网站" → "添加网站"
3. 填写信息：
   - **网站名称：** `TransferCard`
   - **物理路径：** `C:\transfer-card\frontend`
   - **端口：** `80`
   - **IP地址：** `全部未分配`
4. 点击"确定"

#### 3.2 配置反向代理

1. 在IIS管理器中，选中刚创建的站点 "TransferCard"
2. 双击 "URL重写" (URL Rewrite)
3. 点击右侧"添加规则"
4. 选择"空白规则"，点击"确定"

#### 3.3 配置API转发规则

**规则1：API请求转发到后端**

```
名称：Proxy to Backend API
模式：^api/(.*)
重写URL：http://localhost:5000/api/{R:1}
条件：无
服务器变量：
  HTTP_X_FORWARDED_HOST -> {HTTP_HOST}
  HTTP_X_FORWARDED_PROTO -> http
  HTTP_X_REAL_IP -> {REMOTE_ADDR}
```

**详细配置步骤：**

1. **模式：**
   - 匹配URL中的部分：`请求的路径`
   - 模式：`^api/(.*)`
   - 勾选"忽略大小写"

2. **操作：**
   - 操作类型：`重写`
   - 重写URL：`http://localhost:5000/api/{R:1}`
   - 勾选"附加查询字符串"

3. **服务器变量（可选，推荐）：**
   - 点击"服务器变量"
   - 添加：
     - 名称：`HTTP_X_FORWARDED_HOST`，值：`{HTTP_HOST}`
     - 名称：`HTTP_X_FORWARDED_PROTO`，值：`http`
     - 名称：`HTTP_X_REAL_IP`，值：`{REMOTE_ADDR}`

4. 点击"应用"

**规则2：其他请求转发到前端（可选）**

如果需要将根路径也转发到前端（虽然静态文件直接服务即可）：

```
名称：Static Files to Frontend
模式：^(?!api/)(.*)
重写URL：http://localhost:80/{R:1}
```

但实际上，对于静态文件，IIS会直接服务，无需转发。

#### 3.4 启用代理功能

1. 在IIS管理器中，点击服务器节点（最顶层）
2. 双击 "Application Request Routing"
3. 点击右侧 "Server Proxy Settings"
4. 勾选 "Enable proxy"
5. 勾选 "Reverse rewrite host in response headers"
6. 点击 "应用"

### 步骤4：修改前端API配置

由于使用了反向代理，前端需要修改API地址配置。

#### 方式A：修改 frontend/js/api.js（不推荐）

```javascript
// 修改API_BASE_URL为相对路径
const API_BASE_URL = '/api';
```

#### 方式B：保持自动适配（推荐）

由于反向代理将 `/api/*` 转发到后端，保持当前配置即可：

```javascript
// frontend/js/api.js 保持不变
const API_BASE_URL = (() => {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}/api`;  // 注意：去掉 :5000
})();
```

**或者更简单的方式：**

```javascript
const API_BASE_URL = '/api';  // 使用相对路径
```

### 步骤5：配置防火墙

```powershell
# 开放HTTP端口（前端）
New-NetFirewallRule -DisplayName "TransferCard HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# 可选：关闭后端5000端口的外部访问（更安全）
# Remove-NetFirewallRule -DisplayName "TransferCard API"
```

### 步骤6：测试

```powershell
# 测试前端
curl http://localhost/

# 测试API代理
curl http://localhost/api/health

# 或在浏览器中访问
# http://服务器IP/
```

## 🚀 方案二：Nginx for Windows（简单）

### 步骤1：下载Nginx

访问：https://nginx.org/en/download.html

下载 Stable 版本的 Windows 版本（如 `nginx-1.24.0.zip`）

### 步骤2：安装Nginx

```powershell
# 解压到 C:\nginx
cd C:\nginx

# 测试配置
nginx -t

# 启动Nginx
start nginx

# 停止Nginx
nginx -s stop

# 重启Nginx
nginx -s reload
```

### 步骤3：配置反向代理

编辑 `C:\nginx\conf\nginx.conf`：

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    # 前端服务器
    upstream frontend {
        server 127.0.0.1:80;  # 如果前端直接由Nginx服务
    }

    # 后端API服务器
    upstream backend {
        server 127.0.0.1:5000;
    }

    server {
        listen       80;
        server_name  localhost;

        # 字符集
        charset utf-8;

        # 静态文件根目录
        root   C:/transfer-card/frontend;
        index  index.html index.htm;

        # API请求转发到后端
        location /api/ {
            proxy_pass http://backend/api/;
            
            # 代理头设置
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 前端静态文件
        location / {
            try_files $uri $uri/ /index.html;
        }

        # 错误页面
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }
}
```

### 步骤4：安装为Windows服务（可选）

使用 WinSW (Windows Service Wrapper)：

1. 下载 WinSW：https://github.com/winsw/winsw/releases
2. 重命名为 `nginx-service.exe`，放在 `C:\nginx\` 目录
3. 创建 `nginx-service.xml`：

```xml
<service>
  <id>nginx</id>
  <name>Nginx Web Server</name>
  <description>Nginx Reverse Proxy for Transfer Card</description>
  <executable>C:\nginx\nginx.exe</executable>
  <startmode>Automatic</startmode>
  <stopexecutable>C:\nginx\nginx.exe</stopexecutable>
  <stopargument>-s stop</stopargument>
  <logpath>C:\nginx\logs</logpath>
</service>
```

4. 安装服务：
```powershell
cd C:\nginx
nginx-service.exe install
nginx-service.exe start
```

### 步骤5：修改前端配置

```javascript
// frontend/js/api.js
const API_BASE_URL = '/api';  // 使用相对路径
```

### 步骤6：测试

```powershell
# 测试Nginx
curl http://localhost/

# 测试API代理
curl http://localhost/api/health
```

## 🚀 方案三：Caddy（最简单）

### 步骤1：下载Caddy

访问：https://caddyserver.com/download

下载 Windows 版本（x64）

### 步骤2：安装Caddy

```powershell
# 解压到 C:\caddy
cd C:\caddy

# 运行Caddy
caddy run
```

### 步骤3：配置Caddyfile

创建 `C:\caddy\Caddyfile`：

```caddyfile
:80 {
    # 前端静态文件
    root * C:/transfer-card/frontend

    # API请求转发到后端
    reverse_proxy /api/* localhost:5000

    # 前端路由支持
    try_files {path} /index.html
}
```

### 步骤4：安装为Windows服务

```powershell
# 使用 sc 命令安装服务
sc create Caddy binPath= "C:\caddy\caddy.exe run --config C:\caddy\Caddyfile" start= auto
sc start Caddy
```

或使用 WinSW（参考Nginx方案）

### 步骤5：修改前端配置

```javascript
// frontend/js/api.js
const API_BASE_URL = '/api';
```

### 步骤6：测试

```powershell
# 测试Caddy
curl http://localhost/

# 测试API代理
curl http://localhost/api/health
```

## 🔒 配置HTTPS（可选但推荐）

### 使用Let's Encrypt免费证书

#### Caddy自动HTTPS（最简单）

Caddyfile：
```caddyfile
your-domain.com {
    root * C:/transfer-card/frontend
    reverse_proxy /api/* localhost:5000
    try_files {path} /index.html
}
```

Caddy会自动申请和续期SSL证书！

#### IIS + Let's Encrypt

使用 "Win-ACME" 工具：
1. 下载：https://www.win-acme.com/
2. 运行工具，选择创建新证书
3. 选择IIS站点
4. 自动申请并安装证书
5. 设置自动续期

#### Nginx + Let's Encrypt

使用 Certbot：
1. 下载Certbot：https://certbot.eff.org/
2. 运行命令申请证书
3. 配置nginx使用证书

## 📊 方案对比

| 特性 | IIS + ARR | Nginx | Caddy |
|------|-----------|-------|-------|
| 安装难度 | 中等 | 简单 | 最简单 |
| Windows集成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 配置复杂度 | 中等 | 简单 | 最简单 |
| 性能 | 良好 | 优秀 | 良好 |
| 自动HTTPS | 需要工具 | 需要工具 | 内置 |
| 管理界面 | 有 | 无 | 无 |
| 推荐场景 | Windows Server企业 | 技术人员 | 快速部署 |

## 🔧 配置检查清单

### 反向代理配置完成后，请确认：

- [ ] 反向代理服务已安装
- [ ] 反向代理服务正在运行
- [ ] 前端可以通过 http://服务器IP/ 访问
- [ ] API可以通过 http://服务器IP/api/ 访问
- [ ] 前端可以正常登录（验证跨域已解决）
- [ ] 后端5000端口已从外部防火墙关闭
- [ ] 日志正常，无错误

### 前端配置确认：

- [ ] API_BASE_URL 已修改为 `/api` 或相对路径
- [ ] 可以正常调用后端API
- [ ] 无跨域错误

### 安全配置确认：

- [ ] 后端5000端口不对外开放
- [ ] 已配置HTTPS（生产环境推荐）
- [ ] 已配置访问日志
- [ ] 已配置速率限制（可选）

## ⚠️ 常见问题

### 问题1：502 Bad Gateway

**可能原因：** 后端服务未启动或端口错误

**解决方案：**
```powershell
# 检查后端服务
sc query TransferCardBackend

# 检查端口
netstat -ano | findstr :5000

# 测试后端
curl http://localhost:5000/api/health
```

### 问题2：404 Not Found

**可能原因：** 路径配置错误

**解决方案：**
- 检查反向代理配置中的路径模式
- 确认前端文件路径正确
- 查看错误日志

### 问题3：跨域错误仍然存在

**可能原因：** 前端API配置未更新

**解决方案：**
```javascript
// 确保使用相对路径
const API_BASE_URL = '/api';
```

### 问题4：静态文件404

**可能原因：** 静态文件路径配置错误

**解决方案：**
- 检查反向代理的root路径
- 确认前端文件存在于指定目录
- 检查文件权限

## 🎯 推荐配置

### Windows Server 2019/2022（生产环境）

**推荐方案：IIS + ARR**
- 原生支持，管理方便
- 与Windows生态集成好
- 适合企业环境

### 快速部署/测试环境

**推荐方案：Caddy**
- 配置最简单
- 自动HTTPS
- 快速上手

### 技术人员/开发者

**推荐方案：Nginx**
- 轻量级
- 配置灵活
- 社区活跃

## 📞 获取帮助

- IIS文档：https://docs.microsoft.com/en-us/iis/
- Nginx文档：https://nginx.org/en/docs/
- Caddy文档：https://caddyserver.com/docs/
- 项目部署文档：`WIN_DEPLOYMENT.md`
- 服务器配置指南：`SERVER_CONFIG_GUIDE.md`

---

**使用反向代理后，前后端将统一通过80端口访问，彻底解决跨域问题！** 🚀
