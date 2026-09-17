# journal.py
# This file contains all journal-related API endpoints.
#
# Endpoints:
#   POST   /journal/         → Create a new journal entry
#   GET    /journal/         → List all entries for the logged-in user
#   GET    /journal/<id>     → Get a single entry by ID
#   PUT    /journal/<id>     → Update an entry by ID
#   DELETE /journal/<id>     → Delete an entry by ID
#   GET    /journal/moods    → List all mood options
#
# All write/read endpoints require a valid JWT token in the Authorization header.
# Example header:  Authorization: Bearer <your_token_here>

from flask import Blueprint, request, jsonify
from auth import decode_token                        # Our helper from auth.py
from models import (
    create_journal_entry,
    get_journal_entries,
    get_journal_entry_by_id,
    update_journal_entry,
    delete_journal_entry,
    get_all_moods
)
from utils.sentiment import analyze_sentiment        # NLP sentiment analysis
from utils.suggestion import SuggestionService      # Rule-based suggestion engine
from agents.pipeline import run_pipeline             # Agentic AI pipeline
import jwt   # For catching JWT exceptions

# Blueprint setup

journal_bp = Blueprint("journal", __name__)

# HELPER: get_current_user_id

def get_current_user_id():
    """
    Reads the Authorization header, verifies the JWT token, and returns
    the logged-in user's ID.

    The frontend should send:
        Authorization: Bearer <token>

    Returns:
        int | None: The user's ID if the token is valid, or None otherwise.
    """
    auth_header = request.headers.get("Authorization", "")

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    try:
        payload = decode_token(token)
        return int(payload["sub"])   
    except jwt.ExpiredSignatureError:
        return None   # Token has expired – user must log in again
    except jwt.InvalidTokenError:
        return None   # Token is tampered or malformed


# ROUTE: POST /journal
# ---------------------------------------------------------------------------
@journal_bp.route("/", methods=["POST"])
def create_entry():
    """
    Creates a new journal entry for the logged-in user.

    Expected JSON body:
        {
            "title":   "My first entry",   (optional)
            "content": "Today I felt ...", (required)
            "mood_id": 1                   (optional – see GET /journal/moods)
        }

    Returns:
        201 Created      : { message, entry }
        400 Bad Request  : { error } – missing content
        401 Unauthorized : { error } – invalid or missing token
    """
    # --- Verify the user is logged in ---
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    content = data.get("content", "").strip()
    title   = data.get("title",   "").strip()
    mood_id = data.get("mood_id", None)  

    # Content is the only required field
    if not content:
        return jsonify({"error": "content is required"}), 400

    # mood_id must be an integer if provided
    if mood_id is not None:
        try:
            mood_id = int(mood_id)
        except (ValueError, TypeError):
            return jsonify({"error": "mood_id must be a number"}), 400

    # --- Run sentiment analysis on the journal content ---
    sentiment = analyze_sentiment(content)
    sentiment_score = sentiment["score"]
    sentiment_label = sentiment["label"]

    # --- Resolve the mood label (for mood-aware suggestions) ---
    mood_label = None
    if mood_id is not None:
        all_moods = get_all_moods()   # small lookup: returns [{id, label}, ...]
        mood_map  = {m["id"]: m["label"] for m in all_moods}
        mood_label = mood_map.get(mood_id)

    # --- Generate wellness suggestion ---
    suggestion = SuggestionService.generate(
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        mood_label=mood_label
    )

    # Save to the database (including sentiment results and suggestion)
    try:
        entry = create_journal_entry(
            user_id,
            title or None,
            content,
            mood_id,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            suggestion=suggestion
        )
    except Exception:
        return jsonify({"error": "Could not save the entry. Please try again."}), 500

    # --- Run the full agentic AI pipeline (after entry is saved) ---
    # This adds rich analysis data to the new entry_analyses table.
    # If the pipeline detects a crisis, crisis resources are included.
    pipeline_result = None
    try:
        pipeline_result = run_pipeline(
            user_id=user_id,
            journal_text=content,
            journal_id=entry.get("id")
        )
    except Exception as pipeline_err:
        print(f"[journal.py] AI pipeline error (non-fatal): {pipeline_err}")
        # Pipeline errors are non-fatal — the entry is already saved

    # Build the response
    response = {
        "message":         "Journal entry saved!",
        "entry":           entry,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "suggestion":      suggestion
    }

    # Attach pipeline results if available
    if pipeline_result:
        # If crisis was detected, include resources
        if pipeline_result.get("crisis"):
            response["crisis_detected"] = True
            response["crisis_resources"] = pipeline_result["crisis"]["resources"]
            response["crisis_severity"] = pipeline_result["crisis"]["severity"]
            # Override suggestion with crisis message
            response["suggestion"] = pipeline_result["crisis"]["resources"]["message"]
        else:
            response["crisis_detected"] = False

        # Attach enriched analysis
        if pipeline_result.get("analysis"):
            response["ai_analysis"] = pipeline_result["analysis"]

        # Attach disclosure if available
        if pipeline_result.get("disclosure"):
            response["ai_reflection"] = pipeline_result["disclosure"]

    return jsonify(response), 201


