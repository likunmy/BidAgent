"""Factory for creating LLM-driven agents bound to tools."""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.agent.tools.file_loader import LoadFileInput, load_file
from app.agent.tools.file_search import FileSearchInput, file_search
from app.agent.tools.missing_info import StoreMissingInfoInput, store_missing_info
from app.core.config import settings


def create_llm(**kwargs) -> BaseChatModel:
    """Create the LLM instance configured for DeepSeek."""
    return ChatOpenAI(
        model=kwargs.pop("model", "deepseek-v4-flash"),
        api_key=settings.deepseek_api_key or "sk-placeholder",
        base_url=settings.deepseek_base_url,
        temperature=kwargs.pop("temperature", 0.3),
        **kwargs,
    )


def _make_tool(fn, input_model):
    """Wrap a function + pydantic model as a langchain tool."""
    desc = (input_model.__doc__ or fn.__doc__ or "").strip()
    @tool(args_schema=input_model, description=desc)
    def wrapper(**kwargs):
        """Execute the wrapped tool function."""
        return fn(input_model(**kwargs))
    return wrapper


def build_main_agent(llm: BaseChatModel | None = None):
    """Main agent: has file_search, file_loader tools."""
    if llm is None:
        llm = create_llm()
    tools = [
        _make_tool(load_file, LoadFileInput),
    ]
    return llm.bind_tools(tools)


def build_chapter_agent(llm: BaseChatModel | None = None):
    """Chapter writer agent: has file_search, file_loader, store_missing_info."""
    if llm is None:
        llm = create_llm()
    tools = [
        _make_tool(file_search, FileSearchInput),
        _make_tool(load_file, LoadFileInput),
        _make_tool(store_missing_info, StoreMissingInfoInput),
    ]
    return llm.bind_tools(tools)


def build_review_agent(llm: BaseChatModel | None = None):
    """Review agent: pure LLM, no tools."""
    if llm is None:
        llm = create_llm(temperature=0.1)
    return llm


def build_final_review_agent(llm: BaseChatModel | None = None):
    """Final review agent: has file_loader to read tender and docx."""
    if llm is None:
        llm = create_llm(temperature=0.1)
    tools = [
        _make_tool(load_file, LoadFileInput),
    ]
    return llm.bind_tools(tools)
