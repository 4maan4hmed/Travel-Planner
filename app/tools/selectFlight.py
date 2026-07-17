from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from app.models.tripModel import FlightDetails


@tool
async def select_flight(
    flight_details: FlightDetails,
    runtime: ToolRuntime,
) -> Command:
    """Record the user's chosen flight for approval. Does not book the flight.

    Call this when the user picks a flight from search results. Booking happens
    only after explicit user approval.

    Args:
        flight_details: The selected flight (airline, flight number, route, date, price).
    """
    content = (
        f"Flight selected for approval: {flight_details.airline} "
        f"{flight_details.flight_number} from {flight_details.departure_location} "
        f"to {flight_details.arrival_location} on {flight_details.departure_date} "
        f"at INR {flight_details.price}. Awaiting user approval before booking."
    )
    return Command(
        update={
            "pending_flight": flight_details.model_dump(),
            "phase": "awaiting_flight_approval",
            "messages": [
                ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
            ],
        }
    )
