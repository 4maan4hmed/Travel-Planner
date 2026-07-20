from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.mongodb import MongoDBSaver

from app.agent.nodes import (
    confirm_booking_node,
    make_agent_node,
    tool_node,
)
from app.agent.routing import (
    route_after_agent,
    route_after_tools,
)
from app.config.settings import get_settings
from app.db.mongo import get_client
from app.models.travelState import TravelState


def build_travel_graph():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=get_settings().groq_api_key,
    )

    builder = StateGraph(TravelState)
    builder.add_node("agent", make_agent_node(llm))
    builder.add_node("tools", tool_node)
    builder.add_node("confirm_booking", confirm_booking_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, ["tools", END])
    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        ["agent", "confirm_booking"],
    )
    builder.add_edge("confirm_booking", "agent")

    checkpointer = MongoDBSaver(
        get_client(),
        db_name=get_settings().mongo_db_name,
    )

    return builder.compile(
        checkpointer=checkpointer,
        name="travel_agent",
    )
