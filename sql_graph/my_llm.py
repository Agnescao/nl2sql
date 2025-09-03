from langchain_openai import ChatOpenAI


from zhipuai import ZhipuAI

#from sql_graph.env_utils import ZHIPU_API_KEY
ZHIPU_API_KEY='xxxx'
zhipuai_client = ZhipuAI(api_key=ZHIPU_API_KEY)

llm = ChatOpenAI(model_name="glm-4-air-250414", temperature=0,
                 api_key=ZHIPU_API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4/")