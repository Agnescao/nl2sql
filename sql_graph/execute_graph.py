import asyncio
from logging import exception
from typing import TypedDict

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

from sql_graph.text2sql_graph import make_graph_context


#工作流执行节点上下文的状态
# class nodestate(TypedDict):
#   message: Annotated[str, "The message to send to the model"]

async def execute_graph():
  """执行SQL数据库查询的工作流"""
  async with make_graph_context() as graph:
    while True:
      user_input = input("用户: ")
      if user_input.lower() in ['q', 'exit', 'quit']:
        print('对话结束，拜拜！')
        break
      else:
        async for event in graph.astream({"messages": [{"role": "user", "content": user_input}]},
                                         stream_mode="values"):
          event["messages"][-1].pretty_print()


#

if __name__ == "__main__":
  # db = SQLDatabase.from_uri("sqlite:///./chinook.db")
  # toolkit = SQLDatabaseToolkit(db=db, llm=llm)
  # tools = toolkit.get_tools()
  #
  # for tool in tools:
  #   print(tool.name)
  # print(f"Description: {tool.description}")
  #
  # list_of_tables  = next(tool for tool in tools if tool.name == "sql_db_schema")
  # print("invoke list of tools")
  # result = list_of_tables.invoke("") # 空字符串表示使用默认参数
  #
  # print(result)
  asyncio.run(execute_graph())