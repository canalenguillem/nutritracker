from dataclasses import dataclass

from app.schemas.health import HealthStatus
from app.services.health import HealthService


@dataclass(frozen=True)
class StubHealthRepository:
    name: str
    available: bool

    async def ping(self) -> None:
        if not self.available:
            raise ConnectionError


async def test_readiness_is_ready_when_all_dependencies_are_available() -> None:
    service = HealthService(
        repositories=(
            StubHealthRepository(name="mariadb", available=True),
            StubHealthRepository(name="redis", available=True),
        ),
        timeout_seconds=0.1,
        app_name="NutriTrack AI",
        environment="test",
        version="0.1.0",
    )

    result = await service.check_readiness()

    assert result.status is HealthStatus.HEALTHY
    assert all(service is HealthStatus.HEALTHY for service in result.services.values())


async def test_readiness_is_unavailable_when_a_dependency_fails() -> None:
    service = HealthService(
        repositories=(
            StubHealthRepository(name="mariadb", available=False),
            StubHealthRepository(name="redis", available=True),
        ),
        timeout_seconds=0.1,
        app_name="NutriTrack AI",
        environment="test",
        version="0.1.0",
    )

    result = await service.check_readiness()

    assert result.status is HealthStatus.UNHEALTHY
    assert result.services["mariadb"] is HealthStatus.UNHEALTHY
    assert result.services["redis"] is HealthStatus.HEALTHY
