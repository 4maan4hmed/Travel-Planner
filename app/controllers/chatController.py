from fastapi import APIRouter, Depends, status

from app.deps import get_current_user_id
from app.models.model import (
    Chat,
    ChatCreateRequest,
    ChatCreateResponse,
    ChatDeleteResponse,
    ChatListResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services import chatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/create",
    summary="Create a new chat session",
    response_model=ChatCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    request: ChatCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> ChatCreateResponse:
    return await chatService.create_chat(request, user_id)


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
    "/{session_id}/message",
    summary="Send a message in a chat session",
    response_model=SendMessageResponse,
)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
) -> SendMessageResponse:
    return await chatService.send_message(session_id, request, user_id)


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
