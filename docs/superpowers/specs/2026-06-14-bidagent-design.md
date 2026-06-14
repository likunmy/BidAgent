# BidAgent - 标书智能助手

## 项目概述

前后端分离的标书辅助系统，基于 AI Agent 实现自动写标书和审核标书。前端 Vue 3 + Naive UI，后端 FastAPI + MySQL，使用 uv 管理 Python 依赖。

## 核心功能

1. **公有文件上传** - 上传可被所有项目引用的公共文档（模板、法规文件等）
2. **项目管理** - 新建、编辑、查看、删除项目
3. **项目私有文件** - 每个项目独立管理其私有文件，文件隔离存储

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + Naive UI + Pinia + Vue Router | 现代前端框架 |
| 后端 | FastAPI + SQLAlchemy + PyMySQL | RESTful API |
| 数据库 | MySQL | 持久化存储 |
| 迁移 | Alembic | 数据库版本管理 |
| 包管理 | uv (backend) / npm (frontend) | 依赖管理 |

## 目录结构

```
BidAgent/
├── frontend/                      # Vue 3 + Vite + Naive UI
│   ├── public/                    # 静态资源
│   ├── src/
│   │   ├── api/                   # API 接口层
│   │   ├── assets/                # 样式/图片等
│   │   ├── components/            # 公共组件
│   │   │   ├── common/            # 通用组件
│   │   │   └── layout/            # 布局组件
│   │   ├── router/                # Vue Router
│   │   ├── stores/                # Pinia 状态管理
│   │   ├── views/                 # 页面视图
│   │   │   ├── project/           # 项目管理
│   │   │   ├── file/              # 文件管理
│   │   │   └── home/              # 首页
│   │   ├── utils/                 # 工具函数
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style/                 # 全局样式
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── backend/                       # FastAPI + MySQL (uv 管理)
│   ├── app/
│   │   ├── api/v1/                # API 路由
│   │   ├── core/                  # 配置、数据库连接
│   │   ├── models/                # SQLAlchemy 模型
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # 业务逻辑
│   │   └── main.py                # 入口
│   ├── uploads/public/            # 公有文件存储
│   ├── uploads/projects/          # 项目私有文件存储
│   ├── alembic/                   # 数据库迁移
│   ├── pyproject.toml
│   └── .env
```

## 数据模型概要

- **Project**: id, name, description, created_at, updated_at
- **File**: id, filename, original_name, file_type (public/project), project_id (nullable), file_path, size, created_at

## 架构要点

- 前后端通过 RESTful API 通信
- 文件隔离：`uploads/public/` 公有文件，`uploads/projects/{project_id}/` 项目私有文件
- API 分层：router → service → model，职责清晰
- 配置通过 `.env` + Pydantic Settings 管理
