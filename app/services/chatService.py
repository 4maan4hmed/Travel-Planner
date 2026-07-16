from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status

from app.agent.travelAgent import run_travel_agent
from app.models.chatModel import (
    Chat,
    ChatCreateRequest,
    ChatCreateResponse,
    ChatDeleteResponse,
    ChatListResponse,
    Message,
    MessageRole,
    SendMessageRequest,
    SendMessageResponse,
)
from app.repositories import chatRepositories



async def create_chat(request: ChatCreateRequest, user_id: str) -> ChatCreateResponse:
    now = datetime.utcnow()
    chat = Chat(
        user_id=user_id,
        created_at=now,
        updated_at=now,
        messages=[],
    )
    chat = await chatRepositories.insert_chat(chat)
    return ChatCreateResponse(session_id=chat.session_id, created_at=chat.created_at)


async def list_chats(user_id: str) -> ChatListResponse:
    chats = await chatRepositories.find_chats_by_user(user_id)
    return ChatListResponse(chats=chats)


async def get_chat(session_id: str, user_id: str) -> Chat:
    chat = await chatRepositories.find_chat_by_id(session_id, user_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="chat not found",
        )
    return chat


async def delete_chat(session_id: str, user_id: str) -> ChatDeleteResponse:
    deleted = await chatRepositories.delete_chat(session_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="chat not found",
        )
    return ChatDeleteResponse(session_id=session_id)


async def send_message(
    request: SendMessageRequest,
    user_id: str,
) -> SendMessageResponse:
    now = datetime.utcnow()
    if request.session_id:
        chat = await chatRepositories.find_chat_by_id(request.session_id, user_id)
        if not chat:
            raise HTTPException(status_code=404, detail="chat not found")
        session_id = request.session_id
    else:
        created = await create_chat(Chat(user_id=user_id), user_id)
        session_id = created.session_id
    user_message = Message(
        id=str(uuid4()),
        role=MessageRole.USER,
        content=request.content,
        created_at=now,
    )

    resp = await run_travel_agent(
        request.content,
        session_id=session_id,
        user_id=user_id,
    )
    assistant_message = Message(
        id=str(uuid4()),
        role=MessageRole.ASSISTANT,
        content=resp,
        created_at=now,
    )
    #assistant_message = agent_invoke()
    chat = await chatRepositories.append_messages(
        session_id,
        user_id,
        [user_message, assistant_message],
        now,
    )
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="chat not found",
        )
    return SendMessageResponse(
        session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
    )
