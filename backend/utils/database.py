# database.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS moods (
            id SERIAL PRIMARY KEY,
            label VARCHAR(50) UNIQUE NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            mood_id INTEGER REFERENCES moods(id),
            title VARCHAR(200),
            content TEXT NOT NULL,
            sentiment_score FLOAT,
            sentiment_label VARCHAR(20),
            suggestion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
            mood       VARCHAR(20) NOT NULL,
            tag        VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------------------------
    # AI Pipeline tables – new tables for the agentic AI system.
    # These are purely additive and do NOT touch existing tables.
    # -----------------------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS entry_analyses (
            id             SERIAL PRIMARY KEY,
            journal_id     INTEGER REFERENCES journals(id) ON DELETE CASCADE,
            user_id        INTEGER REFERENCES users(id) ON DELETE CASCADE,
            sentiment      VARCHAR(20),
            primary_emotion VARCHAR(50),
            emotion_intensity FLOAT,
            stress_level   VARCHAR(20),
            keywords       JSONB DEFAULT '[]',
            cognitive_distortions JSONB DEFAULT '[]',
            confidence     FLOAT DEFAULT 0.0,
            risk_level     VARCHAR(20) DEFAULT 'none',
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS memory_patterns (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER REFERENCES users(id) ON DELETE CASCADE,
            patterns         JSONB DEFAULT '{}',
            entries_analyzed INTEGER DEFAULT 0,
            confidence       FLOAT DEFAULT 0.0,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS verification_results (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
            patterns    JSONB DEFAULT '{}',
            confidence  FLOAT DEFAULT 0.0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS disclosure_history (
            id                 SERIAL PRIMARY KEY,
            user_id            INTEGER REFERENCES users(id) ON DELETE CASCADE,
            disclosed_patterns JSONB DEFAULT '{}',
            disclosure_text    TEXT,
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS safety_logs (
            id                       SERIAL PRIMARY KEY,
            user_id                  INTEGER REFERENCES users(id) ON DELETE CASCADE,
            decision                 VARCHAR(20),
            reason                   TEXT,
            memory_confidence        FLOAT,
            verification_confidence  FLOAT,
            agreement_score          FLOAT,
            created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS crisis_events (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER REFERENCES users(id) ON DELETE CASCADE,
            journal_id       INTEGER REFERENCES journals(id) ON DELETE SET NULL,
            severity         VARCHAR(20),
            matched_patterns JSONB DEFAULT '[]',
            response_given   TEXT,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # -----------------------------------------------------------------------
    # Live migrations – safely add columns to existing tables.
    # ADD COLUMN IF NOT EXISTS is supported in PostgreSQL 9.6+.
    # These are no-ops if the columns already exist.
    # -----------------------------------------------------------------------
    migrations = [
        "ALTER TABLE journals ADD COLUMN IF NOT EXISTS sentiment_score FLOAT;",
        "ALTER TABLE journals ADD COLUMN IF NOT EXISTS sentiment_label VARCHAR(20);",
        "ALTER TABLE journals ADD COLUMN IF NOT EXISTS suggestion TEXT;",
        # Study-participant flag – added to scope Journey Report out of the research study.
        # is_study_participant = TRUE means the user is enrolled as a study participant
        # and ungated LLM disclosure features (e.g. Journey Report) are disabled for them.
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_study_participant BOOLEAN DEFAULT FALSE;",
    ]
    for migration_sql in migrations:
        cur.execute(migration_sql)

    cur.execute("""
        INSERT INTO moods (label)
        VALUES ('Happy'), ('Sad'), ('Anxious'), ('Calm'), ('Angry')
        ON CONFLICT (label) DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("[database.py] PostgreSQL database ready.")