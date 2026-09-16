# main.py
# This is the entry point of the MindMate Flask server.
# Running `python main.py` starts the web server.
#
# What this file does:
#   1. Creates the Flask app object
#   2. Sets up CORS so the React frontend can call our API
#   3. Initialises the database (creates tables if they don't exist)
#   4. Registers all route blueprints
#   5. Starts the development server

from dotenv import load_dotenv
load_dotenv()   # Reads .env file and sets all variables as environment variables

from flask import Flask
from flask_cors import CORS
from database import init_db
from routes import register_routes

# ---------------------------------------------------------------------------
# Create the Flask application
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Enable CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------------------------------
# By default, browsers block requests from one origin (e.g. localhost:3000)
# to another (e.g. localhost:5000). CORS headers tell the browser it's okay.
# In production, replace "*" with your actual frontend domain.
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------------------------
# Health-check route
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def health_check():
    """
    Simple endpoint to verify the server is running.
    Visit http://localhost:5000/ in your browser to check.
    """
    return {"message": "MindMate API is up and running! 🧠✨"}, 200

# ---------------------------------------------------------------------------
# Initialise database tables and register routes
# ---------------------------------------------------------------------------
# init_db() creates the users, moods, and journals tables if they don't
# already exist. It also seeds the default mood options.
init_db()

# register_routes() attaches all blueprints (auth, etc.) to the app
register_routes(app)

# ---------------------------------------------------------------------------
# Start the server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True enables:
    #   - Automatic reloading when you save a file (very handy!)
    #   - A detailed error page in the browser
    # NEVER set debug=True in a production deployment.
    print("Starting MindMate Flask server on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
