
# Agent 最大决策次数
MAX_STEP = 15

# 工具执行失败后的最大重试次数
MAX_RETRY = 1


def should_continue(state):
    # 整个计划已经完成，结束工作流
    if state.get("plan_completed", False):
        return "end"

    # 超过最大决策次数，停止继续循环
    step = state.get("step", 0)

    if step > MAX_STEP:
        return "end"

    # 处理工具执行错误
    if state.get("has_error", False):
        retry_cnt = state.get("retry_count", 0)

        if retry_cnt >= MAX_RETRY + 1:
            return "end"

        return "continue"

    # 获取 Brain 决策
    action = state.get("action") or {}
    action_type = action.get("action")

    # Brain 决定最终结束
    if action_type == "final":
        return "end"

    # 这些动作需要交给 Executor 执行
    if action_type in ["mcp", "rag", "tool", "memory", "chat"]:
        return "continue"

    # 未识别的动作不继续执行
    return "end"


def memory_router(state):
    # 存在待处理的记忆操作时，进入记忆保存节点
    if state.get("new_memory"):
        return "save"

    # 普通问题跳过记忆保存
    return "brain"
