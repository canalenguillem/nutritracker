from fastapi import APIRouter

from app.api.deps import CurrentUserDependency, ProfileServiceDependency
from app.schemas.profiles import ProfileResponse, ProfileUpdateRequest
from app.services.profiles import ProfileChanges

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def read_profile(
    user: CurrentUserDependency,
    service: ProfileServiceDependency,
) -> ProfileResponse:
    profile = await service.get_profile(user)
    return ProfileResponse.model_validate(profile)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    user: CurrentUserDependency,
    service: ProfileServiceDependency,
) -> ProfileResponse:
    provided = payload.model_fields_set
    profile = await service.update_profile(
        user,
        ProfileChanges(
            height_cm=payload.height_cm,
            height_cm_provided="height_cm" in provided,
            target_weight_kg=payload.target_weight_kg,
            target_weight_kg_provided="target_weight_kg" in provided,
            birth_date=payload.birth_date,
            birth_date_provided="birth_date" in provided,
            biological_sex=payload.biological_sex,
            biological_sex_provided="biological_sex" in provided,
            activity_level=payload.activity_level,
            primary_goal=payload.primary_goal,
        ),
    )
    return ProfileResponse.model_validate(profile)
