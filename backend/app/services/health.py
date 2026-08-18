import asyncio
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from time import perf_counter

from app.repositories.health import HealthRepository
from app.schemas.health import HealthStatus, ReadinessResponse

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(
        self,
        repositories: Sequence[HealthRepository],
        timeout_seconds: float,
        app_name: str,
        environment: str,
        version: str,
    ) -> None:
        self._repositories = tuple(repositories)
        self._timeout_seconds = timeout_seconds
        self._app_name = app_name
        self._environment = environment
        self._version = version

    async def check_readiness(self) -> ReadinessResponse:
        results = await asyncio.gather(
            *(self._check_repository(repository) for repository in self._repositories)
        )
        services = dict(results)
        health_status = (
            HealthStatus.HEALTHY
            if all(service is HealthStatus.HEALTHY for service in services.values())
            else HealthStatus.UNHEALTHY
        )
        return ReadinessResponse(
            status=health_status,
            app_name=self._app_name,
            environment=self._environment,
            version=self._version,
            timestamp=datetime.now(UTC),
            services=services,
        )

    async def _check_repository(self, repository: HealthRepository) -> tuple[str, HealthStatus]:
        started_at = perf_counter()
        dependency_status = HealthStatus.HEALTHY
        try:
            await asyncio.wait_for(repository.ping(), timeout=self._timeout_seconds)
        except Exception as exception:
            dependency_status = HealthStatus.UNHEALTHY
            logger.warning(
                "dependency_healthcheck_failed",
                extra={
                    "dependency": repository.name,
                    "error_type": type(exception).__name__,
                    "latency_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
        return repository.name, dependency_status
