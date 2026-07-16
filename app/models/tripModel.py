from datetime import datetime
from pydantic import BaseModel, Field


class LocationVisit(BaseModel):
    location: str = Field(..., description="The location of the visit")
    date: str = Field(..., description="Visit date in YYYY-MM-DD format")
    notes: str = Field(..., description="The notes of the visit")

class FlightDetails(BaseModel):
    airline: str = Field(..., description="Airline name, e.g. IndiGo")
    flight_number: str = Field(..., description="Flight number, e.g. 6E-204")
    departure_location: str = Field(..., description="Departure city or airport code")
    arrival_location: str = Field(..., description="Arrival city or airport code")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    price: float = Field(..., description="Ticket price in INR")

class Trip(BaseModel):
    trip_id: str | None = Field(default=None, description="MongoDB _id as string")
    user_id: str = Field(..., description="The ID of the user who created the trip")
    time_created: datetime = Field(..., description="The time the trip was created")
    name: str = Field(..., description="The name of the trip")
    from_location: str = Field(..., description="The starting location of the trip")
    to_location: str = Field(..., description="The destination location of the trip")
    start_date: datetime = Field(..., description="The start date of the trip")
    end_date: datetime = Field(..., description="The end date of the trip")
    location_visits: list[LocationVisit] = Field(default=[], description="The list of location to be visited in the trip")  
    flight_details: FlightDetails | None = Field(default=None, description="The flight details for the trip")


class TripCreateRequest(BaseModel):
    name: str
    from_location: str
    to_location: str
    start_date: datetime
    end_date: datetime


class TripListResponse(BaseModel):
    trips: list[Trip]


class TripDeleteResponse(BaseModel):
    trip_id: str
    message: str = "trip deleted successfully"
