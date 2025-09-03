from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from sql_graph.my_llm import llm

db = SQLDatabase.from_uri("sqlite:///./chinook.db")
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()
# get the sql_db_schema tool
# next() 函数用于获取可迭代对象中的下一个元素
# 这里是获取 tools 中第一个 name 为 "sql_db_schema" 的工具
list_of_tables = next(tool for tool in tools if tool.name == "sql_db_schema")
print(list_of_tables.invoke('employees'))  # 查询 employees 表的 schema
