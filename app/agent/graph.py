from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.mongodb import MongoDBSaver

from app.agent.nodes import (
    book_and_save_node,
    flight_approval_node,
    make_agent_node,
    tool_node,
)
from app.agent.routing import (
    route_after_agent,
    route_after_approval,
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
    builder.add_node("flight_approval", flight_approval_node)
    builder.add_node("book_and_save", book_and_save_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent, ["tools", END])
    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        ["agent", "flight_approval"],
    )
    builder.add_conditional_edges(
        "flight_approval",
        route_after_approval,
        ["book_and_save", "agent"],
    )
    builder.add_edge("book_and_save", "agent")

    checkpointer = MongoDBSaver(
        get_client(),
        db_name=get_settings().mongo_db_name,
    )

    return builder.compile(checkpointer=checkpointer)
