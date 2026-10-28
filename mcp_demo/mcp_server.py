import sys
from pathlib import Path

# =========================
# 1. 添加项目根目录到 Python 搜索路径
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =========================
# 2. 导入 MCP 和现有 RAG 检索函数
# =========================

from mcp.server.mcpserver import MCPServer
from rag.retriever import search


# 创建 MCP Server
mcp = MCPServer("ai-study-agent-server")


# =========================
# 3. 普通 MCP Tools
# =========================

@mcp.tool()
def add(a: int, b: int) -> int:
    """计算两个整数的和。"""
    return a + b


@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市的模拟天气信息。"""

    weather_data = {
        "北京": "晴天，气温 25°C",
        "上海": "多云，气温 23°C",
        "广州": "小雨，气温 28°C",
    }

    return weather_data.get(
        city,
        f"暂时没有{city}的天气数据"
    )


@mcp.tool()
def search_notes(keyword: str) -> str:
    """根据关键词搜索学习笔记，当前为模拟搜索。"""

    notes = {
        "Python": "Python 是一种常用的编程语言。",
        "RAG": "RAG 结合检索和大语言模型生成回答。",
        "MCP": "MCP 是用于连接 AI 应用与外部工具、资源的协议。",
    }

    for key, content in notes.items():
        if keyword.lower() in key.lower():
            return content

    return f"没有找到与“{keyword}”相关的学习笔记。"


# =========================
# 4. 接入现有 RAG 检索能力
# =========================

@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """在 AI Study Agent 的 RAG 知识库中检索与问题相关的内容。"""

    results = search(query)

    if not results:
        return "知识库中没有找到相关内容。"

    return "\n\n".join(results)


# =========================
# 5. MCP Resource
# =========================

@mcp.resource("study://notes/python")
def get_python_notes() -> str:
    """提供 Python 学习笔记。"""

    return """
# Python 学习笔记

Python 是一种常用的编程语言。

装饰器可以在不直接修改原函数代码的情况下，
扩展函数的行为。

RAG 是检索增强生成，结合检索系统和大语言模型生成回答。
"""

@mcp.resource("study://roadmap")
def get_learning_roadmap() -> str:
    """提供 AI Study Agent 的学习路线。"""

    return """
# AI Study Agent 学习路线

1. Python
2. LLM API
3. Memory
4. System Prompt
5. Tool Calling
6. RAG
7. Agent 架构
8. LangGraph
9. MCP
10. FastAPI
11. Docker 部署
12. 前端开发
13. GitHub 项目包装
"""


# =========================
# 6. 启动 MCP Server
# =========================

if __name__ == "__main__":
    mcp.run(transport="stdio")