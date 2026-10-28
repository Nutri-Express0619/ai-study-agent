from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes import (
    memory_extractor_node,
    planner_node,
    memory_save_node,
    brain_node,
    executor_node,
    plan_progress_node,
    plan_step_judge_node,
    final_summary_node,
)
from agent.error_handler import error_handler_node
from agent.router import should_continue, memory_router


# =====================
# 创建 Graph
# =====================
workflow = StateGraph(AgentState)


# =====================
# 添加节点
# =====================
workflow.add_node("memory_extractor", memory_extractor_node)
workflow.add_node("memory_save", memory_save_node)
workflow.add_node("planner", planner_node)
workflow.add_node("brain", brain_node)
workflow.add_node("executor", executor_node)
workflow.add_node("error_handler", error_handler_node)
workflow.add_node("plan_progress", plan_progress_node)
workflow.add_node("plan_step_judge", plan_step_judge_node)
workflow.add_node("final_summary", final_summary_node)


# =====================
# 入口与 Memory 路由
# =====================
workflow.add_edge(START, "memory_extractor")
workflow.add_conditional_edges(
    "memory_extractor",
    memory_router,
    {"save": "memory_save", "brain": "planner"},
)
workflow.add_edge("memory_save", "planner")


# =====================
# Planner 路由
# =====================
def planner_router(state):
    if state.get("plan_failed", False):
        return "failed"
    if not state.get("plan") or not state.get("current_task"):
        return "failed"
    return "brain"


workflow.add_conditional_edges(
    "planner",
    planner_router,
    {"brain": "brain", "failed": END},
)


# =====================
# Brain 路由
# =====================
workflow.add_conditional_edges(
    "brain",
    should_continue,
    {"continue": "executor", "end": END},
)


# =====================
# Executor 路由
# =====================
def executor_router(state):
    if state.get("has_error", False):
        return "error"
    if state.get("plan") and state.get("current_task"):
        return "judge"
    return "brain"


workflow.add_conditional_edges(
    "executor",
    executor_router,
    {"error": "error_handler", "judge": "plan_step_judge", "brain": "brain"},
)


# =====================
# 计划步骤验收路由
# =====================
def plan_step_judge_router(state):
    if state.get("plan_failed", False):
        return "failed"
    if state.get("plan_step_completed", False):
        return "progress"
    return "brain"


workflow.add_conditional_edges(
    "plan_step_judge",
    plan_step_judge_router,
    {"progress": "plan_progress", "brain": "brain", "failed": END},
)


# =====================
# 计划推进：全部完成后进入最终汇总
# =====================
def plan_progress_router(state):
    if state.get("plan_completed", False):
        return "summary"
    return "brain"


workflow.add_conditional_edges(
    "plan_progress",
    plan_progress_router,
    {"summary": "final_summary", "brain": "brain"},
)
workflow.add_edge("final_summary", END)


# =====================
# 错误恢复后重新进入 Brain
# =====================
workflow.add_edge("error_handler", "brain")


# =====================
# 编译 Graph，启用 Checkpoint
# =====================
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
