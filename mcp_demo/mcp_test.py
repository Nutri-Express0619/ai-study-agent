import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # 1. 配置 MCP Server 启动参数
    server_path = Path(__file__).with_name("mcp_server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    # 2. 启动 MCP Server，并建立客户端连接
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 3. 获取工具列表
            tools_result = await session.list_tools()

            print("=== MCP 工具列表 ===")
            for tool in tools_result.tools:
                print(f"\n工具名称：{tool.name}")
                print(f"工具描述：{tool.description}")
                print(f"参数结构：{tool.input_schema}")

            # 4. 调用计算工具
            add_result = await session.call_tool(
                "add",
                arguments={"a": 10, "b": 20},
            )

            print("\n=== 计算工具结果 ===")
            for item in add_result.content:
                if hasattr(item, "text"):
                    print(item.text)

            # 5. 调用天气工具
            weather_result = await session.call_tool(
                "get_weather",
                arguments={"city": "上海"},
            )

            print("\n=== 天气工具结果 ===")
            for item in weather_result.content:
                if hasattr(item, "text"):
                    print(item.text)

            # 6. 调用现有 RAG 知识库
            rag_result = await session.call_tool(
                "search_knowledge_base",
                arguments={"query": "LangGraph Checkpoint"},
            )

            print("\n=== RAG 知识库检索结果 ===")
            for item in rag_result.content:
                if hasattr(item, "text"):
                    print(item.text)

            # 7. 获取 Resource 列表
            resources_result = await session.list_resources()

            print("\n=== MCP 资源列表 ===")
            for resource in resources_result.resources:
                print(f"\n资源名称：{resource.name}")
                print(f"资源地址：{resource.uri}")
                print(f"资源描述：{resource.description}")

            # 8. 读取 Python 学习笔记 Resource
            resource_result = await session.read_resource(
                "study://notes/python"
            )

            print("\n=== Python 学习笔记内容 ===")
            for item in resource_result.contents:
                if hasattr(item, "text"):
                    print(item.text)

            # 9. 读取 AI Study Agent 学习路线 Resource
            roadmap_result = await session.read_resource(
                "study://roadmap"
            )

            print("\n=== AI Study Agent 学习路线 ===")
            for item in roadmap_result.contents:
                if hasattr(item, "text"):
                 print(item.text)


if __name__ == "__main__":
    asyncio.run(main())