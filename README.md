# BidAgent - 标书智能助手

基于 AI Agent 的标书自动编写与审核系统。

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + Naive UI + Pinia + Vue Router | 现代前端框架 |
| 后端 | FastAPI + SQLAlchemy + PyMySQL | RESTful API |
| 数据库 | MySQL | 持久化存储 |
| 迁移 | Alembic | 数据库版本管理 |
| 包管理 | uv (backend) / npm (frontend) | 依赖管理 |

## 项目结构

```
BidAgent/
├── frontend/               # 前端项目
│   └── src/
│       ├── api/            # API 接口层
│       ├── components/     # 公共组件
│       ├── router/         # 路由配置
│       ├── stores/         # 状态管理
│       └── views/          # 页面视图
├── backend/                # 后端项目
│   └── app/
│       ├── api/v1/         # API 路由
│       ├── core/           # 配置与数据库
│       ├── models/         # ORM 模型
│       ├── schemas/        # 数据模型
│       └── services/       # 业务逻辑
└── docs/                   # 设计文档
```

## 快速开始

### 后端

```bash
cd backend
uv sync
# 编辑 .env 配置数据库连接
uv run uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 功能

- 公有文件上传与管理
- 项目创建与管理
- 项目私有文件管理
- 标书自动编写与审核（开发中）
