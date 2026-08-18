from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserDependency, WeightServiceDependency
from app.schemas.weights import (
    WeightCreateRequest,
    WeightEntryResponse,
    WeightHistoryResponse,
    WeightPointResponse,
)
from app.services.weights import NewWeightEntry, WeightEntryNotFoundError

router = APIRouter(prefix="/weights", tags=["weights"])


@router.get("", response_model=list[WeightEntryResponse])
async def list_weights(
    user: CurrentUserDependency,
    service: WeightServiceDependency,
) -> list[WeightEntryResponse]:
    entries = await service.list_entries(user)
    return [WeightEntryResponse.model_validate(entry) for entry in entries]


@router.get("/history", response_model=WeightHistoryResponse)
async def read_history(
    user: CurrentUserDependency,
    service: WeightServiceDependency,
) -> WeightHistoryResponse:
    """The readings with their smoothed trend, which is what shows a direction."""
    history = await service.history(user)
    return WeightHistoryResponse(
        points=[
            WeightPointResponse(
                measured_on=point.measured_on,
                weight_kg=point.weight_kg,
                trend_kg=point.trend_kg,
            )
            for point in history.points
        ],
        latest_weight_kg=history.latest_weight_kg,
        latest_trend_kg=history.latest_trend_kg,
        change_7_days_kg=history.change_7_days_kg,
        change_30_days_kg=history.change_30_days_kg,
        target_weight_kg=history.target_weight_kg,
        body_mass_index=history.body_mass_index,
    )


@router.post("", response_model=WeightEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_weight(
    payload: WeightCreateRequest,
    user: CurrentUserDependency,
    service: WeightServiceDependency,
) -> WeightEntryResponse:
    entry = await service.record(
        user,
        NewWeightEntry(
            weight_kg=payload.weight_kg,
            measured_at=payload.measured_at,
            notes=payload.notes,
        ),
    )
    return WeightEntryResponse.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight(
    entry_id: UUID,
    user: CurrentUserDependency,
    service: WeightServiceDependency,
) -> None:
    try:
        await service.delete_entry(user, entry_id)
    except WeightEntryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This weight entry does not exist."
        ) from error
