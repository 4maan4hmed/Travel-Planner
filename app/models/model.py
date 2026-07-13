from pydantic import BaseModel, Enum
from datetime import datetime


class Trip(BaseModel):
    id: str
    name: str
    from_location: str
    to_location: str
    start_date: datetime
    end_date: datetime


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