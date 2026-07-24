from enum import StrEnum


class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
