"""Club service.
CRUD-style helpers for the clubs table.
"""
from datetime import datetime

from database.db import get_connection


def get_all_clubs():
    """Return all clubs as list[dict], sorted by name."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name, COALESCE(description, '') AS description, created_at
            FROM clubs
            ORDER BY name COLLATE NOCASE
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def add_club(name: str, description: str = ""):
    """Insert a new club. Raises ValueError on invalid input/duplicates."""
    clean_name = (name or "").strip()
    clean_desc = (description or "").strip()

    if not clean_name:
        raise ValueError("Club name is required.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM clubs WHERE LOWER(name) = LOWER(?)", (clean_name,))
        if cur.fetchone() is not None:
            raise ValueError("Club already exists.")

        cur.execute(
            "INSERT INTO clubs (name, description, created_at) VALUES (?, ?, ?)",
            (clean_name, clean_desc, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


def update_club(name: str, description: str = ""):
    """Update an existing club by name. Raises ValueError on invalid input."""
    clean_name = (name or "").strip()
    clean_desc = (description or "").strip()

    if not clean_name:
        raise ValueError("Club name is required.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE clubs SET description = ? WHERE LOWER(name) = LOWER(?)",
            (clean_desc, clean_name),
        )
        conn.commit()
    finally:
        conn.close()


def delete_club(name: str):
    """Delete a club by name."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM clubs WHERE LOWER(name) = LOWER(?)", (name,))
        conn.commit()
    finally:
        conn.close()
