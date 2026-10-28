import json
import os


MEMORY_FILE = "storage/user_memory.json"



def load_memory():

    if not os.path.exists(MEMORY_FILE):

        return {}


    with open(
        MEMORY_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def save_memory(key, value):

    memory = load_memory()


    if key not in memory:

        memory[key] = []


    if isinstance(memory[key], list):

        if value not in memory[key]:

            memory[key].append(value)

    else:

        memory[key] = value



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



def get_memory():

    return load_memory()