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

    # ── Reminders ──────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_id        INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            reminder_type   TEXT    NOT NULL CHECK(reminder_type IN ('event_start', 'event_update', 'weather_alert', 'transport')),
            reminder_time   TEXT    NOT NULL,  -- ISO datetime string
            is_active       INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
            created_at      TEXT    NOT NULL,
            UNIQUE(user_id, event_id, reminder_type)
        )
    """)

    # ── User Preferences ────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email_reminders       INTEGER NOT NULL DEFAULT 1 CHECK(email_reminders IN (0,1)),
            push_notifications    INTEGER NOT NULL DEFAULT 1 CHECK(push_notifications IN (0,1)),
            weather_alerts        INTEGER NOT NULL DEFAULT 1 CHECK(weather_alerts IN (0,1)),
            transport_reminders   INTEGER NOT NULL DEFAULT 1 CHECK(transport_reminders IN (0,1)),
            default_reminder_1day INTEGER NOT NULL DEFAULT 1 CHECK(default_reminder_1day IN (0,1)),
            default_reminder_1hr  INTEGER NOT NULL DEFAULT 1 CHECK(default_reminder_1hr IN (0,1)),
            updated_at            TEXT    NOT NULL,
            UNIQUE(user_id)
        )
    """)

    # ── Friend Connections ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS friend_connections (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            friend_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status       TEXT    NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'blocked')),
            created_at   TEXT    NOT NULL,
            updated_at   TEXT    NOT NULL,
            UNIQUE(user_id, friend_id)
        )
    """)

    # ── Study Groups ───────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_groups (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT,
            event_id    INTEGER REFERENCES events(id) ON DELETE CASCADE,
            creator_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            max_members INTEGER NOT NULL DEFAULT 10,
            is_active   INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
            created_at  TEXT    NOT NULL,
            meeting_time TEXT,
            location    TEXT
        )
    """)

    # ── Study Group Members ────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_group_members (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            study_group_id INTEGER NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role           TEXT    NOT NULL DEFAULT 'member' CHECK(role IN ('creator', 'member')),
            joined_at      TEXT    NOT NULL,
            UNIQUE(study_group_id, user_id)
        )
    """)

    # ── Club Ambassadors ───────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS club_ambassadors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            club_name   TEXT    NOT NULL,
            title       TEXT    NOT NULL DEFAULT 'Ambassador',
            bio         TEXT,
            contact_info TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
            created_at  TEXT    NOT NULL,
            UNIQUE(user_id, club_name)
        )
    """)

    # ── Event Shares ───────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_shares (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id   INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            share_type TEXT    NOT NULL CHECK(share_type IN ('social_media', 'friend_link', 'group_chat')),
            platform   TEXT,  -- e.g., 'facebook', 'twitter', 'whatsapp', etc.
            shared_at  TEXT    NOT NULL,
            recipient_count INTEGER DEFAULT 0
        )
    """)

    # ── Achievement Badges ─────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievement_badges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT    NOT NULL,
            icon        TEXT    NOT NULL,  -- emoji or icon name
            category    TEXT    NOT NULL CHECK(category IN ('attendance', 'participation', 'first_time', 'social', 'feedback')),
            requirement_type TEXT NOT NULL CHECK(requirement_type IN ('count', 'streak', 'first', 'points')),
            requirement_value INTEGER NOT NULL,
            points_reward INTEGER NOT NULL DEFAULT 10,
            is_active   INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
            created_at  TEXT    NOT NULL
        )
    """)

    # ── User Achievements ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            badge_id    INTEGER NOT NULL REFERENCES achievement_badges(id) ON DELETE CASCADE,
            earned_at   TEXT    NOT NULL,
            progress    INTEGER NOT NULL DEFAULT 0,  -- current progress towards badge
            is_completed INTEGER NOT NULL DEFAULT 0 CHECK(is_completed IN (0,1)),
            UNIQUE(user_id, badge_id)
        )
    """)

    # ── User Points ────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_points (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            total_points INTEGER NOT NULL DEFAULT 0,
            current_level INTEGER NOT NULL DEFAULT 1,
            points_this_month INTEGER NOT NULL DEFAULT 0,
            last_updated TEXT    NOT NULL,
            UNIQUE(user_id)
        )
    """)

    # ── Points Transactions ────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS points_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            points      INTEGER NOT NULL,  -- positive for earned, negative for spent
            reason      TEXT    NOT NULL,  -- e.g., 'event_attendance', 'feedback_submitted', 'club_engagement'
            reference_id INTEGER,  -- ID of related record (event_id, feedback_id, etc.)
            created_at  TEXT    NOT NULL
        )
    """)

    # ── Leaderboards ───────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leaderboards (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category    TEXT    NOT NULL CHECK(category IN ('monthly_points', 'total_points', 'attendance_streak', 'club_participation')),
            score       INTEGER NOT NULL,
            rank        INTEGER NOT NULL,
            period      TEXT    NOT NULL,  -- e.g., '2026-04' for monthly, 'all_time' for total
            updated_at  TEXT    NOT NULL,
            UNIQUE(user_id, category, period)
        )
    """)

    # ── Progress Tracking ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress_tracking (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            club_id     INTEGER NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
            requirement_type TEXT NOT NULL CHECK(requirement_type IN ('events_attended', 'feedback_given', 'social_engagement', 'study_groups_joined')),
            current_value INTEGER NOT NULL DEFAULT 0,
            target_value INTEGER NOT NULL,
            is_completed INTEGER NOT NULL DEFAULT 0 CHECK(is_completed IN (0,1)),
            last_updated TEXT    NOT NULL,
            UNIQUE(user_id, club_id, requirement_type)
        )
    """)

    # ── Seed data (only if tables are empty) ───────────────────────────────
    cur.execute("SELECT COUNT(*) FROM clubs")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO clubs (name, description, created_at) VALUES (?,?,?)",
            [
                ("Tech Club", "Focuses on technology and coding events", "2026-01-01T00:00:00"),
                ("Sports Club", "Organizes sports and fitness activities", "2026-01-01T00:00:00"),
                ("Cultural Club", "Promotes cultural events and traditions", "2026-01-01T00:00:00"),
                ("Arts Club", "Supports artistic and creative activities", "2026-01-01T00:00:00"),
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
                ("Tech Fest 2026",        "2026-09-15", club_map["Tech Club"], "Tech Club"),
                ("Annual Sports Day",     "2026-10-02", club_map["Sports Club"], "Sports Club"),
                ("Cultural Night",        "2026-11-20", club_map["Cultural Club"], "Cultural Club"),
                ("Coding Hackathon",      "2026-08-28", club_map["Tech Club"], "Tech Club"),
                ("Photography Workshop",  "2026-09-05", club_map["Arts Club"], "Arts Club"),
            ],
        )

    # Seed achievement badges
    cur.execute("SELECT COUNT(*) FROM achievement_badges")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO achievement_badges (name, description, icon, category, requirement_type, requirement_value, points_reward, created_at) VALUES (?,?,?,?,?,?,?,?)",
            [
                # Attendance badges
                ("First Timer", "Attend your first event", "🎯", "first_time", "first", 1, 25, "2026-01-01T00:00:00"),
                ("Regular Attendee", "Attend 5 events", "📅", "attendance", "count", 5, 50, "2026-01-01T00:00:00"),
                ("Club Enthusiast", "Attend 10 events", "🏆", "attendance", "count", 10, 100, "2026-01-01T00:00:00"),
                ("Event Champion", "Attend 25 events", "👑", "attendance", "count", 25, 250, "2026-01-01T00:00:00"),
                ("Streak Master", "Attend 5 events in a row", "🔥", "attendance", "streak", 5, 75, "2026-01-01T00:00:00"),
                ("Perfect Month", "Attend all events in a month", "⭐", "attendance", "count", 4, 150, "2026-01-01T00:00:00"),

                # Participation badges
                ("Feedback Guru", "Submit feedback for 3 events", "💬", "feedback", "count", 3, 30, "2026-01-01T00:00:00"),
                ("Club Member", "Join your first club activity", "🤝", "participation", "first", 1, 20, "2026-01-01T00:00:00"),
                ("Social Butterfly", "Connect with 5 friends", "🦋", "social", "count", 5, 40, "2026-01-01T00:00:00"),
                ("Study Group Leader", "Create a study group", "📚", "participation", "first", 1, 60, "2026-01-01T00:00:00"),
                ("Event Sharer", "Share 3 events with friends", "📤", "social", "count", 3, 35, "2026-01-01T00:00:00"),
                ("Ambassador", "Become a club ambassador", "🏛️", "participation", "first", 1, 200, "2026-01-01T00:00:00"),
            ],
        )

    # Keep legacy demo records aligned to year 2026.
    cur.execute(
        """
        UPDATE clubs
        SET created_at = '2026' || substr(created_at, 5)
        WHERE substr(created_at, 1, 4) <> '2026'
        """
    )
    cur.execute(
        """
        UPDATE events
        SET date = '2026' || substr(date, 5)
        WHERE substr(date, 1, 4) <> '2026'
        """
    )

    conn.commit()
    conn.close()
