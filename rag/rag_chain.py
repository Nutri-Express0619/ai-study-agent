from rag.retriever import search
from memory import add_message, get_messages
from llm import call_llm



def rag_chat(question):

    # 1. 检索知识库
    docs = search(question)

    context = "\n".join(docs)

    print("======检索结果======")
    print(context)
    print("===================")


    # 2. 获取历史聊天
    messages = get_messages()


    # 3. 创建临时prompt
    rag_prompt = f"""
你是一个知识库问答助手。

请严格根据下面的参考资料回答问题。

规则：
1. 只能使用参考资料中的信息。
2. 不允许使用自己的知识补充。
3. 如果资料没有相关信息，请回答：
"知识库中没有相关信息。"

参考资料：
{context}

用户问题：
{question}
"""


    # 4. 临时组合，不修改memory
    temp_messages = messages + [
        {
            "role":"user",
            "content":rag_prompt
        }
    ]


    # 5. 调LLM
    response = call_llm(temp_messages)


    answer = response["message"]["content"]


    # 6. 保存真实聊天
    add_message(
        "user",
        question
    )

    add_message(
        "assistant",
        answer
    )


    return answer