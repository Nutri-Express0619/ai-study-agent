import json

from llm import call_llm
from agent.logger import log


def is_simple_task(question: str) -> bool:
    """
    使用确定性规则识别简单任务。

    简单任务直接生成单步计划，避免 LLM 将单一问题
    过度拆解为多个子任务。
    """
    text = " ".join(question.strip().split())

    if not text:
        return True

    # 明确包含多个目标或复杂工作要求时，交给 LLM 规划。
    complex_markers = [
        "制定计划",
        "制定方案",
        "设计方案",
        "学习计划",
        "实施方案",
        "比较",
        "对比",
        "分析并",
        "然后",
        "接着",
        "最后",
        "并且",
        "以及",
        "分别查询",
        "多个主题",
        "多个文档",
        "分阶段",
        "第一步",
        "第二步",
    ]

    if any(marker in text for marker in complex_markers):
        return False

    # 包含多个明确目标的常见表达，视为复杂任务。
    multi_goal_markers = [
        "并制定",
        "并设计",
        "并生成",
        "并实现",
        "并完成",
        "再制定",
        "再设计",
        "再生成",
        "再比较",
        "后制定",
        "后总结",
    ]

    if any(marker in text for marker in multi_goal_markers):
        return False

    # 其他未被识别为复杂任务的请求，按单步任务处理。
    return True


def plan_task(question: str) -> dict:
    """
    根据用户任务生成结构化计划。

    简单任务：生成一个步骤，保留用户原始问题。
    复杂任务：交给 LLM 生成多步骤计划。
    """

    # 确定性判断：简单任务不再交给 LLM 拆分。
    if is_simple_task(question):
        result = {
            "goal": question.strip(),
            "plan": [
                {
                    "step": 1,
                    "task": question.strip()
                }
            ]
        }

        log("Planner 识别为简单任务，使用单步计划", result)
        return result

    prompt = f"""
你是一个严谨的 AI Agent 任务规划器 Planner。

你的职责是将复杂任务拆解成清晰、有顺序、可以逐步执行的子任务。

要求：
1. 准确保留用户的真实目标。
2. 复杂任务拆解为 2 到 5 个步骤。
3. 每个步骤只描述一个主要任务。
4. 步骤按照合理的执行顺序排列。
5. 不要擅自增加用户没有要求的目标。
6. 不要编造工具调用结果。
7. 不要因为某个技术名词常见，就将它添加为必做步骤。
8. 每个步骤都必须服务于用户的原始目标。
9. 只输出合法 JSON，不要输出 Markdown 代码块。

输出格式：
{{
    "goal": "用户的最终目标",
    "plan": [
        {{
            "step": 1,
            "task": "第一个子任务"
        }},
        {{
            "step": 2,
            "task": "第二个子任务"
        }}
    ]
}}

用户任务：
{question}
"""

    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    try:
        result = call_llm(messages)
        content = result["message"]["content"].strip()

        # 清理模型可能返回的 Markdown 代码块
        content = content.replace("```json", "").replace("```", "").strip()

        log("Planner 原始输出", content)

        plan_data = json.loads(content)

    except (json.JSONDecodeError, TypeError, KeyError, AttributeError) as e:
        log("Planner 输出解析失败", str(e))
        return {
            "goal": question,
            "plan": [],
            "error": "Planner 返回的内容无法解析"
        }

    except Exception as e:
        log("Planner 调用失败", str(e))
        return {
            "goal": question,
            "plan": [],
            "error": "Planner 调用失败"
        }

    # 校验返回结构
    if not isinstance(plan_data, dict):
        return {
            "goal": question,
            "plan": [],
            "error": "Planner 返回的数据格式错误"
        }

    goal = plan_data.get("goal")
    plan = plan_data.get("plan")

    if not isinstance(goal, str) or not isinstance(plan, list):
        return {
            "goal": question,
            "plan": [],
            "error": "Planner 缺少 goal 或 plan 字段"
        }

    # 校验每个计划步骤
    validated_plan = []

    for item in plan:
        if not isinstance(item, dict):
            continue

        task = item.get("task")

        if not isinstance(task, str) or not task.strip():
            continue

        validated_plan.append({
            "step": len(validated_plan) + 1,
            "task": task.strip()
        })

    if not validated_plan:
        return {
            "goal": goal,
            "plan": [],
            "error": "Planner 没有生成有效的任务步骤"
        }

    final_result = {
        "goal": goal,
        "plan": validated_plan
    }

    log("Planner 生成计划", final_result)

    return final_result