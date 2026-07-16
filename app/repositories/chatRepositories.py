from datetime import datetime

from bson import ObjectId
from pymongo import ReturnDocument

from app.db.mongo import get_chat_collection
from app.models.chatModel import Chat, Message


def _doc_to_chat(doc: dict) -> Chat:
    session_id = str(doc.pop("_id"))
    return Chat(**doc, session_id=session_id)


async def insert_chat(chat: Chat) -> Chat:
    collection = get_chat_collection()
    result = collection.insert_one(chat.model_dump(exclude={"session_id"}))
    chat.session_id = str(result.inserted_id)
    return chat


async def find_chats_by_user(user_id: str) -> list[Chat]:
    collection = get_chat_collection()
    chats: list[Chat] = []
    for doc in collection.find({"user_id": user_id}):
        chats.append(_doc_to_chat(doc))
    return chats


async def find_chat_by_id(session_id: str, user_id: str) -> Chat | None:
    collection = get_chat_collection()
    doc = collection.find_one({"_id": ObjectId(session_id), "user_id": user_id})
    if not doc:
        return None
    return _doc_to_chat(doc)


async def delete_chat(session_id: str, user_id: str) -> bool:
    collection = get_chat_collection()
    result = collection.delete_one({"_id": ObjectId(session_id), "user_id": user_id})
    return result.deleted_count > 0


async def append_messages(
    session_id: str,
    user_id: str,
    messages: list[Message],
    updated_at: datetime,
) -> Chat | None:
    collection = get_chat_collection()
    result = collection.find_one_and_update(
        {"_id": ObjectId(session_id), "user_id": user_id},
        {
            "$push": {"messages": {"$each": [m.model_dump() for m in messages]}},
            "$set": {"updated_at": updated_at},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        return None
    return _doc_to_chat(result)
