# 流转卡管理系统 (Transfer Card Management System)

一个基于Vue.js + Flask的现代化流转卡管理系统，支持多部门协作、权限管理、模板化数据录入等功能。

## 🌟 项目特点

- **前后端分离架构**：Vue.js前端 + Flask后端
- **权限管理系统**：支持管理员和普通用户角色
- **模板化数据录入**：可配置的字段模板
- **多部门协作**：支持跨部门数据流转
- **响应式设计**：适配各种屏幕尺寸
- **实时数据保存**：自动保存，防止数据丢失

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Node.js 14+
- MySQL 5.7+

### 1. 克隆项目

```bash
git clone https://github.com/your-username/transfer-card-system.git
cd transfer-card-system
```

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 配置数据库
# 1. 复制配置文件模板
cp config/config.json.example config/config.json

# 2. 编辑配置文件，填入你的数据库信息
# 主要修改数据库连接信息
```

**数据库配置示例 (config/config.json):**
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "transfer_card_system",
    "charset": "utf8mb4"
  }
}
```

```bash
# 初始化数据库
python init_db.py

# 启动后端服务
python app.py
```

后端服务将在 `http://localhost:5000` 启动

### 3. 前端设置

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装Node.js依赖
npm install

# 启动前端服务
npm start
```

前端服务将在 `http://localhost:8080` 启动

### 4. 访问系统

打开浏览器访问 `http://localhost:8080`

## 📋 默认账号

系统预置了以下测试账号：

| 用户类型 | 用户名 | 密码 | 角色 | 部门 |
|---------|--------|------|------|------|
| 管理员 | admin | admin123 | 管理员 | 研发部 |
| 普通用户 | user1 | user123 | 普通用户 | 采购部 |

## 🏗️ 项目结构

```
transfer-card-system/
├── backend/                 # 后端代码
│   ├── app.py              # Flask主应用
│   ├── init_db.py          # 数据库初始化
│   ├── requirements.txt     # Python依赖
│   └── config/             # 配置文件
├── frontend/               # 前端代码
│   ├── index.html         # 主页面
│   ├── css/               # 样式文件
│   ├── js/                # JavaScript文件
│   └── package.json       # Node.js配置
├── database/               # 数据库相关
│   └── schema.sql         # 数据库结构
└── README.md              # 项目说明
```

## 🎯 主要功能

### 用户管理
- ✅ 用户登录/退出
- ✅ 角色权限控制（管理员/普通用户）
- ✅ 部门管理
- ✅ 密码安全存储

### 流转卡管理
- ✅ 创建流转卡
- ✅ 基于模板创建流转卡
- ✅ 流转卡状态管理
- ✅ 数据编辑和保存
- ✅ 流转卡列表查看

### 字段管理
- ✅ 动态字段配置
- ✅ 字段类型支持（文本、数字、日期、选择等）
- ✅ 部门权限控制
- ✅ 字段显示/隐藏设置

### 模板管理
- ✅ 创建和管理模板
- ✅ 模板字段配置
- ✅ 模板启用/禁用
- ✅ 基于模板快速创建流转卡

## 🔧 技术栈

### 后端
- **Flask**: Web框架
- **Flask-JWT-Extended**: JWT认证
- **PyMySQL**: 数据库连接
- **bcrypt**: 密码加密
- **Flask-CORS**: 跨域支持

### 前端
- **Vue.js 2**: 前端框架
- **Element UI**: UI组件库
- **Axios**: HTTP客户端
- **Bootstrap**: CSS框架

### 数据库
- **MySQL**: 关系型数据库

## 📖 API文档

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户退出
- `GET /api/auth/profile` - 获取用户信息

### 流转卡接口
- `GET /api/cards` - 获取流转卡列表
- `POST /api/cards` - 创建流转卡
- `GET /api/cards/{id}/data` - 获取流转卡数据
- `PUT /api/cards/{id}/data` - 更新流转卡数据

### 模板接口
- `GET /api/templates` - 获取模板列表
- `POST /api/templates` - 创建模板
- `GET /api/templates/{id}/fields` - 获取模板字段

完整的API文档可以参考后端代码中的路由定义。

## 🛠️ 开发指南

### 添加新的字段类型

1. **后端修改**：
   - 在 `backend/app.py` 中的字段处理逻辑中添加新类型
   - 更新数据库字段类型映射

2. **前端修改**：
   - 在 `frontend/js/app.js` 中添加字段类型的处理逻辑
   - 更新表单组件渲染逻辑

### 添加新的权限角色

1. **数据库修改**：
   - 更新用户表的role字段
   - 添加相应的权限记录

2. **代码修改**：
   - 更新后端权限检查逻辑
   - 修改前端角色判断逻辑

## 🔍 故障排除

### 常见问题

**1. 后端启动失败**
```bash
# 检查Python版本
python --version

# 检查依赖是否安装
pip list

# 检查数据库连接
python -c "import pymysql; print('MySQL连接正常')"
```

**2. 前端启动失败**
```bash
# 检查Node.js版本
node --version

# 清除npm缓存
npm cache clean --force

# 重新安装依赖
rm -rf node_modules
npm install
```

**3. 数据库连接失败**
- 检查MySQL服务是否启动
- 确认配置文件中的数据库信息正确
- 检查数据库用户权限

**4. 跨域问题**
- 确认后端CORS配置正确
- 检查前端API请求地址

### 日志查看

**后端日志**：控制台直接输出
**前端日志**：浏览器开发者工具的Console面板

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如果您有任何问题或建议，请通过以下方式联系：

- 提交Issue: [GitHub Issues](https://github.com/your-username/transfer-card-system/issues)
- 邮箱: your-email@example.com

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

---

**注意**: 这是一个学习项目，适合初学者了解前后端分离架构、权限管理、数据库设计等概念。如果您是初学者，建议先阅读项目结构，然后按照快速开始指南一步步运行项目。
