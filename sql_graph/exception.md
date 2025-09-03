NotImplementedError: As of langchain-mcp-adapters 0.1.0, MultiServerMCPClient cannot be used as a context manager (e.g., async with MultiServerMCPClient(...)). Instead, you can do one of the following:
client = MultiServerMCPClient(...) tools = await client.get_tools()
client = MultiServerMCPClient(...) async with client.session(server_name) as session: tools = await load_mcp_tools(session) 但是 langchain-mcp-adapters 是0.1.9不是0.1.0

langchain-mcp-adapters 0.1.9的文档中，MultiServerMCPClient的session方法返回的是一个Session对象，而不是一个AsyncSession对象。因此，在0.1.9版本中，您不能使用async with MultiServerMCPClient(...) as session: 来创建Session对象。