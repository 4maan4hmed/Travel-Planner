import asyncio
import serpapi
from dotenv import load_dotenv
import os
from langchain_core.tools import tool
from app.tools.current_location import get_current_city
load_dotenv()

client = serpapi.Client(api_key=os.getenv("SERPAPI_KEY"))

@tool
async def check_flight(departure_city: str, arrival_city: str, outbound_date: str, return_date: str):
  """Check flight availability between two cities on given dates.

    Args:
        departure_city: City or airport name to depart from, e.g. "Bangalore".
        arrival_city: City or airport name to arrive at, e.g. "Delhi".
        outbound_date: Departure date in YYYY-MM-DD format.
        return_date: Return date in YYYY-MM-DD format.
    """
  print(f"Checking flight from {departure_city} to {arrival_city} on {outbound_date} and {return_date}")
  departure_id,arrival_id = await asyncio.gather(city_to_code(departure_city), city_to_code(arrival_city))
  results = client.search({
      "engine": "google_flights",
      "departure_id": departure_id,
      "arrival_id": arrival_id,
      "outbound_date": outbound_date,
      "return_date": return_date,
      "currency": "INR",
      "hl": "en"})
  best_flights = results.get("best_flights", []) 

  return str(summarize_flights(best_flights))

def summarize_flights(flight_list):
    summary = []
    for itinerary in flight_list:
        legs = itinerary["flights"]
        first_leg = legs[0]
        last_leg = legs[-1]
        
        summary.append({
            "price": itinerary.get("price"),
            "airline": first_leg.get("airline"),
            "flight_numbers": [leg["flight_number"] for leg in legs],
            "departure": f"{first_leg['departure_airport']['id']} at {first_leg['departure_airport']['time']}",
            "arrival": f"{last_leg['arrival_airport']['id']} at {last_leg['arrival_airport']['time']}",
            "total_duration_min": itinerary.get("total_duration"),
            "stops": len(legs) - 1,
            "type": itinerary.get("type"),
            #"booking_token": itinerary.get("departure_token"),
        })
    return summary


async def city_to_code(city_query: str) -> str:
    """Returns a list of IATA codes for a given city/keyword."""
    results = client.search({
        "engine": "google_flights_autocomplete",
        "q": city_query,
        "hl": "en",
        "gl": "in"
    })
    suggestions = results.get("suggestions", [])
    codes = []
    for s in suggestions:
        for airport in s.get("airports", []):
            codes.append(airport["id"])
    return codes[0] if codes else None

if __name__ == "__main__":
  out = (asyncio.run(check_flight("Banglore", "New Delhi", "2026-07-15", "2026-07-15"))) 
  with open("flight_check.txt", "w", encoding="utf-8") as file:
    file.write(out)