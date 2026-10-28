import requests

from config import BASE_URL, MODEL



def call_llm(messages, tools=None):


    response = requests.post(

        f"{BASE_URL}/api/chat",

        json={

            "model": MODEL,

            "messages": messages,

            "tools": tools,

            "stream": False

        }

    )


    return response.json()