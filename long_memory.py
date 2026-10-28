import json
import os

from agent.logger import log


MEMORY_FILE = "storage/user_memory.json"


def load_memory():

    if not os.path.exists(
        MEMORY_FILE
    ):

        return {}


    with open(
        MEMORY_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)





def save_memory(memory):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:


        json.dump(
            memory,
            f,
            ensure_ascii=False,
            indent=4
        )





def init_user(memory, user_id):

    if user_id not in memory:

        memory[user_id] = {

            "name":"",
            "nickname":"",
            "hobbies":[],
            "goal":""

        }



    default_fields = {

        "name":"",
        "nickname":"",
        "hobbies":[],
        "goal":""

    }


    for field, value in default_fields.items():

        if field not in memory[user_id]:

            memory[user_id][field] = value





# =====================
# 新增记忆
# =====================

def add_memory(
        user_id,
        key,
        value
):


    memory = load_memory()


    init_user(
        memory,
        user_id
    )



    if not value:

        log(
            "空记忆，不保存",
            value
        )

        return




    if key not in memory[user_id]:

        memory[user_id][key] = []




    if isinstance(
        memory[user_id][key],
        list
    ):


        if value not in memory[user_id][key]:

            memory[user_id][key].append(
                value
            )

        else:

            log(
                "记忆已存在，不重复保存",
                value
            )


    else:

        memory[user_id][key] = value





    save_memory(
        memory
    )


    log(
        "保存memory完成",
        {
            "key":key,
            "value":value
        }
    )







# =====================
# 修改记忆
# =====================

def update_memory(
        user_id,
        key,
        old_value,
        new_value
):


    memory = load_memory()


    init_user(
        memory,
        user_id
    )



    if key not in memory[user_id]:


        log(
            "不存在该记忆字段",
            key
        )

        return




    current = memory[user_id][key]




    if isinstance(
        current,
        list
    ):



        if old_value in current:



            index = current.index(
                old_value
            )



            # 删除旧记忆

            current.pop(
                index
            )



            # 防止新记忆重复

            if new_value not in current:


                current.append(
                    new_value
                )



            log(
                "记忆更新成功",
                {
                    "old":old_value,
                    "new":new_value
                }
            )



        else:


            log(
                "没有找到旧记忆",
                old_value
            )




    else:


        memory[user_id][key] = new_value





    save_memory(
        memory
    )



    log(
        "更新memory完成",
        memory
    )









# =====================
# 删除记忆
# =====================

def delete_memory(
        user_id,
        key,
        value
):


    memory = load_memory()


    init_user(
        memory,
        user_id
    )



    if key not in memory[user_id]:


        log(
            "不存在该字段",
            key
        )

        return




    current = memory[user_id][key]



    if isinstance(
        current,
        list
    ):


        if value in current:


            current.remove(
                value
            )


            log(
                "记忆删除成功",
                value
            )


        else:


            log(
                "没有找到需要删除的记忆",
                value
            )



    else:


        if current == value:


            memory[user_id][key] = ""






    save_memory(
        memory
    )



    log(
        "删除memory完成",
        {
            "key":key,
            "value":value
        }
    )








# =====================
# 查询用户记忆
# =====================

def get_user_memory(user_id):


    memory = load_memory()



    user_memory = memory.get(
        user_id,
        {}
    )



    return user_memory