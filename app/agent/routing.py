from typing import Literal

from langchain_core.messages import AIMessage

from app.models.travelState import TravelState


def route_after_agent(state: TravelState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "__end__"


def route_after_tools(state: TravelState) -> Literal["agent", "flight_approval"]:
    if (
        state.get("phase") == "awaiting_flight_approval"
        and state.get("pending_flight")
    ):
        return "flight_approval"
    return "agent"


def route_after_approval(state: TravelState) -> Literal["book_and_save", "agent"]:
    if state.get("flight_approved"):
        return "book_and_save"
    return "agent"
