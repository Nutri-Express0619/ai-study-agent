from agent.graph import graph
from memory import get_messages, add_message


while True:

    question = input(
        "有什么能帮助您的:"
    )

    if question == "exit":
        break

    # ======================
    # 保存用户输入
    # ======================

    add_message(
        "user",
        question
    )

    # ======================
    # 获取聊天历史
    # ======================

    chat_history = get_messages()

    # ======================
    # Agent初始状态
    # ======================
    state = graph.invoke(

        {
            # 用户问题
            "question":
            question,

            # Agent思考
            "thought":
            None,

            # Agent行动
            "action":
            None,

            # 执行观察

            "observation":
            None,

            # 最终回答
            "answer":
            None,

            # 当前步骤
            "step":
            0,

            # 来源
            "source":
            None,


            # 短期聊天历史
            "chat_history":
            chat_history,


            # 长期记忆

            # brain节点自动读取
            "long_memory":
            None,

            # 是否查询长期记忆
            "memory_used":
            False,

            # Memory模块
            "new_memory":
            None,
            "memory_saved":
            False
        },

        config={

            "configurable":{

                "thread_id":

                "user_001"
            }
        }
    )

    # ======================
    # 获取回答
    # ======================

    answer = state.get(
        "answer"
    )

    if not answer:

        answer = "抱歉，我暂时无法回答这个问题。"

    # ======================
    # 保存AI回答
    # ======================

    add_message(

        "assistant",

        answer

    )

    # ======================
    # 输出
    # ======================

    print("\nAI:")

    print(answer)

    print()