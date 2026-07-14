import asyncio
import json
import os

import serpapi
from langchain_core.tools import tool

_client: serpapi.Client | None = None


def _get_client() -> serpapi.Client:
    global _client
    if _client is None:
        _client = serpapi.Client(api_key=os.getenv("SERPAPI_KEY"))
    return _client


def summarize_places(sights: list[dict]) -> list[dict]:
    summary = []
    for place in sights[:5]:
        summary.append(
            {
                "name": place.get("title"),
                "description": place.get("description"),
                "rating": place.get("rating"),
                "reviews": place.get("reviews"),
                "price": place.get("price"),
            }
        )
    return summary


@tool
async def find_visit_locations(city: str) -> str:
    """Find popular places to visit and things to do inside a city.

    Args:
        city: City to explore, e.g. "Bangalore", "Paris", "Maldives".
    """
    try:
        results = await asyncio.to_thread(
            _get_client().search,
            {
                "engine": "google",
                "q": f"things to do in {city}",
                "hl": "en",
                "gl": "in",
            },
        )
    except Exception as e:
        return json.dumps({"error": f"Places search failed: {e}"})

    sights = (results.get("top_sights") or {}).get("sights", [])
    if not sights:
        return json.dumps({"error": f"No places found to visit in '{city}'."})

    return json.dumps(summarize_places(sights[:5]))


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    out = asyncio.run(find_visit_locations.ainvoke({"city": "Bangalore"}))
    print(out)
