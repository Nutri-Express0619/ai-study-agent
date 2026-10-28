
from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    # 用户问题
    question: str

    # Agent 思考
    thought: Optional[str]

    # Agent 行动
    action: Optional[dict]

    # 执行观察结果
    observation: Optional[dict]

    # 错误恢复
    has_error: Optional[bool]
    error: Optional[str]

    # Tool 调用历史
    tool_history: Optional[List[dict]]

    # 最终回答
    answer: Optional[str]

    # Agent 决策次数
    step: int

    # 来源：rag / memory / tool / chat
    source: Optional[str]

    # 短期聊天历史
    chat_history: Optional[List[dict]]

    # 长期记忆
    long_memory: Optional[dict]

    # Memory Extractor
    remember: Optional[bool]

    # 记忆操作
    new_memory: Optional[dict]

    # 触发记忆的原始文本
    memory_source: Optional[str]

    # Memory 保存结果
    memory_saved: Optional[bool]

    # 是否使用长期记忆回答
    memory_used: Optional[bool]

    # 工具执行错误的重试次数
    retry_count: Optional[int]

    # Planner：完整任务计划
    plan: Optional[List[dict]]

    # Planner：当前计划步骤，从 1 开始
    current_plan_step: Optional[int]

    # Planner：当前步骤的具体任务
    current_task: Optional[str]

    # 当前步骤是否完成
    plan_step_completed: Optional[bool]

    # 当前步骤验收失败后的重试次数
    plan_step_retry_count: Optional[int]

    # 整个计划是否完成
    plan_completed: Optional[bool]

    # 整个计划是否因步骤未完成而失败
    plan_failed: Optional[bool]

    # Planner：保存每个步骤的执行结果
    # 每项可以记录步骤编号、任务、执行结果、回答和来源
    plan_results: Optional[List[dict]]
