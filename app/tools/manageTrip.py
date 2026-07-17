from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from app.models.travelState import TravelState
from app.models.tripModel import FlightDetails, LocationVisit, TripCreateRequest
from app.services import tripService
from app.services.tripService import TripError


@dataclass
class AgentContext:
    user_id: str


def _parse_date(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


@tool
async def create_trip(
    name: str,
    from_location: str,
    to_location: str,
    start_date: str,
    end_date: str,
    state: Annotated[TravelState, InjectedState],
    runtime: ToolRuntime,
) -> str | Command:
    """Create a new trip for the current user. Call this when the user wants to start planning a trip.

    Args:
        name: Trip name, e.g. "Bangalore to Delhi weekend".
        from_location: Starting city.
        to_location: Destination city.
        start_date: Trip start date in YYYY-MM-DD format.
        end_date: Trip end date in YYYY-MM-DD format.
    """
    try:
        trip = await tripService.create_trip(
            TripCreateRequest(
                name=name,
                from_location=from_location,
                to_location=to_location,
                start_date=_parse_date(start_date),
                end_date=_parse_date(end_date),
            ),
            state["user_id"],
        )
    except TripError as exc:
        return f"Error: {exc.message}"

    content = (
        f"Trip created successfully. trip_id={trip.trip_id}. "
        f"Use this trip_id when adding flight details or location visits."
    )
    return Command(
        update={
            "trip_id": trip.trip_id,
            "phase": "planning_trip",
            "messages": [
                ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
            ],
        }
    )


@tool
async def add_flight_to_trip(
    trip_id: str,
    flight_details: FlightDetails,
    state: Annotated[TravelState, InjectedState],
) -> str:
    """Save the chosen flight onto an existing trip. Call after the user confirms which flight to book.

    Args:
        trip_id: The trip_id returned by create_trip.
        flight_details: Selected flight details (airline, number, route, date, price).
    """
    try:
        await tripService.add_flight_to_trip(
            trip_id,
            state["user_id"],
            flight_details,
        )
    except TripError as exc:
        return f"Error: {exc.message}"

    return (
        f"Flight details saved on trip {trip_id}: "
        f"{flight_details.airline} {flight_details.flight_number} "
        f"from {flight_details.departure_location} to {flight_details.arrival_location}."
    )


@tool
async def add_location_visits_to_trip(
    trip_id: str,
    visits: list[LocationVisit],
    state: Annotated[TravelState, InjectedState],
) -> str:
    """Add places the user wants to visit to an existing trip.

    Args:
        trip_id: The trip_id returned by create_trip.
        visits: List of visits with location, date (YYYY-MM-DD), and notes.
    """
    try:
        await tripService.add_location_visits_to_trip(
            trip_id,
            state["user_id"],
            visits,
        )
    except TripError as exc:
        return f"Error: {exc.message}"

    names = ", ".join(v.location for v in visits)
    return f"Added {len(visits)} location visit(s) to trip {trip_id}: {names}."
