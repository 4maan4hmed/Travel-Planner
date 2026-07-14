from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LocationVisit(BaseModel):
    location: str = Field(..., description="The location of the visit")
    date: datetime = Field(..., description="The date of the visit")
    notes: str = Field(..., description="The notes of the visit")

class FlightDetails(BaseModel):
    flight_number: str = Field(..., description="The flight number")
    departure_date: datetime = Field(..., description="The departure date")
    arrival_date: datetime = Field(..., description="The arrival date")
    departure_location: str = Field(..., description="The departure location")
    arrival_location: str = Field(..., description="The arrival location")
    price: float = Field(..., description="The price of the flight")
    airline: str = Field(..., description="The airline of the flight")
    flight_duration: int = Field(..., description="The duration of the flight")
    stops: int = Field(..., description="The number of stops of the flight")
    booking_token: str = Field(..., description="The booking token of the flight")

class Trip(BaseModel):
    trip_id: str | None = Field(default=None, description="MongoDB _id as string")
    user_id: str = Field(..., description="The ID of the user who created the trip")
    time_created: datetime = Field(..., description="The time the trip was created")
    name: str = Field(..., description="The name of the trip")
    from_location: str = Field(..., description="The starting location of the trip")
    to_location: str = Field(..., description="The destination location of the trip")
    start_date: datetime = Field(..., description="The start date of the trip")
    end_date: datetime = Field(..., description="The end date of the trip")

class TripCreated(Trip):
    location_visits: list[LocationVisit] = Field(..., description="The list of location to be visited in the trip")
    flight_details: FlightDetails = Field(default=None, description="The flight details for the trip")

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


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime


class Chat(BaseModel):
    session_id: str | None = None
    user_id: str
    trip_id: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[Message] = []


class ChatCreateRequest(BaseModel):
    trip_id: str | None = None


class ChatCreateResponse(BaseModel):
    session_id: str
    created_at: datetime


class ChatListResponse(BaseModel):
    chats: list[Chat]


class ChatDeleteResponse(BaseModel):
    session_id: str
    message: str = "chat deleted successfully"


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    session_id: str
    user_message: Message
    assistant_message: Message  # stub for now
