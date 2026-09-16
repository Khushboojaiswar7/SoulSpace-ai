# mood.py
# Flask blueprint for standalone mood logging.
#
# Endpoint:
#   POST /api/mood   – Log a mood + life-area tag for the current user.
#
# This is completely independent of the journal system.
# The journal endpoint is NOT modified.

import jwt
from flask import Blueprint, request, jsonify
from functools import wraps
from models import create_mood_log
from auth import decode_token

# ---------------------------------------------------------------------------
# Blueprint definition
# ---------------------------------------------------------------------------
mood_bp = Blueprint("mood", __name__)

# ---------------------------------------------------------------------------
# Allowed values  (validated server-side to prevent junk data)
# ---------------------------------------------------------------------------
VALID_MOODS = {"happy", "sad", "calm", "angry", "anxious"}
VALID_TAGS  = {"work", "stress", "health", "relationships", "gratitude", "goals"}


# ---------------------------------------------------------------------------
# JWT auth decorator  (mirrors the pattern used in journal.py / analytics.py)
# ---------------------------------------------------------------------------
def require_token(f):
    """
    Decorator that extracts and verifies the Bearer JWT from the
    Authorization header.  Injects `user_id` into the wrapped function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        # Pass the user's id into the route handler
        
        user_id = int(payload["sub"])
        return f(user_id=user_id, *args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# POST /api/mood
# ---------------------------------------------------------------------------
@mood_bp.route("/mood", methods=["POST"])
@require_token
def log_mood(user_id):
    """
    Log a standalone mood entry for the authenticated user.

    Request JSON:
        {
            "mood": "happy",   # one of: happy, sad, calm, angry, anxious
            "tag":  "work"     # one of: work, stress, health,
                               #         relationships, gratitude, goals
        }

    Returns:
        201 + { "message": "Mood logged", "mood_log": { ... } }
        400 if mood/tag is missing or invalid
    """
    data = request.get_json(silent=True) or {}

    # ── Validate ─────────────────────────────────────────────────────────
    mood = str(data.get("mood", "")).strip().lower()
    tag  = str(data.get("tag",  "")).strip().lower()

    if not mood:
        return jsonify({"error": "'mood' is required"}), 400
    if mood not in VALID_MOODS:
        return jsonify({
            "error": f"Invalid mood '{mood}'. Must be one of: {', '.join(sorted(VALID_MOODS))}"
        }), 400

    if not tag:
        return jsonify({"error": "'tag' is required"}), 400
    if tag not in VALID_TAGS:
        return jsonify({
            "error": f"Invalid tag '{tag}'. Must be one of: {', '.join(sorted(VALID_TAGS))}"
        }), 400

    # ── Persist ──────────────────────────────────────────────────────────
    try:
        mood_log = create_mood_log(user_id=user_id, mood=mood, tag=tag)
    except Exception as err:
        print(f"[mood.py] DB error: {err}")
        return jsonify({"error": "Failed to save mood log"}), 500

    return jsonify({
        "message":  "Mood logged",
        "mood_log": mood_log,
    }), 201
