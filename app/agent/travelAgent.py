from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langgraph.checkpoint.mongodb import MongoDBSaver
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
from app.config.settings import get_settings
from app.db.mongo import get_client

SYSTEM_PROMPT = """You are a travel planning assistant.
Workflow:
1. When the user wants to plan a trip, call create_trip first and remember the trip_id, get what city you are in with get_current_city, parse out the rest of the information
by asking the user for the details. Do not ask the user for trip name , just name the trip whatever you feel is appropriate, keep it professional.
2. Help them find flights with check_flight. After they choose one, call book_flight, then add_flight_to_trip with that trip_id. After booking the flight let the user know you have book the flight with details 
3. Suggest places with find_visit_locations. After they pick places, call add_location_visits_to_trip with that trip_id.
Use YYYY-MM-DD dates. Always reuse the trip_id from create_trip for later updates.
4. If the user wants to add more details to the trip, ask them for the details and call the appropriate tool.
"""


def build_travel_agent():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=get_settings().groq_api_key,
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

    checkpointer = MongoDBSaver(
        get_client(),
        db_name=get_settings().mongo_db_name,
    )

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        context_schema=AgentContext,
        checkpointer=checkpointer,
    )


agent = build_travel_agent()


async def run_travel_agent(
    message: str,
    session_id: str,
    user_id: str = "anonymous",
) -> str:
    context = AgentContext(user_id=user_id)
    config = {"configurable": {"thread_id": session_id}}
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        context=context,
        config=config,
    )
    return result["messages"][-1].content


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
