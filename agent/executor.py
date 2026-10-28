import asyncio
from rag.retriever import search
from llm import call_llm
from tools.registry import tool_registry
from long_memory import get_user_memory
from agent.logger import log
from agent.mcp_client import MCPClient
# =====================
# MCP Tool调用
# =====================
def call_mcp_tool(
        tool_name,
        args
):
    async def run():
        client = MCPClient()
        await client.connect()
        result = await client.call_tool(
            tool_name,
            args
        )
        output = []
        for item in result.content:
            if hasattr(item, "text"):
                output.append(
                    item.text
                )
        await client.disconnect()
        return "\n".join(output)
    return asyncio.run(
        run()
    )
def execute(state):
    action = state["action"]
    action_type = action["action"]
    question = state["question"]
    # =====================
    # RAG
    # =====================
    
    # =====================
    # RAG
    # =====================
    if action_type == "rag":
        # 优先执行 Planner 指定的当前任务
        current_task = state.get("current_task")

        task = (
            current_task.strip()
            if isinstance(current_task, str) and current_task.strip()
            else question
        )

        log(
            "RAG执行任务",
            task
        )

        # 使用当前任务进行知识检索
        docs = search(task)

        log(
            "检索结果",
            docs
        )

        context = "\n".join(docs)

        messages = [
            {
                "role": "system",
                "content": """
你是AI学习助手。

回答规则：
1. 优先参考检索资料。
2. 当前任务是本轮需要完成的具体目标。
3. 围绕当前任务回答，不要提前展开后续计划步骤。
4. 技术问题可以结合已有知识回答。
5. 不得编造检索资料中没有的用户个人信息。
6. 如果资料不足，可以结合可靠的技术知识回答，并明确区分资料内容与补充解释。
7. 使用清晰、自然的中文。
"""
            },
            {
                "role": "user",
                "content": f"""
用户的原始问题：
{question}

Planner当前任务：
{task}

参考资料：
{context}

请优先完成Planner当前任务。如果原始问题还有其他部分需要处理，留给后续步骤。
"""
            }
        ]

        result = call_llm(messages)
        answer = result["message"]["content"]

        return {
            "source": "rag",
            "memory_used": state.get("memory_used", False),
            "observation": {
                "observation": context,
                "answer": answer
            },
            "answer": answer,
            "retry_count": state.get("retry_count", 0)
        }

    # =====================
    # Memory
    # =====================
    elif action_type == "memory":
        user_id = "user_001"
        user_memory = get_user_memory(
            user_id
        )
        log(
            "长期记忆",
            user_memory
        )
        messages = [
            {
                "role": "system",
                "content":
                    """
你是AI学习助手。
只能根据长期记忆回答。
禁止编造。
"""
            },
            {
                "role": "user",
                "content":
                    f"""
长期记忆：
{user_memory}
问题：
{question}
"""
            }
        ]
        result = call_llm(
            messages
        )
        answer = result["message"]["content"]
        return {
            "source": "memory",
            "memory_used": True,
            "observation": {
                "observation":
                    user_memory,
                "answer":
                    answer
            },
            "answer":
                answer,
            "retry_count": state.get("retry_count", 0)
        }
    # =====================
    # MCP
    # =====================
    elif action_type == "mcp":
        tool_name = action.get(
            "tool"
        )
        args = action.get(
            "args",
            {}
        )
        log(
            "调用MCP工具",
            tool_name
        )
        log(
            "MCP参数",
            args
        )
        try:

            # 临时制造一次错误，用于测试
            # raise Exception("测试错误恢复")
        
            result = call_mcp_tool(
                tool_name,
                args
            )
        except Exception as e:
            error_message = (
                f"MCP调用失败:{e}"
            )
            log(
                "MCP错误",
                error_message
            )
            return {
                "source":
                    "mcp",
                "observation": {
                    "observation":
                        error_message,
                    "answer":
                        ""
                },
                "error":
                    error_message,
                "has_error":
                    True,
                "tool_history":
                    state.get(
                        "tool_history",
                        []
                    )
                    +
                    [
                        {
                            "tool":
                                tool_name,
                            "args":
                                args,
                            "error":
                                error_message
                        }
                    ],
                "answer":
                    ""
            }
        log(
            "MCP原始结果",
            result
        )
        # =====================
        # MCP结果整理
        # =====================
        messages = [
            {
                "role":
                    "system",
                "content":
                    """
你是AI学习助手。
你的任务：
根据工具查询结果回答用户问题。
回答规则：
1. 优先回答用户真正询问的内容。
2. 不输出工具原始格式。
3. 不说“根据工具结果”。
4. 不添加资料之外的信息。
5. 不夸张描述人物。
6. 使用简洁自然的中文回答。
"""
            },
            {
                "role":
                    "user",
                "content":
                    f"""
用户问题：
{question}
工具查询结果：
{result}
请生成最终回答。
"""
            }
        ]
        final_result = call_llm(
            messages
        )
        answer = final_result["message"]["content"]
        return {
            "source":
                "mcp",
            "memory_used":
                state.get(
                    "memory_used",
                    False
                ),
            "observation": {
                "observation":
                    result,
                "answer":
                    answer
            },
            "tool_history":
                state.get(
                    "tool_history",
                    []
                )
                +
                [
                    {
                        "tool":
                            tool_name,
                        "args":
                            args,
                        "result":
                            result
                    }
                ],
            "has_error":
                False,
            "error":
                None,
            "retry_count": state.get("retry_count", 0), # 修复：不再硬编码0
            "answer":
                answer
        }
        # =====================
    # 本地 Tool
    # =====================
    elif action_type == "tool":
        tool_name = action.get("tool")
        args = action.get("args", {})

        log("调用本地工具", tool_name)
        log("工具参数", args)

        # 1. 检查工具是否存在
        if tool_name not in tool_registry:
            error_message = f"不存在工具: {tool_name}"

            log("本地工具错误", error_message)

            return {
                "source": "tool",
                "observation": {
                    "observation": error_message,
                    "answer": ""
                },
                "answer": "",
                "has_error": True,
                "error": error_message
            }

        # 2. 执行本地工具
        tool_function = tool_registry[tool_name]

        try:
            result = tool_function(**args)

        except Exception as e:
            error_message = f"本地工具执行失败: {e}"

            log("本地工具错误", error_message)

            return {
                "source": "tool",
                "observation": {
                    "observation": error_message,
                    "answer": ""
                },
                "answer": "",
                "has_error": True,
                "error": error_message
            }

        # 3. 工具执行成功
        log("本地工具执行成功", result)

        return {
            "source": "tool",
            "observation": {
                "observation": result,
                "answer": str(result)
            },
            "answer": str(result),
            "has_error": False,
            "error": None,
            "retry_count": state.get("retry_count", 0)
        }
    # =====================
    # Chat
    # =====================
    
    # =====================
    # Chat
    # =====================
    elif action_type == "chat":
        # 优先使用 Planner 当前步骤作为任务
        current_task = state.get("current_task")

        task = (
            current_task.strip()
            if isinstance(current_task, str) and current_task.strip()
            else question
        )

        # 获取上一步的执行结果
        observation = state.get("observation")

        if isinstance(observation, dict):
            previous_result = (
                observation.get("answer")
                or observation.get("observation")
                or "暂无上一步执行结果"
            )
        else:
            previous_result = (
                str(observation)
                if observation
                else "暂无上一步执行结果"
            )

        messages = [
            {
                "role": "system",
                "content": f"""
你是 AI Study Agent 的执行模块。

请完成当前任务，不要擅自跳过 Planner 的当前步骤。

用户的完整问题：
{question}

当前计划任务：
{task}

上一步执行结果：
{previous_result}

执行要求：
1. 优先完成当前计划任务。
2. 如果上一步提供了检索结果或工具结果，应充分利用。
3. 不要编造上一步没有提供的信息。
4. 如果当前任务是总结、解释或整理，请基于已有结果完成。
5. 只输出当前任务所需的结果。
"""
            }
        ]

        result = call_llm(messages)
        answer = result["message"]["content"]

        log(
            "Chat执行结果",
            {
                "task": task,
                "answer": answer
            }
        )

        return {
            "source": "chat",
            "observation": {
                "observation": "普通聊天",
                "answer": answer
            },
            "answer": answer,
            "retry_count": state.get("retry_count", 0)
        }

    # =====================
    # Error
    # =====================
    else:
        return {
            "source": "unknown",
            "observation": {
                "observation":
                    "未知行动",
                "answer":
                        "无法处理"
            },
            "answer":
                "无法处理",
            "retry_count": state.get("retry_count", 0)
        }
