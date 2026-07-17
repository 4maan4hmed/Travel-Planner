from langchain_core.messages import AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt

from app.models.tripModel import FlightDetails
from app.models.travelState import TravelState
from app.services import tripService
from app.tools.currentLocation import get_current_city
from app.tools.findVisitLocation import find_visit_locations
from app.tools.flightBook import book_flight
from app.tools.flightCheck import check_flight
from app.tools.manageTrip import add_location_visits_to_trip, create_trip
from app.tools.selectFlight import select_flight

SYSTEM_PROMPT = """You are a travel planning assistant.
- Use create_trip when the user wants to plan a trip (infer trip name yourself).
- Use get_current_city to detect origin when needed.
- Use check_flight to search; present options clearly.
- When the user chooses a flight, call select_flight, the booking would be managed by that end automatically, once confirmation recieved move to the next step.
- Use find_visit_locations and add_location_visits_to_trip for sightseeing.
- Reuse trip_id from prior tool results. Use YYYY-MM-DD dates(reformat if needed from user)
"""

SAFE_TOOLS = [
    get_current_city,
    check_flight,
    select_flight,
    find_visit_locations,
    create_trip,
    add_location_visits_to_trip,
]


def _flight_details_from_state(raw: FlightDetails | dict) -> FlightDetails:
    if isinstance(raw, FlightDetails):
        return raw
    return FlightDetails(**raw)


def make_agent_node(llm: ChatGroq):
    llm_with_tools = llm.bind_tools(SAFE_TOOLS)

    async def agent_node(state: TravelState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    return agent_node


tool_node = ToolNode(SAFE_TOOLS)


async def flight_approval_node(state: TravelState) -> dict:
    pending = state.get("pending_flight")
    if not pending:
        return {"phase": "searching_flights"}

    flight = _flight_details_from_state(pending)
    decision = interrupt(
        {
            "type": "flight_approval",
            "trip_id": state.get("trip_id"),
            "flight": flight.model_dump(),
            "flight_options": state.get("flight_options"),
        }
    )

    if decision.get("approved"):
        return {"flight_approved": True}

    return {
        "flight_approved": False,
        "pending_flight": None,
        "phase": "searching_flights",
        "messages": [
            AIMessage(
                content=(
                    "Flight booking was not approved. "
                    "Let me know if you want to search for other flights."
                )
            )
        ],
    }


async def book_and_save_node(state: TravelState) -> dict:
    pending = state.get("pending_flight")
    trip_id = state.get("trip_id")
    user_id = state.get("user_id")

    if not pending or not trip_id or not user_id:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Unable to complete booking: missing flight selection or trip."
                    )
                )
            ],
            "flight_approved": None,
        }

    flight = _flight_details_from_state(pending)
    await book_flight.ainvoke({"flight_details": flight})
    await tripService.add_flight_to_trip(trip_id, user_id, flight)

    return {
        "pending_flight": None,
        "flight_approved": None,
        "phase": "flight_booked",
        "messages": [
            AIMessage(
                content=(
                    f"Flight booked and saved to your trip: {flight.airline} "
                    f"{flight.flight_number} from {flight.departure_location} "
                    f"to {flight.arrival_location} on {flight.departure_date} "
                    f"(INR {flight.price})."
                )
            )
        ],
    }
