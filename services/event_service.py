"""
Event service.
CRUD operations for the events table.
"""
from database.db import get_connection
from models.event import Event


def get_all_events():
    """Return all events as a list of Event objects."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM events ORDER BY date")
        return [Event(r["id"], r["name"], r["date"], r["club"]) for r in cur.fetchall()]
    finally:
        conn.close()


def get_total_events():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM events")
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def get_club_count():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT club) AS cnt FROM events")
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def get_club_summary():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT club, COUNT(*) AS event_count FROM events GROUP BY club ORDER BY event_count DESC"
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def add_event(name: str, date: str, club: str):
    """Insert a new event. Raises ValueError on empty fields."""
    if not name.strip() or not date.strip() or not club.strip():
        raise ValueError("All event fields are required.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (name, date, club) VALUES (?, ?, ?)",
            (name.strip(), date.strip(), club.strip()),
        )
        conn.commit()
    finally:
        conn.close()


def delete_event(event_id: int):
    """Delete an event by ID."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
    finally:
        conn.close()


def update_event(event_id: int, name: str, date: str, club: str):
    """Update an existing event."""
    if not name.strip() or not date.strip() or not club.strip():
        raise ValueError("All event fields are required.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE events SET name=?, date=?, club=? WHERE id=?",
            (name.strip(), date.strip(), club.strip(), event_id),
        )
        conn.commit()
    finally:
        conn.close()
