from sql_graph.my_llm import llm
from sql_graph.sql_state import SQLState

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import ToolNode

db = SQLDatabase.from_uri('sqlite:///../chinook.db')
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

tools = toolkit.get_tools()

get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")


# 生成 call get schema tool 的指令/prompt with llm
def call_get_schema_tool(state: SQLState):
    # 这里使用大模型生成， bind tool
    llm_with_bind_tool = llm.bind_tools(
        [get_schema_tool], tool_choice="any"
    )
    #这个指令会调用 get_schema_tool
    response = llm_with_bind_tool.invoke(state["messages"])
    return {"messages": response}

#第三个节点，调用 get_schema_tool 工具
get_schema_node = ToolNode([get_schema_tool],name="get_schema_node") # 使用langgraph 创建节点toolnode直接调用tool




