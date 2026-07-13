from langchain.agents import create_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def build_travel_agent():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",  # or another Groq-supported model
        temperature=0,
    )

    tools = []  # Add your tools later

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt="You are a travel planning assistant...",
    )

agent = build_travel_agent()


def run_travel_agent(
    messages: list[dict],
    trip_context: dict | None = None,
) -> str:
    result = agent.invoke({"messages": messages})
    return result["messages"][-1].content

if __name__ == "__main__":
    out = run_travel_agent([{"role": "user", "content": "What is the capital of France?"}])
    print(out)