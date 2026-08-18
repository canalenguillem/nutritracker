from typing import Any

from app.core.config import Settings

TEST_JWT_SECRET = "unit-test-secret-key-value-32-chars"


def build_settings(**overrides: Any) -> Settings:
    """Settings for a test, independent of the machine it runs on.

    Values are pinned here because the container carries the developer's own
    configuration in its environment, and a test must not change meaning
    because of what sits in .env.
    """
    values: dict[str, Any] = {
        "app_env": "test",
        "jwt_secret_key": TEST_JWT_SECRET,
        "registration_open": True,
        "openai_api_key": "",
        "openai_model": "",
        "google_client_id": "",
        "google_client_secret": "",
        "google_redirect_uri": None,
        **overrides,
    }
    return Settings(_env_file=None, **values)
