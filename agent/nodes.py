
import json

from agent.brain import think, judge_plan_step
from agent.executor import execute
from agent.memory_extractor import extract_memory
from agent.planner import plan_task
from agent.logger import log
from llm import call_llm

from long_memory import (
    add_memory,
    update_memory,
    delete_memory,
    get_user_memory
)


# =====================
# 判断用户是否明确提出记忆操作
# =====================
def is_explicit_memory_request(question):
    """
    只识别明确的长期记忆操作意图。
    这是一层简单的规则防线，不替代 Memory Extractor。
    """

    text = question.strip()

    if not text:
        return False

    # 明确的记忆保存意图
    add_patterns = (
        "记住",
        "请记住",
        "帮我记住",
        "记一下",
        "记下来",
        "把这个记下来",
        "保存到记忆",
        "存入记忆",
        "记到长期记忆",
    )

    # 明确的记忆修改意图
    update_patterns = (
        "把我的",
        "修改我的记忆",
        "更新我的记忆",
        "更改我的记忆",
        "以前喜欢",
        "现在改成",
        "把之前的",
    )

    # 明确的记忆删除意图
    delete_patterns = (
        "忘记我的",
        "删除我的记忆",
        "删掉我的记忆",
        "删除关于我的",
        "忘掉关于我的",
    )

    patterns = (
        add_patterns
        + update_patterns
        + delete_patterns
    )

    return any(pattern in text for pattern in patterns)


# =====================
# Memory Extractor 节点
# =====================
def memory_extractor_node(state):
    question = state.get("question", "")

    # 普通任务不进入记忆提取流程
    if not is_explicit_memory_request(question):
        log(
            "MEMORY SKIPPED",
            {
                "reason": "用户没有明确提出记忆操作",
                "question": question
            }
        )

        return {
            "new_memory": None,
            "memory_source": None,
            "remember": False
        }

    # 只有明确提出记忆操作时才调用 LLM
    result = extract_memory(state)

    remember = result.get("remember", False)
    new_memory = result.get("new_memory")

    # 再做一次基本结构校验
    if not remember or not isinstance(new_memory, dict):
        return {
            "new_memory": None,
            "memory_source": question,
            "remember": False
        }

    if new_memory.get("action") not in {
        "add",
        "update",
        "delete"
    }:
        return {
            "new_memory": None,
            "memory_source": question,
            "remember": False
        }

    return {
        "new_memory": new_memory,
        "memory_source": question,
        "remember": True
    }



# =====================
# Planner 节点
# =====================

def planner_node(state):
    question = state.get("question", "")

    log("PLANNER INPUT", question)

    result = plan_task(question)
    plan = result.get("plan", [])

    # 计划生成失败：明确记录状态，不伪装成完成。
    if not plan:
        error_message = result.get(
            "error",
            "未生成有效计划"
        )

        log("PLANNER FAILED", error_message)

        return {
            "plan": [],
            "plan_results": [],
            "current_plan_step": 0,
            "current_task": None,
            "plan_step_completed": False,
            "plan_step_retry_count": 0,
            "plan_completed": False,
            "plan_failed": True,
            "answer": f"计划生成失败：{error_message}"
        }

    # 找到第一步任务。
    first_task = next(
        (
            item.get("task")
            for item in plan
            if (
                isinstance(item, dict)
                and item.get("step") == 1
            )
        ),
        None
    )

    # 计划没有有效的第一步任务时，终止计划。
    if not first_task:
        log("PLANNER FAILED", "计划中没有有效的第一步任务")

        return {
            "plan": [],
            "plan_results": [],
            "current_plan_step": 0,
            "current_task": None,
            "plan_step_completed": False,
            "plan_step_retry_count": 0,
            "plan_completed": False,
            "plan_failed": True,
            "answer": "计划生成失败：没有有效的第一步任务。"
        }

    log("PLANNER GOAL", result.get("goal"))
    log("PLANNER PLAN", plan)
    log("PLANNER CURRENT TASK", first_task)

    return {
        "plan": plan,
        "plan_results": [],
        "current_plan_step": 1,
        "current_task": first_task,
        "plan_step_completed": False,
        "plan_step_retry_count": 0,
        "plan_completed": False,
        "plan_failed": False,
        "observation": None,
        "action": {},
        "has_error": False,
        "error": None,
        "retry_count": 0
    }




# =====================
# Brain 节点
# =====================


