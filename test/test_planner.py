import json
import unittest
from unittest.mock import patch

from agent.planner import plan_task


class TestPlanner(unittest.TestCase):

    @patch("agent.planner.call_llm")
    def test_valid_plan(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {
                "content": json.dumps({
                    "goal": "学习 Python",
                    "plan": [
                        {"step": 1, "task": "学习变量和数据类型"},
                        {"step": 2, "task": "学习条件语句和循环"},
                        {"step": 3, "task": "完成一个小项目"},
                    ],
                }, ensure_ascii=False)
            }
        }

        result = plan_task("帮我制定 Python 学习计划")

        self.assertEqual(result["goal"], "学习 Python")
        self.assertEqual(len(result["plan"]), 3)
        self.assertEqual(
            result["plan"][0],
            {"step": 1, "task": "学习变量和数据类型"},
        )
        self.assertEqual(result["plan"][2]["step"], 3)
        self.assertNotIn("error", result)
        mock_call_llm.assert_called_once()

    @patch("agent.planner.call_llm")
    def test_markdown_json(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {
                "content": '''```json
{
    "goal": "学习 RAG",
    "plan": [
        {"step": 1, "task": "学习 Embedding"},
        {"step": 2, "task": "学习向量检索"}
    ]
}
```'''
            }
        }

        result = plan_task("帮我学习 RAG")

        self.assertEqual(result["goal"], "学习 RAG")
        self.assertEqual(len(result["plan"]), 2)
        self.assertNotIn("error", result)

    @patch("agent.planner.call_llm")
    def test_invalid_json(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {"content": "这不是合法 JSON"}
        }

        result = plan_task("测试任务")

        self.assertEqual(result["goal"], "测试任务")
        self.assertEqual(result["plan"], [])
        self.assertIn("error", result)

    @patch("agent.planner.call_llm")
    def test_missing_fields(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {
                "content": json.dumps({
                    "goal": "学习 Python"
                }, ensure_ascii=False)
            }
        }

        result = plan_task("测试任务")

        self.assertEqual(result["plan"], [])
        self.assertIn("error", result)

    @patch("agent.planner.call_llm")
    def test_invalid_plan_items(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {
                "content": json.dumps({
                    "goal": "学习 Agent",
                    "plan": [
                        {"step": 99, "task": "  学习 Tool Calling  "},
                        {"step": 100, "task": "   "},
                        "无效步骤",
                        {"step": 101, "task": "学习 RAG"},
                    ],
                }, ensure_ascii=False)
            }
        }

        result = plan_task("学习 Agent")

        self.assertEqual(
            result["plan"],
            [
                {"step": 1, "task": "学习 Tool Calling"},
                {"step": 2, "task": "学习 RAG"},
            ],
        )
        self.assertNotIn("error", result)

    @patch("agent.planner.call_llm")
    def test_json_not_dict(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {"content": '["任务一", "任务二"]'}
        }

        result = plan_task("测试任务")

        self.assertEqual(result["plan"], [])
        self.assertIn("error", result)

    @patch("agent.planner.call_llm")
    def test_no_valid_steps(self, mock_call_llm):
        mock_call_llm.return_value = {
            "message": {
                "content": json.dumps({
                    "goal": "学习 Agent",
                    "plan": [
                        {"step": 1, "task": ""},
                        {"step": 2, "task": "   "},
                        {"step": 3},
                    ],
                }, ensure_ascii=False)
            }
        }

        result = plan_task("学习 Agent")

        self.assertEqual(result["goal"], "学习 Agent")
        self.assertEqual(result["plan"], [])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)