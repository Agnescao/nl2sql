# 添加新的节点用于处理多个查询
def execute_multiple_queries_parallel(state: SQLState):
    """
    并行执行多个 SQL 查询的节点
    """
    # 从状态中获取多个查询
    queries = extract_multiple_queries_from_state(state)

    # 使用 AsyncTaskScheduler 并行执行
    scheduler = AsyncTaskScheduler(max_concurrent_tasks=3)

    tasks = [
        (f"execute_query_{i}", execute_single_db_query, (query,), {})
        for i, query in enumerate(queries)
    ]

    # 异步执行所有查询
    results = await scheduler.schedule_tasks(tasks)

    # 处理结果并返回
    return process_multiple_query_results(results)


async def execute_single_db_query(query):
    """
    执行单个数据库查询
    """
    # 可以使用从 MCP 获取的 db_query_tool
    # 或者直接使用数据库连接执行查询
    result = db.run_no_throw(query)
    return {
        "query": query,
        "result": result,
        "status": "success" if result else "error"
    }


def process_multiple_query_results(results):
    """
    处理多个查询的结果
    """
    # 聚合所有查询结果
    aggregated_result = {
        "results": results,
        "total_queries": len(results),
        "successful_queries": len([r for r in results if r["status"] == "success"])
    }

    # 创建响应消息
    response_message = AIMessage(
        content=f"执行了 {len(results)} 个查询，成功 {aggregated_result['successful_queries']} 个",
        additional_kwargs=aggregated_result
    )

    return {"messages": [response_message]}