def brain_node(state):
    user_id = "user_001"

    long_memory = get_user_memory(user_id)
    state["memory"] = long_memory

    # Brain 只负责决策，不在这里判断上一步是否完成。
    action = think(state)

    log(
        "Brain决策",
        {
            "current_plan_step": state.get("current_plan_step"),
            "current_task": state.get("current_task"),
            "action": action.get("action"),
            "reason": action.get("reason")
        }
    )

    return {
        "action": action,
        "thought": action.get("reason"),
        "long_memory": long_memory,
        "step": state.get("step", 0) + 1,
        "has_error": state.get("has_error", False),
        "error": state.get("error"),
        "retry_count": state.get("retry_count", 0)
    }


# =====================
# Executor 节点
# =====================
def executor_node(state):
    result = execute(state)

    current_retry = state.get("retry_count", 0)
    has_error = result.get("has_error", False)

    if has_error:
        new_retry = current_retry + 1
    else:
        new_retry = current_retry

    return {
        # 执行结果
        "observation": result.get("observation"),

        # 最终回答
        "answer": result.get("answer"),

        # 来源
        "source": result.get("source"),

        # Tool 调用历史
        "tool_history": result.get(
            "tool_history",
            state.get("tool_history", [])
        ),

        # 错误恢复
        "has_error": result.get("has_error", False),
        "error": result.get("error"),

        # 更新重试计数器
        "retry_count": new_retry
    }


# =====================
# Memory 保存节点
# =====================
def memory_save_node(state):
    remember = state.get("remember", False)
    new_memory = state.get("new_memory")

    log(
        "MEMORY SAVE",
        {
            "remember": remember,
            "new_memory": new_memory
        }
    )

    if not remember or not new_memory:
        return {
            "memory_saved": False,
            "answer": None,
            "retry_count": state.get("retry_count", 0)
        }

    user_id = "user_001"

    action = new_memory.get("action", "add")
    key = new_memory.get("key")
    value = new_memory.get("value")
    old_value = new_memory.get("old_value")
    new_value = new_memory.get("new_value")

    if action == "add":
        add_memory(user_id, key, value)
        answer = f"好的，我已经记住你的{key}：{value}。"

    elif action == "update":
        update_memory(
            user_id,
            key,
            old_value,
            new_value
        )

        answer = (
            f"好的，我已经把你的"
            f"{old_value}"
            f"修改为"
            f"{new_value}。"
        )

    elif action == "delete":
        delete_memory(user_id, key, value)
        answer = f"好的，我已经删除你的{value}记录。"

    else:
        answer = "未知记忆操作。"

    log(
        "MEMORY SAVED",
        {
            "action": action,
            "key": key,
            "value": value
        }
    )

    return {
        "memory_saved": True,
        "remember": False,
        "new_memory": None,
        "long_memory": get_user_memory(user_id),
        "answer": answer,
        "retry_count": state.get("retry_count", 0)
    }




def plan_progress_node(state):
    """
    根据当前步骤完成状态推进 Planner 计划。
    只有当前步骤验收通过，才允许推进到下一步。
    """
    plan = state.get("plan") or []
    current_step = state.get("current_plan_step", 1)
    completed = state.get("plan_step_completed", False)

    if not plan:
        log("计划推进", "没有计划，保持原状态")
        return {}

    if not completed:
        log(
            "计划推进",
            f"步骤 {current_step} 尚未完成，暂不推进"
        )
        return {}

    current_index = None

    for index, item in enumerate(plan):
        if (
            isinstance(item, dict)
            and item.get("step") == current_step
        ):
            current_index = index
            break

    if current_index is None:
        log("计划推进", f"找不到步骤 {current_step}")
        return {}

    # 还有后续步骤，进入下一步。
    if current_index + 1 < len(plan):
        next_item = plan[current_index + 1]
        next_step = next_item.get("step", current_step + 1)
        next_task = next_item.get("task")

        log(
            "计划推进",
            {
                "完成步骤": current_step,
                "下一步骤": next_step,
                "下一任务": next_task
            }
        )

        return {
            "current_plan_step": next_step,
            "current_task": next_task,
            "plan_step_completed": False,
            "plan_step_retry_count": 0,
            "plan_completed": False,
            "plan_failed": False,
            "observation": None,
            "action": {},
            "has_error": False,
            "error": None,
            "retry_count": 0,
            "answer": None
        }

    # 最后一步完成：保留最后一步编号，结束整个计划。
    log("计划推进", "所有计划步骤均已完成")

    return {
        "current_plan_step": current_step,
        "current_task": None,
        "plan_step_completed": True,
        "plan_completed": True,
        "plan_failed": False,
        "action": {
            "action": "final",
            "reason": "所有计划步骤均已完成"
        }
    }


