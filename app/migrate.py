from __future__ import annotations
from sqlalchemy import text
from flask import current_app
from . import db

def _is_sqlite() -> bool:
    return db.engine.url.get_backend_name() == "sqlite"

def _has_column_sqlite(table: str, column: str) -> bool:
    rows = db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)

def _has_column_pg(table: str, column: str) -> bool:
    q = text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = :table AND column_name = :col
        LIMIT 1
    """)
    r = db.session.execute(q, {"table": table, "col": column}).fetchone()
    return r is not None

def ensure_schema():
    backend = db.engine.url.get_backend_name()
    current_app.logger.info("Schema check on %s", backend)

    if _is_sqlite():
        def addcol(table: str, col: str, ctype: str):
            if not _has_column_sqlite(table, col):
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}"))

        addcol("skill", "pass_pct", "INTEGER")
        addcol("attempt", "passed", "BOOLEAN")
        addcol("attempt", "draft_answers_json", "TEXT")
        addcol("attempt", "last_saved_at", "DATETIME")

        addcol("question", "status", "TEXT")
        addcol("question", "created_by_id", "TEXT")
        addcol("question", "created_by_role", "TEXT")
        addcol("question", "approved_by_id", "TEXT")
        addcol("question", "approved_at", "DATETIME")

        db.session.commit()
        return

    if backend in ("postgresql", "postgres"):
        def addcol(table: str, col: str, ctype: str):
            if not _has_column_pg(table, col):
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}"))

        addcol("skill", "pass_pct", "INTEGER")
        addcol("attempt", "passed", "BOOLEAN")
        addcol("attempt", "draft_answers_json", "TEXT")
        addcol("attempt", "last_saved_at", "TIMESTAMP")

        addcol("question", "status", "VARCHAR(16)")
        addcol("question", "created_by_id", "VARCHAR(64)")
        addcol("question", "created_by_role", "VARCHAR(16)")
        addcol("question", "approved_by_id", "VARCHAR(64)")
        addcol("question", "approved_at", "TIMESTAMP")

        db.session.execute(text("UPDATE question SET status = COALESCE(status,'draft')"))
        db.session.commit()
