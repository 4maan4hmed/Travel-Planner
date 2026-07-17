from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status

from app.agent.travelAgent import (
    build_interrupt_payload,
    is_session_interrupted,
    resume_travel_agent,
    run_travel_agent,
)
from app.models.chatModel import (
    Chat,
    ChatDeleteResponse,
    ChatListResponse,
    InterruptPayload,
    Message,
    MessageRole,
    ResumeRequest,
    ResumeResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.models.tripModel import FlightDetails
from app.repositories import chatRepositories


def _to_interrupt_payload(raw: dict | None) -> InterruptPayload | None:
    if not raw:
        return None
    payload = build_interrupt_payload(raw)
    return InterruptPayload(
        type="flight_approval",
        trip_id=payload.get("trip_id"),
        flight=FlightDetails(**payload["flight"]),
        flight_options=payload.get("flight_options"),
    )


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
        chat = await chatRepositories.insert_chat(
            Chat(
                user_id=user_id,
                created_at=now,
                updated_at=now,
                messages=[],
            )
        )
        session_id = chat.session_id

    if await is_session_interrupted(session_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is awaiting flight approval. Use /chat/resume instead.",
        )

    user_message = Message(
        id=str(uuid4()),
        role=MessageRole.USER,
        content=request.content,
        created_at=now,
    )

    try:
        result = await run_travel_agent(
            request.content,
            session_id=session_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    interrupt = _to_interrupt_payload(result.interrupt)
    messages_to_append = [user_message]

    if result.status == "interrupted":
        assistant_message = Message(
            id=str(uuid4()),
            role=MessageRole.ASSISTANT,
            content="Waiting for your flight approval.",
            created_at=now,
        )
        messages_to_append.append(assistant_message)
        chat = await chatRepositories.append_messages(
            session_id,
            user_id,
            messages_to_append,
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
            status="interrupted",
            interrupt=interrupt,
        )

    assistant_message = Message(
        id=str(uuid4()),
        role=MessageRole.ASSISTANT,
        content=result.message or "",
        created_at=now,
    )
    messages_to_append.append(assistant_message)
    chat = await chatRepositories.append_messages(
        session_id,
        user_id,
        messages_to_append,
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
        status="complete",
    )


async def resume_message(
    request: ResumeRequest,
    user_id: str,
) -> ResumeResponse:
    now = datetime.utcnow()
    chat = await chatRepositories.find_chat_by_id(request.session_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="chat not found")

    try:
        result = await resume_travel_agent(
            session_id=request.session_id,
            user_id=user_id,
            approved=request.approved,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    interrupt = _to_interrupt_payload(result.interrupt)

    if result.status == "interrupted":
        assistant_message = Message(
            id=str(uuid4()),
            role=MessageRole.ASSISTANT,
            content="Waiting for your flight approval.",
            created_at=now,
        )
        chat = await chatRepositories.append_messages(
            request.session_id,
            user_id,
            [assistant_message],
            now,
        )
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="chat not found",
            )
        return ResumeResponse(
            session_id=request.session_id,
            status="interrupted",
            assistant_message=assistant_message,
            interrupt=interrupt,
        )

    assistant_message = Message(
        id=str(uuid4()),
        role=MessageRole.ASSISTANT,
        content=result.message or "",
        created_at=now,
    )
    chat = await chatRepositories.append_messages(
        request.session_id,
        user_id,
        [assistant_message],
        now,
    )
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="chat not found",
        )
    return ResumeResponse(
        session_id=request.session_id,
        status="complete",
        assistant_message=assistant_message,
    )
