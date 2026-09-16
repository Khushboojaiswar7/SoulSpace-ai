# analytics.py
# This file contains all analytics-related API endpoints.
#
# Endpoints:
#   GET /analytics/mood-trends  → Returns mood counts for the last 7 days
#   GET /analytics/summary      → Returns a weekly + monthly summary
#   GET /analytics/streak       → Returns how many consecutive days the user journalled
#
# NOTE: Right now these endpoints return a MIX of real data from the database
# and dummy/sample data to demonstrate how the frontend charts will look.
# In a later version, all data will be pulled from the live database.
#
# All endpoints require a valid JWT token in the Authorization header.
# Example header:  Authorization: Bearer <your_token_here>

import random
import datetime

from flask import Blueprint, request, jsonify
from auth import decode_token
from database import get_connection
import jwt

# ---------------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------------
analytics_bp = Blueprint("analytics", __name__)


# ---------------------------------------------------------------------------
# HELPER: get_current_user_id  (same pattern as journal.py)
# ---------------------------------------------------------------------------
def get_current_user_id():
    """
    Reads the Authorization header, verifies the JWT, and returns the user ID.

    Returns:
        int | None: User ID if token is valid, None otherwise.
    """
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        payload = decode_token(token)
        return payload["sub"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ---------------------------------------------------------------------------
# HELPER: get_real_mood_counts(user_id, days)
# ---------------------------------------------------------------------------
def get_real_mood_counts(user_id, days=7):
    """
    Queries the database for this user's journal mood counts over the last
    `days` days and returns a dict of { mood_label: count }.

    If the user has no entries yet, returns an empty dict so the caller
    can fall back to dummy data.

    Args:
        user_id (int): The current user's ID.
        days    (int): How many days to look back (default: 7).

    Returns:
        dict: e.g. { "Happy": 3, "Calm": 1 }
    """
    sql = """
        SELECT m.label, COUNT(*) AS cnt
        FROM   journals j
        JOIN   moods m ON m.id = j.mood_id
        WHERE  j.user_id   = %s
          AND  j.created_at >= NOW() - INTERVAL '%s days'
        GROUP  BY m.label
        ORDER  BY cnt DESC;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, days))
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    except Exception as error:
        print(f"[analytics.py] get_real_mood_counts error: {error}")
        return {}
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# HELPER: get_real_entry_count(user_id, days)
# ---------------------------------------------------------------------------
def get_real_entry_count(user_id, days=7):
    """
    Returns the total number of journal entries the user wrote in the
    last `days` days.

    Args:
        user_id (int): The current user's ID.
        days    (int): How many days to look back.

    Returns:
        int: Total entry count.
    """
    sql = """
        SELECT COUNT(*)
        FROM   journals
        WHERE  user_id   = %s
          AND  created_at >= NOW() - INTERVAL '%s days';
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, days))
        row = cursor.fetchone()
        return row[0] if row else 0
    except Exception as error:
        print(f"[analytics.py] get_real_entry_count error: {error}")
        return 0
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# HELPER: build_dummy_weekly_trend()
# ---------------------------------------------------------------------------
def build_dummy_weekly_trend():
    """
    Generates a list of dummy mood data points for the last 7 days.
    Each item represents one day and a randomly chosen mood score (1-5).

    Used when the user has no real entries yet so the frontend still has
    data to render sample charts.

    Returns:
        list[dict]: 7 items, each with 'date' (YYYY-MM-DD) and 'mood_score'.
    """
    today = datetime.date.today()
    moods = ["Happy", "Calm", "Anxious", "Sad", "Excited"]

    trend = []
    for i in range(6, -1, -1):          # 6 days ago → today
        day = today - datetime.timedelta(days=i)
        trend.append({
            "date":       day.strftime("%Y-%m-%d"),
            "mood":       random.choice(moods),
            "mood_score": random.randint(1, 5)   # 1 = very low, 5 = great
        })
    return trend


