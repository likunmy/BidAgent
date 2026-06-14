# Agent 工具模块设计

## 概述

在 `app/agent/` 下创建 Agent 工具模块，为后续 AI Agent 提供 4 个可调用的工具函数。这些工具负责文件搜索、文件加载、缺失信息存储和 docx 输出。

## 目录结构

```
backend/app/
  agent/
    __init__.py
    tool_registry.py            # 工具注册表，供 agent 发现
    tools/
      __init__.py
      file_search.py            # Tool 1 — 文件内容搜索
      file_loader.py            # Tool 2 — 加载 MD 文件进上下文
      missing_info.py           # Tool 3 — 缺失信息存储
      docx_output.py            # Tool 4 — 输出 docx
      image_extractor.py        # 图片提取公用模块
  models/
    missing_info.py             # 缺失信息数据库模型
```

## Tool 1: 文件内容搜索

**文件**: `app/agent/tools/file_search.py`

**输入**:
- `project_id: int` — 必填，限定项目
- `query: str` — 搜索关键词
- `filename_filter: str | None` — 可选，按文件名（路径+名称）筛选

**搜索范围**（在该 project_id 下）:
- `uploads/projects/{project_id}/*.md`，排除招标文件的 md（`file_type == "tender"` 的文件的 md_path）
- `uploads/public/*.md`

**逻辑**:
1. 从 DB 查询项目中 `file_type != "tender"` 的所有文件的 md_path
2. 从 DB 查询 `file_type == "public"` 的所有文件的 md_path
3. 如果传了 `filename_filter`，只保留文件名匹配的文件
4. 遍历每个 md 文件，全文搜索 query
5. 对匹配的文件，提取上下文中 2 行作为片段

**输出**:
```json
{
  "total": 1,
  "results": [
    {
      "file_path": "uploads/projects/1/技术方案.md",
      "display_name": "技术方案",
      "snippets": ["...符合招标文件第3条要求..."],
      "match_count": 2
    }
  ]
}
```

## Tool 2: 加载 MD 文件进上下文

**文件**: `app/agent/tools/file_loader.py`

**依赖**: `app/agent/tools/image_extractor.py`（图片处理公用模块）

**输入**:
- `file_path: str` — MD 文件路径
- `section_heading: str | None` — 可选，Markdown 标题名称

**输出**:
```json
{
  "content": "## 技术方案\n\n根据招标文件要求...\n[图: md5=a1b2c3, 尺寸=800x600, 路径=...]\n\n...",
  "images": [
    {"md5": "a1b2c3", "width": 800, "height": 600, "size_bytes": 102400, "path": "uploads/projects/1/招标文件_images/a1b2c3.png"}
  ]
}
```

### 按标题章节截取

- 从 `section_heading` 匹配的第一个标题（`#`、`##`、`###`）开始
- 截取到下一个同级或上级标题为止
- 如果没有匹配的标题，返回空内容
- 如果不传 `section_heading`，返回整个文件内容

### 图片占位符处理

- 在文件上传转换时，图片从源文件提取到 `{md_path}_images/` 目录，以 MD5 命名
- 读取 MD 内容中的图片引用，替换为 `[图: md5={hash}, 尺寸={W}x{H}, 路径={path}]`
- 占位符包含：md5 值、原始图片尺寸（宽x高）、文件路径
- 同时返回 images 数组供后续使用

### 图片提取 (image_extractor.py)

**文件**: `app/agent/tools/image_extractor.py`

这个模块被文件上传流程和 Tool 2 共同使用。

- `extract_images_from_source(source_path, md_path)` — 从源文件提取内嵌图片
  - DOCX: 解压 ZIP 从 `word/media/` 获取图片
  - PDF: 使用 PyMuPDF 或 pdfplumber 提取图片
  - 图片以 MD5 命名存入 `{md_path}_images/` 目录
  - 同时将 MD 内容中的图片引用替换为标记
- `get_image_info(md_path, md5)` — 按 md5 获取图片元数据（尺寸、大小）
- `get_image_bytes(md_path, md5)` — 按 md5 获取图片二进制数据

## Tool 3: 缺失信息存储

### 数据库模型

**文件**: `app/models/missing_info.py`

