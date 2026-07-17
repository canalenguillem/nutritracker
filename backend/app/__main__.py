import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        access_log=False,
        log_config=None,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    run()
