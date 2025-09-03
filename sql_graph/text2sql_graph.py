from contextlib import asynccontextmanager
from typing import Literal

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from langgraph.constants import START, END

from sql_graph.my_llm import llm
from sql_graph.sql_state import SQLState
from sql_graph.tool_node import call_get_schema_tool, get_schema_node

mcp_server_config = {
    "url": "http://localhost:8000/sse",
    "transport": "sse"
}
query_check_system = """您是一位注重细节的SQL专家。
请仔细检查SQLite查询中的常见错误，包括：
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

如果发现上述任何错误，请重写查询。如果没有错误，请原样返回查询语句。

检查完成后，您将调用适当的工具来执行查询。"""


def should_continue(state: SQLState) -> Literal[END, "check_query"]:  # Literal 是 Python 3.8 引入的一个类型提示工具，用于指定变量只能取特定的值
    """判断是否继续执行工作流, 一个条件路由"""
    # 获取上一个节点生成的sql查询语句,而不需要整个消息列表
    last_message = state["messages"][-1]
    if not last_message.tool_calls:  # 如果上一个节点没有生成工具调用，说明sql查询语句没有生成成功，需要重新生成
        return END
    else:
        return "check_query"


@asynccontextmanager  # 定义异步上下文管理器 它可以使得异步资源的获取和释放更加方便 后面可以使用 async with 语法来使用这个上下文管理器
async def make_graph_context():
    """定义并且编译工作流 """
    client = MultiServerMCPClient({'sql_mcp': mcp_server_config})  # 创建一个MCP客户端, 并且传入配置信息 用与MCP服务器进行交互,
    tools = await client.get_tools()
    # 获取数据库中的所有表的工具
    get_list_table_tool = next(tool for tool in tools if tool.name == 'get_list_table_tool')
    # 执行sql查询的工具
    db_query_tool = next(tool for tool in tools if tool.name == 'db_query_tool')

    # 生成一个调用工具的指令
    def list_of_tables_command(state: SQLState):
        # 第一个节点
        tool_call = {
            "name": "get_list_table_tool",
            "args": {},
            "id": "abc123",
            "type": "tool_call",
        }

        tool_call_message = AIMessage(content="", tool_calls=[tool_call])  # 将这个调用工具的指令包装成为一个ai消息
        # # 实际调用工具
        # tool_message = list_of_tools.invoke(tool_call_message)
        #
        # response = AIMessage(f"数据库中的表有：{tool_message.content}")

        return {"messages": [tool_call_message]}
     # 第二个节点
    list_tables_tool = ToolNode([get_list_table_tool], name="list_tables_tool")

    def generate_sql_query(state: SQLState):
        """第四个节点，根据用户的输入生成sql查询语句，并且返回 json格式的数据,格式为：{sql: 'sql查询语句'},可以查看system message 里面的prompt要求"""
        system_message = {
            "role": "system",
            "content": "你是一个数据库查询助手，你需要根据用户的输入生成一个sql查询语句，你需要返回一个json格式的数据，格式为：{sql: 'sql查询语句'}",
        }
        # 通过 bind_tools，可以将外部工具的功能与 LLM 结合，使模型能够根据输入内容决定是否需要调用某个工具。
        # 工具调用：绑定后的模型可以在生成响应时自动或手动触发工具调用，执行特定任务（如查询数据库、获取外部数据等）。
        llm_with_tools = llm.bind_tools([db_query_tool])
        response = llm_with_tools.invoke([system_message] + state['messages'])

        return {'messages': [response]}

    def check_query(state: SQLState):
        """第五个节点，检查生成的sql查询语句是否正确，并且返回json格式的数据,格式为：{result: '查询结果'},可以查看system message 里面的prompt要求"""
        system_message = {
            "role": "system",
            "content": query_check_system,
        }
        # 获取上一个节点生成的sql查询语句,而不需要整个消息列表

        tool_call = state["messages"][-1].tool_calls[0]  # -1 获取最后一个消息 -1, -2 获取倒数第二个消息
        sql_query = tool_call["args"]["query"]  # 这个才是真正要执行的sqL查询语句
        sqlquery_message = {"role": "user", "content": sql_query}
        llm_with_tools = llm.bind_tools([db_query_tool], tool_choice='any')  # 绑定工具，并且设置为必须使用工具

        response = llm_with_tools.invoke([system_message, sqlquery_message])
        response.id = state["messages"][
            -1].id  # 保持消息ID一致，便于追踪,保证同一个sql查询语句的id一致,它和上个节点生成sql一致，如果执行有问题， 又会回到上一个节点去重新生成sql查询语句

        return {'messages': [response]}

    # 第六个节点执行sql查询的节点 ToolNode 是一个预定义的节点类型，专门用于调用工具
    run_query_node = ToolNode([db_query_tool], name="run_sql_query")


    # 开始定义工作流
    # 创建一个workflow state
    workflow = StateGraph(SQLState)
    # 添加工具
    workflow.add_node(list_of_tables_command)
    workflow.add_node(list_tables_tool)
    workflow.add_node(call_get_schema_tool)
    workflow.add_node(get_schema_node)
    workflow.add_node(generate_sql_query)
    workflow.add_node(check_query)
    workflow.add_node(run_query_node)

    # 添加边 定义节点之间的连接关系
    workflow.add_edge(START, "list_of_tables_command")
    workflow.add_edge("list_of_tables_command", "list_tables_tool")
    workflow.add_edge("list_tables_tool", "call_get_schema_tool")
    workflow.add_edge("call_get_schema_tool", "get_schema_node")
    workflow.add_edge("get_schema_node", "generate_sql_query")
    workflow.add_conditional_edges("generate_sql_query", should_continue)
    workflow.add_edge("check_query", "run_sql_query")
    workflow.add_edge("run_sql_query", "generate_sql_query")  # 如果执行sql查询有问题，就回到生成sql查询语句的节点，重新生成sql查询语句
    graph = workflow.compile() # 编译工作流
    yield graph # 返回工作流
