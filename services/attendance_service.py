import sys, os
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if basedir not in sys.path:
    sys.path.insert(0, basedir)
from database.db import get_connection
import services.gamification_service as gamif_svc


"""
Attendance service.
Manages attendance marking and reporting for events.
"""
def mark_attendance(user_id: int, event_id: int, status: str):
    if status not in ("present", "absent"):
        raise ValueError("Attendance status must be 'present' or 'absent'.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        if not cur.fetchone():
            raise ValueError(f"User id {user_id} not found.")

        cur.execute("SELECT 1 FROM events WHERE id = ?", (event_id,))
        if not cur.fetchone():
            raise ValueError(f"Event id {event_id} not found.")

        cur.execute("SELECT 1 FROM registrations WHERE user_id = ? AND event_id = ?", (user_id, event_id))
        if not cur.fetchone():
            raise ValueError(f"No registration found for user {user_id} in event {event_id}.")

        cur.execute(
            "INSERT OR REPLACE INTO attendance (user_id, event_id, status) VALUES (?, ?, ?)",
            (user_id, event_id, status),
        )
        conn.commit()

        # Award points and check achievements if attendance is present
        if status == "present":
            gamif_svc.award_points(user_id, 10, "event_attendance", event_id)
            gamif_svc.check_and_award_achievements(user_id)

        return True
    finally:
        conn.close()


def get_all_attendance():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                r.id AS registration_id,
                r.user_id,
                r.event_id,
                u.username,
                u.email,
                e.name AS event_name,
                e.date,
                e.club,
                COALESCE(a.status, 'unmarked') AS status
            FROM registrations r
            JOIN users u ON u.id = r.user_id
            JOIN events e ON e.id = r.event_id
            LEFT JOIN attendance a ON a.user_id = r.user_id AND a.event_id = r.event_id
            ORDER BY e.date, u.username
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_attendance_summary():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.id as event_id, e.name AS event_name, e.date, e.club,
                   COUNT(DISTINCT r.user_id) AS registered,
                   SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS present,
                   SUM(CASE WHEN a.status='absent' THEN 1 ELSE 0 END) AS absent
            FROM events e
            LEFT JOIN registrations r ON r.event_id = e.id
            LEFT JOIN attendance a ON a.user_id = r.user_id AND a.event_id = e.id
            GROUP BY e.id
            ORDER BY e.date
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        for row in rows:
            attended = row.get('present', 0) or 0
            absent = row.get('absent', 0) or 0
            total = attended + absent
            row['total'] = total
            row['attendance_rate'] = round((attended / total) * 100, 1) if total > 0 else 0.0
        return rows
    finally:
        conn.close()


def get_total_present():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM attendance WHERE status='present'")
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def get_total_absent():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM attendance WHERE status='absent'")
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def get_today_event_count():
    from datetime import date
    today = date.today().isoformat()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM events WHERE date = ?", (today,))
        return cur.fetchone()["cnt"]
    finally:
        conn.close()
