from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

class SQLState(TypedDict):
    """工作流执行节点上下文的状态"""
    """后面节点可以访问前面节点的messages"""
    """后面节点输出的message会覆盖前面节点的message"""
    """后一个列表覆盖前一个列表"在前一个列表的基础上追加，需要在某些情况下发生"""
    """需要考虑什么时候覆盖，什么时候追加"""

    messages: Annotated[list[AnyMessage], add_messages] #每个节点输出的message添加到list 中,不管是#AI Message, HumanMessage, SystemMessage,toolMessage


