from langchain.agents import create_agent
from langchain_groq import ChatGroq
from app.tools.currentLocation import get_current_city
from app.tools.flightCheck import check_flight
import asyncio
from app.tools.flightBook import book_flight
from app.tools.findVisitLocation import find_visit_locations
from app.tools.manageTrip import (
    AgentContext,
    add_flight_to_trip,
    add_location_visits_to_trip,
    create_trip,
)

SYSTEM_PROMPT = """You are a travel planning assistant.
Workflow:
1. When the user wants to plan a trip, call create_trip first and remember the trip_id, get what city you are in with get_current_city, parse out the rest of the information
by asking the user for the details.
2. Help them find flights with check_flight. After they choose one, call book_flight, then add_flight_to_trip with that trip_id.
3. Suggest places with find_visit_locations. After they pick places, call add_location_visits_to_trip with that trip_id.
Use YYYY-MM-DD dates. Always reuse the trip_id from create_trip for later updates.
4. If the user wants to add more details to the trip, ask them for the details and call the appropriate tool.
"""


def build_travel_agent():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )

    tools = [
        get_current_city,
        check_flight,
        book_flight,
        find_visit_locations,
        create_trip,
        add_flight_to_trip,
        add_location_visits_to_trip,
    ]

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        context_schema=AgentContext,
    )


agent = build_travel_agent()


async def run_travel_agent(
    messages: list[dict],
    trip_context: dict | None = None,
) -> str:
    context = AgentContext(
        user_id=(trip_context or {}).get("user_id") or "anonymous",
        trip_id=(trip_context or {}).get("trip_id"),
    )
    result = await agent.ainvoke({"messages": messages}, context=context)
    return result["messages"][-1].content


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    out = asyncio.run(
        run_travel_agent(
            [{"role": "user", "content": "Tell me about the flight to Chennai on 07/15/2026"}]
        )
    )
    print(out)
