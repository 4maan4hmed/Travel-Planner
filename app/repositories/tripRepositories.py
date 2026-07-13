from bson import ObjectId

from app.db.mongo import get_trips_collection
from app.models.model import Trip


async def insert_trip(trip: Trip) -> Trip:
    collection = get_trips_collection()
    result = collection.insert_one(trip.model_dump(exclude={"trip_id"}))
    trip.trip_id = str(result.inserted_id)
    return trip 


async def find_trips_by_user(user_id: str) -> list[Trip]:
    collection = get_trips_collection()
    docs = collection.find({"user_id": user_id})
    trips: list[Trip] = []
    for doc in docs:
        trip_id = str(doc.pop("_id"))
        trips.append(Trip(**doc, trip_id=trip_id))
    return trips


async def delete_trip(trip_id: str, user_id: str) -> bool:
    collection = get_trips_collection()
    result = collection.delete_one({"_id": ObjectId(trip_id), "user_id": user_id})
    return result.deleted_count > 0