# ---------------------------------------------------------------------------
# ROUTE: GET /journal/
# ---------------------------------------------------------------------------
@journal_bp.route("/", methods=["GET"])
def list_entries():
    """
    Returns all journal entries belonging to the logged-in user,
    ordered from newest to oldest.

    Returns:
        200 OK           : { entries: [ ... ] }
        401 Unauthorized : { error }
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    try:
        entries = get_journal_entries(user_id)
    except Exception:
        return jsonify({"error": "Could not fetch entries. Please try again."}), 500

    return jsonify({"entries": entries}), 200


# ---------------------------------------------------------------------------
# ROUTE: GET /journal/<int:entry_id>
# ---------------------------------------------------------------------------
@journal_bp.route("/<int:entry_id>", methods=["GET"])
def get_entry(entry_id):
    """
    Returns a single journal entry by its ID.
    The entry must belong to the logged-in user.

    URL param:
        entry_id (int): The journal entry's primary key.

    Returns:
        200 OK           : { entry }
        401 Unauthorized : { error }
        404 Not Found    : { error } – entry doesn't exist or belongs to someone else
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    try:
        entry = get_journal_entry_by_id(entry_id, user_id)
    except Exception:
        return jsonify({"error": "Could not fetch the entry. Please try again."}), 500

    if entry is None:
        return jsonify({"error": "Entry not found."}), 404

    return jsonify({"entry": entry}), 200


# ---------------------------------------------------------------------------
# ROUTE: DELETE /journal/<int:entry_id>
# ---------------------------------------------------------------------------
@journal_bp.route("/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    """
    Permanently deletes a journal entry.
    The entry must belong to the logged-in user.

    URL param:
        entry_id (int): The journal entry's primary key.

    Returns:
        200 OK           : { message }
        401 Unauthorized : { error }
        404 Not Found    : { error } – entry doesn't exist or belongs to someone else
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    try:
        deleted = delete_journal_entry(entry_id, user_id)
    except Exception:
        return jsonify({"error": "Could not delete the entry. Please try again."}), 500

    if not deleted:
        return jsonify({"error": "Entry not found."}), 404

    return jsonify({"message": "Entry deleted successfully."}), 200


# ---------------------------------------------------------------------------
# ROUTE: PUT /journal/<int:entry_id>
# ---------------------------------------------------------------------------
@journal_bp.route("/<int:entry_id>", methods=["PUT"])
def update_entry(entry_id):
    """
    Updates an existing journal entry that belongs to the logged-in user.
    You only need to send the fields you want to change – the rest stays as-is.

    URL param:
        entry_id (int): The journal entry's primary key.

    Expected JSON body (all fields optional, but at least one required):
        {
            "title":   "Updated title",
            "content": "Updated content ...",
            "mood_id": 2
        }

    Returns:
        200 OK           : { message, entry }
        400 Bad Request  : { error } – no fields provided, or bad mood_id
        401 Unauthorized : { error } – missing/invalid token
        404 Not Found    : { error } – entry doesn't exist or belongs to someone else
    """
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"error": "Unauthorized. Please log in first."}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Read optional fields – we pass None for anything not in the request
    title   = data.get("title")    # None if key missing
    content = data.get("content")
    mood_id = data.get("mood_id")

    # Strip whitespace from text fields when provided
    if title is not None:
        title = title.strip() or None   # Treat empty string as no change
    if content is not None:
        content = content.strip()
        if not content:
            return jsonify({"error": "content cannot be empty"}), 400

    # Validate mood_id is an integer when provided
    if mood_id is not None:
        try:
            mood_id = int(mood_id)
        except (ValueError, TypeError):
            return jsonify({"error": "mood_id must be a number"}), 400

    # Make sure at least one field was given
    if title is None and content is None and mood_id is None:
        return jsonify({"error": "Provide at least one field to update: title, content, or mood_id"}), 400

    try:
        updated_entry = update_journal_entry(entry_id, user_id, title, content, mood_id)
    except Exception:
        return jsonify({"error": "Could not update the entry. Please try again."}), 500

    if updated_entry is None:
        return jsonify({"error": "Entry not found."}), 404

    return jsonify({
        "message": "Entry updated successfully!",
        "entry":   updated_entry
    }), 200


@journal_bp.route("/moods", methods=["GET"])
def list_moods():
    """
    Returns the list of all available mood options.
    The frontend uses this to populate the mood picker when writing an entry.

    Returns:
        200 OK : { moods: [ { id, label }, ... ] }
    """
    try:
        moods = get_all_moods()
    except Exception:
        return jsonify({"error": "Could not fetch moods."}), 500

    return jsonify({"moods": moods}), 200
