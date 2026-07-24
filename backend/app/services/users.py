from dataclasses import dataclass
from uuid import UUID

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


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def create_user(self, data: NewUser) -> User:
        email = data.email.strip().lower()
        existing_user = await self._repository.get_by_email(email)
        if existing_user is not None:
            raise UserAlreadyExistsError(email)

        user = User(
            email=email,
            display_name=data.display_name.strip(),
            password_hash=data.password_hash,
            role=data.role,
        )
        return await self._repository.add(user)

    async def assign_role(self, user_id: UUID, role: UserRole) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        user.role = role
        return user
