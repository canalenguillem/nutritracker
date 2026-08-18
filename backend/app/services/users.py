from dataclasses import dataclass
from uuid import UUID

from app.models.base import utc_now
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.users import UserRepository


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class NewUser:
    email: str
    display_name: str
    password_hash: str | None = None
    role: UserRole = UserRole.USER
    avatar_url: str | None = None
    email_verified: bool = False


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def create_user(self, data: NewUser) -> User:
        email = normalize_email(data.email)
        existing_user = await self._repository.get_by_email(email)
        if existing_user is not None:
            raise UserAlreadyExistsError(email)

        user = User(
            email=email,
            display_name=data.display_name.strip(),
            password_hash=data.password_hash,
            role=data.role,
            avatar_url=data.avatar_url,
            email_verified_at=utc_now() if data.email_verified else None,
        )
        return await self._repository.add(user)

    async def get_by_email(self, email: str) -> User | None:
        return await self._repository.get_by_email(normalize_email(email))

    async def get_by_id(self, user_id: UUID) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        return user

    async def record_login(self, user: User) -> None:
        user.last_login_at = utc_now()

    async def assign_role(self, user_id: UUID, role: UserRole) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        user.role = role
        return user
