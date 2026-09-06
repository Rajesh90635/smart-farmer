"""Soil sample/test-result repositories. Ownership enforced the same way
as every other farmer-scoped entity in this project."""
import uuid
from datetime import date

from sqlalchemy import func, select
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


def list_stale_unalerted_soil_test_results(db: Session, *, cutoff_date: date) -> list[SoilTestResult]:
    """D20-13 (docs/audit/FINAL_CANONICAL_group_D.md): the LATEST
    SoilTestResult per plot, when that latest result is itself stale
    (test_date before cutoff_date) and hasn't been reminded about yet. An
    older stale result for a plot that has since been retested is
    correctly excluded here - only a plot's CURRENT (latest) result
    matters, mirroring SoilTestResult.is_stale's own "today - test_date"
    comparison (cutoff_date = today - max_age_days, so "before cutoff"
    means "more than max_age_days old", exactly as is_stale defines it)."""
    latest_per_plot = (
        select(SoilSample.plot_id.label("plot_id"), func.max(SoilTestResult.test_date).label("latest_test_date"))
        .join(SoilTestResult, SoilTestResult.soil_sample_id == SoilSample.id)
        .group_by(SoilSample.plot_id)
        .subquery()
    )
    return list(
        db.execute(
            select(SoilTestResult)
            .join(SoilSample, SoilTestResult.soil_sample_id == SoilSample.id)
            .join(
                latest_per_plot,
                (SoilSample.plot_id == latest_per_plot.c.plot_id) & (SoilTestResult.test_date == latest_per_plot.c.latest_test_date),
            )
            .where(SoilTestResult.test_date < cutoff_date, SoilTestResult.reminder_alerted_at.is_(None))
        ).scalars().unique().all()
    )
