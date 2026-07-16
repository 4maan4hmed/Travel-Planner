from pydantic import BaseModel
from enum import Enum
from datetime import datetime

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


class SendMessageResponse(BaseModel):
    session_id: str
    user_message: Message
    assistant_message: Message 
