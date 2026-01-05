# 流转卡系统

一个基于前后端分离的企业流转卡管理系统，支持多部门协作流转和模板化配置。

## 项目结构

```
study/
├── backend/              # Flask后端
│   ├── app.py           # 主应用
│   ├── flow_api.py      # 流转API
│   ├── requirements.txt # Python依赖
│   └── config/          # 配置文件
├── frontend/            # 前端
│   ├── index.html       # 主页面
│   ├── package.json     # Node依赖
│   ├── css/             # 样式文件
│   └── js/              # JavaScript文件
└── database/            # 数据库
    └── schema.sql       # 数据库结构
```

## 技术栈

### 后端
- Python 3.x
- Flask
- MySQL
- PyMySQL
- bcrypt
- JWT

### 前端
- HTML5
- CSS3
- JavaScript (ES6+)
- Vite

## 快速开始

### 前置要求

- Python 3.x
- Node.js
- MySQL 5.7+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/setmee/study.git
cd study
```

2. **配置数据库**
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE transfer_card_system;
```

3. **配置后端**
```bash
cd backend
cp config/config.json.example config/config.json
# 编辑 config/config.json，填入数据库连接信息
```

4. **初始化数据库**
```bash
mysql -u root -p transfer_card_system < database/schema.sql
```

5. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

6. **安装前端依赖**
```bash
cd frontend
npm install
```

7. **启动服务**

**Windows:**
```bash
# 启动后端
cd backend
python app.py

# 启动前端（新终端）
cd frontend
npm start
```

**Linux/Mac:**
```bash
# 启动后端
cd backend
python app.py &

# 启动前端
cd frontend
npm start &
```

或使用启动脚本：
```bash
# Windows
./start.bat

# Linux/Mac
./start.sh
```

8. **访问应用**
- 前端: http://localhost:8080
- 后端API: http://localhost:5000

## 默认账户

- 用户名: `admin`
- 密码: `admin123`

## 功能特性

### 基础功能
- 用户认证和授权
- 模板管理
- 流转卡创建和管理
- 多部门流转
- 数据录入和编辑

### 流转功能
- 部门间流转
- 流转状态跟踪
- 流转操作日志
- 模板部门流转配置

## API文档

### 认证
- `POST /api/login` - 用户登录

### 模板
- `GET /api/templates` - 获取模板列表
- `POST /api/templates` - 创建模板
- `GET /api/templates/<id>` - 获取模板详情
- `PUT /api/templates/<id>` - 更新模板
- `DELETE /api/templates/<id>` - 删除模板

### 流转卡
- `GET /api/cards` - 获取流转卡列表
- `POST /api/cards` - 创建流转卡
- `GET /api/cards/<id>` - 获取流转卡详情
- `PUT /api/cards/<id>` - 更新流转卡
- `DELETE /api/cards/<id>` - 删除流转卡
- `GET /api/template-cards` - 获取模板流转卡列表

### 流转
- `POST /api/cards/<id>/start-flow` - 开始流转
- `POST /api/cards/<id>/next-step` - 下一步流转
- `GET /api/cards/<id>/flow-status` - 获取流转状态

## 开发说明

### 数据库结构

系统包含以下主要表：
- `departments` - 部门表
- `users` - 用户表
- `fields` - 字段定义表
- `templates` - 模板表
- `template_fields` - 模板字段关联表
- `transfer_cards` - 流转卡主表
- `card_data` - 流转卡数据表
- `card_flow_status` - 流转卡流转状态表
- `template_department_flow` - 模板部门流转配置表
- `operation_logs` - 操作日志表
- `flow_operation_logs` - 流转操作日志表

### 配置文件

后端配置文件位于 `backend/config/config.json`，包含：
- 服务器配置
- 数据库配置
- JWT配置
- 日志配置
- CORS配置

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题，请提交Issue或联系项目维护者。
