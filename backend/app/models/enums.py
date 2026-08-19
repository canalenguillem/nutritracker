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


class MealType(StrEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MealSource(StrEnum):
    PHOTO_AI = "photo_ai"
    MANUAL = "manual"
    IMPORTED = "imported"


class MealStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExerciseIntensity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ExerciseSource(StrEnum):
    MANUAL = "manual"
    DEVICE = "device"
    IMPORTED = "imported"


class SleepQuality(StrEnum):
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    VERY_GOOD = "very_good"
