from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from zhipuaiclient import zhipuai_client, llm
from pydantic import BaseModel, Field
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

response = zhipuai_client.chat.completions.create(
    model="glm-4-air-250414",
    messages=[{'role': 'user', 'content': '2025年4月重要财经事件 政策变化 市场数据'}],

)


class SearchInput(BaseModel):
    query: str = Field(description='需要搜索的内容或者关键词')


@tool('my_search_tool', description = '专门搜索互联网中的内容', args_schema = SearchInput)

def my_search(query: str) -> str:
    websearch = zhipuai_client.websearch.create(query=query)
    return response.output


prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手，尽可能的调用工具回答用户的问题"),
    MessagesPlaceholder(variable_name="chat_history"),  # 添加历史对话, 用于存储历史对话 记录
    ("human", "{input}"),
    MessagesPlaceholder(variable_name='agent_scratchpad', optional=True),  # 用于存储中间思考过程

])
tools = [my_search]
agent = create_tool_calling_agent(llm, tools,prompt) # 创建代理
executor = AgentExecutor(agent=agent, tools=tools) # 创建执行器
resp = executor.invoke({'input': '上海的天气怎么样'}) # 调用执行器
print(resp)

#session history 带有记忆功能
store = {}


class BaseChatMessageHistory:
    pass


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


agent_with_history = RunnableWithMessageHistory(
    executor,
    get_session_history,
    input_messages_key='input',
    history_messages_key='chat_history'
)

resp1 = agent_with_history.invoke(
    {'input': '你好， 我是LAOXIAO，出生在1983年'},
    config={'configurable': {'session_id': 'lx111'}}
)

print(resp1)

