import os

from dotenv import load_dotenv
# 添加verbose=False来减少警告信息
load_dotenv(override=True, verbose=False)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')

