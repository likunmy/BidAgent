# BidAgent — 标书智能编制系统

基于 AI Agent（LangGraph）的智能化标书编写与审核平台，辅助投标团队高效完成招标文件解析、技术方案编写、商务条款审核及标书生成全流程。

## 技术架构

| 层 | 技术选型 | 说明 |
|---|---|---|
| 前端 | Vue 3 + Vite + Naive UI | 响应式界面，SSE 实时进度推送 |
| 后端 | FastAPI + SQLAlchemy + PyMySQL | RESTful API + LangGraph 编排 |
| 数据库 | MySQL 8.0 | 项目与文件持久化 |
| AI 编排 | LangGraph StateGraph | 多 Agent 分阶段协作 |
| LLM | DeepSeek V4 Flash | 兼容 OpenAI 接口协议 |

## 目录结构

```
BidAgent/
├── frontend/                   # 前端项目
│   └── src/
│       ├── api/                # API 接口层
│       ├── components/         # 公共组件
│       ├── router/             # 路由配置
│       ├── stores/             # Pinia 状态管理
│       └── views/              # 页面视图
├── backend/                    # 后端项目
│   └── app/
│       ├── agent/
│       │   ├── tools/          # Agent 工具（文件检索、缺失信息记录、docx 输出）
│       │   └── graph/          # LangGraph 流程编排（状态定义、节点逻辑、提示词）
│       ├── api/v1/             # RESTful API + SSE 流式推送
│       ├── core/               # 系统配置与数据库连接
│       ├── models/             # ORM 持久化模型
│       ├── schemas/            # Pydantic 校验模型
│       └── services/           # 业务逻辑层
├── data/                       # 上传的源文件（PDF/DOCX/TXT）
├── uploads/                    # 转换后的 Markdown、图片、输出标书
└── docs/                       # 设计文档
```

## 快速开始

### 前置条件

- Python >= 3.11
- Node.js >= 18
- MySQL 8.0
- DeepSeek API Key

### 1. 初始化数据库

```bash
make db-init      # 创建 bidagent 数据库
make migrate      # 执行数据库迁移
```

### 2. 启动后端

```bash
cp backend/.env.example backend/.env          # 编辑配置，填写数据库连接与 API Key
make install-dev                               # 安装依赖（含开发工具）
make run                                       # 服务运行于 http://localhost:8000
```

### 3. 启动前端

```bash
make frontend-install
make frontend-dev                              # 开发服务器 http://localhost:5173
```

### 4. 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DATABASE_URL` | MySQL 连接字符串 | `mysql+pymysql://root:password@localhost:3306/bidagent` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `DEEPSEEK_BASE_URL` | API 接口地址 | `https://api.deepseek.com` |
| `UPLOAD_DIR` | 转换文件存储目录 | `./uploads` |

## Agent 工作流程

```
招标文件解析 → 大纲生成 → 多章节并行编写（≤6）→ 逐章审核
  ↻ 修改 ← 审核不通过
  → 标书合并编译 → 终审 → 完成
```

系统内置四类 Agent：

- **解析 Agent**：读取招标文件，提取关键要求和评分标准，生成标书大纲
- **章节 Agent**（并发 6 路）：按大纲分章节编写，自动检索项目资料，记录缺失信息
- **审核 Agent**：逐章校验是否满足招标要求，不通过则反馈修改意见
- **终审 Agent**：对标书全文进行完整性、合规性和逻辑一致性审核

## 常用命令

```bash
make install          # 安装后端依赖
make run              # 启动后端服务
make lint             # 代码检查与自动修复
make test             # 运行测试
make migrate          # 执行数据库迁移
make migrate-new name="xxx"   # 创建新迁移
make frontend-dev     # 启动前端开发服务器
```

## Agent 工具清单

| 工具 | 用途 | 调用方 |
|---|---|---|
| `file_search` | 全文检索项目资料 | 章节 Agent |
| `file_loader` | 加载文件内容至上下文 | 解析 Agent、章节 Agent、终审 Agent |
| `store_missing_info` | 记录缺失资料至数据库 | 章节 Agent |
| `output_docx` | 生成与追加标书文档 | 系统内部 |
