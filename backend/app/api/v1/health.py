from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.schemas.health import HealthStatus, LivenessResponse, ReadinessResponse
from app.services.health import HealthService

router = APIRouter(prefix="/health", tags=["health"])


def get_health_service(request: Request) -> HealthService:
    service = request.app.state.health_service
    if not isinstance(service, HealthService):
        raise RuntimeError("Health service is not configured")
    return service


HealthServiceDependency = Annotated[HealthService, Depends(get_health_service)]


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    return LivenessResponse.create()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def readiness(service: HealthServiceDependency) -> ReadinessResponse | JSONResponse:
    response = await service.check_readiness()
    if response.status is HealthStatus.UNHEALTHY:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(mode="json"),
        )
    return response
