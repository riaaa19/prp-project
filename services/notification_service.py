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


def mark_all_read(user_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE notifications SET read_flag = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
