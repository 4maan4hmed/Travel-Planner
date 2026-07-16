import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from app.config.settings import get_settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        mongo_uri = get_settings().mongo_uri

        _client = MongoClient(mongo_uri)
    return _client


def get_db() -> Database:
    db_name = get_settings().mongo_db_name
    print(db_name)
    return get_client()[db_name]


def get_trips_collection() -> Collection:
    return get_db()["trips"]

def get_chat_collection() -> Collection:
    return get_db()["chats"]
