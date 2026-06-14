# BidAgent - 标书智能助手

基于 AI Agent (LangGraph) 的标书自动编写与审核系统。

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + Naive UI + Pinia + Vue Router | 现代前端框架 |
| 后端 | FastAPI + SQLAlchemy + PyMySQL | RESTful API + SSE 流式推送 |
| 数据库 | MySQL 8.0 | 持久化存储 |
| 迁移 | Alembic | 数据库版本管理 |
| AI 编排 | LangGraph StateGraph | 多 Agent 协作流程 |
| LLM | DeepSeek V4 Flash (OpenAI 兼容接口) | 标书生成与审核 |

## 项目结构

```
BidAgent/
├── frontend/                   # 前端项目
│   └── src/
│       ├── api/                # API 接口层
│       ├── components/         # 公共组件
│       ├── router/             # 路由配置
│       ├── stores/             # 状态管理 (Pinia)
│       └── views/              # 页面视图
├── backend/                    # 后端项目
│   └── app/
│       ├── agent/
│       │   ├── tools/          # Agent 工具 (file_search, file_loader, missing_info, docx_output)
│       │   └── graph/          # LangGraph 编排 (state, nodes, router, agent_factory, prompts)
│       ├── api/v1/             # RESTful API + SSE
│       ├── core/               # 配置与数据库
│       ├── models/             # ORM 模型
│       ├── schemas/            # Pydantic 数据模型
│       └── services/           # 业务逻辑
├── data/                       # 上传的原始文件 (PDF/DOCX/TXT)
├── uploads/                    # 转换后的 MD 文件 + 图片 + 输出的 docx
└── docs/                       # 设计文档
```

## 快速开始

### 前置要求

- Python >= 3.11
- Node.js >= 18
- MySQL 8.0
- DeepSeek API Key

### 1. 数据库

```bash
make db-init      # 创建 bidagent 数据库
make migrate      # 执行数据库迁移
```

### 2. 后端

```bash
cp backend/.env.example backend/.env    # 编辑 .env 配置数据库和 API Key
make install-dev                          # 安装依赖（含开发工具）
make run                                  # 启动 http://localhost:8000
```

### 3. 前端

```bash
make frontend-install
make frontend-dev                         # 启动 http://localhost:5173
```

### 4. 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DATABASE_URL` | MySQL 连接字符串 | `mysql+pymysql://root:password@localhost:3306/bidagent` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | (必填) |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com/v1` |
| `UPLOAD_DIR` | MD 文件存储目录 | `./uploads` |

## Agent 工作流

```
解析招标文件 → 生成大纲 → 并行生成章节 (≤6) → 逐章审核
  ↻ 修改 ← 不通过
  → 编译 docx → 终审 → 完成
```

每个 Agent 类型：
- **主 Agent** — 解析招标文件、生成大纲、编译 docx
- **章节 Agent** (×6 并行) — 撰写章节内容，可调用工具查询文件、记录缺失信息
- **审核 Agent** — 纯 LLM 判断，不调用工具
- **终审 Agent** — 对比招标文件与最终 docx 全篇审核

## 常用命令

```bash
make install          # 安装后端依赖
make run              # 启动后端
make lint             # 代码检查 + 自动修复
make test             # 运行测试
make migrate          # 执行数据库迁移
make migrate-new name="xxx"   # 创建新迁移
make frontend-dev     # 启动前端
```

## 工具

| 工具 | 用途 | 给 Agent 用 |
|---|---|---|
| `file_search` | 搜索项目 MD 文件内容 | ✅ |
| `file_loader` | 加载 MD 文件/章节到上下文 | ✅ |
| `store_missing_info` | 记录缺失信息到数据库 | ✅ |
| `output_docx` | 生成/追加 docx 标书文件 | ✅ |
