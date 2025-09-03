import requests
import json


class CompatibleOpenAI:
    def __init__(self, api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key
        self.base_url = base_url

    class ChatCompletions:
        def __init__(self, client):
            self.client = client

        def create(self, model, messages, **kwargs):
            url = f"{self.client.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": messages,
                **kwargs
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API请求失败: {response.status_code} - {response.text}")

    @property
    def chat_completions(self):
        return self.ChatCompletions(self)


# 使用方式与OpenAI SDK类似
client = CompatibleOpenAI(api_key="sk-e1fceffb22bb4cceb226a760ee653294")

try:
    completion = client.chat_completions.create(
        model="qwen3-coder-plus",
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user',
             'content': '请编写一个Python函数 find_prime_numbers，该函数接受一个整数 n 作为参数，并返回一个包含所有小于 n 的质数（素数）的列表。'}
        ]
    )

    print("=" * 20 + "回复内容" + "=" * 20)
    print(completion['choices'][0]['message']['content'])
    print("=" * 20 + "Token消耗" + "=" * 20)
    print(completion['usage'])

except Exception as e:
    print(f"发生错误: {e}")
