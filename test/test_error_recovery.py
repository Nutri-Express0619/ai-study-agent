from unittest.mock import patch

from agent.graph import graph


def fake_memory_extractor(state):
    return {
        "remember": False,
        "new_memory": None,
        "memory_source": None,
    }


def fake_planner(state):
    return {
        "plan": [],
        "current_plan_step": 0,
        "current_task": None,
        "plan_step_completed": False,
        "plan_completed": False,
        "retry_count": state.get("retry_count", 0),
    }


def fake_brain(state):
    retry_count = state.get("retry_count", 0)

    if retry_count > 1:
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
    return {
        "has_error": True,
        "error": "模拟工具执行失败",
        "observation": None,
        "answer": None,
        "source": None,
        "tool_history": state.get("tool_history", []),
    }


initial_state = {
    "question": "测试重试次数耗尽",
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

config = {
    "configurable": {
        "thread_id": "test_error_recovery",
    }
}

with (
    patch("agent.nodes.memory_extractor_node", side_effect=fake_memory_extractor),
    patch("agent.nodes.planner_node", side_effect=fake_planner),
    patch("agent.nodes.brain_node", side_effect=fake_brain),
    patch("agent.nodes.execute", side_effect=fake_execute),
):
    result = graph.invoke(initial_state, config=config)

print("最终 action：", result.get("action"))
print("最终 retry_count：", result.get("retry_count"))
print("最终 step：", result.get("step"))

assert result.get("action", {}).get("action") == "final", (
    "失败：Graph 没有以 final 动作结束"
)
assert result.get("retry_count") == 2, (
    "失败：重试次数不是预期的 2"
)

print("✅ 端到端错误恢复测试通过")
