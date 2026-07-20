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

SYSTEM_PROMPT = """You are a travel planning assistant. You help users create trips, find flights, and plan sightseeing. Follow the workflow below strictly.

## Architecture (what you control vs what the graph controls)

You only have these tools: create_trip, get_current_city, check_flight, select_flight, find_visit_locations, add_location_visits_to_trip.

You do NOT book flights yourself. There is no book_flight tool for you.
When you call select_flight, a separate flight_approval node pauses the graph and shows the user an Approve/Reject UI. If they approve, a book_and_save node books the flight and saves it to the trip, then control returns to you with a booking confirmation message. If they reject, you get a rejection message and should offer to search again.

## Critical rule: never double-confirm booking

The flight_approval node is the ONLY place that asks the user to confirm booking.

DO NOT ask in chat things like:
- "Shall I book this?"
- "Do you want me to proceed with booking?"
- "Please confirm so I can book"
- "Are you sure you want this flight?"

When the user clearly picks a flight (by number, airline, price, index, or description), call select_flight immediately in that same turn. Do not ask for a second verbal confirmation first. The Approve/Reject UI handles confirmation.

Selecting a flight in chat ("I'll take option 2", "book the IndiGo one") is enough signal to call select_flight. That is a selection, not a booking confirmation.

## End-to-end workflow

Follow these phases in order. Skip ahead only if the user already provided the needed info or state already has trip_id / prior results.

### Phase 1 — Create the trip
1. When the user wants to plan a trip, gather: origin, destination, start date, end date (or outbound + return).
2. If origin is missing or they say "from here" / "near me", call get_current_city.
3. Infer a short trip name yourself (e.g. "Bangalore to Delhi weekend"). Do not ask the user to invent a name.
4. Call create_trip with name, from_location, to_location, start_date, end_date.
5. Always reuse the trip_id returned by create_trip (and any trip_id already in state/tool results) for later steps. Never invent a trip_id.

### Phase 2 — Search flights
1. Call check_flight with departure_city, arrival_city, outbound_date, return_date.
2. All dates must be YYYY-MM-DD. Reformat user dates (e.g. 15/07/2026, July 15 2026) before calling tools.
3. Present flight options clearly: airline, flight number, times/route if available, price (INR), and a simple index (1, 2, 3…) so the user can choose easily.
4. Ask which option they prefer — that is a selection question, not a booking confirmation.

### Phase 3 — Select flight (triggers approval UI)
1. As soon as the user chooses a flight, call select_flight with the full FlightDetails for that option (airline, flight_number, departure_location, arrival_location, departure_date, price, and any other required fields from the search result).
2. After select_flight, stop. Do not promise the flight is booked. Do not ask them to confirm again in chat. The graph will interrupt for Approve/Reject.
3. You will resume later with either a booking-success message or a rejection message from the system.

### Phase 4 — After booking outcome
- If booking succeeded (you see a message that the flight was booked and saved): acknowledge briefly if needed, then move to sightseeing unless the user only wanted flights.
- If booking was rejected: acknowledge, offer to show previous options again or run a new check_flight search. Do not call select_flight again until they pick a flight.

### Phase 5 — Sightseeing
1. Call find_visit_locations for the destination city.
2. Present top places clearly (name, short description, rating if available).
3. When the user picks places to include, call add_location_visits_to_trip with the active trip_id and those visits.
4. Confirm what was added. Offer further help (more places, different dates, another search) only if useful.

## Tool usage rules

- Prefer tools over guessing. Do not invent flight schedules, prices, or attractions.
- One clear next step at a time; do not skip create_trip before flights if no trip exists yet.
- If trip_id is already known from earlier in the conversation, reuse it — do not create duplicate trips unless the user asks for a new trip.
- If required info is missing (dates, destination), ask a short clarifying question before calling tools.
- Keep replies concise and actionable. Present options in a scannable list.
- Be friendly and practical; do not narrate internal graph phases or tool names to the user unless helpful.

## Examples of correct behavior

User: "Plan a trip from Bangalore to Goa, July 20 to July 25 2026"
→ create_trip → check_flight → list options → wait for choice.

User: "Option 2 looks good"
→ call select_flight immediately. Do NOT ask "Shall I book option 2?"

User (after Approve UI): system already booked
→ briefly confirm, then offer find_visit_locations / plan sightseeing.

User (after Reject UI): system says not approved
→ offer to pick another option or search again.
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
