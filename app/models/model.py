from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class Activity(BaseModel):
    id: str
    location: str
    description: str

class Trip(BaseModel):
    id: str
    name: str
    from_location: str
    to_location: str
    start_date: datetime
    end_date: datetime
    activities: list[Activity]

class Message(BaseModel):
    session_id: str
    id: str
    content: str
    role: Literal["user", "assistant"]
    created_at: datetime

class Chat(BaseModel):
    session_id: str
    messages: list[Message]

class ChatSession(BaseModel):
    session_id: str
    messages: list[Message]
    created_at: datetime