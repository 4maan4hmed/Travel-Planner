from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.models.tripModel import FlightDetails


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
    created_at: datetime
    updated_at: datetime
    messages: list[Message] = []


class ChatListResponse(BaseModel):
    chats: list[Chat]


class ChatDeleteResponse(BaseModel):
    session_id: str
    message: str = "chat deleted successfully"


class SendMessageRequest(BaseModel):
    session_id: str | None = None
    content: str


class InterruptPayload(BaseModel):
    type: Literal["flight_approval"]
    trip_id: str | None = None
    flight: FlightDetails
    flight_options: list[dict] | None = None


class SendMessageResponse(BaseModel):
    session_id: str
    user_message: Message
    assistant_message: Message | None = None
    status: Literal["complete", "interrupted"]
    interrupt: InterruptPayload | None = None


class ResumeRequest(BaseModel):
    session_id: str
    approved: bool


class ResumeResponse(BaseModel):
    session_id: str
    status: Literal["complete", "interrupted"]
    assistant_message: Message | None = None
    interrupt: InterruptPayload | None = None
