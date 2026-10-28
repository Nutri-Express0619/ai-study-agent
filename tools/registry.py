from tools.calculator import calculator



# ======================
# 给Executor调用
# ======================

tool_registry = {


    "calculator": calculator

}




# ======================
# 给LLM看的工具描述
# ======================

tools = [

    {
        "type":"function",

        "function":{

            "name":"calculator",

            "description":
            "计算两个数字相加",


            "parameters":{

                "type":"object",

                "properties":{

                    "a":{

                        "type":"number"

                    },


                    "b":{

                        "type":"number"

                    }

                },


                "required":[

                    "a",
                    "b"

                ]

            }

        }

    }

]