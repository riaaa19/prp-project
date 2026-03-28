"""
Authentication service.
Handles login validation against the database.
"""
from database.db import get_connection
from models.user import User
from utils.validators import is_valid_email


def login(email: str, password: str):
    """
    Attempt to log in with email + password.
    Returns a User object on success, or raises ValueError with a message.
    """
    if not email or not password:
        raise ValueError("Email and password are required.")

    if not is_valid_email(email):
        raise ValueError("Please enter a valid email address.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email.strip(), password),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError("Invalid email or password.")

    return User(row["id"], row["username"], row["email"], row["password"], row["role"])


def register_user(username: str, email: str, password: str, password_confirm: str):
    if not username.strip() or not email.strip() or not password:
        raise ValueError("All fields are required.")

    if password != password_confirm:
        raise ValueError("Passwords do not match.")

    if not is_valid_email(email):
        raise ValueError("Please enter a valid email address.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'student')",
            (username.strip(), email.strip(), password),
        )
        conn.commit()
        user_id = cur.lastrowid
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            raise ValueError("Email address already registered.")
        raise
    finally:
        conn.close()

    return User(user_id, username.strip(), email.strip(), password, "student")
