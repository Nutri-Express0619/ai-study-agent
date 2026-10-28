from unittest.mock import patch

from langgraph.graph import END, START, StateGraph

from agent.state import AgentState
from agent.nodes import executor_node
from agent.error_handler import error_handler_node
from agent.router import should_continue, executor_router


execution_attempts = []


def fake_memory_extractor(state):
    return {
        "remember": False,
        "new_memory": None,
        "memory_source": None,
    }


def fake_planner(state):
    # 测试错误恢复，不调用真实 Planner。
    return {
        "plan": [],
        "current_plan_step": 0,
        "current_task": None,
        "plan_step_completed": False,
        "plan_completed": False,
    }


def fake_brain(state):
    # 模拟 Brain：重试次数达到 2 后结束。
    retry_count = state.get("retry_count", 0)

    if retry_count >= 2:
        action = {
            "action": "final",
            "reason": "重试次数已耗尽，结束任务",
        }
    else:
        action = {
            "action": "mcp",
            "tool": "simulated_failure",
            "args": {},
            "reason": "测试错误恢复",
        }

    return {
        "action": action,
        "thought": action["reason"],
        "step": state.get("step", 0) + 1,
        "has_error": state.get("has_error", False),
        "error": state.get("error"),
        "retry_count": retry_count,
    }


def fake_execute(state):
    # 模拟工具连续失败，不连接真实 MCP。
    execution_attempts.append(state.get("retry_count", 0))

    return {
        "has_error": True,
        "error": "模拟工具执行失败",
        "observation": None,
        "answer": None,
        "source": None,
        "tool_history": state.get("tool_history", []),
    }


builder = StateGraph(AgentState)

builder.add_node("memory_extractor", fake_memory_extractor)
builder.add_node("planner", fake_planner)
builder.add_node("brain", fake_brain)
builder.add_node("executor", executor_node)
builder.add_node("error_handler", error_handler_node)

builder.add_edge(START, "memory_extractor")
builder.add_edge("memory_extractor", "planner")
builder.add_edge("planner", "brain")

builder.add_conditional_edges(
    "brain",
    should_continue,
    {
        "continue": "executor",
        "end": END,
    },
)

builder.add_conditional_edges(
    "executor",
    executor_router,
    {
        "error": "error_handler",
        "judge": "brain",
        "brain": "brain",
    },
)

builder.add_edge("error_handler", "brain")

test_graph = builder.compile()

initial_state = {
    "question": "测试错误恢复",
    "thought": None,
    "action": None,
    "observation": None,
    "answer": None,
    "step": 0,
    "source": None,
    "chat_history": [],
    "long_memory": {},
    "memory_used": False,
    "remember": False,
    "new_memory": None,
    "memory_source": None,
    "memory_saved": False,
    "retry_count": 0,
    "has_error": False,
    "error": None,
    "tool_history": [],
    "plan": [],
    "current_plan_step": 0,
    "current_task": None,
    "plan_step_completed": False,
    "plan_completed": False,
}

with patch("agent.nodes.execute", side_effect=fake_execute):
    result = test_graph.invoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": "isolated_error_recovery_test",
            }
        },
    )

print("工具执行次数：", len(execution_attempts))
print("执行前的重试次数：", execution_attempts)
print("最终 action：", result.get("action"))
print("最终 retry_count：", result.get("retry_count"))

assert execution_attempts == [0, 1], (
    f"预期执行两次，实际记录：{execution_attempts}"
)
assert result.get("action", {}).get("action") == "final", (
    f"预期 action 为 final，实际：{result.get('action')}"
)
assert result.get("retry_count") == 2, (
    f"预期 retry_count 为 2，实际：{result.get('retry_count')}"
)

print("✅ 隔离测试通过")