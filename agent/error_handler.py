from agent.logger import log


def error_handler_node(state):
    error = state.get("error")
    retry_count = state.get("retry_count", 0)

    log(
        "ERROR HANDLER",
        {
            "error": error,
            "retry_count": retry_count
        }
    )

    return {
        # 清除本轮错误标志
        "has_error": False,
        "error": None,

        # 清空失败结果，避免旧结果干扰下一轮思考
        "observation": None,
        "answer": None,

        # 保留错误信息，供 Brain 下一轮参考
        "thought": f"""
上一次工具执行失败。
错误原因：{error}
当前重试次数：{retry_count}
最多允许重试1次。
请分析错误并重新规划；重试次数耗尽后必须结束任务。
""",

        # 关键：不要重置重试次数
        "retry_count": retry_count
    }