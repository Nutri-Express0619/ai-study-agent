import asyncio
import json
import sys
from pathlib import Path

import requests

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# =====================
# 项目路径
# =====================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from config import BASE_URL, MODEL
from memory import add_message, get_messages



# =====================
# 最大工具调用次数
# =====================

MAX_TOOL_ROUNDS = 5



# =====================
# MCP工具转换
# =====================

def convert_mcp_tools(mcp_tools):

    ollama_tools = []

    tool_mapping = {}


    for tool in mcp_tools:

        exposed_name = f"mcp_{tool.name}"


        ollama_tools.append(
            {
                "type": "function",
                "function": {
                    "name": exposed_name,
                    "description": (
                        f"MCP 工具。{tool.description or ''}"
                    ),
                    "parameters": tool.input_schema,
                },
            }
        )


        tool_mapping[exposed_name] = tool.name


    return ollama_tools, tool_mapping




# =====================
# 调用LLM
# =====================

def ask_ollama(messages, tools):

    response = requests.post(

        f"{BASE_URL.rstrip('/')}/api/chat",

        json={
            "model": MODEL,
            "messages": messages,
            "tools": tools,
            "stream": False,
        },

        timeout=120,

    )


    response.raise_for_status()


    return response.json()["message"]





# =====================
# MCP结果格式化
# =====================

def format_tool_result(result):

    parts = []


    for item in result.content:

        if getattr(item, "text", None) is not None:

            parts.append(item.text)

        else:

            parts.append(str(item))


    if getattr(result, "isError", False):

        return "工具执行失败：" + "\n".join(parts)


    return "\n".join(parts) if parts else "工具没有返回内容"





async def main():


    if not BASE_URL or not MODEL:

        raise ValueError(
            "没有读取到 BASE_URL 或 MODEL，请检查 .env"
        )



    server_path = Path(__file__).with_name(
        "mcp_server.py"
    )



    server_params = StdioServerParameters(

        command=sys.executable,

        args=[
            str(server_path)
        ],

    )



    print(f"当前模型：{MODEL}")

    print("正在连接 MCP Server……")




    async with stdio_client(server_params) as (

        read_stream,

        write_stream,

    ):


        async with ClientSession(

            read_stream,

            write_stream,

        ) as session:



            await session.initialize()



            # =====================
            # MCP工具发现
            # =====================

            tools_result = await session.list_tools()



            ollama_tools, tool_mapping = convert_mcp_tools(

                tools_result.tools

            )



            print("\n=== 可用 MCP 工具 ===")



            for tool in ollama_tools:

                function = tool["function"]

                print(
                    f"- {function['name']}: {function['description']}"
                )





            # =====================
            # 多轮对话循环
            # =====================

            while True:



                user_input = input(

                    "\n请输入问题（输入 exit 退出）："

                ).strip()



                if not user_input:

                    continue



                if user_input.lower() == "exit":

                    print("退出 Agent。")

                    break




                # =====================
                # 保存用户消息
                # =====================

                add_message(

                    "user",

                    user_input

                )



                messages = get_messages()




                # =====================
                # Agent执行循环
                # =====================

                for round_number in range(

                    MAX_TOOL_ROUNDS + 1

                ):



                    message = await asyncio.to_thread(

                        ask_ollama,

                        messages,

                        ollama_tools,

                    )



                    messages.append(message)




                    tool_calls = message.get(

                        "tool_calls"

                    ) or []





                    # =====================
                    # 没有工具调用
                    # =====================

                    if not tool_calls:



                        answer = (

                            message.get("content")

                            or

                            "模型没有返回文本。"

                        )



                        print(

                            "\n=== AI 最终回答 ==="

                        )



                        print(answer)




                        add_message(

                            "assistant",

                            answer

                        )



                        break





                    if round_number >= MAX_TOOL_ROUNDS:



                        print(

                            "达到工具调用次数限制"

                        )

                        break





                    # =====================
                    # 执行MCP工具
                    # =====================

                    for tool_call in tool_calls:



                        function = tool_call["function"]



                        exposed_name = function["name"]



                        arguments = function.get(

                            "arguments",

                            {}

                        )




                        if isinstance(arguments, str):

                            arguments = json.loads(

                                arguments

                            )




                        actual_name = tool_mapping.get(

                            exposed_name

                        )




                        print(

                            f"\n正在调用 MCP 工具：{actual_name}"

                        )


                        print(

                            f"参数：{arguments}"

                        )




                        result = await session.call_tool(

                            actual_name,

                            arguments=arguments,

                        )



                        tool_output = format_tool_result(

                            result

                        )



                        print(

                            f"工具结果：{tool_output}"

                        )





                        messages.append(

                            {

                                "role": "tool",

                                "tool_name": exposed_name,

                                "content": tool_output,

                            }

                        )





if __name__ == "__main__":

    asyncio.run(main())