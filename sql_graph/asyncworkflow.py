"""异步工作流定义"""
"""优势
使用 AsyncTaskScheduler 的优势包括：
并发执行：可以同时执行多个查询，提高效率
资源控制：通过 max_concurrent_tasks 控制并发数量，避免资源耗尽
错误处理：单个查询失败不会影响其他查询的执行
统一管理：所有异步任务都在同一个调度器中管理
可扩展性：容易添加新的任务类型"""

@asynccontextmanager
async def make_graph_context():
    # ... 现有代码 ...

    # 添加处理多个查询的节点
    handle_multiple_queries_node = ToolNode([multiple_queries_handler_tool])
    execute_multiple_queries_node = execute_multiple_queries_parallel  # 新的执行节点

    # 在工作流中添加新节点
    workflow.add_node("handle_multiple_queries", handle_multiple_queries_node)
    workflow.add_node("execute_multiple_queries", execute_multiple_queries_node)

    # 添加条件边来处理单个或多个查询
    workflow.add_conditional_edges(
        "generate_sql_query",
        route_single_or_multiple_queries,
        {
            "single_query": "check_query",
            "multiple_queries": "handle_multiple_queries",
            END: END
        }
    )

    # 添加多查询执行流程的边
    workflow.add_edge("handle_multiple_queries", "execute_multiple_queries")
    workflow.add_edge("execute_multiple_queries", END)
