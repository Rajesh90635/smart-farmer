from sqlalchemy import text

from app.db.session import SessionLocal


def test_database_connection_executes_a_query():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        db.close()


def test_audit_logs_table_exists_after_migration():
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT to_regclass('public.audit_logs')")
        ).scalar()
        assert result == "audit_logs"
    finally:
        db.close()
