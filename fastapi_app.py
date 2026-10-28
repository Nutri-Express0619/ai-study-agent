from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.graph import graph
from memory import get_messages, add_message


app = FastAPI(
    title="AI Study Agent API",
    description="通过 FastAPI 调用 LangGraph AI 学习助手",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=1000,
        description="用户提出的问题，长度为 1 到 1000 个字符",
    )


@app.get("/")
def home():
    return {
        "message": "AI Study Agent API is running",
        "project": "AI Study Agent",
        "status": "running",
    }


@app.get("/weather")
def get_weather(city: str = "Beijing"):
    return {
        "city": city,
        "weather": "Sunny",
        "temperature": 25,
    }


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="question 不能为空",
        )

    # 1. 保存用户输入
    add_message("user", question)

    # 2. 获取现有聊天历史
    chat_history = get_messages()

    # 3. 构造 Agent 初始状态
    initial_state = {
        "question": question,
        "thought": None,
        "action": None,
        "observation": None,
        "answer": None,
        "step": 0,
        "source": None,
        "chat_history": chat_history,
        "long_memory": None,
        "memory_used": False,
        "new_memory": None,
        "memory_saved": False,
    }

    # 4. 调用真正的 LangGraph
    try:
        state = graph.invoke(
            initial_state,
            config={
                "configurable": {
                    "thread_id": "user_001",
                }
            },
        )
    except Exception:
        # 记录完整异常到服务端日志，不将内部细节直接暴露给客户端
        import logging

        logging.exception("LangGraph 执行失败")

        raise HTTPException(
            status_code=500,
            detail="AI 助手执行失败，请检查服务端日志。",
        )

    # 5. 获取最终回答
    if state.get("has_error", False):
        raise HTTPException(
            status_code=502,
            detail={
            "code": "OUTPUT_CONSTRAINT_VALIDATION_FAILED",
            "message": state.get("error")
            or "AI 助手未能生成符合要求的回答。",
            },
        )

    answer = state.get("answer")

    if not answer:
        raise HTTPException(
        status_code=502,
        detail={
            "code": "EMPTY_ANSWER",
            "message": "AI 助手未能生成有效回答。",
        },
    )

    add_message("assistant", answer)

    return {
        "question": question,
        "answer": answer,
        "source": state.get("source"),
        "status": "success",
    }