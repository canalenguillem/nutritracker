from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class LivenessResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime

    @classmethod
    def create(cls) -> "LivenessResponse":
        return cls(status=HealthStatus.HEALTHY, timestamp=datetime.now(UTC))


class ReadinessResponse(BaseModel):
    status: HealthStatus
    app_name: str
    environment: str
    version: str
    timestamp: datetime
    services: dict[str, HealthStatus]