```python
class MissingInfo(Base):
    __tablename__ = "missing_infos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### 工具函数

**文件**: `app/agent/tools/missing_info.py`

**输入**:
```json
{
  "project_id": 1,
  "items": [
    {"name": "企业营业执照", "description": "企业营业执照副本扫描件或照片"},
    {"name": "项目负责人简历", "description": "项目主要负责人简历及资格证书"}
  ]
}
```

**逻辑**:
1. 清除该项目下所有现有缺失信息（每轮生成以最新为准）
2. 批量写入新的缺失项
3. 返回存储结果

**输出**: `{ "stored": 2, "items": [...] }`

### REST API（前端用）

- `GET /api/v1/projects/{id}/missing-infos` — 获取项目缺失信息列表
- 替代现有的硬编码 `REQUIREMENT_DEFS` + `get_project_requirements`

## Image Extractor 集成到上传流程

在 `app/services/file_service.py` 的 `upload_project_file` 和 `upload_public_file` 中，markitdown 转换完成后，增加一步：

```python
# 2.5. Extract embedded images from source
from app.agent.tools.image_extractor import extract_images_from_source
image_dir = extract_images_from_source(src_path, md_path)
```

`extract_images_from_source` 负责：
1. 从源文件提取内嵌图片（DOCX 从 ZIP media/，PDF 用 PyMuPDF）
2. 以 MD5 命名存入 `{md_path}_images/` 目录
3. 返回图片列表 `[{md5, width, height, ext, size}]`

## 清理旧代码

`REQUIREMENT_DEFS`、`_KEYWORD_MAP`、`get_project_requirements` 在 Tool 3 + 新 REST API 就绪后移除。

## Tool 4: 输出 docx 文件

**文件**: `app/agent/tools/docx_output.py`

**依赖**: python-docx, Pillow

**输入**:
```json
{
  "project_id": 1,
  "output_filename": "投标文件_XX项目.docx",
  "sections": [
    {
      "heading": "第一章 公司简介",
      "level": 1,
      "children": [
        {"type": "paragraph", "text": "我公司成立于2010年..."},
        {"type": "image", "source_md_path": "uploads/projects/1/招标文件.md", "md5": "a1b2c3", "width": 400, "height": 300},
        {"type": "table", "headers": ["项目", "金额"], "rows": [["营收", "1000万"]]},
        {"type": "placeholder", "name": "企业营业执照", "width": 400, "height": 250}
      ]
    }
  ]
}
```

**逻辑**:

1. 递归遍历 sections，逐项生成 docx 内容
2. `paragraph` — 直接写入文本段落
3. `image` — 从 `{md_path}_images/` 按 md5 查找图片，按 AI 指定的 width/height 缩放插入
4. `table` — 生成表格（首行为表头样式）
5. `placeholder` — 生成占位图：浅灰背景 + 居中文字"缺失: {name}" + 边框，指定尺寸插入 docx；同时自动调用 Tool 3 将该缺失项写入 DB
6. `heading` — 标题行，按 level 设置 docx 标题样式

3. `image` — 从 `{source_md_path}_images/` 按 md5 查找图片，按 AI 指定的 width/height 缩放插入。如果不传 source_md_path，则搜索所有项目文件的 `_images/` 目录

**输出路径**: `uploads/projects/{project_id}/output/{output_filename}`

**输出返回**:
```json
{
  "file_path": "uploads/projects/1/output/投标文件_XX项目.docx",
  "missing_items": [
    {"name": "企业营业执照", "description": "请上传营业执照扫描件"}
  ]
}
```

## 工具注册表

**文件**: `app/agent/tool_registry.py`

```python
TOOLS = [
    {
        "name": "file_search",
        "description": "搜索项目目录和公共目录下的 MD 文件内容，返回匹配的文件路径和片段",
        "input_schema": FileSearchInput,
    },
    {
        "name": "load_file",
        "description": "加载 MD 文件内容，支持按标题章节截取，图片替换为占位符",
        "input_schema": LoadFileInput,
    },
    {
        "name": "store_missing_info",
        "description": "存储缺失信息项，自动清除该项目的旧记录",
        "input_schema": StoreMissingInfoInput,
    },
    {
        "name": "output_docx",
        "description": "根据结构化内容生成 docx 文件，支持文本、图片、表格和占位图",
        "input_schema": OutputDocxInput,
    },
]
```

后续 agent 通过 `tool_registry.TOOLS` 了解所有可用工具，做 function calling 映射。

## 数据库迁移

新增 `missing_infos` 表，需要新建 Alembic 迁移。

## 后续计划

- 现有 `REQUIREMENT_DEFS` 和 `get_project_requirements` 在 Tool 3 + REST API 就绪后可移除
- `image_extractor` 需集成到文件上传流程中：文件转换 MD 后自动提取图片