# ===========================================================================
# ROUTE: GET /analytics/mood-trends
# ===========================================================================
@analytics_bp.route("/mood-trends", methods=["GET"])
def mood_trends():
    """
    Returns mood frequency data for use in bar/pie charts on the frontend.

    Response combines:
    - Real mood counts from the database (if entries exist)
    - A dummy 7-day daily trend for the line chart (always present)

    Query params (optional):
        days (int): How many past days to analyse. Default = 7.

    Returns:
        200 OK           : { period_days, mood_counts, daily_trend, source }
        401 Unauthorized : { error }

    Example response:
        {
            "period_days": 7,
            "mood_counts": { "Happy": 3, "Calm": 2, "Anxious": 1 },
            "daily_trend": [
                { "date": "2026-02-15", "mood": "Happy", "mood_score": 4 },
                ...
            ],
            "source": "real"   // or "demo" if no real data exists yet
        }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # Allow ?days=30 for monthly view, default to 7
    try:
        days = int(request.args.get("days", 7))
        if days not in (7, 30):       # Only support weekly / monthly for now
            days = 7
    except ValueError:
        days = 7

    # Try to get real data first
    real_counts = get_real_mood_counts(user_id, days)

    if real_counts:
        # User has real data → use it
        mood_counts = real_counts
        source = "real"
    else:
        # No real data yet → send friendly demo data so the UI isn't empty
        mood_counts = {
            "Happy":   3,
            "Calm":    2,
            "Anxious": 1,
            "Sad":     1,
            "Excited": 2
        }
        source = "demo"

    return jsonify({
        "period_days": days,
        "mood_counts": mood_counts,
        "daily_trend": build_dummy_weekly_trend(),
        "source":      source      # "real" or "demo"
    }), 200


# ===========================================================================
# ROUTE: GET /analytics/summary
# ===========================================================================
@analytics_bp.route("/summary", methods=["GET"])
def summary():
    """
    Returns a combined weekly + monthly summary for the logged-in user.

    Real data used:
        - Entry counts for the last 7 and 30 days (from the database)

    Dummy/demo data used:
        - Average mood score (placeholder – will be a real average in v2)
        - Most frequent mood label (placeholder)
        - Motivational tip based on the dominant mood

    Returns:
        200 OK           : { weekly, monthly, tip }
        401 Unauthorized : { error }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # --- Real data: entry counts ---
    weekly_entries  = get_real_entry_count(user_id, days=7)
    monthly_entries = get_real_entry_count(user_id, days=30)

    # --- Real data: dominant mood this week (if any entries exist) ---
    weekly_mood_counts = get_real_mood_counts(user_id, days=7)

    if weekly_mood_counts:
        top_mood = max(weekly_mood_counts, key=weekly_mood_counts.get)
        avg_mood_score = round(random.uniform(3.0, 4.5), 1)  # Placeholder average
    else:
        top_mood       = "N/A  (write your first entry!)"
        avg_mood_score = None

    # --- AI Pipeline data: emotion + stress from entry_analyses ---
    primary_emotion = None
    stress_trend = None
    avg_emotion_intensity = None
    recurring_themes = []
    emotional_growth = []

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Get the most frequent primary emotion this week
        cursor.execute("""
            SELECT primary_emotion, COUNT(*) as cnt,
                   ROUND(AVG(emotion_intensity)::numeric, 2) as avg_intensity
            FROM   entry_analyses
            WHERE  user_id = %s
              AND  created_at >= NOW() - INTERVAL '7 days'
            GROUP  BY primary_emotion
            ORDER  BY cnt DESC
            LIMIT  1;
        """, (user_id,))
        emotion_row = cursor.fetchone()
        if emotion_row:
            primary_emotion = emotion_row[0]
            avg_emotion_intensity = float(emotion_row[2]) if emotion_row[2] else None

        # Get average stress level this week
        cursor.execute("""
            SELECT stress_level, COUNT(*) as cnt
            FROM   entry_analyses
            WHERE  user_id = %s
              AND  created_at >= NOW() - INTERVAL '7 days'
            GROUP  BY stress_level
            ORDER  BY cnt DESC
            LIMIT  1;
        """, (user_id,))
        stress_row = cursor.fetchone()
        if stress_row:
            stress_trend = stress_row[0]

        # Get latest memory patterns for recurring themes & growth
        cursor.execute("""
            SELECT patterns
            FROM   memory_patterns
            WHERE  user_id = %s
            ORDER  BY created_at DESC
            LIMIT  1;
        """, (user_id,))
        pattern_row = cursor.fetchone()
        if pattern_row and pattern_row[0]:
            patterns = pattern_row[0] if isinstance(pattern_row[0], dict) else {}
            recurring_themes = patterns.get("recurring_stressors", [])[:5]
            emotional_growth = patterns.get("positive_improvements", [])[:3]

        cursor.close()
    except Exception as error:
        print(f"[analytics.py] AI data fetch error: {error}")
    finally:
        conn.close()

    # --- Motivational tips keyed by mood ---
    tips = {
        "Happy":   "You're glowing! Keep nurturing what makes you happy. 🌟",
        "Calm":    "Steady and grounded – a great foundation for growth. 🌿",
        "Anxious": "Take it one breath at a time. You've got this. 💙",
        "Sad":     "It's okay to feel low. Be kind to yourself today. 🌧️",
        "Excited": "Channel that energy into something you love! 🚀",
        "Angry":   "Take a pause. Write it out – that's what SoulSpace is for. ✍️",
    }
    tip = tips.get(top_mood, "Keep journalling – every entry is a step forward. 📖")

    return jsonify({
        "weekly": {
            "entries":              weekly_entries,
            "top_mood":             top_mood,
            "avg_mood_score":       avg_mood_score,
            "primary_emotion":      primary_emotion,
            "avg_emotion_intensity": avg_emotion_intensity,
            "stress_trend":         stress_trend,
        },
        "monthly": {
            "entries":         monthly_entries,
        },
        "recurring_themes":  recurring_themes,
        "emotional_growth":  emotional_growth,
        "tip": tip
    }), 200


