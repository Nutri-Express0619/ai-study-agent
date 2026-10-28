
from llm import call_llm
import json
from agent.logger import log


MAX_RETRY = 1

# 已注册的 MCP 工具及其参数字段
MCP_TOOLS = {
    "search_knowledge_base": {"query"},
    "get_weather": {"city"},
    "add": {"a", "b"},
}


def clean_search_query(question, tool_name):
    """
    清理用户明确指定知识库搜索工具时的查询参数。
    """
    query = question

    tool_index = query.lower().find(tool_name.lower())
    if tool_index >= 0:
        query = (
            query[:tool_index]
            + query[tool_index + len(tool_name):]
        )

    prefixes = [
        "请帮我",
        "帮我",
        "请调用",
        "调用",
        "请使用",
        "使用",
        "请通过",
        "通过",
    ]

    query = query.strip(" ：:，,。！？!?、\t\n")

    for prefix in prefixes:
        if query.startswith(prefix):
            query = query[len(prefix):].strip(
                " ：:，,。！？!?、\t\n"
            )

    query_prefixes = [
        "搜索一下",
        "查询一下",
        "检索一下",
        "查找一下",
        "搜索",
        "查询",
        "检索",
        "查找",
    ]

    for prefix in query_prefixes:
        if query.startswith(prefix):
            query = query[len(prefix):].strip(
                " ：:，,。！？!?、\t\n"
            )
            break

    query = " ".join(query.split())
    return query


def judge_plan_step(state):
    """
    判断 Planner 当前步骤是否完成。

    返回：
        True：当前步骤完成
        False：当前步骤尚未完成
    """
    plan = state.get("plan") or []
    current_step = state.get("current_plan_step", 1)
    current_task = state.get("current_task")
    observation = state.get("observation")
    has_error = state.get("has_error", False)

    # 没有计划或当前任务时，不擅自判定完成
    if not plan or not current_task:
        return False

    # 执行失败时，不能判定步骤完成
    if has_error:
        return False

    # 尚无执行结果时，当前步骤还没有完成依据
    if not observation:
        return False

    prompt = f"""
你是一个严格的计划步骤完成度评估器。

请判断当前步骤是否已经被执行结果充分完成。

完整计划：
{json.dumps(plan, ensure_ascii=False, indent=2)}

当前步骤编号：
{current_step}

当前步骤任务：
{current_task}

最近一次执行结果：
{json.dumps(observation, ensure_ascii=False, indent=2) if isinstance(observation, (dict, list)) else str(observation)}

判断规则：
1. 只判断当前步骤，不判断整个计划是否完成。
2. 执行结果必须实质性地回应当前任务。
3. 仅仅成功调用工具，不代表任务已经完成。
4. 如果结果只是部分信息、报错、空结果或无关内容，返回 false。
5. 不要因为用户的整体目标很大，就自动判定当前步骤完成。
6. 不确定时返回 false。

只输出合法 JSON：
{{"completed": true}}
或
{{"completed": false}}
"""

    try:
        result = call_llm([
            {
                "role": "system",
                "content": prompt
            }
        ])

        content = result["message"]["content"].strip()
        content = content.replace("```json", "").replace("```", "").strip()

        log("计划步骤完成度原始判断", content)

        parsed = json.loads(content)

        if not isinstance(parsed, dict):
            return False

        return parsed.get("completed") is True

    except Exception as e:
        log("计划步骤完成度判断失败", str(e))
        return False



