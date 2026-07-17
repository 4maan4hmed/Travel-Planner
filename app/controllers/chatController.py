from fastapi import APIRouter, Depends

from app.deps import get_current_user_id
from app.models.chatModel import (
    Chat,
    ChatDeleteResponse,
    ChatListResponse,
    ResumeRequest,
    ResumeResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services import chatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get(
    "/list",
    summary="List all chat sessions for the current user",
    response_model=ChatListResponse,
)
async def list_chats(
    user_id: str = Depends(get_current_user_id),
) -> ChatListResponse:
    return await chatService.list_chats(user_id)


@router.get(
    "/{session_id}",
    summary="Get a chat session by id",
    response_model=Chat,
)
async def get_chat(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> Chat:
    return await chatService.get_chat(session_id, user_id)


@router.post(
    "/message",
    summary="Send a message; creates a new chat session when session_id is omitted",
    response_model=SendMessageResponse,
)
async def send_message(
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
) -> SendMessageResponse:
    return await chatService.send_message(request, user_id)


@router.post(
    "/resume",
    summary="Resume an interrupted graph turn (e.g. approve or reject a flight)",
    response_model=ResumeResponse,
)
async def resume_message(
    request: ResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> ResumeResponse:
    return await chatService.resume_message(request, user_id)


@router.delete(
    "/{session_id}",
    summary="Delete a chat session",
    response_model=ChatDeleteResponse,
)
async def delete_chat(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
) -> ChatDeleteResponse:
    return await chatService.delete_chat(session_id, user_id)
