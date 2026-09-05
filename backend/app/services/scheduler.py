"""
Background scheduler - the concrete replacement for this project's
long-disclosed "no background scheduler yet" limitation (see
docs/CASE_MANAGEMENT.md, docs/NOTIFICATION_ARCHITECTURE.md). Runs
in-process (APScheduler, MIT, no external broker) - deliberately not a
distributed task queue, consistent with "do not introduce a complicated
distributed architecture unnecessarily" until real scale needs one.

Disabled in the `testing` environment (see conftest.py's ENVIRONMENT=testing)
so a background thread never races against a test's own transactions -
tests call `run_case_sla_sweep` directly instead (see test_case_sla_service.py).

Every job function opens its OWN DB session (never a request-scoped one)
and never lets an exception kill the scheduler thread - failures are
logged and the job simply runs again next tick.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import Settings
from app.core.weather_provider_dependency import get_weather_provider
from app.db.session import SessionLocal
from app.services.case_sla_service import run_case_sla_sweep
from app.services.input_inventory_service import run_expiry_check_sweep
from app.services.weather_alert_orchestration_service import run_proactive_weather_alert_sweep

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_case_sla_sweep_job(settings: Settings) -> None:
    db = SessionLocal()
    try:
        result = run_case_sla_sweep(db, settings)
        logger.info(
            "case_sla_sweep reminders_sent=%s expired=%s reassigned=%s escalated=%s",
            result.reminders_sent, result.expired, result.reassigned, result.escalated,
        )
    except Exception:
        logger.exception("case_sla_sweep tick failed - will retry next interval")
        db.rollback()
    finally:
        db.close()


def _run_input_expiry_sweep_job(settings: Settings) -> None:
    db = SessionLocal()
    try:
        alerted = run_expiry_check_sweep(db, settings)
        logger.info("input_inventory_expiry_sweep alerted=%s", alerted)
    except Exception:
        logger.exception("input_inventory_expiry_sweep tick failed - will retry next interval")
        db.rollback()
    finally:
        db.close()


def _run_proactive_weather_alert_sweep_job(settings: Settings) -> None:
    db = SessionLocal()
    try:
        created = run_proactive_weather_alert_sweep(db, get_weather_provider(), settings)
        logger.info("proactive_weather_alert_sweep notifications_created=%s", created)
    except Exception:
        logger.exception("proactive_weather_alert_sweep tick failed - will retry next interval")
        db.rollback()
    finally:
        db.close()


def start_scheduler(settings: Settings) -> BackgroundScheduler | None:
    """Idempotent - calling twice (e.g. lifespan re-entry in tests that
    build the app more than once) never starts a second scheduler."""
    global _scheduler
    if not settings.scheduler_enabled or settings.environment == "testing":
        logger.info("Background scheduler not started (disabled or testing environment)")
        return None
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_case_sla_sweep_job,
        "interval",
        seconds=settings.case_sla_sweep_interval_seconds,
        args=[settings],
        id="case_sla_sweep",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=settings.case_sla_sweep_interval_seconds,
    )
    scheduler.add_job(
        _run_input_expiry_sweep_job,
        "interval",
        seconds=settings.input_inventory_expiry_sweep_interval_seconds,
        args=[settings],
        id="input_inventory_expiry_sweep",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=settings.input_inventory_expiry_sweep_interval_seconds,
    )
    scheduler.add_job(
        _run_proactive_weather_alert_sweep_job,
        "interval",
        seconds=settings.proactive_weather_alert_sweep_interval_seconds,
        args=[settings],
        id="proactive_weather_alert_sweep",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=settings.proactive_weather_alert_sweep_interval_seconds,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Background scheduler started (case_sla_sweep every %ss, input_inventory_expiry_sweep every %ss, "
        "proactive_weather_alert_sweep every %ss)",
        settings.case_sla_sweep_interval_seconds, settings.input_inventory_expiry_sweep_interval_seconds,
        settings.proactive_weather_alert_sweep_interval_seconds,
    )
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
