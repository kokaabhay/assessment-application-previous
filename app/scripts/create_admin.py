import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import AsyncSessionLocal
from app.db.models import User


async def create_admin() -> None:
    """Create the initial administrator account."""

    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")

    if not email:
        raise ValueError("Email cannot be empty.")

    if not password:
        raise ValueError("Password cannot be empty.")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.role == "admin":
                print("Admin account already exists.")
                return

            existing_user.role = "admin"

            await db.commit()

            print(f"Existing user '{email}' promoted to admin.")
            return

        admin = User(
            email=email,
            password_hash=hash_password(password),
            role="admin",
            category=None,
            is_active=True,
        )

        db.add(admin)

        await db.commit()

        print(f"Admin account '{email}' created successfully.")


if __name__ == "__main__":
    asyncio.run(create_admin())