"""
Database module: handles SQLite connection and table creation.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "college_club.db")


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access to rows
    return conn


def initialize_db():
    """Create all tables if they do not already exist, and seed demo data."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL CHECK(role IN ('admin', 'student'))
        )
    """)

    # ── Clubs ─────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT,
            created_at  TEXT    NOT NULL
        )
    """)

    # ── Registrations ──────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            UNIQUE(user_id, event_id)          -- prevent duplicate registrations
        )
    """)

    # ── Attendance ─────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            status   TEXT    NOT NULL CHECK(status IN ('present', 'absent')),
            UNIQUE(user_id, event_id)
        )
    """)

    # ── Notifications ───────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message    TEXT    NOT NULL,
            created_at TEXT    NOT NULL,
            read_flag  INTEGER NOT NULL DEFAULT 0 CHECK(read_flag IN (0,1))
        )
    """)

    # ── Seed data (only if tables are empty) ───────────────────────────────
    cur.execute("SELECT COUNT(*) FROM clubs")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO clubs (name, description, created_at) VALUES (?,?,?)",
            [
                ("Tech Club", "Focuses on technology and coding events", "2025-01-01T00:00:00"),
                ("Sports Club", "Organizes sports and fitness activities", "2025-01-01T00:00:00"),
                ("Cultural Club", "Promotes cultural events and traditions", "2025-01-01T00:00:00"),
                ("Arts Club", "Supports artistic and creative activities", "2025-01-01T00:00:00"),
            ],
        )

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users (username, email, password, role) VALUES (?,?,?,?)",
            [
                ("Admin User",  "admin@college.edu",   "admin123",   "admin"),
                ("Alice Smith", "alice@college.edu",   "alice123",   "student"),
                ("Bob Jones",   "bob@college.edu",     "bob123",     "student"),
            ],
        )

    cur.execute("SELECT COUNT(*) FROM events")
    if cur.fetchone()[0] == 0:
        # Get club IDs for seeding
        cur.execute("SELECT id, name FROM clubs")
        club_map = {row["name"]: row["id"] for row in cur.fetchall()}
        cur.executemany(
            "INSERT INTO events (name, date, club_id, club) VALUES (?,?,?,?)",
            [
                ("Tech Fest 2025",        "2025-09-15", club_map["Tech Club"], "Tech Club"),
                ("Annual Sports Day",     "2025-10-02", club_map["Sports Club"], "Sports Club"),
                ("Cultural Night",        "2025-11-20", club_map["Cultural Club"], "Cultural Club"),
                ("Coding Hackathon",      "2025-08-28", club_map["Tech Club"], "Tech Club"),
                ("Photography Workshop",  "2025-09-05", club_map["Arts Club"], "Arts Club"),
            ],
        )

    conn.commit()
    conn.close()