def plan_step_judge_node(state):
    """
    判断当前计划步骤是否完成。
    验收失败时，独立记录步骤重试次数。
    """
    plan = state.get("plan") or []
    current_task = state.get("current_task")

    # 没有当前计划任务，不进行验收。
    if not plan or not current_task:
        log("计划步骤判断", "没有当前计划任务")
        return {
            "plan_step_completed": False
        }

    # 工具执行错误由现有 error_handler 处理。
    # 不把工具错误计入步骤验收重试次数。
    if state.get("has_error", False):
        log("计划步骤判断", "执行发生错误，交由错误恢复流程处理")
        return {
            "plan_step_completed": False
        }

    completed = judge_plan_step(state)

    current_retry = state.get(
        "plan_step_retry_count",
        0
    ) or 0

    # 验收通过，允许后续节点推进计划。
    if completed:
        log(
            "计划步骤判断",
            {
                "步骤": state.get("current_plan_step"),
                "结果": "验收通过",
                "重试次数": current_retry
            }
        )

        # 只有验收通过后，才把当前步骤记入结果列表。
        # 这样验收失败重试时，不会把失败尝试当作正式结果。
        plan_results = list(state.get("plan_results") or [])
        current_step = state.get("current_plan_step", 1)

        # 防止同一步骤意外重复记录：已存在则更新，不存在则追加。
        step_result = {
            "step": current_step,
            "task": current_task,
            "observation": state.get("observation"),
            "answer": state.get("answer"),
            "source": state.get("source"),
        }

        existing_index = next(
            (
                index
                for index, item in enumerate(plan_results)
                if isinstance(item, dict) and item.get("step") == current_step
            ),
            None
        )

        if existing_index is None:
            plan_results.append(step_result)
        else:
            plan_results[existing_index] = step_result

        log(
            "计划步骤结果已保存",
            {
                "步骤": current_step,
                "任务": current_task,
                "来源": state.get("source"),
                "结果数量": len(plan_results),
            }
        )

        return {
            "plan_step_completed": True,
            "plan_results": plan_results,
        }

    # 验收未通过，增加独立的重试计数。
    new_retry = current_retry + 1

    # 初次执行不通过后，允许再尝试两次。
    max_retries = 2

    log(
        "计划步骤判断",
        {
            "步骤": state.get("current_plan_step"),
            "任务": current_task,
            "结果": "验收未通过",
            "当前重试次数": new_retry,
            "最大重试次数": max_retries
        }
    )

    # 重试耗尽：明确标记计划失败，不能伪装成完成。
    if new_retry > max_retries:
        log(
            "计划步骤判断",
            f"步骤 {state.get('current_plan_step')} 重试次数耗尽，计划终止"
        )

        return {
            "plan_step_completed": False,
            "plan_step_retry_count": new_retry,
            "plan_completed": False,
            "plan_failed": True,
            "current_task": None,
            "answer": (
                f"计划未能完成：第 "
                f"{state.get('current_plan_step')} 步"
                f"「{current_task}」连续未通过验收，"
                f"已达到最大重试次数（{max_retries} 次）。"
            ),
            "action": {
                "action": "final",
                "reason": "计划步骤验收失败，重试次数耗尽"
            }
        }

    # 还有重试机会，保留当前任务并返回 Brain 再次决策。
    return {
        "plan_step_completed": False,
        "plan_step_retry_count": new_retry
    }

