# 文件管理模块 - 上传与格式转换

## 概述

完成文件管理页面，支持上传 PDF/DOCX/TXT 文件，自动转换为 Markdown 格式存储，并强制用户填写文件展示名和简介。

## 数据流

```
用户选择文件 → 填写展示名+简介（强提醒）
  → POST /api/v1/files/public (multipart)
  → 后端:
     1. 源文件存入 data/{format}/{file_name}
     2. markitdown 转 MD
     3. MD 存入 uploads/public/{display_name}.md
     4. MySQL 记录映射关系
  → 返回结果 → 前端刷新列表
```

## 数据库模型 (File)

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int (PK) | 自增主键 |
| display_name | str(255) | 前端填写的展示名，MD 文件名 |
| description | text\|null | 简介 |
| original_name | str(255) | 原始上传文件名 |
| source_format | str(10) | pdf/docx/txt |
| source_path | str(512) | data/ 下路径 |
| md_path | str(512) | uploads/public/ 下路径 |
| file_type | str(20) | public（预留 project） |
| size | int | 文件大小 |
| created_at | datetime | 创建时间 |

## 目录存储

```
data/pdf/{filename}_{timestamp}.pdf
data/docx/{filename}_{timestamp}.docx
data/txt/{filename}_{timestamp}.txt
uploads/public/{display_name}.md
```

## API 接口

```
POST /api/v1/files/public  (multipart: file + display_name + description)
GET  /api/v1/files/public
DELETE /api/v1/files/{id}
```

## 前端交互

- 上传表单顶部用 `n-alert type="warning"` 展示强提醒
- 表单字段：文件选择、展示名、简介
- 列表页：表格展示所有公有文件，支持删除
- 上传后自动刷新列表

## 后端实现要点

- markitdown 同步转换（`MarkItDown().convert()`）
- 重名源文件加时间戳后缀
- MD 文件展示名去重时自动加序号
- 转换异常时清理已保存的文件并返回错误

## 依赖

- `markitdown>=0.1.0`
