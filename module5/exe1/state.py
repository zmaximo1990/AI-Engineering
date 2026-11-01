from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages, MessagesState
from langchain_core.tools import ToolCall


class State(TypedDict):
    messages: Annotated[list, add_messages]  # conversation history
    is_escalated: bool  # True if the case was escalated to a human
    attempts: int  # how many times the agent has tried to resolve the problem
    tool_call: ToolCall | None # tool call to run conditional route


class StateMessages(MessagesState): # conversation history inheritance from `MessagesState`
    is_escalated: bool  # True if the case was escalated to a human
    attempts: int  # how many times the agent has tried to resolve the problem
    tool_call: ToolCall | None # tool call to run conditional route