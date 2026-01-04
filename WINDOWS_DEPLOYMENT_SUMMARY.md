# Windows Server 部署方案总结

## 📋 文档说明

本文档总结了流转卡系统在Windows Server 2022上的完整部署方案，包括所有脚本和配置。

## 📁 文件清单

### 核心文档
| 文件名 | 说明 | 用途 |
|--------|------|------|
| `WIN_DEPLOYMENT.md` | 完整部署文档 | 详细的部署指南，包含所有细节 |
| `QUICK_START.md` | 快速部署指南 | 10分钟快速部署步骤 |
| `WINDOWS_DEPLOYMENT_SUMMARY.md` | 本文档 | 部署方案总结 |

### 自动化脚本
| 脚本名 | 功能 | 使用场景 |
|--------|------|----------|
| `deploy-windows.bat` | 部署/更新系统 | 首次部署或远程推送更新 |
| `rollback-windows.bat` | 版本回滚 | 回滚到指定版本 |
| `manage-services.bat` | 服务管理 | 启动/停止/重启/查看状态 |
| `backup-windows.bat` | 数据备份 | 备份配置和数据库 |

## 🚀 快速开始

### 最快部署路径（10分钟）
```
1. 安装软件（Python、Node.js、MySQL、Git）→ 3分钟
2. 克隆代码 → 1分钟
3. 配置环境变量和数据库 → 2分钟
4. 安装依赖 → 1分钟
5. 注册Windows服务 → 2分钟
6. 启动服务 → 1分钟
```

详细步骤请查看: `QUICK_START.md`

## 🔧 主要功能

### 1. 自动化部署
```powershell
# 部署或更新系统
deploy-windows.bat
```

**功能包括：**
- 停止服务
- 备份当前版本（配置+数据库）
- 拉取最新代码
- 恢复配置文件
- 更新依赖
- 启动服务
- 健康检查
- 清理旧备份

### 2. 版本回滚
```powershell
# 回滚到上一个版本
rollback-windows.bat

# 选择回滚选项：
# 1. 回滚到上一个Git版本（保留数据）
# 2. 恢复指定的配置文件备份
# 3. 恢复指定的数据库备份
# 4. 完整回滚（代码+配置+数据库）
# 5. 列出Git历史并选择版本
```

### 3. 服务管理
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

### 4. 数据备份
```powershell
# 备份配置和数据库
backup-windows.bat
```

**备份内容包括：**
- 配置文件（.env, config.json）
- 数据库完整备份
- 自动清理30天前的旧备份

## 🔄 远程更新流程

### 从本地开发环境推送更新
```bash
# 1. 修改代码
# 2. 提交到Git仓库
git add .
git commit -m "更新描述"
git push origin main
```

### 在服务器上拉取更新
```powershell
# 3. 执行更新脚本
cd C:\transfer-card
deploy-windows.bat
```

**自动完成：**
- 停止服务
- 备份当前版本
- 拉取最新代码
- 更新依赖（如有变化）
- 启动服务
- 健康检查

## ⏰ 定时自动更新

### 设置每天凌晨2点自动更新
1. 打开"任务计划程序"
2. 创建基本任务: `TransferCard Auto Update`
3. 触发器: 每天凌晨2:00
4. 操作: 运行 `C:\transfer-card\deploy-windows.bat`
5. 设置: 不管用户是否登录都要运行，使用最高权限

详细说明请查看: `WIN_DEPLOYMENT.md` 或 `QUICK_START.md`

## 📊 目录结构

```
C:\transfer-card\
├── backend/              # 后端代码
│   ├── venv/            # Python虚拟环境
│   ├── app.py           # 应用入口
│   └── config/          # 配置文件
├── frontend/            # 前端代码
│   ├── node_modules/    # Node依赖
│   └── ...
├── database/           # 数据库文件
│   └── schema.sql      # 数据库结构
├── logs/              # 日志目录
│   ├── update_*.log    # 更新日志
│   ├── rollback_*.log  # 回滚日志
│   ├── backend.log     # 后端日志
│   └── frontend.log    # 前端日志
├── backups/           # 备份目录
│   ├── config/        # 配置备份
│   │   └── config_YYYYMMDD_HHMMSS/
│   └── database/      # 数据库备份
│       └── backup_YYYYMMDD_HHMMSS.sql
├── .env              # 环境变量配置
├── deploy-windows.bat      # 部署/更新脚本
├── rollback-windows.bat    # 回滚脚本
├── manage-services.bat     # 服务管理脚本
├── backup-windows.bat     # 备份脚本
├── WIN_DEPLOYMENT.md      # 完整部署文档
└── QUICK_START.md         # 快速部署指南
```

