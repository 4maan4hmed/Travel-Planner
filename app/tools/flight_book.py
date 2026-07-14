from langchain_core.tools import tool
from app.models.model import FlightDetails

from langchain_core.tools import tool
from app.models.model import FlightDetails

@tool
async def book_flight(flight_details: FlightDetails):
    """Fake-book a flight. Call this only after the user confirms which flight to book.

    Args:
        flight_details: The selected flight (airline, flight number, route, dates, price, etc.).
    """
    print(
        f"Flight booked: {flight_details.airline} {flight_details.flight_number} "
        f"from {flight_details.departure_location} to {flight_details.arrival_location} "
        f"on {flight_details.departure_date} | price: {flight_details.price}"
    )
    return (
        f"Flight successfully booked: {flight_details.airline} "
        f"{flight_details.flight_number} from {flight_details.departure_location} "
        f"to {flight_details.arrival_location} on {flight_details.departure_date}."
    )