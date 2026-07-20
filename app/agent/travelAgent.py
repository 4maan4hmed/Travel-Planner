import asyncio
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agent.graph import build_travel_graph
from app.config.langsmith import configure_langsmith
from app.models.tripModel import FlightDetails

SYSTEM_PROMPT = ""  # kept for backwards compatibility; prompt lives in nodes.py

configure_langsmith()
graph = build_travel_graph()


@dataclass
class AgentRunResult:
    status: Literal["complete", "interrupted"]
    message: str | None = None
    interrupt: dict[str, Any] | None = None


def _graph_config(
    session_id: str,
    *,
    user_id: str = "anonymous",
    run_name: str = "travel_agent",
) -> dict:
    """LangGraph config plus LangSmith run metadata for flow visibility."""
    return {
        "configurable": {"thread_id": session_id},
        "run_name": run_name,
        "tags": ["travel-planner", run_name],
        "metadata": {
            "session_id": session_id,
            "user_id": user_id,
        },
    }


def _extract_interrupt(result: dict) -> dict | None:
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    first = interrupts[0]
    if hasattr(first, "value"):
        return first.value
    if isinstance(first, dict):
        return first.get("value", first)
    return first


def _last_ai_content(result: dict) -> str | None:
    messages = result.get("messages", [])
    for message in reversed(messages):
        if getattr(message, "type", None) == "ai" and message.content:
            return message.content
    return None


async def is_session_interrupted(session_id: str) -> bool:
    snapshot = await graph.aget_state(_graph_config(session_id))
    return bool(snapshot.next)


async def run_travel_agent(
    message: str,
    session_id: str,
    user_id: str = "anonymous",
) -> AgentRunResult:
    if await is_session_interrupted(session_id):
        raise ValueError("Session is awaiting flight approval. Use resume instead.")

    config = _graph_config(
        session_id,
        user_id=user_id,
        run_name="travel_agent",
    )
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
        },
        config=config,
    )

    interrupt_payload = _extract_interrupt(result)
    if interrupt_payload:
        return AgentRunResult(status="interrupted", interrupt=interrupt_payload)

    return AgentRunResult(
        status="complete",
        message=_last_ai_content(result) or "",
    )


async def resume_travel_agent(
    session_id: str,
    user_id: str,
    approved: bool,
) -> AgentRunResult:
    if not await is_session_interrupted(session_id):
        raise ValueError("Session is not awaiting approval.")

    config = _graph_config(
        session_id,
        user_id=user_id,
        run_name="travel_agent_resume",
    )
    result = await graph.ainvoke(
        Command(resume={"approved": approved}),
        config=config,
    )

    interrupt_payload = _extract_interrupt(result)
    if interrupt_payload:
        return AgentRunResult(status="interrupted", interrupt=interrupt_payload)

    return AgentRunResult(
        status="complete",
        message=_last_ai_content(result) or "",
    )


def build_interrupt_payload(raw: dict) -> dict:
    flight = raw.get("flight", {})
    if isinstance(flight, FlightDetails):
        flight = flight.model_dump()
    return {
        "type": raw.get("type", "flight_approval"),
        "trip_id": raw.get("trip_id"),
        "flight": flight,
        "flight_options": raw.get("flight_options"),
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    out = asyncio.run(
        run_travel_agent(
            "Tell me about the flight to Chennai on 07/15/2026",
            session_id="demo-session",
        )
    )
    print(out)