## 🔐 安全建议

1. **修改默认密码**
   - 数据库root密码
   - 数据库用户密码
   - JWT_SECRET_KEY（必须修改为强随机字符串）

2. **配置防火墙**
   - 只开放必要端口（80, 5000）
   - 限制远程访问IP

3. **启用HTTPS**
   - 配置SSL证书
   - 使用IIS配置HTTPS

4. **定期备份**
   - 设置定时自动备份
   - 保留多个备份版本

5. **监控日志**
   - 定期检查日志文件
   - 设置日志告警

6. **定期更新**
   - Windows更新
   - Python和Node.js版本更新
   - 依赖包更新

## 🛠️ 故障排除

### 常见问题及解决方案

#### 1. 服务启动失败
```powershell
# 查看服务日志
eventvwr

# 手动测试
cd C:\transfer-card\backend
.\venv\Scripts\python.exe app.py
```

#### 2. 数据库连接失败
```powershell
# 测试连接
mysql -u transfer_user -p transfer_card

# 检查服务
sc query MySQL80
net start MySQL80
```

#### 3. 端口被占用
```powershell
# 查看端口
netstat -ano | findstr :80

# 结束进程
taskkill /PID <进程ID> /F
```

#### 4. Git拉取失败
```powershell
# 检查网络
ping github.com

# 配置凭证
git config --global credential.helper manager-core
```

更多故障排除请查看: `WIN_DEPLOYMENT.md` 的"常见问题"章节

## 📈 性能优化建议

1. **数据库优化**
   - 定期执行 `OPTIMIZE TABLE`
   - 添加适当的索引
   - 清理旧数据

2. **日志管理**
   - 定期清理旧日志
   - 设置日志轮转
   - 监控日志大小

3. **缓存优化**
   - 启用静态文件缓存
   - 配置HTTP缓存头

4. **资源监控**
   - 监控CPU、内存、磁盘使用
   - 设置告警阈值

## 📞 获取帮助

### 文档资源
- **快速部署**: `QUICK_START.md`
- **完整文档**: `WIN_DEPLOYMENT.md`
- **项目地址**: https://github.com/你的用户名/study

### 服务管理命令
```powershell
# 查看帮助
manage-services.bat

# 健康检查
manage-services.bat health

# 查看状态
manage-services.bat status
```

## ✅ 部署检查清单

部署完成后，请确认以下项目：

- [ ] 所有必要软件已安装（Python、Node.js、MySQL、Git）
- [ ] 代码已成功克隆到服务器
- [ ] 环境变量已正确配置（.env文件）
- [ ] 数据库已创建并初始化
- [ ] 后端依赖已安装
- [ ] 前端依赖已安装
- [ ] Windows服务已注册
- [ ] 后端服务运行正常
- [ ] 前端服务运行正常
- [ ] 可以访问 http://服务器IP
- [ ] 可以访问 http://服务器IP:5000/api/health
- [ ] 数据库连接正常
- [ ] 所有默认密码已修改
- [ ] 防火墙已正确配置
- [ ] 定时备份已设置
- [ ] 更新和回滚流程已测试

## 🎯 最佳实践

1. **测试环境验证**
   - 在测试环境先验证更新
   - 确认无问题后再更新生产环境

2. **非高峰期更新**
   - 选择用户访问量少的时间段
   - 提前通知用户

3. **备份数据**
   - 更新前务必备份
   - 验证备份可用性

4. **版本管理**
   - 使用Git进行版本控制
   - 每次更新都记录日志

5. **监控告警**
   - 设置服务监控
   - 配置告警通知

6. **文档维护**
   - 记录所有变更
   - 更新相关文档

## 📝 版本历史

- **v1.0.0** (2026-01-04)
  - 初始Windows Server部署方案
  - 完整的自动化脚本
  - 远程更新支持
  - 版本回滚功能

## 🎉 总结

本部署方案提供了：
- ✅ 完整的Windows Server 2022部署方案
- ✅ 自动化部署、更新、回滚脚本
- ✅ 远程推送更新支持
- ✅ 完善的服务管理工具
- ✅ 详细的文档和故障排除指南
- ✅ 安全建议和最佳实践

使用本方案，您可以：
1. 在10分钟内完成首次部署
2. 通过Git远程推送更新
3. 设置定时自动更新
4. 快速回滚到任意版本
5. 轻松管理和监控服务

**祝您部署顺利！** 🚀
