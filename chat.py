# chat.py
# Flask Blueprint for the MindMate mini mental wellness chatbot.
#
# Endpoints:
#   POST /api/chat   → Send a message, receive a supportive reply
#
# No JWT required — the chatbot is an open wellness helper.
# Add @require_token to the route if you want to restrict it to logged-in users.

from flask import Blueprint, request, jsonify
from utils.chat import ChatService      # All logic lives in the service

# ---------------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------------
chat_bp = Blueprint("chat", __name__)


# ---------------------------------------------------------------------------
# ROUTE: POST /api/chat
# ---------------------------------------------------------------------------
@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Accepts a user message and returns a supportive wellness chatbot reply.

    Request body (JSON):
        {
            "message": "I feel so stressed about my exams"
        }

    Success response (200 OK):
        {
            "reply": "Sounds like you're carrying a lot right now. ..."
        }

    Error responses:
        400 Bad Request  – missing or empty message field
        500 Internal     – unexpected server error

    Example cURL:
        curl -X POST http://localhost:5000/api/chat \\
          -H "Content-Type: application/json" \\
          -d '{"message": "I feel so alone today"}'
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "'message' field is required and cannot be empty"}), 400

    try:
        reply = ChatService.get_reply(message)
    except Exception as exc:
        print(f"[chat.py] ChatService error: {exc}")
        return jsonify({"error": "Chatbot encountered an error. Please try again."}), 500

    return jsonify({"reply": reply}), 200
