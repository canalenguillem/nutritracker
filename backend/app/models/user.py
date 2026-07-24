from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.models.enums import AuthProvider, UserRole, UserStatus


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, create_constraint=True),
        default=UserRole.USER,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=False, create_constraint=True),
        default=UserStatus.ACTIVE,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default="es")
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Madrid")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    auth_identities: Mapped[list["AuthIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class AuthIdentity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id"),
        Index("ix_auth_identities_provider_email", "provider", "provider_email"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider, name="auth_provider", native_enum=False, create_constraint=True)
    )
    provider_user_id: Mapped[str] = mapped_column(String(255))
    provider_email: Mapped[str] = mapped_column(String(255))

    user: Mapped[User] = relationship(back_populates="auth_identities")


class RefreshToken(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utc_now)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class UserProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    current_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    target_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    biological_sex: Mapped[str | None] = mapped_column(String(32), nullable=True)
    activity_level: Mapped[str] = mapped_column(String(32), default="moderate")
    primary_goal: Mapped[str] = mapped_column(String(32), default="maintain_weight")
    daily_calorie_target: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    protein_target_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    carbohydrate_target_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    fat_target_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")
