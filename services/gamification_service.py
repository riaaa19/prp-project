"""
Gamification Service
Handles achievements, points, leaderboards, and progress tracking.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
from database.db import get_connection


class GamificationService:
    """Service for managing gamification features."""

    @staticmethod
    def get_user_points(user_id: int) -> Dict:
        """Get user's current points and level information."""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT total_points, current_level, points_this_month, last_updated
            FROM user_points
            WHERE user_id = ?
        """, (user_id,))

        row = cur.fetchone()
        if not row:
            # Initialize user points if not exists
            now = datetime.now().isoformat()
            cur.execute("""
                INSERT INTO user_points (user_id, total_points, current_level, points_this_month, last_updated)
                VALUES (?, 0, 1, 0, ?)
            """, (user_id, now))
            conn.commit()
            row = {"total_points": 0, "current_level": 1, "points_this_month": 0, "last_updated": now}

        conn.close()
        return dict(row)

    @staticmethod
    def award_points(user_id: int, points: int, reason: str, reference_id: Optional[int] = None) -> bool:
        """Award points to a user and update their totals."""
        conn = get_connection()
        cur = conn.cursor()

        try:
            now = datetime.now().isoformat()

            # Insert points transaction
            cur.execute("""
                INSERT INTO points_transactions (user_id, points, reason, reference_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, points, reason, reference_id, now))

            # Update or insert user points
            cur.execute("""
                INSERT INTO user_points (user_id, total_points, current_level, points_this_month, last_updated)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_points = total_points + excluded.total_points,
                    points_this_month = points_this_month + excluded.points_this_month,
                    last_updated = excluded.last_updated,
                    current_level = CASE
                        WHEN total_points + excluded.total_points >= 1000 THEN 5
                        WHEN total_points + excluded.total_points >= 500 THEN 4
                        WHEN total_points + excluded.total_points >= 200 THEN 3
                        WHEN total_points + excluded.total_points >= 50 THEN 2
                        ELSE 1
                    END
            """, (user_id, points, points, now))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error awarding points: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_user_achievements(user_id: int) -> List[Dict]:
        """Get all achievements for a user."""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT ua.*, ab.name, ab.description, ab.icon, ab.category, ab.points_reward
            FROM user_achievements ua
            JOIN achievement_badges ab ON ua.badge_id = ab.id
            WHERE ua.user_id = ?
            ORDER BY ua.earned_at DESC
        """, (user_id,))

        achievements = [dict(row) for row in cur.fetchall()]
        conn.close()
        return achievements

    @staticmethod
    def get_available_badges(user_id: int) -> List[Dict]:
        """Get badges user hasn't earned yet."""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT ab.*, COALESCE(ua.progress, 0) as current_progress
            FROM achievement_badges ab
            LEFT JOIN user_achievements ua ON ab.id = ua.badge_id AND ua.user_id = ?
            WHERE ua.id IS NULL AND ab.is_active = 1
            ORDER BY ab.category, ab.points_reward DESC
        """, (user_id,))

        badges = [dict(row) for row in cur.fetchall()]
        conn.close()
        return badges

    @staticmethod
    def check_and_award_achievements(user_id: int) -> List[Dict]:
        """Check if user qualifies for any new achievements and award them."""
        conn = get_connection()
        cur = conn.cursor()

        awarded_badges = []

        try:
            # Get all active badges user hasn't earned
            cur.execute("""
                SELECT ab.*, COALESCE(ua.progress, 0) as current_progress
                FROM achievement_badges ab
                LEFT JOIN user_achievements ua ON ab.id = ua.badge_id AND ua.user_id = ?
                WHERE ua.id IS NULL AND ab.is_active = 1
            """, (user_id,))

            badges = cur.fetchall()

            for badge in badges:
                badge_dict = dict(badge)
                qualifies = GamificationService._check_badge_requirement(user_id, badge_dict, cur)

                if qualifies:
                    now = datetime.now().isoformat()

                    # Award the badge
                    cur.execute("""
                        INSERT INTO user_achievements (user_id, badge_id, earned_at, progress, is_completed)
                        VALUES (?, ?, ?, ?, 1)
                    """, (user_id, badge_dict['id'], now, badge_dict['requirement_value']))

                    # Award points for the badge
                    GamificationService.award_points(user_id, badge_dict['points_reward'],
                                                   f"achievement_earned:{badge_dict['name']}", badge_dict['id'])

                    awarded_badges.append({
                        "badge": badge_dict,
                        "earned_at": now
                    })

            conn.commit()

        except Exception as e:
            print(f"Error checking achievements: {e}")
        finally:
            conn.close()

        return awarded_badges

    @staticmethod
    def _check_badge_requirement(user_id: int, badge: Dict, cur) -> bool:
        """Check if user meets the requirement for a specific badge."""
        req_type = badge['requirement_type']
        req_value = badge['requirement_value']

        if req_type == 'first':
            # Check if user has done this at least once
            if badge['category'] == 'first_time':
                # First event attendance
                cur.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ? AND status = 'present'", (user_id,))
                return cur.fetchone()[0] >= 1
            elif badge['category'] == 'participation':
                if 'club' in badge['name'].lower():
                    # First club activity (attendance at any event)
                    cur.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ? AND status = 'present'", (user_id,))
                    return cur.fetchone()[0] >= 1
                elif 'study' in badge['name'].lower():
                    # Created a study group
                    cur.execute("SELECT COUNT(*) FROM study_groups WHERE creator_id = ?", (user_id,))
                    return cur.fetchone()[0] >= 1
                elif 'ambassador' in badge['name'].lower():
                    # Became ambassador
                    cur.execute("SELECT COUNT(*) FROM club_ambassadors WHERE user_id = ?", (user_id,))
                    return cur.fetchone()[0] >= 1

        elif req_type == 'count':
            if badge['category'] == 'attendance':
                # Event attendance count
                cur.execute("SELECT COUNT(*) FROM attendance WHERE user_id = ? AND status = 'present'", (user_id,))
                return cur.fetchone()[0] >= req_value
            elif badge['category'] == 'feedback':
                # Feedback submissions (we'll need to track this elsewhere)
                return False  # Placeholder
            elif badge['category'] == 'social':
                if 'friend' in badge['name'].lower():
                    # Friend connections
                    cur.execute("""
                        SELECT COUNT(*) FROM friend_connections
                        WHERE (user_id = ? OR friend_id = ?) AND status = 'accepted'
                    """, (user_id, user_id))
                    return cur.fetchone()[0] >= req_value
                elif 'share' in badge['name'].lower():
                    # Event shares
                    cur.execute("SELECT COUNT(*) FROM event_shares WHERE user_id = ?", (user_id,))
                    return cur.fetchone()[0] >= req_value

        elif req_type == 'streak':
            # Attendance streak
            return GamificationService._check_attendance_streak(user_id, req_value, cur)

        return False

    @staticmethod
    def _check_attendance_streak(user_id: int, required_streak: int, cur) -> bool:
        """Check if user has an attendance streak of required length."""
        # Get recent attendance records ordered by event date
        cur.execute("""
            SELECT a.status, e.date
            FROM attendance a
            JOIN events e ON a.event_id = e.id
            WHERE a.user_id = ? AND a.status = 'present'
            ORDER BY e.date DESC
            LIMIT ?
        """, (user_id, required_streak * 2))  # Get extra to check for gaps

        attendances = cur.fetchall()

        if len(attendances) < required_streak:
            return False

        # Check for consecutive attendance (allowing for some flexibility)
        streak_count = 0
        prev_date = None

        for attendance in attendances:
            event_date = date.fromisoformat(attendance['date'])

            if prev_date is None:
                streak_count = 1
            else:
                # Allow up to 7 days gap between events for streak continuity
                days_diff = (prev_date - event_date).days
                if days_diff <= 7:
                    streak_count += 1
                else:
                    streak_count = 1

            if streak_count >= required_streak:
                return True

            prev_date = event_date

        return False

    @staticmethod
    def get_leaderboard(category: str, period: str = "all_time", limit: int = 10) -> List[Dict]:
        """Get leaderboard for a specific category and period."""
        conn = get_connection()
        cur = conn.cursor()

        if category == "total_points":
            cur.execute("""
                SELECT u.username, up.total_points as score, up.current_level,
                       ROW_NUMBER() OVER (ORDER BY up.total_points DESC) as rank
                FROM user_points up
                JOIN users u ON up.user_id = u.id
                ORDER BY up.total_points DESC
                LIMIT ?
            """, (limit,))

        elif category == "monthly_points":
            current_month = datetime.now().strftime("%Y-%m")
            cur.execute("""
                SELECT u.username, up.points_this_month as score, up.current_level,
                       ROW_NUMBER() OVER (ORDER BY up.points_this_month DESC) as rank
                FROM user_points up
                JOIN users u ON up.user_id = u.id
                ORDER BY up.points_this_month DESC
                LIMIT ?
            """, (limit,))

        elif category == "attendance_streak":
            # This would require more complex logic to calculate current streaks
            # For now, return based on total attendance
            cur.execute("""
                SELECT u.username, COUNT(a.id) as score, 1 as current_level,
                       ROW_NUMBER() OVER (ORDER BY COUNT(a.id) DESC) as rank
                FROM users u
                LEFT JOIN attendance a ON u.id = a.user_id AND a.status = 'present'
                WHERE u.role = 'student'
                GROUP BY u.id, u.username
                ORDER BY score DESC
                LIMIT ?
            """, (limit,))

        else:
            conn.close()
            return []

        leaderboard = [dict(row) for row in cur.fetchall()]
        conn.close()
        return leaderboard

    @staticmethod
    def get_user_progress(user_id: int) -> List[Dict]:
        """Get user's progress towards club membership requirements."""
        conn = get_connection()
        cur = conn.cursor()

        # Get all clubs
        cur.execute("SELECT id, name FROM clubs")
        clubs = cur.fetchall()

        progress_list = []

        for club in clubs:
            club_id = club['id']
            club_name = club['name']

            # Initialize progress tracking if not exists
            GamificationService._ensure_progress_tracking(user_id, club_id, cur)

            # Get current progress
            cur.execute("""
                SELECT requirement_type, current_value, target_value, is_completed
                FROM progress_tracking
                WHERE user_id = ? AND club_id = ?
                ORDER BY requirement_type
            """, (user_id, club_id))

            requirements = cur.fetchall()

            progress_list.append({
                "club_id": club_id,
                "club_name": club_name,
                "requirements": [dict(req) for req in requirements]
            })

        conn.close()
        return progress_list

    @staticmethod
    def _ensure_progress_tracking(user_id: int, club_id: int, cur):
        """Ensure progress tracking records exist for user-club combination."""
        now = datetime.now().isoformat()

        # Define club membership requirements
        requirements = [
            ("events_attended", 3),  # Attend 3 events
            ("feedback_given", 2),   # Give feedback 2 times
            ("social_engagement", 1), # Connect with 1 friend or join 1 study group
            ("study_groups_joined", 1) # Join 1 study group
        ]

        for req_type, target in requirements:
            cur.execute("""
                INSERT OR IGNORE INTO progress_tracking
                (user_id, club_id, requirement_type, current_value, target_value, last_updated)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (user_id, club_id, req_type, target, now))

    @staticmethod
    def update_progress(user_id: int, club_id: int, requirement_type: str, increment: int = 1):
        """Update user's progress for a specific requirement."""
        conn = get_connection()
        cur = conn.cursor()

        try:
            now = datetime.now().isoformat()

            cur.execute("""
                UPDATE progress_tracking
                SET current_value = current_value + ?,
                    is_completed = CASE WHEN current_value + ? >= target_value THEN 1 ELSE 0 END,
                    last_updated = ?
                WHERE user_id = ? AND club_id = ? AND requirement_type = ?
            """, (increment, increment, now, user_id, club_id, requirement_type))

            conn.commit()
        except Exception as e:
            print(f"Error updating progress: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_gamification_stats(user_id: int) -> Dict:
        """Get comprehensive gamification statistics for a user."""
        conn = get_connection()
        cur = conn.cursor()

        # Get points info
        points_info = GamificationService.get_user_points(user_id)

        # Get achievement counts
        cur.execute("""
            SELECT
                COUNT(CASE WHEN ua.is_completed = 1 THEN 1 END) as earned_badges,
                COUNT(ab.id) as total_available_badges
            FROM achievement_badges ab
            LEFT JOIN user_achievements ua ON ab.id = ua.badge_id AND ua.user_id = ?
            WHERE ab.is_active = 1
        """, (user_id,))

        badge_stats = cur.fetchone()

        # Get recent achievements
        cur.execute("""
            SELECT ab.name, ab.icon, ua.earned_at
            FROM user_achievements ua
            JOIN achievement_badges ab ON ua.badge_id = ab.id
            WHERE ua.user_id = ? AND ua.is_completed = 1
            ORDER BY ua.earned_at DESC
            LIMIT 3
        """, (user_id,))

        recent_achievements = [dict(row) for row in cur.fetchall()]

        # Get leaderboard position
        cur.execute("""
            SELECT COUNT(*) + 1 as rank
            FROM user_points
            WHERE total_points > (SELECT total_points FROM user_points WHERE user_id = ?)
        """, (user_id,))

        rank_result = cur.fetchone()
        leaderboard_rank = rank_result['rank'] if rank_result else None

        return progress_list


# Module-level convenience functions
def get_gamification_stats(user_id: int) -> Dict:
    """Get comprehensive gamification statistics for a user."""
    return GamificationService.get_gamification_stats(user_id)


def get_user_points(user_id: int) -> Dict:
    """Get user's current points and level information."""
    return GamificationService.get_user_points(user_id)


def award_points(user_id: int, points: int, reason: str, reference_id: Optional[int] = None) -> bool:
    """Award points to a user and update their totals."""
    return GamificationService.award_points(user_id, points, reason, reference_id)


def check_and_award_achievements(user_id: int) -> List[Dict]:
    """Check if user qualifies for any new achievements and award them."""
    return GamificationService.check_and_award_achievements(user_id)


def get_user_achievements(user_id: int) -> List[Dict]:
    """Get all achievements for a user."""
    return GamificationService.get_user_achievements(user_id)


def get_available_badges(user_id: int) -> List[Dict]:
    """Get badges user hasn't earned yet."""
    return GamificationService.get_available_badges(user_id)


def get_leaderboard(category: str, period: str = "all_time", limit: int = 10) -> List[Dict]:
    """Get leaderboard for a specific category and period."""
    return GamificationService.get_leaderboard(category, period, limit)


def get_user_progress(user_id: int) -> List[Dict]:
    """Get user's progress towards club membership requirements."""
    return GamificationService.get_user_progress(user_id)


def update_progress(user_id: int, club_id: int, requirement_type: str, increment: int = 1):
    """Update user's progress for a specific requirement."""
    GamificationService.update_progress(user_id, club_id, requirement_type, increment)