# models.py
# This file contains helper functions that talk to the database on behalf
# of the rest of the application.
#
# Think of each function here as a "model" – it knows how to create,
# read, update, or delete one type of data (users, journals, moods).
#
# We do NOT use an ORM (like SQLAlchemy) to keep things beginner-friendly.
# All queries are plain SQL strings executed via psycopg2.

from database import get_connection


# ===========================================================================
# USER HELPERS
# ===========================================================================

def create_user(username, email, hashed_password):
    """
    Inserts a new user row into the 'users' table.

    Args:
        username (str)        : Unique username chosen by the user.
        email (str)           : Unique email address.
        hashed_password (str) : The bcrypt hash of the user's password.
                                NEVER pass plain-text passwords here.

    Returns:
        dict: The newly created user's id, username, and email.

    Raises:
        Exception: If the username or email is already taken.
    """
    sql = """
        INSERT INTO users (username, email, password)
        VALUES (%s, %s, %s)
        RETURNING id, username, email;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username, email, hashed_password))
        row = cursor.fetchone()   # Fetch the row returned by RETURNING clause
        conn.commit()
        return {"id": row[0], "username": row[1], "email": row[2]}
    except Exception as error:
        conn.rollback()
        print(f"[models.py] create_user error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_user_by_email(email):
    """
    Looks up a user by their email address.

    Args:
        email (str): The email to search for.

    Returns:
        dict | None: User data (id, username, email, password hash) if found,
                     or None if no matching user exists.
    """
    sql = "SELECT id, username, email, password FROM users WHERE email = %s;"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (email,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {"id": row[0], "username": row[1], "email": row[2], "password": row[3]}
    except Exception as error:
        print(f"[models.py] get_user_by_email error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    """
    Looks up a user by their numeric ID.

    Args:
        user_id (int): The primary key of the user.

    Returns:
        dict | None: User data without the password, or None if not found.
    """
    sql = "SELECT id, username, email FROM users WHERE id = %s;"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return {"id": row[0], "username": row[1], "email": row[2]}
    except Exception as error:
        print(f"[models.py] get_user_by_id error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


# ===========================================================================
# MOOD HELPERS  (mood options lookup)
# ===========================================================================

def get_all_moods():
    """
    Returns every mood option available in the 'moods' table.

    Returns:
        list[dict]: A list of mood objects, each with 'id' and 'label'.
    """
    sql = "SELECT id, label FROM moods ORDER BY id;"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        # Turn each row tuple into a readable dict
        return [{"id": row[0], "label": row[1]} for row in rows]
    except Exception as error:
        print(f"[models.py] get_all_moods error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


# ===========================================================================
# MOOD LOG HELPERS  (standalone mood logging – separate from journals)
# ===========================================================================

def create_mood_log(user_id, mood, tag):
    """
    Inserts a new standalone mood log into the 'mood_logs' table.

    This is completely independent of the journal system.  Users can log
    how they feel at any time, optionally tagging it with a life area.

    Args:
        user_id (int) : The ID of the logged-in user.
        mood    (str) : One of: happy, sad, calm, angry, anxious.
        tag     (str) : One of: work, stress, health, relationships,
                        gratitude, goals.

    Returns:
        dict: The newly created mood log with id, user_id, mood, tag,
              and created_at.
    """
    sql = """
        INSERT INTO mood_logs (user_id, mood, tag)
        VALUES (%s, %s, %s)
        RETURNING id, user_id, mood, tag, created_at;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, mood, tag))
        row = cursor.fetchone()
        conn.commit()
        return {
            "id":         row[0],
            "user_id":    row[1],
            "mood":       row[2],
            "tag":        row[3],
            "created_at": str(row[4]),
        }
    except Exception as error:
        conn.rollback()
        print(f"[models.py] create_mood_log error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_mood_logs_by_user(user_id):
    """
    Returns all standalone mood logs for a user, newest first.

    Args:
        user_id (int): The ID of the logged-in user.

    Returns:
        list[dict]: Each dict has id, mood, tag, and created_at.
    """
    sql = """
        SELECT id, mood, tag, created_at
        FROM   mood_logs
        WHERE  user_id = %s
        ORDER  BY created_at DESC;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        return [
            {
                "id":         row[0],
                "mood":       row[1],
                "tag":        row[2],
                "created_at": str(row[3]),
            }
            for row in rows
        ]
    except Exception as error:
        print(f"[models.py] get_mood_logs_by_user error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


# ===========================================================================
# JOURNAL HELPERS
# ===========================================================================

def create_journal_entry(user_id, title, content, mood_id=None,
                         sentiment_score=None, sentiment_label=None,
                         suggestion=None):
    """
    Inserts a new journal entry for the given user.

    Args:
        user_id          (int)        : The ID of the currently logged-in user.
        title            (str)        : Short title for the entry (optional).
        content          (str)        : The main body / text of the journal entry.
        mood_id          (int|None)   : Optional ID from the 'moods' table.
        sentiment_score  (float|None) : TextBlob polarity score [-1.0, 1.0].
        sentiment_label  (str|None)   : One of 'positive', 'negative', 'neutral'.
        suggestion       (str|None)   : Rule-based wellness suggestion generated
                                        after sentiment analysis.

    Returns:
        dict: The newly created entry with all fields including sentiment & suggestion.
    """
    sql = """
        INSERT INTO journals (user_id, title, content, mood_id,
                              sentiment_score, sentiment_label, suggestion)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, title, content, mood_id, created_at,
                  sentiment_score, sentiment_label, suggestion;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            sql,
            (user_id, title, content, mood_id, sentiment_score, sentiment_label, suggestion)
        )
        row = cursor.fetchone()
        conn.commit()
        return {
            "id":              row[0],
            "user_id":         row[1],
            "title":           row[2],
            "content":         row[3],
            "mood_id":         row[4],
            "created_at":      str(row[5]),
            "sentiment_score": row[6],
            "sentiment_label": row[7],
            "suggestion":      row[8]
        }
    except Exception as error:
        conn.rollback()
        print(f"[models.py] create_journal_entry error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_journal_entries(user_id):
    """
    Returns ALL journal entries for a given user, newest first.

    Args:
        user_id (int): The ID of the logged-in user.

    Returns:
        list[dict]: A list of journal entry dicts ordered by created_at DESC.
    """
    sql = """
        SELECT j.id, j.title, j.content, j.created_at, m.label AS mood
        FROM   journals j
        LEFT JOIN moods m ON m.id = j.mood_id
        WHERE  j.user_id = %s
        ORDER  BY j.created_at DESC;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        return [
            {
                "id":         row[0],
                "title":      row[1],
                "content":    row[2],
                "created_at": str(row[3]),
                "mood":       row[4]    # Human-readable label e.g. "Happy"
            }
            for row in rows
        ]
    except Exception as error:
        print(f"[models.py] get_journal_entries error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def get_journal_entry_by_id(entry_id, user_id):
    """
    Returns a single journal entry, but ONLY if it belongs to user_id.
    This prevents one user from reading another user's private entries.

    Args:
        entry_id (int): Primary key of the journal entry.
        user_id  (int): Must match the entry's owner.

    Returns:
        dict | None: The entry dict, or None if not found / not owned by user.
    """
    sql = """
        SELECT j.id, j.title, j.content, j.created_at, m.label AS mood
        FROM   journals j
        LEFT JOIN moods m ON m.id = j.mood_id
        WHERE  j.id = %s AND j.user_id = %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (entry_id, user_id))
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id":         row[0],
            "title":      row[1],
            "content":    row[2],
            "created_at": str(row[3]),
            "mood":       row[4]
        }
    except Exception as error:
        print(f"[models.py] get_journal_entry_by_id error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def delete_journal_entry(entry_id, user_id):
    """
    Deletes a single journal entry, but ONLY if it belongs to user_id.

    Args:
        entry_id (int): Primary key of the entry to delete.
        user_id  (int): Must match the entry's owner.

    Returns:
        bool: True if a row was deleted, False if nothing matched.
    """
    sql = """
        DELETE FROM journals
        WHERE id = %s AND user_id = %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (entry_id, user_id))
        rows_deleted = cursor.rowcount   # Number of rows actually deleted
        conn.commit()
        return rows_deleted > 0
    except Exception as error:
        conn.rollback()
        print(f"[models.py] delete_journal_entry error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


def update_journal_entry(entry_id, user_id, title=None, content=None, mood_id=None):
    """
    Updates an existing journal entry, but ONLY if it belongs to user_id.

    Only the fields that are provided (not None) will be changed.
    This means you can update just the mood without touching the title/content,
    for example.

    Args:
        entry_id (int)       : Primary key of the entry to update.
        user_id  (int)       : Must match the entry's owner (security check).
        title    (str|None)  : New title, or None to leave it unchanged.
        content  (str|None)  : New content, or None to leave it unchanged.
        mood_id  (int|None)  : New mood ID, or None to leave it unchanged.

    Returns:
        dict | None: The updated entry dict, or None if not found / not owned.
    """
    # Build the SET clause dynamically based on which fields were provided.
    # This avoids accidentally overwriting fields the user didn't touch.
    fields = []    # List of "column = %s" strings
    values = []    # Corresponding values to substitute

    if title is not None:
        fields.append("title = %s")
        values.append(title)

    if content is not None:
        fields.append("content = %s")
        values.append(content)

    if mood_id is not None:
        fields.append("mood_id = %s")
        values.append(mood_id)

    # If no fields were provided there is nothing to update
    if not fields:
        return None

    # Add the WHERE clause values at the end
    values.append(entry_id)
    values.append(user_id)

    sql = f"""
        UPDATE journals
        SET    {', '.join(fields)}
        WHERE  id = %s AND user_id = %s
        RETURNING id, title, content, mood_id, created_at;
    """

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(values))
        row = cursor.fetchone()
        conn.commit()

        if row is None:
            return None   # Entry not found or doesn't belong to this user

        return {
            "id":         row[0],
            "title":      row[1],
            "content":    row[2],
            "mood_id":    row[3],
            "created_at": str(row[4])
        }
    except Exception as error:
        conn.rollback()
        print(f"[models.py] update_journal_entry error: {error}")
        raise
    finally:
        cursor.close()
        conn.close()
