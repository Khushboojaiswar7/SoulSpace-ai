# routes.py
# This file is the central place where we register all of our Blueprints
# (groups of related routes) onto the Flask application.
#
# Currently registered blueprints:
#   auth_bp  → /signup, /login
#
# In Phase 2 we will add:
#   journal_bp → /journal  (CRUD for journal entries)
#
# In Phase 3 we will add:
#   analytics_bp → /analytics (mood trends, summaries)

from auth import auth_bp
from journal import journal_bp
from analytics import analytics_bp
from chat import chat_bp
from mood import mood_bp  # ← Standalone mood logging (Part 1)
from insights import insights_bp  # ← AI pipeline insights (Upgrade)


def register_routes(app):
    """
    Attaches all route blueprints to the Flask app instance.

    Args:
        app (Flask): The Flask application object created in main.py.
    """
    # Auth routes: /auth/signup, /auth/login
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Journal routes: /journal/, /journal/<id>, /journal/moods
    app.register_blueprint(journal_bp, url_prefix="/journal")

    # Analytics routes: /analytics/mood-trends, /analytics/summary, /analytics/streak
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    # Chatbot routes: POST /api/chat
    app.register_blueprint(chat_bp, url_prefix="/api")

    # Mood log routes: POST /api/mood  (standalone – separate from journal)
    app.register_blueprint(mood_bp, url_prefix="/api")

    # AI insights routes: /insights/timeline, /insights/patterns, etc.
    app.register_blueprint(insights_bp, url_prefix="/insights")

    print("[routes.py] All blueprints registered successfully.")
