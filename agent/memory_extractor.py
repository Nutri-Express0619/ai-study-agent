from llm import call_llm
import json

from agent.logger import log





def extract_memory(state):


    question = state["question"]



    prompt = f"""

你是一个长期记忆提取器。


你的唯一任务：

判断用户输入是否包含需要长期保存的信息。


================

最高优先级规则（必须遵守）

================


如果用户是在：

- 调用工具
- 查询信息
- 搜索资料
- 请求执行动作
- 使用MCP
- 使用search_knowledge_base
- 查询天气
- 计算数字


这些都不是长期记忆。


例如：


用户：

请调用 search_knowledge_base 查询李子豪学习目标


必须返回：

{{
"remember":false
}}



用户：

帮我查询北京天气


必须返回：

{{
"remember":false
}}



禁止输出：

call_function

tool_call

function_call

mcp

search


这些不是记忆类型。




================

允许保存的记忆

================


只有以下内容可以保存：


1. 用户长期兴趣


例如：

我喜欢篮球


返回：

{{
"remember":true,
"memory_action":"add",
"memory_key":"hobbies",
"memory_value":"篮球"
}}



2. 用户学习目标


例如：

我的目标是成为AI工程师


返回：

{{
"remember":true,
"memory_action":"add",
"memory_key":"learning_goal",
"memory_value":"成为AI工程师"
}}



3. 用户稳定信息


例如：

我是软件工程专业学生


返回：

{{
"remember":true,
"memory_action":"add",
"memory_key":"major",
"memory_value":"软件工程"
}}



================

修改记忆

================


只有出现：

以前...

现在...

改成...

变成...


才属于update。


例如：

以前喜欢篮球，现在喜欢足球


返回：

{{
"remember":true,
"memory_action":"update",
"memory_key":"hobbies",
"old_value":"篮球",
"new_value":"足球"
}}




================

删除记忆

================


例如：

我不喜欢篮球了


返回：

{{
"remember":true,
"memory_action":"delete",
"memory_key":"hobbies",
"memory_value":"篮球"
}}





================

禁止保存

================


不要保存：

今天发生的事情

临时任务

工具调用

查询请求

一次性问题



================

输出规则

================


1. 只能输出JSON

2. 不允许Markdown

3. 不解释

4. memory_action只能是：

add

update

delete


5. 如果不是长期信息：

必须：

{{
"remember":false
}}



用户输入：

{question}

"""



    messages=[

        {

            "role":"system",

            "content":prompt

        }

    ]



    result = call_llm(
        messages
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



    log(
        "Memory Extract结果",
        content
    )



    try:

        memory=json.loads(
            content
        )


    except Exception:


        memory={

            "remember":False

        }





    # =====================
    # 防御机制
    # =====================


    valid_actions = [

        "add",

        "update",

        "delete"

    ]



    if memory.get(
        "memory_action"
    ) not in valid_actions:


        memory = {

            "remember":False

        }





    if memory.get(
        "remember",
        False
    ):


        action = memory.get(
            "memory_action",
            "add"
        )



        return {


            "new_memory":{


                "action":
                action,


                "key":
                memory.get(
                    "memory_key"
                ),



                "value":
                (
                    memory.get(
                        "memory_value"
                    )
                    if action != "update"
                    else
                    memory.get(
                        "new_value"
                    )
                ),



                "old_value":
                memory.get(
                    "old_value"
                ),



                "new_value":
                memory.get(
                    "new_value"
                )

            },



            "memory_source":
            question,



            "remember":
            True

        }





    return {


        "new_memory":None,


        "memory_source":
        question,


        "remember":
        False

    }