"""
User service.
"""
from database.db import get_connection


def get_total_members():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'student'")
        return cur.fetchone()["cnt"]
    finally:
        conn.close()


def get_all_members():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT username, email, role FROM users WHERE role = 'student' ORDER BY username")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
