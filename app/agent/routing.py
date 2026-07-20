from typing import Literal

from langchain_core.messages import AIMessage

from app.models.travelState import TravelState


def route_after_agent(state: TravelState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "__end__"


def route_after_tools(state: TravelState) -> Literal["agent", "confirm_booking"]:
    if state.get("pending_flight"):
        return "confirm_booking"
    return "agent"
