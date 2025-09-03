from langchain_openai import ChatOpenAI


from zhipuai import ZhipuAI


zhipuai_client = ZhipuAI(api_key='b4af0ae174654a1aa7893b98aec88deb.fPS1Nn2kd0aAXUHH')

llm = ChatOpenAI(model_name="glm-4-air-250414", temperature=0,
                 api_key='b4af0ae174654a1aa7893b98aec88deb.fPS1Nn2kd0aAXUHH', base_url="https://open.bigmodel.cn/api/paas/v4/")