def think(state):
    question = state["question"]
    observation = state.get("observation")
    has_error = state.get("has_error", False)
    error_msg = state.get("error")
    retry_count = state.get("retry_count", 0)

    # 新增：读取 Planner 生成的计划
    plan = state.get("plan") or []
    current_plan_step = state.get("current_plan_step", 1)

    # 从计划中定位当前任务
    current_task = None

    if isinstance(plan, list):
        for item in plan:
            if (
                isinstance(item, dict)
                and item.get("step") == current_plan_step
            ):
                current_task = item.get("task")
                break

    # 重试次数耗尽，必须结束任务
    if retry_count > MAX_RETRY:
        log("达到最大重试次数，终止任务", retry_count)
        return {
            "reason": "工具调用失败且重试次数已耗尽",
            "action": "final"
        }

    # 已经成功取得工具结果时，结束任务
    
    if (
        not has_error
        and isinstance(observation, dict)
        and observation.get("observation")
        and retry_count == 0
        and not state.get("plan")
    ):
        return {
            "reason": "已有工具结果",
            "action": "final"
        }


    # 确定性识别：用户明确指定 MCP 工具
    # 保留原有行为，避免破坏明确的工具调用请求
    if retry_count == 0 and not has_error:
        for tool_name in MCP_TOOLS:
            if tool_name.lower() in (
                current_task if plan and current_task else question
            ).lower():

                if tool_name == "search_knowledge_base":
                    query = clean_search_query(
                        question,
                        tool_name
                    )

                    if not query:
                        query = question

                    action = {
                        "reason": "用户明确指定 MCP 工具",
                        "action": "mcp",
                        "tool": tool_name,
                        "args": {
                            "query": query
                        }
                    }

                    log("识别到明确的 MCP 工具调用", action)
                    return action

    memory = state.get("memory") or "暂无用户长期记忆"
    step = state.get("step", 0)
    thought = state.get("thought") or "无"
    tool_history = state.get("tool_history") or []

    # 新增：向 Brain 提供计划执行上下文
    if plan and current_task:
        planner_context = f"""
当前计划目标：
{question}

完整执行计划：
{json.dumps(plan, ensure_ascii=False, indent=2)}

当前计划步骤：
第 {current_plan_step} 步

当前步骤任务：
{current_task}

计划执行要求：
1. 优先围绕当前步骤任务决定下一步行动。
2. 不要无故跳过当前步骤，或直接转去完成其他步骤。
3. 如果当前步骤需要查询知识库，可以选择 rag 或 mcp。
4. 如果当前步骤需要调用工具，应选择合适的工具。
5. 如果当前步骤只是分析、理解或整理，可以使用 chat 生成对应内容。
6. 只有当用户的整体目标已经完成，或确实无法继续时，才选择 final。
7. 不要声称已经完成尚未执行的计划步骤。
"""
    else:
        planner_context = """
当前没有可用的执行计划。
请根据用户问题和其他上下文正常决定下一步行动。
"""

    prompt = f"""
你是一个 AI Agent 的大脑，必须根据用户问题和当前状态决定下一步行动。

================
行动类型
================
action 只能是：
- mcp：调用 MCP 工具
- rag：检索本地知识库
- tool：调用本地工具
- memory：查询长期记忆
- chat：普通聊天
- final：结束任务

================
MCP 工具规则
================
可用工具：

1. search_knowledge_base
参数：{{"query": "搜索内容"}}

2. get_weather
参数：{{"city": "城市名称"}}

3. add
参数：{{"a": 10, "b": 20}}

调用 MCP 必须使用以下格式：
{{
  "reason": "调用 MCP 工具",
  "action": "mcp",
  "tool": "search_knowledge_base",
  "args": {{
    "query": "搜索内容"
  }}
}}

禁止把工具名直接作为 action 的值。
如果用户明确要求调用已知 MCP 工具，必须选择 action="mcp"。
不要将明确的 MCP 调用请求改成 memory、rag 或 chat。

================
Planner 计划执行规则
================
{planner_context}

================
错误恢复规则
================
最大重试次数：{MAX_RETRY}
当前重试次数：{retry_count}

如果上一轮工具调用失败：
1. 分析错误信息。
2. 如果仍有重试机会，允许再次尝试。
3. 可以调整参数或方案。
4. retry_count 大于 {MAX_RETRY} 时必须选择 final。

================
其他行动格式
================
RAG：
{{"reason": "查询知识库", "action": "rag"}}

本地工具：
{{"reason": "执行工具", "action": "tool", "tool": "calculator", "args": {{"a": 10, "b": 20}}}}

长期记忆：
{{"reason": "查询用户记忆", "action": "memory"}}

普通聊天：
{{"reason": "普通聊天", "action": "chat"}}

结束任务：
{{"reason": "任务完成", "action": "final"}}

================
输出要求
================
1. 只输出合法 JSON。
2. 不要输出 Markdown 代码块或额外解释。
3. action 必须是规定的行动类型。
4. 不要编造工具名或参数。
5. 不要输出 remember、memory_key、memory_value 等字段。

================
当前上下文
================
用户问题：{question}
当前观察：{observation}
用户长期记忆：{memory}
上一轮思考：{thought}
工具调用历史：{tool_history}
当前步骤：{step}
是否存在错误：{has_error}
上一轮错误信息：{error_msg or "无"}
当前重试次数：{retry_count}
"""

    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    result = call_llm(messages)
    content = result["message"]["content"].strip()

    # 清理模型可能返回的 Markdown 代码块
    content = content.replace("```json", "").replace("```", "").strip()

    log("LLM原始决策", content)

    try:
        action = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        log("LLM输出JSON解析失败", content)
        return {
            "reason": "模型输出不是合法 JSON",
            "action": "final"
        }

    if not isinstance(action, dict):
        log("LLM返回的动作不是JSON对象", action)
        return {
            "reason": "模型返回的动作格式错误",
            "action": "final"
        }

    # 兼容模型错误地把 MCP 工具名写入 action 字段
    action_type = action.get("action")

    if action_type in MCP_TOOLS:
        tool_name = action_type
        args = action.get("args")

        if not isinstance(args, dict):
            args = {
                key: value
                for key, value in action.items()
                if key in MCP_TOOLS[tool_name]
            }

        action = {
            "reason": action.get("reason", "调用 MCP 工具"),
            "action": "mcp",
            "tool": tool_name,
            "args": args
        }

        log("已修正 MCP 动作格式", action)

    # 校验最终动作
    allowed_actions = {
        "mcp", "rag", "tool", "memory", "chat", "final"
    }

    if action.get("action") not in allowed_actions:
        log("未知行动类型，终止任务", action)
        return {
            "reason": "模型返回了不支持的行动类型",
            "action": "final"
        }

    # MCP 参数格式校验
    if action["action"] == "mcp":
        tool_name = action.get("tool")
        args = action.get("args")

        if (
            tool_name not in MCP_TOOLS
            or not isinstance(args, dict)
        ):
            log("MCP工具名或参数格式错误", action)
            return {
                "reason": "MCP 工具名或参数格式错误",
                "action": "final"
            }

        required_args = MCP_TOOLS[tool_name]
        missing_args = required_args - args.keys()

        if missing_args:
            log("MCP工具缺少必需参数", {
                "tool": tool_name,
                "missing_args": list(missing_args)
            })
            return {
                "reason": "MCP 工具缺少必需参数",
                "action": "final"
            }

    return action
