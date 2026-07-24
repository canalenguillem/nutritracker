from dataclasses import dataclass, field
from uuid import UUID, uuid4

import pytest

from app.models.enums import UserRole
from app.models.user import User
from app.services.users import NewUser, UserAlreadyExistsError, UserNotFoundError, UserService


@dataclass
class FakeUserRepository:
    users: list[User] = field(default_factory=list)

    async def add(self, user: User) -> User:
        self.users.append(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        return next((user for user in self.users if user.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return next((user for user in self.users if user.id == user_id), None)


async def test_create_user_normalizes_email_and_assigns_default_role() -> None:
    repository = FakeUserRepository()
    service = UserService(repository)

    user = await service.create_user(
        NewUser(email="  USER@EXAMPLE.COM ", display_name="  User Name  ")
    )

    assert user.email == "user@example.com"
    assert user.display_name == "User Name"
    assert user.role is UserRole.USER


async def test_create_user_rejects_existing_email() -> None:
    repository = FakeUserRepository(users=[User(email="user@example.com", display_name="User")])
    service = UserService(repository)

    with pytest.raises(UserAlreadyExistsError):
        await service.create_user(NewUser(email="USER@example.com", display_name="Duplicate"))


async def test_assign_role_updates_existing_user() -> None:
    user = User(id=uuid4(), email="user@example.com", display_name="User")
    repository = FakeUserRepository(users=[user])
    service = UserService(repository)

    assigned_user = await service.assign_role(user.id, UserRole.ADMIN)

    assert assigned_user.role is UserRole.ADMIN


async def test_assign_role_rejects_unknown_user() -> None:
    service = UserService(FakeUserRepository())

    with pytest.raises(UserNotFoundError):
        await service.assign_role(UUID("00000000-0000-0000-0000-000000000000"), UserRole.ADMIN)
