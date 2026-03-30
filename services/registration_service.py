"""
Registration service.
Handles student ↔ event registration logic.
"""
import sqlite3
from database.db import get_connection


def register_student(user_id: int, event_id: int):
    """
    Register a student for an event.
    Raises ValueError if already registered.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO registrations (user_id, event_id) VALUES (?, ?)",
            (user_id, event_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("You are already registered for this event.")
    finally:
        conn.close()


def get_events_for_student(user_id: int):
    """Return list of event dicts the student is registered for."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.id, e.name, e.date, e.club
            FROM   registrations r
            JOIN   events e ON e.id = r.event_id
            WHERE  r.user_id = ?
            ORDER BY e.date
            """,
            (user_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_all_registrations():
    """Return all registrations with student and event info (admin view)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT u.username, u.email, e.name AS event_name, e.date, e.club
            FROM   registrations r
            JOIN   users  u ON u.id  = r.user_id
            JOIN   events e ON e.id  = r.event_id
            ORDER BY u.username, e.date
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def cancel_registration(user_id: int, event_id: int):
    """Remove a student's registration and any linked attendance record."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM registrations WHERE user_id = ? AND event_id = ?",
            (user_id, event_id),
        )
        if cur.fetchone() is None:
            raise ValueError("You are not registered for this event.")

        cur.execute("DELETE FROM attendance WHERE user_id = ? AND event_id = ?", (user_id, event_id))
        cur.execute("DELETE FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
        conn.commit()
    finally:
        conn.close()


def get_registration_summary():
    """Return registration totals per event for dashboard insights."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.id, e.name AS event_name, e.date, e.club,
                   COUNT(r.user_id) AS total_registered
            FROM events e
            LEFT JOIN registrations r ON r.event_id = e.id
            GROUP BY e.id
            ORDER BY e.date
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_event_registrations(event_id: int):
    """Return list of registrations for a specific event."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT u.id, u.username, u.email
            FROM   registrations r
            JOIN   users u ON u.id = r.user_id
            WHERE  r.event_id = ?
            ORDER BY u.username
            """,
            (event_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
