from datetime import datetime

from app.models.model import (
    FlightDetails,
    LocationVisit,
    Trip,
    TripCreateRequest,
    TripDeleteResponse,
    TripListResponse,
)
from app.repositories import tripRepositories


class TripError(Exception):
    """Domain error for trip operations (not HTTP-specific)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TripValidationError(TripError):
    pass


class TripNotFoundError(TripError):
    pass


async def create_trip(request: TripCreateRequest, user_id: str) -> Trip:
    if request.end_date < request.start_date:
        raise TripValidationError("end_date must be on or after start_date")

    trip = Trip(
        user_id=user_id,
        time_created=datetime.utcnow(),
        name=request.name,
        from_location=request.from_location,
        to_location=request.to_location,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return await tripRepositories.insert_trip(trip)


async def list_trips(user_id: str) -> TripListResponse:
    trips = await tripRepositories.find_trips_by_user(user_id)
    return TripListResponse(trips=trips)


async def add_flight_to_trip(
    trip_id: str,
    user_id: str,
    flight_details: FlightDetails,
) -> Trip:
    trip = await tripRepositories.set_flight_details(trip_id, user_id, flight_details)
    if not trip:
        raise TripNotFoundError(f"trip '{trip_id}' not found for this user")
    return trip


async def add_location_visits_to_trip(
    trip_id: str,
    user_id: str,
    visits: list[LocationVisit],
) -> Trip:
    trip = await tripRepositories.add_location_visits(trip_id, user_id, visits)
    if not trip:
        raise TripNotFoundError(f"trip '{trip_id}' not found for this user")
    return trip


async def delete_trip(trip_id: str, user_id: str) -> TripDeleteResponse:
    deleted = await tripRepositories.delete_trip(trip_id, user_id)
    if not deleted:
        raise TripNotFoundError("trip not found")
    return TripDeleteResponse(trip_id=trip_id)
