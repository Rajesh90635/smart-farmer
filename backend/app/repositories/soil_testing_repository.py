"""Soil sample/test-result repositories. Ownership enforced the same way
as every other farmer-scoped entity in this project."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.soil_sample import SoilSample
from app.models.soil_test_result import SoilTestResult


def create_sample(db: Session, sample: SoilSample) -> SoilSample:
    db.add(sample)
    return sample


def get_sample_owned(db: Session, sample_id: uuid.UUID, farmer_id: uuid.UUID) -> SoilSample | None:
    return db.execute(select(SoilSample).where(SoilSample.id == sample_id, SoilSample.farmer_id == farmer_id)).scalar_one_or_none()


def list_samples_for_plot(db: Session, plot_id: uuid.UUID, farmer_id: uuid.UUID) -> list[SoilSample]:
    return list(
        db.execute(
            select(SoilSample)
            .where(SoilSample.plot_id == plot_id, SoilSample.farmer_id == farmer_id)
            .order_by(SoilSample.collection_date.desc())
        ).scalars().all()
    )


def create_result(db: Session, result: SoilTestResult) -> SoilTestResult:
    db.add(result)
    return result


def get_result_owned(db: Session, result_id: uuid.UUID, farmer_id: uuid.UUID) -> SoilTestResult | None:
    return db.execute(select(SoilTestResult).where(SoilTestResult.id == result_id, SoilTestResult.farmer_id == farmer_id)).scalar_one_or_none()


def list_results_for_sample(db: Session, sample_id: uuid.UUID, farmer_id: uuid.UUID) -> list[SoilTestResult]:
    return list(
        db.execute(
            select(SoilTestResult)
            .where(SoilTestResult.soil_sample_id == sample_id, SoilTestResult.farmer_id == farmer_id)
            .order_by(SoilTestResult.test_date.desc())
        ).scalars().all()
    )
