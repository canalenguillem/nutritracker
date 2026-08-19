from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUserDependency, SleepServiceDependency
from app.core.errors import ApiError
from app.models.base import utc_now
from app.models.sleep import SleepEntry
from app.schemas.sleep import (
    SleepCreateRequest,
    SleepEntryResponse,
    SleepUpdateRequest,
    SleptNightResponse,
)
from app.services.daily_logs import local_log_date
from app.services.sleep import (
    ImpossibleNightError,
    NewSleepEntry,
    SleepChanges,
    SleepEntryNotFoundError,
    hours_of,
)

router = APIRouter(prefix="/sleep", tags=["sleep"])

LogDateQuery = Annotated[date | None, Query(alias="date")]


@router.get("", response_model=SleptNightResponse | None)
async def read_night(
    user: CurrentUserDependency,
    service: SleepServiceDependency,
    log_date: LogDateQuery = None,
) -> SleptNightResponse | None:
    """The night that ended on this day, or nothing if none was recorded."""
    day = log_date if log_date is not None else local_log_date(utc_now(), user.timezone)
    night = await service.night_of(user, day)
    if night is None:
        return None

    return _to_response(night.entry)


@router.post("", response_model=SleptNightResponse, status_code=status.HTTP_201_CREATED)
async def create_night(
    payload: SleepCreateRequest,
    user: CurrentUserDependency,
    service: SleepServiceDependency,
) -> SleptNightResponse:
    try:
        entry = await service.record(
            user,
            NewSleepEntry(
                started_at=payload.started_at,
                ended_at=payload.ended_at,
                quality=payload.quality,
                notes=payload.notes,
            ),
        )
    except ImpossibleNightError as error:
        raise _impossible(error) from error

    return _to_response(entry)


@router.get("/{entry_id}", response_model=SleptNightResponse)
async def read_entry(
    entry_id: UUID,
    user: CurrentUserDependency,
    service: SleepServiceDependency,
) -> SleptNightResponse:
    try:
        entry = await service.get_entry(user, entry_id)
    except SleepEntryNotFoundError as error:
        raise _not_found() from error

    return _to_response(entry)


@router.patch("/{entry_id}", response_model=SleptNightResponse)
async def update_entry(
    entry_id: UUID,
    payload: SleepUpdateRequest,
    user: CurrentUserDependency,
    service: SleepServiceDependency,
) -> SleptNightResponse:
    provided = payload.model_fields_set
    try:
        entry = await service.update_entry(
            user,
            entry_id,
            SleepChanges(
                started_at=payload.started_at,
                ended_at=payload.ended_at,
                quality=payload.quality,
                quality_provided="quality" in provided,
                notes=payload.notes,
                notes_provided="notes" in provided,
            ),
        )
    except SleepEntryNotFoundError as error:
        raise _not_found() from error
    except ImpossibleNightError as error:
        raise _impossible(error) from error

    return _to_response(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_night(
    entry_id: UUID,
    user: CurrentUserDependency,
    service: SleepServiceDependency,
) -> None:
    try:
        await service.delete_entry(user, entry_id)
    except SleepEntryNotFoundError as error:
        raise _not_found() from error


def _to_response(entry: SleepEntry) -> SleptNightResponse:
    return SleptNightResponse(
        **SleepEntryResponse.model_validate(entry).model_dump(), hours=hours_of(entry)
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This night does not exist.")


def _impossible(error: ImpossibleNightError) -> ApiError:
    return ApiError(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        detail=str(error),
    )
