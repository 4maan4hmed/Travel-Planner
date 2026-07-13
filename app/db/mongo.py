import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

_client: MongoClient | None = None

load_dotenv()

def get_client() -> MongoClient:
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

        _client = MongoClient(mongo_uri)
    return _client


def get_db() -> Database:
    db_name = os.getenv("MONGO_DB_NAME", "travel_planner")
    print(db_name)
    return get_client()[db_name]


def get_trips_collection() -> Collection:
    return get_db()["trips"]

def get_chat_collection() -> Collection:
    return get_db()["chats"]
