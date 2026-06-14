"""Agent tool registry for discovery and function calling.

Each tool entry exposes name, description, and input_schema so the
agent can decide which tool to call and how to format the arguments.
"""

from app.agent.tools.docx_output import OutputDocxInput
from app.agent.tools.file_loader import LoadFileInput
from app.agent.tools.file_search import FileSearchInput
from app.agent.tools.missing_info import StoreMissingInfoInput

TOOL_REGISTRY = [
    {
        "name": "file_search",
        "description": "搜索项目目录下（除招标文件外）及公共目录中所有 MD 文件的内容，支持关键字搜索与文件名过滤",
        "input_schema": FileSearchInput.model_json_schema(),
    },
    {
        "name": "file_loader",
        "description": "加载单个 MD 文件的全部内容或指定章节内容至上下文，图片引用会被替换为占位符（含 MD5 及尺寸信息）",
        "input_schema": LoadFileInput.model_json_schema(),
    },
    {
        "name": "store_missing_info",
        "description": "将本次标书生成中缺失的信息项存入数据库，每个项目每次生成前会清空旧记录",
        "input_schema": StoreMissingInfoInput.model_json_schema(),
    },
    {
        "name": "output_docx",
        "description": "根据结构化的章节内容（段落/图片/表格/占位符）生成 docx 标书文件，缺失部分自动插入占位图并记录缺失信息",
        "input_schema": OutputDocxInput.model_json_schema(),
    },
]
