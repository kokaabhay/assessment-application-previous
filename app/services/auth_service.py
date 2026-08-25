from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Business logic for authentication."""

    DEFAULT_ROLE = "user"

    @staticmethod
    async def register_user(
        db: AsyncSession,
        email: str,
        password: str,
        role: str = "CUSTOMER",
    ) -> User:
        """
        Register a new application user.

        Raises:
            ValueError: If the email is already registered.
        """

        existing_user = await UserRepository.get_by_email(
            db,
            email,
        )

        if existing_user is not None:
            raise ValueError(
                "A user with this email already exists."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role.upper(),
            category=None,
            is_active=True,
        )

        return await UserRepository.create(
            db,
            user,
        )

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User | None:
        """Authenticate a user using email and password."""

        user = await UserRepository.get_by_email(
            db,
            email,
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user

    @staticmethod
    def generate_token(user: User) -> str:
        """Generate a JWT for an authenticated user."""

        return create_access_token(
            user_id=user.id,
            role=user.role,
        )