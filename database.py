import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from config import DATA_DIR, DB_PATH


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            cv_version TEXT NOT NULL,
            language TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_description TEXT NOT NULL,
            original_data TEXT NOT NULL,
            adapted_data TEXT NOT NULL,
            changes_json TEXT NOT NULL,
            accepted_changes TEXT NOT NULL,
            pdf_blob BLOB NOT NULL
        )
    """)

    migrations = [
        "ALTER TABLE history ADD COLUMN company_name TEXT",
        "ALTER TABLE history ADD COLUMN position_title TEXT",
        "ALTER TABLE history ADD COLUMN application_date TEXT",
        "ALTER TABLE history ADD COLUMN offer_link TEXT",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def save_history(
    cv_version: str,
    language: str,
    job_title: str,
    job_description: str,
    original_data: dict[str, Any],
    adapted_data: dict[str, Any],
    changes: list[dict],
    accepted_paths: list[str],
    pdf_blob: bytes,
    company_name: str | None = None,
    position_title: str | None = None,
    application_date: str | None = None,
    offer_link: str | None = None,
) -> str:
    record_id = str(uuid.uuid4())
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO history (id, created_at, cv_version, language, job_title,
            job_description, original_data, adapted_data, changes_json,
            accepted_changes, pdf_blob, company_name, position_title,
            application_date, offer_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_id,
            datetime.now(timezone.utc).isoformat(),
            cv_version,
            language,
            job_title,
            job_description,
            json.dumps(original_data),
            json.dumps(adapted_data),
            json.dumps(changes),
            json.dumps(accepted_paths),
            pdf_blob,
            company_name,
            position_title,
            application_date,
            offer_link,
        ),
    )
    conn.commit()
    conn.close()
    return record_id


def list_history() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, created_at, cv_version, language, job_title,
                  company_name, position_title, application_date, offer_link
           FROM history ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pdf(record_id: str) -> bytes | None:
    conn = get_connection()
    row = conn.execute("SELECT pdf_blob FROM history WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    if row:
        return row["pdf_blob"]
    return None
