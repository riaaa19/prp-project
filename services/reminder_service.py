"""
Reminder service.
Manages reminders, notifications, and user preferences for events.
"""
import json
from datetime import datetime, timedelta
from database.db import get_connection
from services import event_service, notification_service


def get_user_preferences(user_id: int):
    """Get user reminder preferences."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        else:
            # Create default preferences
            create_default_preferences(user_id)
            return get_user_preferences(user_id)
    finally:
        conn.close()


def create_default_preferences(user_id: int):
    """Create default reminder preferences for a user."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_preferences
            (user_id, email_reminders, push_notifications, weather_alerts, transport_reminders,
             default_reminder_1day, default_reminder_1hr, updated_at)
            VALUES (?, 1, 1, 1, 1, 1, 1, ?)
        """, (user_id, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def update_user_preferences(user_id: int, preferences: dict):
    """Update user reminder preferences."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_preferences SET
                email_reminders = ?,
                push_notifications = ?,
                weather_alerts = ?,
                transport_reminders = ?,
                default_reminder_1day = ?,
                default_reminder_1hr = ?,
                updated_at = ?
            WHERE user_id = ?
        """, (
            preferences.get('email_reminders', 1),
            preferences.get('push_notifications', 1),
            preferences.get('weather_alerts', 1),
            preferences.get('transport_reminders', 1),
            preferences.get('default_reminder_1day', 1),
            preferences.get('default_reminder_1hr', 1),
            datetime.now().isoformat(),
            user_id
        ))
        conn.commit()
    finally:
        conn.close()


def create_event_reminders(user_id: int, event_id: int):
    """Create default reminders for an event registration."""
    prefs = get_user_preferences(user_id)

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Get event details
        event = event_service.get_event_by_id(event_id)
        if not event:
            return

        event_datetime = datetime.fromisoformat(event.date + "T00:00:00")  # Assuming date only, add time if available

        reminders_to_create = []

        # 1-day reminder
        if prefs.get('default_reminder_1day'):
            reminder_time = event_datetime - timedelta(days=1)
            reminders_to_create.append(('event_start', reminder_time.isoformat()))

        # 1-hour reminder
        if prefs.get('default_reminder_1hr'):
            reminder_time = event_datetime - timedelta(hours=1)
            reminders_to_create.append(('event_start', reminder_time.isoformat()))

        # Weather alert (simulate - would normally check weather API)
        if prefs.get('weather_alerts') and is_outdoor_event(event.name):
            weather_time = event_datetime - timedelta(hours=24)
            reminders_to_create.append(('weather_alert', weather_time.isoformat()))

        # Transport reminder
        if prefs.get('transport_reminders'):
            transport_time = event_datetime - timedelta(hours=2)
            reminders_to_create.append(('transport', transport_time.isoformat()))

        # Insert reminders
        for reminder_type, reminder_time in reminders_to_create:
            cur.execute("""
                INSERT OR REPLACE INTO reminders
                (user_id, event_id, reminder_type, reminder_time, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (user_id, event_id, reminder_type, reminder_time, datetime.now().isoformat()))

        conn.commit()
    finally:
        conn.close()


def get_user_reminders(user_id: int):
    """Get all active reminders for a user."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, e.name as event_name, e.date as event_date, e.club
            FROM reminders r
            JOIN events e ON r.event_id = e.id
            WHERE r.user_id = ? AND r.is_active = 1
            ORDER BY r.reminder_time
        """, (user_id,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def check_and_send_reminders():
    """Check for due reminders and send notifications. Call this periodically."""
    now = datetime.now()
    window_start = now - timedelta(minutes=5)  # Check for reminders in the last 5 minutes

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.*, u.username, e.name as event_name, e.date as event_date, e.club
            FROM reminders r
            JOIN users u ON r.user_id = u.id
            JOIN events e ON r.event_id = e.id
            WHERE r.is_active = 1
            AND r.reminder_time BETWEEN ? AND ?
        """, (window_start.isoformat(), now.isoformat()))

        due_reminders = cur.fetchall()

        for reminder in due_reminders:
            send_reminder_notification(reminder)

            # Mark reminder as inactive after sending
            cur.execute("UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder['id'],))

        conn.commit()
        return len(due_reminders)
    finally:
        conn.close()


def send_reminder_notification(reminder):
    """Send appropriate notification based on reminder type."""
    user_id = reminder['user_id']
    event_name = reminder['event_name']
    event_date = reminder['event_date']
    reminder_type = reminder['reminder_type']

    messages = {
        'event_start': f"⏰ Reminder: '{event_name}' is coming up on {event_date}!",
        'event_update': f"📝 Update: '{event_name}' details have changed. Check the latest information.",
        'weather_alert': f"🌧️ Weather Alert: '{event_name}' on {event_date} may be affected by weather. Check forecast!",
        'transport': f"🚌 Transport Reminder: Don't forget transportation for '{event_name}' on {event_date}. Check shuttle schedules!"
    }

    message = messages.get(reminder_type, f"Reminder for '{event_name}' on {event_date}")
    notification_service.create_notification(user_id, message)


def is_outdoor_event(event_name: str) -> bool:
    """Simple heuristic to determine if an event is likely outdoor."""
    outdoor_keywords = ['sports', 'outdoor', 'park', 'field', 'stadium', 'marathon', 'hiking', 'camping']
    return any(keyword in event_name.lower() for keyword in outdoor_keywords)


def cancel_event_reminders(user_id: int, event_id: int):
    """Cancel all reminders for a specific event."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE reminders SET is_active = 0
            WHERE user_id = ? AND event_id = ?
        """, (user_id, event_id))
        conn.commit()
    finally:
        conn.close()


def get_simulated_weather_forecast(event_date: str) -> dict:
    """Simulate weather forecast (in real app, would call weather API)."""
    # Simple simulation based on date
    import random
    conditions = ['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy']
    temperatures = range(15, 30)

    return {
        'condition': random.choice(conditions),
        'temperature': random.choice(temperatures),
        'precipitation_chance': random.randint(0, 100)
    }


def get_transport_schedule(event_date: str) -> dict:
    """Get simulated transport schedule for events."""
    # Simulate campus shuttle schedule
    return {
        'shuttle_times': ['08:00', '09:00', '10:00', '14:00', '15:00', '16:00'],
        'parking_available': True,
        'peak_hours': ['08:00-10:00', '14:00-16:00']
    }