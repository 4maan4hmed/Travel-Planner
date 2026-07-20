from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages

from app.models.tripModel import FlightDetails


class TravelState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    user_id: str
    trip_id: str | None
    phase: Literal[
        "idle",
        "planning_trip",
        "searching_flights",
        "flight_booked",
        "planning_visits",
    ]
    flight_options: list[dict] | None
    pending_flight: FlightDetails | dict | None
