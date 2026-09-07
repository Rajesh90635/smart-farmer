"""
Task: the ONLY genuinely missing piece of Step 16's "crop-stage / task
engine" - crop stage already exists in full as CropCycle.cultivation_status
(Prompt 4), unchanged here.

Per Requirement 10's own list of authoritative task sources, this project
has no crop-calendar, no validated agronomic rule dataset, and no source
for "day 30 after sowing -> irrigate" style auto-generated tasks - only
source #1 ("explicit farmer-created task") can be implemented without
inventing agronomy. So this model represents ONLY farmer-created tasks -
never an auto-generated recommendation.

Status is deliberately minimal and farmer-driven: PENDING/COMPLETED/
CANCELLED are the only STORED states. "Overdue" and "due" are NEVER
stored - they are computed at read time from due_date + current time +
status (see task_service.py), exactly matching the rule "never mark
overdue merely because time passed" - storing an overdue flag risks it
going stale; computing it fresh every read cannot.
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    # D9-12 (docs/audit/FINAL_CANONICAL_group_A.md): distinct from CANCELLED -
    # the farmer attempted the task but genuinely could not (e.g. irrigation
    # pump broke), a real-world outcome worth reporting differently from
    # simply choosing not to do it.
    FAILED = "failed"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(str, enum.Enum):
    GENERAL = "general"
    IRRIGATION = "irrigation"
    SPRAYING = "spraying"
    FERTILIZING = "fertilizing"
    WEEDING = "weeding"
    HARVESTING = "harvesting"
    # D13-05 (docs/audit/FINAL_CANONICAL_group_A.md): perennial-crop
    # pruning previously had no dedicated value - a farmer could only
    # mislabel it via OTHER/GENERAL.
    PRUNING = "pruning"
    OTHER = "other"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status != 'completed' OR completed_at IS NOT NULL",
            name="ck_tasks_completed_has_timestamp",
        ),
        CheckConstraint(
            "repeat_interval_days IS NULL OR repeat_interval_days > 0",
            name="ck_tasks_repeat_interval_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crop_cycles.id", ondelete="CASCADE"), nullable=False, index=True)

    task_type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_type", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=TaskType.GENERAL,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, name="task_priority", native_enum=True, values_callable=lambda e: [x.value for x in e]),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    # D9-10 (docs/audit/FINAL_CANONICAL_group_A.md): farmer-entered, optional,
    # shared across cancel/skip/fail - never auto-populated.
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # D9-16/D9-03 (docs/audit/FINAL_CANONICAL_group_A.md): mirrors
    # InputInventoryItem.low_stock_alerted_at's "fires once per episode" gate
    # - cleared whenever the task stops being overdue (due_date pushed out,
    # completed, cancelled, or skipped), so a farmer who reschedules and goes
    # overdue again is correctly re-alerted.
    overdue_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # D8-07/D8-08 (docs/FINAL_GAP_REPORT.md): both optional, farmer-set only
    # - never inferred or auto-generated, consistent with this model's own
    # "farmer-created tasks only" rule. depends_on_task_id blocks completion
    # of THIS task until the referenced one is completed (self-referential,
    # same crop_cycle enforced in task_service). repeat_interval_days, when
    # set, makes completing this task auto-create its own next occurrence
    # (a plain future date offset - never a cron/calendar rule).
    depends_on_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    repeat_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # D37-01 (docs/audit/FINAL_CANONICAL_group_B.md): optional, farmer-
    # confirmed only - a review outcome only ever SUGGESTS this task (see
    # case_service._build_task_suggestion), it is never auto-created.
    # A reference, not a copy, mirroring TreatmentRecord.before_analysis_id's
    # own "reference, don't duplicate" pattern.
    source_case_review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_reviews.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
