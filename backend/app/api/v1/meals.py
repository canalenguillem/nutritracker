from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.api.deps import (
    CurrentUserDependency,
    FoodAnalysisServiceDependency,
    MealServiceDependency,
    SettingsDependency,
)
from app.core.errors import ApiError
from app.models.base import utc_now
from app.schemas.analysis import (
    ClarificationQuestionResponse,
    EstimatedItemResponse,
    FoodEstimateResponse,
)
from app.schemas.meals import (
    DailySummaryResponse,
    MealCreateRequest,
    MealItemRequest,
    MealResponse,
    MealUpdateRequest,
)
from app.services.food_analysis import (
    FoodAnalysisDisabledError,
    FoodAnalysisError,
    FoodEstimate,
    MealPhoto,
)
from app.services.image_validation import ImageTooLargeError, InvalidImageError, validate_photo
from app.services.meals import (
    EmptyMealError,
    MealChanges,
    MealNotFoundError,
    NewMeal,
    NewMealItem,
    local_log_date,
)

router = APIRouter(prefix="/meals", tags=["meals"])

LogDateQuery = Annotated[date | None, Query(alias="date")]


def _to_new_item(item: MealItemRequest) -> NewMealItem:
    return NewMealItem(
        name=item.name,
        quantity=item.quantity,
        unit=item.unit,
        kcal=item.kcal,
        protein_g=item.protein_g,
        fat_g=item.fat_g,
        carbohydrates_g=item.carbohydrates_g,
    )


@router.get("", response_model=list[MealResponse])
async def list_meals(
    user: CurrentUserDependency,
    service: MealServiceDependency,
    log_date: LogDateQuery = None,
) -> list[MealResponse]:
    meals = await service.list_meals(user, log_date)
    return [MealResponse.model_validate(meal) for meal in meals]


@router.get("/summary", response_model=DailySummaryResponse)
async def read_daily_summary(
    user: CurrentUserDependency,
    service: MealServiceDependency,
    log_date: LogDateQuery = None,
) -> DailySummaryResponse:
    day = log_date if log_date is not None else local_log_date(utc_now(), user.timezone)
    summary = await service.daily_totals(user, day)
    return DailySummaryResponse(
        log_date=summary.log_date,
        meal_count=summary.meal_count,
        total_kcal=summary.totals.kcal,
        protein_g=summary.totals.protein_g,
        fat_g=summary.totals.fat_g,
        carbohydrates_g=summary.totals.carbohydrates_g,
    )


@router.get("/recent", response_model=list[MealResponse])
async def list_recent_meals(
    user: CurrentUserDependency,
    service: MealServiceDependency,
    query: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> list[MealResponse]:
    """The meals worth repeating, so a usual dish need not be typed again."""
    meals = await service.recent_meals(user, query, limit)
    return [MealResponse.model_validate(meal) for meal in meals]


@router.post("/describe", response_model=FoodEstimateResponse)
async def describe_meal(
    user: CurrentUserDependency,
    analysis: FoodAnalysisServiceDependency,
    settings: SettingsDependency,
    description: Annotated[str, Form(min_length=1, max_length=600)],
    photo: Annotated[UploadFile | None, File()] = None,
) -> FoodEstimateResponse:
    """Estimate a meal from a description, optionally with a picture of the label.

    Nothing is stored: neither the estimate nor the picture, which is sent to
    the provider to be read and then dropped.
    """
    meal_photo = await _read_photo(photo, settings.max_upload_mb)

    try:
        estimate = await analysis.describe(user.id, description, user.locale, meal_photo)
    except FoodAnalysisDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The food estimator is not configured.",
        ) from error
    except FoodAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The meal could not be estimated. Try describing it again.",
        ) from error

    return _to_estimate_response(estimate)


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(
    payload: MealCreateRequest,
    user: CurrentUserDependency,
    service: MealServiceDependency,
) -> MealResponse:
    meal = await service.create_meal(
        user,
        NewMeal(
            meal_type=payload.meal_type,
            eaten_at=payload.eaten_at,
            items=[_to_new_item(item) for item in payload.items],
            notes=payload.notes,
        ),
    )
    return MealResponse.model_validate(meal)


@router.get("/{meal_id}", response_model=MealResponse)
async def read_meal(
    meal_id: UUID,
    user: CurrentUserDependency,
    service: MealServiceDependency,
) -> MealResponse:
    try:
        meal = await service.get_meal(user, meal_id)
    except MealNotFoundError as error:
        raise _not_found() from error
    return MealResponse.model_validate(meal)


@router.patch("/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: UUID,
    payload: MealUpdateRequest,
    user: CurrentUserDependency,
    service: MealServiceDependency,
) -> MealResponse:
    changes = MealChanges(
        meal_type=payload.meal_type,
        eaten_at=payload.eaten_at,
        notes=payload.notes,
        notes_provided="notes" in payload.model_fields_set,
        items=(
            [_to_new_item(item) for item in payload.items] if payload.items is not None else None
        ),
    )

    try:
        meal = await service.update_meal(user, meal_id, changes)
    except MealNotFoundError as error:
        raise _not_found() from error
    except EmptyMealError as error:
        raise _empty_meal() from error

    return MealResponse.model_validate(meal)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: UUID,
    user: CurrentUserDependency,
    service: MealServiceDependency,
) -> None:
    try:
        await service.delete_meal(user, meal_id)
    except MealNotFoundError as error:
        raise _not_found() from error


async def _read_photo(photo: UploadFile | None, max_upload_mb: int) -> MealPhoto | None:
    if photo is None or not photo.filename:
        return None

    content = await photo.read()
    try:
        return validate_photo(content, max_upload_mb * 1024 * 1024)
    except ImageTooLargeError as error:
        raise ApiError(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            code="IMAGE_TOO_LARGE",
            detail=f"The picture must be {max_upload_mb} MB or smaller.",
        ) from error
    except InvalidImageError as error:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="INVALID_IMAGE",
            detail="The picture must be a JPEG, PNG or WebP image.",
        ) from error


def _to_estimate_response(estimate: FoodEstimate) -> FoodEstimateResponse:
    return FoodEstimateResponse(
        summary=estimate.summary,
        items=[
            EstimatedItemResponse(
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                kcal=item.kcal,
                protein_g=item.protein_g,
                fat_g=item.fat_g,
                carbohydrates_g=item.carbohydrates_g,
                confidence=item.confidence,
                assumptions=item.assumptions,
            )
            for item in estimate.items
        ],
        total_kcal=estimate.total_kcal,
        questions=[
            ClarificationQuestionResponse(
                key=question.key, question=question.question, options=question.options
            )
            for question in estimate.questions
        ],
        confidence=estimate.confidence,
        warning=estimate.warning,
        from_cache=estimate.from_cache,
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This meal does not exist.")


def _empty_meal() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="A meal must contain at least one food item.",
    )
