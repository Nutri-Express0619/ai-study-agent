from config import SYSTEM_PROMPT


messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]



def add_message(role, content):

    messages.append(
        {
            "role": role,
            "content": content
        }
    )



def get_messages():

    return messages



def clear_memory():

    global messages

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]