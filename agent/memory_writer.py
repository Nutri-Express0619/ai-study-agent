from llm import call_llm
from long_memory import add_memory
import json



def extract_memory(question):


    prompt = f"""

你是一个用户信息提取器。


你的任务：

从用户输入中提取值得长期保存的信息。


只提取：

- 兴趣 hobbies
- 目标 goal
- 姓名 name
- 昵称 nickname


如果没有信息：

返回空JSON。



用户输入：

{question}



返回格式：

{{
    "hobbies":[],
    "goal":"",
    "name":"",
    "nickname":""
}}



只能返回JSON。

"""


    result = call_llm(
        [
            {
                "role":"system",
                "content":prompt
            }
        ]
    )


    content = result["message"]["content"]


    content = content.replace(
        "```json",
        ""
    )

    content = content.replace(
        "```",
        ""
    )


    content = content.strip()



    try:

        memory = json.loads(content)


    except:

        memory = {}



    return memory





def memory_writer_node(state):


    question = state["question"]


    user_id = "user_001"



    memory = extract_memory(
        question
    )



    # 保存

    for key,value in memory.items():


        if value:


            if isinstance(value,list):

                for item in value:

                    add_memory(
                        user_id,
                        key,
                        item
                    )

            else:

                add_memory(
                    user_id,
                    key,
                    value
                )



    return {

        "memory":memory

    }