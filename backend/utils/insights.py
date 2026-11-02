# insights.py
# Flask Blueprint for AI insight endpoints.
#
# These endpoints expose the data produced by the agentic AI pipeline
# to the frontend dashboard.
#
# Endpoints:
#   GET /insights/me          → Current user profile flags (incl. is_study_participant)
#   GET /insights/timeline    → Emotional timeline from entry analyses
#   GET /insights/patterns    → Approved Memory Agent patterns
#   GET /insights/reflection  → Latest Disclosure Agent output
#   GET /insights/crisis-resources → Crisis support resources (always available)
#   GET /insights/journey-report   → Full-history LLM report (disabled for study participants)
#
# All endpoints (except crisis-resources) require a valid JWT token.

import json

from flask import Blueprint, request, jsonify
from auth import decode_token
from database import get_connection
from agents.crisis_detector import CRISIS_RESOURCES
import jwt

# ---------------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------------
insights_bp = Blueprint("insights", __name__)


# ---------------------------------------------------------------------------
# HELPER: get_current_user_id
# ---------------------------------------------------------------------------
def get_current_user_id():
    """
    Reads the Authorization header, verifies the JWT, and returns the user ID.
    """
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ===========================================================================
# ROUTE: GET /insights/me
# ===========================================================================
@insights_bp.route("/me", methods=["GET"])
def get_me():
    """
    Returns lightweight profile flags for the current user.
    Currently exposes:
        - is_study_participant (bool): whether this user is a research study participant.

    The frontend uses this to conditionally hide features that are excluded from
    the study's safety claims (e.g. the Journey Report button).
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT is_study_participant FROM users WHERE id = %s;",
            (user_id,)
        )
        row = cur.fetchone()
        is_study_participant = bool(row[0]) if row and row[0] is not None else False
        return jsonify({"is_study_participant": is_study_participant}), 200
    except Exception as error:
        print(f"[insights.py] get_me error: {error}")
        return jsonify({"is_study_participant": False}), 200
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


# ===========================================================================
# ROUTE: GET /insights/timeline
# ===========================================================================
@insights_bp.route("/timeline", methods=["GET"])
def emotional_timeline():
    """
    Returns the user's emotional timeline — a time-series of entry analyses
    for charting emotion intensity, stress levels, and sentiment over time.

    Query params (optional):
        limit (int): Number of entries to return. Default = 30.

    Returns:
        200 OK: { timeline: [ { date, sentiment, primary_emotion,
                                 emotion_intensity, stress_level,
                                 risk_level, confidence } ] }
        401 Unauthorized: { error }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    try:
        limit = int(request.args.get("limit", 30))
        limit = min(max(limit, 1), 100)  # clamp between 1 and 100
    except ValueError:
        limit = 30

    sql = """
        SELECT ea.sentiment, ea.primary_emotion, ea.emotion_intensity,
               ea.stress_level, ea.risk_level, ea.confidence,
               ea.keywords, ea.cognitive_distortions, ea.created_at
        FROM   entry_analyses ea
        WHERE  ea.user_id = %s
        ORDER  BY ea.created_at DESC
        LIMIT  %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, limit))
        rows = cursor.fetchall()
        timeline = [
            {
                "sentiment": row[0],
                "primary_emotion": row[1],
                "emotion_intensity": row[2],
                "stress_level": row[3],
                "risk_level": row[4],
                "confidence": row[5],
                "keywords": row[6] if row[6] else [],
                "cognitive_distortions": row[7] if row[7] else [],
                "date": str(row[8])
            }
            for row in rows
        ]
        # Reverse so oldest is first (better for line charts)
        timeline.reverse()
        return jsonify({"timeline": timeline}), 200
    except Exception as error:
        print(f"[insights.py] emotional_timeline error: {error}")
        return jsonify({"error": "Could not fetch timeline data."}), 500
    finally:
        cursor.close()
        conn.close()


# ===========================================================================
# ROUTE: GET /insights/patterns
# ===========================================================================
@insights_bp.route("/patterns", methods=["GET"])
def get_patterns():
    """
    Returns the most recent approved patterns from the Memory Agent,
    filtered through the Safety Gate.

    Returns:
        200 OK: { patterns: {...}, has_patterns: bool, last_updated: str }
        401 Unauthorized: { error }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # Get latest memory patterns
    sql_patterns = """
        SELECT patterns, entries_analyzed, confidence, created_at
        FROM   memory_patterns
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  1;
    """

    # Get latest safety decision
    sql_safety = """
        SELECT decision, reason, agreement_score, created_at
        FROM   safety_logs
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  1;
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Fetch patterns
        cursor.execute(sql_patterns, (user_id,))
        pattern_row = cursor.fetchone()

        # Fetch safety decision
        cursor.execute(sql_safety, (user_id,))
        safety_row = cursor.fetchone()

        if not pattern_row:
            return jsonify({
                "patterns": None,
                "has_patterns": False,
                "message": "Not enough journal entries to detect patterns yet. Keep journaling!"
            }), 200

        patterns = pattern_row[0] if pattern_row[0] else {}
        entries_analyzed = pattern_row[1]
        confidence = pattern_row[2]
        last_updated = str(pattern_row[3])

        # Check if safety gate approved the patterns
        safety_approved = False
        safety_reason = "No safety evaluation yet."
        if safety_row:
            safety_approved = safety_row[0] == "approved"
            safety_reason = safety_row[1] or ""

        return jsonify({
            "patterns": patterns if safety_approved else None,
            "has_patterns": safety_approved,
            "entries_analyzed": entries_analyzed,
            "confidence": confidence,
            "safety_approved": safety_approved,
            "safety_reason": safety_reason,
            "last_updated": last_updated
        }), 200

    except Exception as error:
        print(f"[insights.py] get_patterns error: {error}")
        return jsonify({"error": "Could not fetch pattern data."}), 500
    finally:
        cursor.close()
        conn.close()


# ===========================================================================
# ROUTE: GET /insights/reflection
# ===========================================================================
@insights_bp.route("/reflection", methods=["GET"])
def get_reflection():
    """
    Returns the latest AI-generated reflection (Disclosure Agent output).

    Returns:
        200 OK: { reflection: {...}, has_reflection: bool }
        401 Unauthorized: { error }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    sql = """
        SELECT disclosed_patterns, disclosure_text, created_at
        FROM   disclosure_history
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  1;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({
                "reflection": None,
                "has_reflection": False,
                "message": "Keep journaling — AI reflections will appear after enough entries."
            }), 200

        return jsonify({
            "reflection": {
                "patterns": row[0] if row[0] else {},
                "text": row[1] or "",
                "date": str(row[2])
            },
            "has_reflection": True
        }), 200

    except Exception as error:
        print(f"[insights.py] get_reflection error: {error}")
        return jsonify({"error": "Could not fetch reflection data."}), 500
    finally:
        cursor.close()
        conn.close()


# ===========================================================================
# ROUTE: GET /insights/crisis-resources
# ===========================================================================
@insights_bp.route("/crisis-resources", methods=["GET"])
def crisis_resources():
    """
    Returns crisis support resources. Always available, no auth required.
    This endpoint can be accessed even without logging in.
    """
    return jsonify(CRISIS_RESOURCES), 200


# ===========================================================================
# ROUTE: GET /insights/journey-report
# ===========================================================================
@insights_bp.route("/journey-report", methods=["GET"])
def get_journey_report():
    """
    Generates and returns the Comprehensive Emotional Journey Report using the Report Agent.

    STUDY GUARD: This feature bypasses the Verification Agent and Safety Gate.
    Users enrolled as study participants (is_study_participant = TRUE) are blocked
    at this layer with HTTP 403. The frontend also hides the button, but this
    server-side check is the authoritative enforcement — never rely on the UI alone.
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    # ── Study participant gate ──────────────────────────────────────────────
    # Check the is_study_participant column on the users table.
    # This column is added via the live migration in database.py.
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT is_study_participant FROM users WHERE id = %s;",
            (user_id,)
        )
        row = cur.fetchone()
        is_study_participant = bool(row[0]) if row and row[0] is not None else False
    except Exception as db_error:
        print(f"[insights.py] study-participant check error: {db_error}")
        is_study_participant = False
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

    if is_study_participant:
        return jsonify({
            "error": "feature_disabled_for_study",
            "message": (
                "The Journey Report feature is not available to research study "
                "participants. This feature has been excluded from the study's "
                "safety claims because it generates LLM output that has not "
                "passed through the Verification Agent or Safety Gate."
            )
        }), 403
    # ── End study participant gate ──────────────────────────────────────────

    try:
        from agents.report_agent import generate_report
        report_data = generate_report(user_id)
        return jsonify({"report": report_data}), 200
    except Exception as error:
        print(f"[insights.py] get_journey_report error: {error}")
        return jsonify({"error": "Could not generate journey report."}), 500
