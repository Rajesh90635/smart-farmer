"""
Insurance policy repository. Ownership enforced the same way as every
other farmer-scoped entity: every read/write is filtered by
InsurancePolicy.farmer_id, resolved from the authenticated session.
"""
import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.insurance_policy import InsurancePolicy


def create(db: Session, policy: InsurancePolicy) -> InsurancePolicy:
    db.add(policy)
    return policy


def get_owned(db: Session, policy_id: uuid.UUID, farmer_id: uuid.UUID) -> InsurancePolicy | None:
    return db.execute(select(InsurancePolicy).where(InsurancePolicy.id == policy_id, InsurancePolicy.farmer_id == farmer_id)).scalar_one_or_none()


def list_for_farmer(db: Session, farmer_id: uuid.UUID) -> list[InsurancePolicy]:
    return list(
        db.execute(select(InsurancePolicy).where(InsurancePolicy.farmer_id == farmer_id).order_by(InsurancePolicy.created_at.desc())).scalars().all()
    )


def delete(db: Session, policy: InsurancePolicy) -> None:
    db.execute(sa_delete(InsurancePolicy).where(InsurancePolicy.id == policy.id))
