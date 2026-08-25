from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ComplaintPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplaintStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class ComplaintCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    channel: str = Field(default="web", pattern="^(web|email|phone|chat)$")
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)
    priority: ComplaintPriority | None = None


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus
    note: str | None = None


class ComplaintAssignment(BaseModel):
    assigned_team_id: int | None = None
    assigned_agent_id: int | None = None


class NoteCreate(BaseModel):
    text: str = Field(min_length=1)
    visibility: str = Field(default="customer", pattern="^(customer|internal)$")


class EscalationCreate(BaseModel):
    level: int = Field(ge=1, le=3)
    reason: str = Field(min_length=3, max_length=255)
    assigned_to: int | None = None


class ComplaintResponse(BaseModel):
    id: int
    customer_id: int
    product_id: str
    category: str
    channel: str
    subject: str
    description: str
    priority: str
    status: str
    assigned_team_id: int | None
    assigned_agent_id: int | None
    created_at: datetime
    sla_due_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
    duplicate_of_id: int | None
    sla_state: str = "on_track"

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    default_sla_hours: int = Field(default=48, ge=1, le=720)


class CategoryResponse(CategoryCreate):
    id: int
    model_config = {"from_attributes": True}


class TrendRequest(BaseModel):
    team_id: int | None = None
    product_id: str | None = None
    category: str | None = None
    instruction: str | None = None


class TrendResponse(BaseModel):
    metrics: dict
    narrative: str
    observations: list[str]