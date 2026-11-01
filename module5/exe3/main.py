import argparse
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import  HumanMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv()

# 1. State
class AgentState(MessagesState):
    ...

# 2. Tools

class WeatherInput(BaseModel):
    """Validated arguments for a weather lookup."""

    location: str = Field(
        ...,
        description="City or place to get the current weather for, such as Madrid or London.",
    )


@tool(
    "get_weather",
    args_schema=WeatherInput,
    description="Get the current weather for a location.",
    return_direct=True,
)
def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny and 22°C."

tools = [get_weather]
tool_node = ToolNode(tools)

# 3. LLM with linked tools
model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)

# 4. LLM call node
async def call_model(state: AgentState):
    response = await model.ainvoke(state["messages"])
    return {"messages": [response]}

# 5. Workflow
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
# tools_condition vuelve a "tools" si hay tool calls, o termina en END
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# 6. Checkpointer
memory = MemorySaver()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weather agent with optional checkpoint memory.")
    parser.add_argument(
        "-m",
        "--memory",
        action="store_true",
        help="Reuse thread_id dev_test_01 so the second question remembers the first.",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    thread_id = "dev_test_01"

    # The checkpointer requires a thread_id. Without --memory, compile to run stateless.
    graph = workflow.compile(checkpointer=memory) if args.memory else workflow.compile()
    config = {"configurable": {"thread_id": thread_id}} if args.memory else None

    # First interaction
    print("--- Step 1 ---")
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="What's the weather in Madrid?")]},
        config,
    )
    print(result["messages"][-1].content)

    # Second interaction (resuming from checkpoint)
    print("--- Step 2 ---")
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="And in London?")]},
        config,
    )
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
