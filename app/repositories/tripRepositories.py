from bson import ObjectId
from pymongo import ReturnDocument

from app.db.mongo import get_trips_collection
from app.models.model import FlightDetails, LocationVisit, Trip


def _doc_to_trip(doc: dict) -> Trip:
    trip_id = str(doc.pop("_id"))
    return Trip(**doc, trip_id=trip_id)


async def insert_trip(trip: Trip) -> Trip:
    collection = get_trips_collection()
    result = collection.insert_one(trip.model_dump(exclude={"trip_id"}))
    trip.trip_id = str(result.inserted_id)
    return trip


async def find_trips_by_user(user_id: str) -> list[Trip]:
    collection = get_trips_collection()
    trips: list[Trip] = []
    for doc in collection.find({"user_id": user_id}):
        trips.append(_doc_to_trip(doc))
    return trips


async def find_trip_by_id(trip_id: str, user_id: str) -> Trip | None:
    collection = get_trips_collection()
    doc = collection.find_one({"_id": ObjectId(trip_id), "user_id": user_id})
    if not doc:
        return None
    return _doc_to_trip(doc)


async def set_flight_details(
    trip_id: str,
    user_id: str,
    flight_details: FlightDetails,
) -> Trip | None:
    collection = get_trips_collection()
    result = collection.find_one_and_update(
        {"_id": ObjectId(trip_id), "user_id": user_id},
        {"$set": {"flight_details": flight_details.model_dump()}},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        return None
    return _doc_to_trip(result)


async def add_location_visits(
    trip_id: str,
    user_id: str,
    visits: list[LocationVisit],
) -> Trip | None:
    collection = get_trips_collection()
    result = collection.find_one_and_update(
        {"_id": ObjectId(trip_id), "user_id": user_id},
        {
            "$push": {
                "location_visits": {
                    "$each": [v.model_dump() for v in visits],
                }
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        return None
    return _doc_to_trip(result)


async def delete_trip(trip_id: str, user_id: str) -> bool:
    collection = get_trips_collection()
    result = collection.delete_one({"_id": ObjectId(trip_id), "user_id": user_id})
    return result.deleted_count > 0
