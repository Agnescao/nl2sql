import requests
import json

url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-e1fceffb22bb4cceb226a760ee653294",
    "Content-Type": "application/json"
}
data = {
    "model": "qwen3-coder-plus",
    "messages": [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': '请编写一个Python函数 find_prime_numbers，该函数接受一个整数 n 作为参数，并返回一个包含所有小于 n 的质数（素数）的列表。质数是指仅能被1和其自身整除的正整数，如2, 3, 5, 7等。不要输出非代码的内容。'}
    ]
}

try:
    response = requests.post(url, headers=headers, json=data)
    print("状态码:", response.status_code)
    print("响应内容:", response.text)
    if response.status_code == 200:
        result = response.json()
        print("="*20+"回复内容"+"="*20)
        print(result['choices'][0]['message']['content'])
        print("="*20+"Token消耗"+"="*20)
        print(result['usage'])
except Exception as e:
    print(f"请求错误: {type(e).__name__}: {e}")
