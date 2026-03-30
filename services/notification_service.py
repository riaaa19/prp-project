"""
Notification service.
Handles in-app notifications for students and admins.
"""
from datetime import datetime
from database.db import get_connection


def create_notification(user_id: int, message: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notifications (user_id, message, created_at, read_flag) VALUES (?, ?, ?, 0)",
            (user_id, message, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_notifications(user_id: int, unread_only: bool = False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        if unread_only:
            cur.execute(
                "SELECT id, message, created_at, read_flag FROM notifications WHERE user_id = ? AND read_flag = 0 ORDER BY created_at DESC",
                (user_id,),
            )
        else:
            cur.execute(
                "SELECT id, message, created_at, read_flag FROM notifications WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_unread_count(user_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = ? AND read_flag = 0",
            (user_id,),
        )
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def broadcast_notification_to_students(message: str):
    clean_message = (message or "").strip()
    if not clean_message:
        raise ValueError("Announcement message cannot be empty.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE role = 'student' ORDER BY id")
        student_ids = [row["id"] for row in cur.fetchall()]
        if not student_ids:
            raise ValueError("No student accounts found to send the announcement.")

        created_at = datetime.utcnow().isoformat()
        cur.executemany(
            "INSERT INTO notifications (user_id, message, created_at, read_flag) VALUES (?, ?, ?, 0)",
            [(student_id, clean_message, created_at) for student_id in student_ids],
        )
        conn.commit()
        return len(student_ids)
    finally:
        conn.close()


def send_event_reminder(event_id: int, extra_message: str = ""):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, date, club FROM events WHERE id = ?",
            (event_id,),
        )
        event_row = cur.fetchone()
        if event_row is None:
            raise ValueError("Selected event was not found.")

        cur.execute(
            "SELECT user_id FROM registrations WHERE event_id = ? ORDER BY user_id",
            (event_id,),
        )
        registrations = [row["user_id"] for row in cur.fetchall()]
        if not registrations:
            raise ValueError("No students are registered for this event yet.")

        base_message = (
            f"Reminder: '{event_row['name']}' is scheduled on {event_row['date']} "
            f"for {event_row['club']}."
        )
        note = (extra_message or "").strip()
        if note:
            base_message = f"{base_message} {note}"

        created_at = datetime.utcnow().isoformat()
        cur.executemany(
            "INSERT INTO notifications (user_id, message, created_at, read_flag) VALUES (?, ?, ?, 0)",
            [(user_id, base_message, created_at) for user_id in registrations],
        )
        conn.commit()
        return len(registrations)
    finally:
        conn.close()


def mark_all_read(user_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE notifications SET read_flag = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
