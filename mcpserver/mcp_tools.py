
from langchain_community.utilities import SQLDatabase
from mcp.server import FastMCP
mcp_server = FastMCP(name='sql-mcp', instructions='我自己的MCP服务', port=8000)
db = SQLDatabase.from_uri('sqlite:///../chinook.db')

@mcp_server.tool(name='get_list_table_tool', description='SQL数据库工具')
def get_list_table_tool() -> str:
    return ", ".join(db.get_usable_table_names())  #   ['emp': “这是一个员工表，”, '']


@mcp_server.tool(name='db_query_tool', description='执行sql查询query,返回结果')
def db_query_tool(query:str) -> str:
    """执行sql查询query,返回结果"""
    result = db.run_no_throw(query)  # 执行查询（不抛出异常）
    if result is None:
        return "没有查询结果"
    return result

