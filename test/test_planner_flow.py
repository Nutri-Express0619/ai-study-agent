import unittest
from unittest.mock import patch

from agent.nodes import (
    plan_progress_node,
    plan_step_judge_node,
)


def make_state(
    current_step=1,
    current_task="学习 Tool Calling",
    plan_step_completed=False,
    plan_completed=False,
    has_error=False,
):
    """构造 Planner 节点测试所需的最小状态。"""
    return {
        "question": "学习 AI Agent",
        "plan": [
            {"step": 1, "task": "学习 Tool Calling"},
            {"step": 2, "task": "学习 RAG"},
            {"step": 3, "task": "学习 LangGraph"},
        ],
        "current_plan_step": current_step,
        "current_task": current_task,
        "plan_step_completed": plan_step_completed,
        "plan_completed": plan_completed,
        "has_error": has_error,
        "error": "模拟执行失败" if has_error else None,
        "retry_count": 0,
        "observation": {"result": "测试结果"},
        "action": {"action": "tool"},
    }


class TestPlannerFlow(unittest.TestCase):

    def test_first_step_advances_to_second(self):
        """第一步完成后，应推进到第二步。"""
        state = make_state(
            current_step=1,
            plan_step_completed=True,
        )

        result = plan_progress_node(state)

        self.assertEqual(result["current_plan_step"], 2)
        self.assertEqual(result["current_task"], "学习 RAG")
        self.assertFalse(result["plan_step_completed"])
        self.assertFalse(result["plan_completed"])
        self.assertIsNone(result["observation"])
        self.assertEqual(result["action"], {})
        self.assertFalse(result["has_error"])
        self.assertIsNone(result["error"])
        self.assertEqual(result["retry_count"], 0)

    def test_middle_step_advances_to_next(self):
        """中间步骤完成后，应推进到第三步。"""
        state = make_state(
            current_step=2,
            current_task="学习 RAG",
            plan_step_completed=True,
        )

        result = plan_progress_node(state)

        self.assertEqual(result["current_plan_step"], 3)
        self.assertEqual(result["current_task"], "学习 LangGraph")
        self.assertFalse(result["plan_completed"])

    def test_last_step_completes_plan(self):
        """最后一步完成后，应结束整个计划。"""
        state = make_state(
            current_step=3,
            current_task="学习 LangGraph",
            plan_step_completed=True,
        )

        result = plan_progress_node(state)

        self.assertEqual(result["current_plan_step"], 3)
        self.assertIsNone(result["current_task"])
        self.assertTrue(result["plan_step_completed"])
        self.assertTrue(result["plan_completed"])
        self.assertEqual(result["action"]["action"], "final")

    def test_incomplete_step_does_not_advance(self):
        """当前步骤未完成时，不应推进。"""
        state = make_state(
            current_step=1,
            plan_step_completed=False,
        )

        result = plan_progress_node(state)

        self.assertEqual(result, {})

    def test_empty_plan_does_not_advance(self):
        """没有计划时，不应推进。"""
        state = make_state()
        state["plan"] = []

        result = plan_progress_node(state)

        self.assertEqual(result, {})

    def test_missing_current_step_does_not_advance(self):
        """当前步骤编号不在计划中时，不应推进。"""
        state = make_state(
            current_step=99,
            plan_step_completed=True,
        )

        result = plan_progress_node(state)

        self.assertEqual(result, {})

    @patch("agent.nodes.judge_plan_step")
    def test_step_judge_uses_judge_result(self, mock_judge):
        """步骤判断节点应使用 judge_plan_step 的结果。"""
        mock_judge.return_value = True
        state = make_state()

        result = plan_step_judge_node(state)

        self.assertTrue(result["plan_step_completed"])
        mock_judge.assert_called_once_with(state)

    @patch("agent.nodes.judge_plan_step")
    def test_failed_execution_cannot_complete_step(self, mock_judge):
        """执行出错时，不应判定步骤完成，也不应调用判断器。"""
        state = make_state(has_error=True)

        result = plan_step_judge_node(state)

        self.assertFalse(result["plan_step_completed"])
        mock_judge.assert_not_called()

    @patch("agent.nodes.judge_plan_step")
    def test_missing_task_cannot_complete_step(self, mock_judge):
        """没有当前任务时，不应判定步骤完成。"""
        state = make_state(current_task=None)

        result = plan_step_judge_node(state)

        self.assertFalse(result["plan_step_completed"])
        mock_judge.assert_not_called()


    @patch("agent.nodes.judge_plan_step")
    def test_failed_judgment_increments_retry_count(self, mock_judge):
        """验收失败时，应增加步骤验收重试次数。"""
        mock_judge.return_value = False

        state = make_state()
        state["plan_step_retry_count"] = 0

        result = plan_step_judge_node(state)

        self.assertFalse(result["plan_step_completed"])
        self.assertEqual(result["plan_step_retry_count"], 1)
        self.assertNotIn("plan_failed", result)

    @patch("agent.nodes.judge_plan_step")
    def test_retry_exhaustion_marks_plan_failed(self, mock_judge):
        """超过允许的额外重试次数后，应明确标记计划失败。"""
        mock_judge.return_value = False

        state = make_state()
        state["plan_step_retry_count"] = 2

        result = plan_step_judge_node(state)

        self.assertFalse(result["plan_step_completed"])
        self.assertEqual(result["plan_step_retry_count"], 3)
        self.assertFalse(result["plan_completed"])
        self.assertTrue(result["plan_failed"])
        self.assertIsNone(result["current_task"])
        self.assertEqual(result["action"]["action"], "final")
        self.assertIn("计划未能完成", result["answer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
