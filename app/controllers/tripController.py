from fastapi import APIRouter, Depends, status

from app.deps import get_current_user_id
from app.models.model import (
    TripCreateRequest,
    Trip,
    TripListResponse,
    TripDeleteResponse,
)
from app.services import tripService

router = APIRouter(prefix="/trip", tags=["trip"])


@router.post(
    "/create",
    summary="Create a new trip",
    response_model=Trip,
    status_code=status.HTTP_201_CREATED,
)
async def create_trip(
    request: TripCreateRequest,
    user_id: str = Depends(get_current_user_id),
) -> Trip:
    return await tripService.create_trip(request, user_id)


@router.get(
    "/list",
    summary="List all trips for the current user",
    response_model=TripListResponse,
)
async def list_trips(
    user_id: str = Depends(get_current_user_id),
) -> TripListResponse:
    return await tripService.list_trips(user_id)


@router.delete(
    "/{trip_id}",
    summary="Delete a trip",
    response_model=TripDeleteResponse,
)
async def delete_trip(
    trip_id: str,
    user_id: str = Depends(get_current_user_id),
) -> TripDeleteResponse:
    return await tripService.delete_trip(trip_id, user_id)
