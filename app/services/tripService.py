from datetime import datetime

from fastapi import HTTPException, status

from app.models.model import (
    Trip,
    TripCreateRequest,
    TripDeleteResponse,
    TripListResponse,
)
from app.repositories import tripRepositories


def create_trip(request: TripCreateRequest, user_id: str) -> Trip:
    if request.end_date < request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date",
        )

    trip = Trip(
        user_id=user_id,
        time_created=datetime.utcnow(),
        name=request.name,
        from_location=request.from_location,
        to_location=request.to_location,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return tripRepositories.insert_trip(trip)


def list_trips(user_id: str) -> TripListResponse:
    trips = tripRepositories.find_trips_by_user(user_id)
    return TripListResponse(trips=trips)


def delete_trip(trip_id: str, user_id: str) -> TripDeleteResponse:
    deleted = tripRepositories.delete_trip(trip_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="trip not found",
        )
    return TripDeleteResponse(trip_id=trip_id)