# ===========================================================================
# ROUTE: GET /analytics/streak
# ===========================================================================
@analytics_bp.route("/streak", methods=["GET"])
def streak():
    """
    Returns the user's current journalling streak – the number of consecutive
    days (ending today) on which they wrote at least one journal entry.

    A streak of 0 means the user hasn't written anything today or yesterday.

    Returns:
        200 OK           : { streak_days, message }
        401 Unauthorized : { error }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # Fetch the distinct dates on which this user has written entries
    sql = """
        SELECT DISTINCT DATE(created_at) AS entry_date
        FROM   journals
        WHERE  user_id = %s
        ORDER  BY entry_date DESC;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
    except Exception as error:
        print(f"[analytics.py] streak error: {error}")
        return jsonify({"error": "Could not calculate streak."}), 500
    finally:
        cursor.close()
        conn.close()

    # Convert to a set of date objects for fast lookup
    entry_dates = {row[0] for row in rows}

    # Walk backwards from today, counting consecutive days with entries
    today         = datetime.date.today()
    streak_days   = 0
    current_day   = today

    while current_day in entry_dates:
        streak_days += 1
        current_day -= datetime.timedelta(days=1)

    # Build a friendly message
    if streak_days == 0:
        message = "No streak yet – write your first entry today! ✍️"
    elif streak_days == 1:
        message = "You journalled today – keep it up! 🌱"
    elif streak_days < 7:
        message = f"{streak_days}-day streak! You're building a great habit. 🔥"
    else:
        message = f"Amazing! {streak_days}-day streak! You're on fire! 🚀🔥"

    return jsonify({
        "streak_days": streak_days,
        "message":     message
    }), 200
