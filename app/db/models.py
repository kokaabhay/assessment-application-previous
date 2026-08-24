from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """Application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    contracts: Mapped[list["Contract"]] = relationship(
        back_populates="owner",
    )


class Vendor(Base):
    """Vendor registered in the procurement system."""

    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    contact_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    onboarded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    annual_budget_cap: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    contracts: Mapped[list["Contract"]] = relationship(
        back_populates="vendor",
        cascade="all, delete-orphan",
    )

    compliance_documents: Mapped[list["ComplianceDocument"]] = relationship(
        back_populates="vendor",
        cascade="all, delete-orphan",
    )


class Contract(Base):
    """Contract belonging to a vendor."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    contract_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    spend: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    renewal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    service_scope: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    vendor: Mapped["Vendor"] = relationship(
        back_populates="contracts",
    )

    owner: Mapped["User"] = relationship(
        back_populates="contracts",
    )


class ComplianceDocument(Base):
    """Compliance document associated with a vendor."""

    __tablename__ = "compliance_documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    expires_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    vendor: Mapped["Vendor"] = relationship(
        back_populates="compliance_documents",
    )


class Job(Base):
    """Tracked background job."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    accepted_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    rejected_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


Index(
    "ix_contract_vendor_end_date",
    Contract.vendor_id,
    Contract.end_date,
)

Index(
    "ix_contract_vendor_status",
    Contract.vendor_id,
    Contract.status,
)