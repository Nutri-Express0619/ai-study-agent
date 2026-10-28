import sys
from pathlib import Path


from mcp import (
    ClientSession,
    StdioServerParameters
)

from mcp.client.stdio import (
    stdio_client
)



# =====================
# MCP Server路径
# =====================


PROJECT_ROOT = Path(__file__).resolve().parent.parent


MCP_SERVER_PATH = (
    PROJECT_ROOT
    /
    "mcp_demo"
    /
    "mcp_server.py"
)





# =====================
# 创建MCP连接参数
# =====================


def get_server_params():


    return StdioServerParameters(

        command=sys.executable,

        args=[
            str(MCP_SERVER_PATH)
        ],

    )





# =====================
# MCP客户端
# =====================


class MCPClient:


    def __init__(self):

        self.session = None



        self._context = None



        self._stdio_context = None





    async def connect(self):


        server_params = get_server_params()



        self._stdio_context = stdio_client(
            server_params
        )



        read_stream, write_stream = (
            await self._stdio_context.__aenter__()
        )



        self._context = ClientSession(

            read_stream,

            write_stream

        )


        self.session = (
            await self._context.__aenter__()
        )



        await self.session.initialize()



    async def disconnect(self):


        if self._context:


            await self._context.__aexit__(
                None,
                None,
                None
            )


        if self._stdio_context:


            await self._stdio_context.__aexit__(
                None,
                None,
                None
            )





    async def list_tools(self):


        result = await self.session.list_tools()


        return result.tools





    async def call_tool(
        self,
        name,
        arguments
    ):


        result = await self.session.call_tool(

            name,

            arguments=arguments

        )


        return result





# =====================
# 测试
# =====================


async def test():


    client = MCPClient()


    await client.connect()



    tools = await client.list_tools()



    print(
        "=== MCP工具列表 ==="
    )


    for tool in tools:


        print(
            tool.name
        )



    result = await client.call_tool(

        "search_knowledge_base",

        {
            "query":
            "LangGraph"
        }

    )



    print(
        "\n===测试结果==="
    )


    for item in result.content:

        if hasattr(
            item,
            "text"
        ):

            print(
                item.text
            )



    await client.disconnect()





if __name__ == "__main__":

    import asyncio


    asyncio.run(
        test()
    )