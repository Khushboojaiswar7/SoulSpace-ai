# auth.py
# This file contains all authentication logic:
#   - /signup : create a new account (hashes password with bcrypt)
#   - /login  : verify credentials and return a JWT token
#
# A JWT (JSON Web Token) is a small, signed piece of data the frontend
# stores and sends back on every request to prove who the user is.

import jwt                          # pip install PyJWT
import bcrypt                       # pip install bcrypt
import os
import datetime

from flask import Blueprint, request, jsonify
from models import create_user, get_user_by_email

# ---------------------------------------------------------------------------
# Blueprint setup
# ---------------------------------------------------------------------------
# A Blueprint is Flask's way of splitting routes across multiple files.
# We register this blueprint in routes.py and then in main.py.
auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------------
# Secret key used to sign JWT tokens.
# Keep this value PRIVATE – store it in an environment variable in production.
# ---------------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "mysecretkey_change_in_production")

# How long a token stays valid before the user must log in again
JWT_EXPIRY_HOURS = 24


# ---------------------------------------------------------------------------
# HELPER: generate_token
# ---------------------------------------------------------------------------
def generate_token(user_id, username):
    """
    Creates a signed JWT token for the given user.

    The token payload contains:
        - sub      : subject (the user's database ID)
        - username : so the frontend doesn't need an extra API call
        - exp      : expiry time (24 hours from now)

    Args:
        user_id  (int) : The user's primary key from the database.
        username (str) : The user's chosen username.

    Returns:
        str: A signed JWT string that the frontend can store and send back.
    """
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    }
    # jwt.encode() signs the payload using our secret key
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


# ---------------------------------------------------------------------------
# HELPER: decode_token
# ---------------------------------------------------------------------------
def decode_token(token):
    """
    Verifies and decodes a JWT token.

    Used by protected routes to confirm the request comes from a real,
    logged-in user.

    Args:
        token (str): The JWT string (usually from the Authorization header).

    Returns:
        dict: The decoded payload (sub, username, exp) if the token is valid.

    Raises:
        jwt.ExpiredSignatureError : If the token has passed its expiry time.
        jwt.InvalidTokenError     : If the token is tampered or malformed.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


# ---------------------------------------------------------------------------
# ROUTE: POST /signup
# ---------------------------------------------------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Registers a brand-new user account.

    Expected JSON body:
        {
            "username": "alice",
            "email":    "alice@example.com",
            "password": "secret123"
        }

    Steps:
        1. Validate that all three fields are present.
        2. Hash the plain-text password with bcrypt.
        3. Save the new user to the database.
        4. Return a JWT token so the user is immediately logged in.

    Returns:
        201 Created  : { message, token, user }
        400 Bad Request: { error } – missing fields or duplicate email/username
    """
    data = request.get_json()   # Parse the JSON body sent by the frontend

    # --- Step 1: Validate input ---
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    username = data.get("username", "").strip()
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    # --- Step 2: Hash the password ---
    # bcrypt.hashpw expects bytes, so we encode the string first.
    # gensalt() adds a random "salt" so two identical passwords produce
    # different hashes – this protects against rainbow table attacks.
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    # Decode bytes → string so it can be stored in the TEXT column
    hashed_password_str = hashed_password.decode("utf-8")

    # --- Step 3: Save to database ---
    try:
        new_user = create_user(username, email, hashed_password_str)
    except Exception as e:
        error_message = str(e)
        # psycopg2 raises an IntegrityError when a UNIQUE constraint fails
        if "unique" in error_message.lower() or "duplicate" in error_message.lower():
            return jsonify({"error": "Email or username is already taken"}), 400
        return jsonify({"error": "Could not create account. Please try again."}), 500

    # --- Step 4: Generate and return a token ---
    token = generate_token(new_user["id"], new_user["username"])

    return jsonify({
        "message": "Account created successfully!",
        "token": token,
        "user": {
            "id":       new_user["id"],
            "username": new_user["username"],
            "email":    new_user["email"]
        }
    }), 201


# ---------------------------------------------------------------------------
# ROUTE: POST /login
# ---------------------------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Logs in an existing user.

    Expected JSON body:
        {
            "email":    "alice@example.com",
            "password": "secret123"
        }

    Steps:
        1. Validate that both fields are present.
        2. Look up the user by email.
        3. Compare the provided password with the stored bcrypt hash.
        4. Return a JWT token if credentials are correct.

    Returns:
        200 OK       : { message, token, user }
        400 Bad Request: { error } – missing fields
        401 Unauthorized: { error } – wrong email or password
    """
    data = request.get_json()

    # --- Step 1: Validate input ---
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    # --- Step 2: Find the user in the database ---
    user = get_user_by_email(email)
    if user is None:
        # Use a vague message so attackers can't enumerate valid emails
        return jsonify({"error": "Invalid email or password"}), 401

    # --- Step 3: Verify the password ---
    # bcrypt.checkpw rehashes the provided password and compares it
    # to the stored hash. Returns True only if they match.
    password_matches = bcrypt.checkpw(
        password.encode("utf-8"),
        user["password"].encode("utf-8")
    )

    if not password_matches:
        return jsonify({"error": "Invalid email or password"}), 401

    # --- Step 4: Issue a JWT ---
    token = generate_token(user["id"], user["username"])

    return jsonify({
        "message": f"Welcome back, {user['username']}!",
        "token": token,
        "user": {
            "id":       user["id"],
            "username": user["username"],
            "email":    user["email"]
        }
    }), 200
