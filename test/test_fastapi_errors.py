from fastapi.testclient import TestClient

import fastapi_app


def test_empty_answer_returns_502(monkeypatch):
    """模拟 Agent 返回空答案，验证 FastAPI 的错误响应。"""

    def fake_invoke(initial_state, config=None):
        return {
            **initial_state,
            "has_error": False,
            "answer": None,
            "error": None,
            "source": None,
        }

    monkeypatch.setattr(fastapi_app.graph, "invoke", fake_invoke)

    client = TestClient(fastapi_app.app)
    response = client.post(
        "/chat",
        json={"question": "测试空答案异常"},
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "EMPTY_ANSWER"
    assert response.json()["detail"]["message"] == "AI 助手未能生成有效回答。"

def test_output_constraint_failure_returns_502(monkeypatch):
    """模拟最终答案校验失败，验证 FastAPI 的错误响应。"""

    def fake_invoke(initial_state, config=None):
        return {
            **initial_state,
            "has_error": True,
            "answer": None,
            "error": "答案未满足三句话约束",
            "source": "planner_summary",
        }

    monkeypatch.setattr(fastapi_app.graph, "invoke", fake_invoke)

    client = TestClient(fastapi_app.app)
    response = client.post(
        "/chat",
        json={"question": "测试输出约束失败"},
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == (
        "OUTPUT_CONSTRAINT_VALIDATION_FAILED"
    )
    assert response.json()["detail"]["message"] == "答案未满足三句话约束"

def test_langgraph_exception_returns_500(monkeypatch):
    """模拟 LangGraph 执行异常，验证 FastAPI 的错误响应。"""

    def fake_invoke(initial_state, config=None):
        raise RuntimeError("模拟 LangGraph 执行异常")

    monkeypatch.setattr(fastapi_app.graph, "invoke", fake_invoke)

    client = TestClient(fastapi_app.app)
    response = client.post(
        "/chat",
        json={"question": "测试 LangGraph 异常"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "AI 助手执行失败，请检查服务端日志。"
    )