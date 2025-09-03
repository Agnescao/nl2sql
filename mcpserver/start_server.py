from langchain_community.utilities import SQLDatabase

from mcpserver.mcp_tools import mcp_server

if __name__ == "__main__":
    # db = SQLDatabase.from_uri("sqlite:///./chinook.db")
    # print(db.get_usable_table_names())
    #
    # res=db.run("SELECT * FROM artists LIMIT 10")
    mcp_server.run (transport='sse')