# =====================
# 最终答案汇总节点
# =====================
def final_summary_node(state):
    """
    汇总计划执行结果，并校验用户明确提出的输出约束。
    当前支持：
    1. 指定句子数量
    2. 指定要点数量
    3. JSON 格式
    4. 校验失败后最多修正两次
    """
    import re

    question = state.get("question", "")
    plan_results = state.get("plan_results") or []

    log(
        "FINAL SUMMARY INPUT",
        {"question": question, "result_count": len(plan_results)},
    )

    if not plan_results:
        return {
            "answer": (
                "计划执行已结束，但没有可用于汇总的步骤结果。"
                "请检查 Planner、步骤验收以及 plan_results 的保存逻辑。"
            ),
            "source": "planner_summary",
            "has_error": True,
            "error": "没有可用于汇总的步骤结果。",
        }

    results_text = json.dumps(
        plan_results,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    chinese_numbers = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }

    def parse_number(value):
        if value.isdigit():
            return int(value)
        return chinese_numbers.get(value)

    constraints = {
        "sentence_count": None,
        "bullet_count": None,
        "json_required": bool(
            re.search(r"\bjson\b", question, re.IGNORECASE)
        ),
    }

    # 识别“用三句话回答”“控制在 5 个句子”等要求。
    sentence_match = re.search(
        r"([一二两三四五六七八九十\d]+)\s*(?:句话|个句子)",
        question,
    )

    if sentence_match:
        constraints["sentence_count"] = parse_number(
            sentence_match.group(1)
        )

    # 只在用户明确要求列点、要点或条目时识别数量。
    if re.search(r"列出|要点|条目|项目|分点|几点", question):
        bullet_match = re.search(
            r"([一二两三四五六七八九十\d]+)\s*"
            r"(?:个要点|条要点|个条目|条目|个项目|项|点|条)",
            question,
        )

        if bullet_match:
            constraints["bullet_count"] = parse_number(
                bullet_match.group(1)
            )

    log("OUTPUT CONSTRAINTS", constraints)

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个严谨的 AI 学习助手。"
                "请直接回答用户的原始问题，并严格遵守用户明确提出的"
                "句子数量、要点数量、格式、语言和详细程度要求。"
                "只使用已完成计划步骤中有依据的信息，不得编造事实。"
                "不要逐步复述计划执行过程。"
                "只输出最终回答正文，不输出分析过程。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"用户原始问题：\n{question}\n\n"
                f"计划执行结果：\n{results_text}\n\n"
                "请综合以上信息直接回答用户的问题，"
                "优先满足用户明确指定的输出约束。"
            ),
        },
    ]

    def validate_answer(answer):
        """返回未通过的约束；空列表表示通过当前可检查的规则。"""
        errors = []
        checked_answer = answer.strip()

        expected_sentences = constraints["sentence_count"]

        if expected_sentences is not None:
            # 统计常见中英文句末标点，忽略小数点。
            endings = re.findall(
                r"[。！？!?]+|(?<!\d)\.(?=\s|$)",
                checked_answer,
            )
            actual_sentences = len(endings)

            if actual_sentences != expected_sentences:
                errors.append(
                    f"用户要求 {expected_sentences} 句话，"
                    f"当前检测到 {actual_sentences} 句。"
                )

        expected_bullets = constraints["bullet_count"]

        if expected_bullets is not None:
            bullet_lines = re.findall(
                r"(?m)^\s*(?:[-*•]\s+|\d+[.、)]\s+)",
                checked_answer,
            )

            if len(bullet_lines) != expected_bullets:
                errors.append(
                    f"用户要求 {expected_bullets} 个要点，"
                    f"当前检测到 {len(bullet_lines)} 个列表项。"
                )

        if constraints["json_required"]:
            json_text = checked_answer

            # 兼容 Markdown 代码围栏包裹的 JSON。
            if json_text.startswith("```"):
                json_text = re.sub(
                    r"^```(?:json)?\s*|\s*```$",
                    "",
                    json_text,
                    flags=re.IGNORECASE,
                ).strip()

            try:
                json.loads(json_text)
            except (json.JSONDecodeError, TypeError):
                errors.append(
                    "用户要求 JSON，但当前输出不是有效 JSON。"
                )

        return errors

    answer = ""
    last_errors = []

    # 总共最多生成三次：首次生成一次，失败后最多修正两次。
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = call_llm(messages)
            answer = (
                (response.get("message") or {})
                .get("content", "")
                .strip()
            )

            if not answer:
                raise ValueError("LLM 返回内容为空")

        except Exception as exc:
            log("FINAL SUMMARY FAILED", str(exc))
            last_errors = ["最终答案生成失败。"]
            break

        errors = validate_answer(answer)
        last_errors = errors

        log(
            "OUTPUT VALIDATION",
            {
                "attempt": attempt + 1,
                "passed": not errors,
                "errors": errors,
            },
        )

        if not errors:
            log(
                "FINAL SUMMARY COMPLETED",
                {"answer_length": len(answer)},
            )
            return {
                "answer": answer,
                "source": "planner_summary",
                "has_error": False,
                "error": None,
            }

        if attempt == max_attempts - 1:
            break

        # 将校验失败原因反馈给模型，让模型修正答案。
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个回答格式修正器。"
                    "请根据校验错误修正原答案，同时保留有依据的事实。"
                    "必须严格遵守用户的原始要求。"
                    "只输出修正后的完整答案，不要解释修改过程。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"用户原始问题：\n{question}\n\n"
                    f"原答案：\n{answer}\n\n"
                    f"校验错误：\n"
                    f"{json.dumps(errors, ensure_ascii=False)}\n\n"
                    "请修正所有列出的错误，并只返回最终答案。"
                ),
            },
        ]

    log(
        "OUTPUT VALIDATION FAILED",
        {"errors": last_errors},
    )

    if answer:
        return {
            "answer": answer,
            "source": "planner_summary",
            "has_error": True,
            "error": (
                "最终答案未通过输出约束校验，"
                "或生成过程中发生错误。"
            ),
        }

    return {
        "answer": None,
        "source": "planner_summary",
        "has_error": True,
        "error": "最终答案生成失败。",
    }
