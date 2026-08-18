from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUserDependency, ExerciseServiceDependency
from app.schemas.exercises import (
    ExerciseCreateRequest,
    ExerciseResponse,
    ExerciseUpdateRequest,
)
from app.services.exercises import ExerciseChanges, ExerciseNotFoundError, NewExercise

router = APIRouter(prefix="/exercises", tags=["exercises"])

LogDateQuery = Annotated[date | None, Query(alias="date")]


@router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    user: CurrentUserDependency,
    service: ExerciseServiceDependency,
    log_date: LogDateQuery = None,
) -> list[ExerciseResponse]:
    exercises = await service.list_exercises(user, log_date)
    return [ExerciseResponse.model_validate(exercise) for exercise in exercises]


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: ExerciseCreateRequest,
    user: CurrentUserDependency,
    service: ExerciseServiceDependency,
) -> ExerciseResponse:
    exercise = await service.create_exercise(
        user,
        NewExercise(
            activity_name=payload.activity_name,
            duration_minutes=payload.duration_minutes,
            intensity=payload.intensity,
            performed_at=payload.performed_at,
            confirmed_calories=payload.confirmed_calories,
            notes=payload.notes,
            weight_kg=payload.weight_kg,
        ),
    )
    return ExerciseResponse.model_validate(exercise)


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def read_exercise(
    exercise_id: UUID,
    user: CurrentUserDependency,
    service: ExerciseServiceDependency,
) -> ExerciseResponse:
    try:
        exercise = await service.get_exercise(user, exercise_id)
    except ExerciseNotFoundError as error:
        raise _not_found() from error
    return ExerciseResponse.model_validate(exercise)


@router.patch("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: UUID,
    payload: ExerciseUpdateRequest,
    user: CurrentUserDependency,
    service: ExerciseServiceDependency,
) -> ExerciseResponse:
    changes = ExerciseChanges(
        activity_name=payload.activity_name,
        duration_minutes=payload.duration_minutes,
        intensity=payload.intensity,
        performed_at=payload.performed_at,
        confirmed_calories=payload.confirmed_calories,
        confirmed_calories_provided="confirmed_calories" in payload.model_fields_set,
        notes=payload.notes,
        notes_provided="notes" in payload.model_fields_set,
    )

    try:
        exercise = await service.update_exercise(user, exercise_id, changes)
    except ExerciseNotFoundError as error:
        raise _not_found() from error

    return ExerciseResponse.model_validate(exercise)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: UUID,
    user: CurrentUserDependency,
    service: ExerciseServiceDependency,
) -> None:
    try:
        await service.delete_exercise(user, exercise_id)
    except ExerciseNotFoundError as error:
        raise _not_found() from error


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="This exercise does not exist."
    )
