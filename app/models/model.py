from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Trip(BaseModel):
    trip_id: str | None = Field(default=None, description="MongoDB _id as string")
    user_id: str = Field(..., description="The ID of the user who created the trip")
    time_created: datetime = Field(..., description="The time the trip was created")
    name: str = Field(..., description="The name of the trip")
    from_location: str = Field(..., description="The starting location of the trip")
    to_location: str = Field(..., description="The destination location of the trip")
    start_date: datetime = Field(..., description="The start date of the trip")
    end_date: datetime = Field(..., description="The end date of the trip")


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
    session_id: str
    id: str
    content: str
    role: MessageRole
    created_at: datetime


class Chat(BaseModel):
    session_id: str
    messages: list[Message]


class ChatSession(BaseModel):
    session_id: str
    created_at: datetime
