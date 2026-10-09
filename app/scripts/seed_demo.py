#Seed a small, repeatable complaint-management demonstration dataset.

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, create_tables
from app.db.models import Complaint, ComplaintCategory, SupportTeam, User


async def seed() -> None:
    await create_tables()
    async with AsyncSessionLocal() as db:
        users = {
            "admin@example.com": "ADMIN",
            "manager@example.com": "SUPPORT_MANAGER",
            "agent@example.com": "SUPPORT_AGENT",
            "customer@example.com": "CUSTOMER",
        }
        user_objects: dict[str, User] = {}
        for email, role in users.items():
            user = await db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(email=email, password_hash=hash_password("Password123!"), role=role, is_active=True)
                db.add(user)
            user_objects[email] = user
        for name, hours in (("Billing", 24), ("Technical", 48), ("Delivery", 72), ("Account", 48)):
            if not await db.scalar(select(ComplaintCategory).where(ComplaintCategory.name == name)):
                db.add(ComplaintCategory(name=name, default_sla_hours=hours))
        if not await db.scalar(select(SupportTeam).where(SupportTeam.name == "General Support")):
            db.add(SupportTeam(name="General Support"))
        await db.flush()
        customer = user_objects["customer@example.com"]
        existing = await db.scalar(select(Complaint).where(Complaint.customer_id == customer.id))
        if existing is None:
            categories = ("Billing", "Technical", "Delivery", "Account")
            for index in range(35):
                created = datetime.utcnow() - timedelta(days=index % 14)
                db.add(Complaint(
                    customer_id=customer.id, product_id=f"product-{index % 3 + 1}",
                    category=categories[index % 4], channel=("web", "email", "phone")[index % 3],
                    subject=f"Demo complaint {index + 1}", description="Seeded complaint for evaluation.",
                    priority=("LOW", "MEDIUM", "HIGH", "CRITICAL")[index % 4],
                    status=("NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED")[index % 5],
                    created_at=created, sla_due_at=created + timedelta(hours=48),
                    resolved_at=created + timedelta(hours=24) if index % 5 in {3, 4} else None,
                    closed_at=created + timedelta(hours=36) if index % 5 == 4 else None,
                ))
        await db.commit()
    print("Demo data ready. Password for all demo users: Password123!")


if __name__ == "__main__":
    asyncio.run(seed())