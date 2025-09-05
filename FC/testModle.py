import json

from openai import OpenAI

from env_utils import OPENAI_API_KEY


def get_weather(location: str):
    """模拟天气查询函数，实际项目中替换为真实API（如和风天气）"""
    print(f"【调试】正在查询 {location} 的天气...")
    weather_data = {
        "location": location,
        "temperature": "24°C",
        "condition": "晴天",
        "wind": "3级"
    }
    return json.dumps(weather_data)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如北京、上海"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

client = OpenAI(
    api_key="sk-BhqVpIBKdsCHrpVnOOGDqN63Mmv6yveETPE2w4LuKSKOOp2c",
    base_url="https://xiaoai.plus/v1"
)

user_input = '今天，北京的天气怎么样？'

resp = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': user_input}],
    tools=tools,
    tool_choice='auto'
)

print(resp)
tool_calls = resp.choices[0].message.tool_calls
if tool_calls:
    function_name = tool_calls[0].function.name
    function_args = json.loads(tool_calls[0].function.arguments)
    location = function_args["location"]

    if function_name == 'get_weather':
        result = get_weather(location)

    second_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "", "tool_calls": tool_calls},
            {"role": "tool", "content": result, "tool_call_id": tool_calls[0].id}
        ],
    )

    #  输出最终回答
    final_answer = second_response.choices[0].message.content
    print(f"AI回答：{final_answer}")


