from langchain.agents import create_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from app.tools.current_location import get_current_city
from app.tools.flight_check import check_flight
import asyncio
load_dotenv()

def build_travel_agent():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",  
        temperature=0,
    )

    tools = [get_current_city, check_flight]  

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a travel planning assistant...",
    )

agent = build_travel_agent()


async def run_travel_agent(
    messages: list[dict],
    trip_context: dict | None = None,
) -> str:
    result = await agent.ainvoke({"messages": messages})
    return result["messages"][-1].content

if __name__ == "__main__":
    out = asyncio.run(run_travel_agent([{"role": "user", "content": "Tell me about the flight to Chennai on 07/15/2026"}]))
    print(out)