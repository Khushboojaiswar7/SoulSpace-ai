# agents/verification_agent.py
# Verification Agent — independently derives emotional patterns from RAW
# journal text, without seeing the Memory Agent's output.
#
# This ensures multi-agent agreement before patterns are disclosed.
# The Safety Gate compares this agent's output with the Memory Agent's
# to confirm patterns are real (not hallucinated by a single LLM call).
#
# Usage:
#   from agents.verification_agent import verify_patterns
#   result = verify_patterns(user_id=1)

import json
import traceback
from collections import Counter

from database import get_connection
from agents.llm_provider import get_llm_provider, parse_json_response


# ---------------------------------------------------------------------------
# Emotion keywords for fallback analysis
# ---------------------------------------------------------------------------
_EMOTION_WORDS = {
    "anxiety":     {"anxious", "worried", "nervous", "panic", "scared", "fear", "dread", "uneasy", "restless"},
    "sadness":     {"sad", "unhappy", "depressed", "miserable", "heartbroken", "crying", "tears", "grief", "lonely"},
    "anger":       {"angry", "furious", "mad", "frustrated", "annoyed", "irritated", "rage", "resentful"},
    "joy":         {"happy", "joy", "excited", "amazing", "wonderful", "great", "fantastic", "love", "grateful"},
    "frustration": {"frustrated", "stuck", "overwhelmed", "exhausted", "tired", "burnout", "stressed", "drained"},
    "calm":        {"calm", "peaceful", "relaxed", "serene", "content", "tranquil", "balanced", "mindful"},
    "hope":        {"hope", "hopeful", "optimistic", "forward", "bright", "positive", "better", "improving"},
    "loneliness":  {"alone", "lonely", "isolated", "nobody", "abandoned", "disconnected"},
    "gratitude":   {"thankful", "grateful", "appreciate", "blessed", "fortunate"},
}


# ---------------------------------------------------------------------------
# Database helper — fetch RAW journal entries (NOT analyses)
# ---------------------------------------------------------------------------
def get_recent_raw_entries(user_id: int, limit: int = 10) -> list:
    """
    Retrieves the most recent raw journal entries for a user.
    CRITICAL: This queries the journals table directly, NOT entry_analyses.

    Args:
        user_id (int): The user's database ID.
        limit (int): Maximum number of entries to retrieve.

    Returns:
        list[dict]: Each dict has id, content, and created_at.
    """
    sql = """
        SELECT id, content, created_at
        FROM   journals
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, limit))
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "content": row[1],
                "created_at": str(row[2])
            }
            for row in rows
        ]
    except Exception as error:
        print(f"[verification_agent] get_recent_raw_entries error: {error}")
        return []
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# Main verification function
# ---------------------------------------------------------------------------
def verify_patterns(user_id: int) -> dict:
    """
    Independently analyzes raw journal texts to derive emotional patterns.

    IMPORTANT: This agent receives ONLY raw journal entries — it does NOT
    see the Memory Agent's output. This ensures independent verification.

    Args:
        user_id (int): The user's database ID.

    Returns:
        dict: Independent pattern analysis:
            recurring_emotions, emotional_trend, key_themes,
            stressors, positive_signals, entries_analyzed, confidence
    """
    entries = get_recent_raw_entries(user_id, limit=10)

    if len(entries) < 3:
        return {
            "insufficient_data": True,
            "entries_analyzed": len(entries),
            "confidence": 0.0,
            "message": "Need at least 3 entries for independent verification."
        }

    # Build prompt with raw entries
    entries_text = []
    for i, entry in enumerate(entries):
        # Truncate very long entries for the prompt
        content = entry["content"][:500]
        entries_text.append(
            f"Entry {i+1} ({entry['created_at']}):\n\"{content}\""
        )

    all_entries = "\n\n".join(entries_text)

    prompt = f"""You are an independent emotional pattern analyzer. Read these {len(entries)} journal entries from a single user and identify emotional patterns.

IMPORTANT: This is an independent analysis. Do NOT rely on any external analysis — derive everything from the raw text below.

JOURNAL ENTRIES:
{all_entries}

Respond with ONLY a valid JSON object (no markdown, no explanation) containing:
{{
    "recurring_emotions": [
        {{"emotion": "emotion_name", "frequency": how_many_entries_show_this}}
    ],
    "emotional_trend": "improving" or "stable" or "declining",
    "key_themes": ["list of recurring themes or topics across entries"],
    "stressors": ["list of recurring sources of stress"],
    "positive_signals": ["list of positive elements or coping strategies noticed"],
    "confidence": float between 0.0 and 1.0
}}"""

    try:
        provider = get_llm_provider()
        raw_response = provider.generate(prompt)

        if raw_response:
            result = parse_json_response(raw_response)
            if result:
                result["entries_analyzed"] = len(entries)
                result.setdefault("recurring_emotions", [])
                result.setdefault("emotional_trend", "stable")
                result.setdefault("key_themes", [])
                result.setdefault("stressors", [])
                result.setdefault("positive_signals", [])
                result.setdefault("confidence", 0.5)
                return result

        # LLM failed — use word-frequency fallback
        print("[verification_agent] LLM response empty, using fallback")
        return _word_frequency_fallback(entries)

    except Exception as e:
        print(f"[verification_agent] LLM error, using fallback: {e}")
        traceback.print_exc()
        return _word_frequency_fallback(entries)


# ---------------------------------------------------------------------------
# Word-frequency fallback (no LLM)
# ---------------------------------------------------------------------------
def _word_frequency_fallback(entries: list) -> dict:
    """
    Basic emotion detection using word frequency analysis.
    Used when the LLM is unavailable.
    """
    all_words = []
    emotion_counter = Counter()

    for entry in entries:
        content = entry.get("content", "")
        words = set(content.lower().split())
        all_words.extend(content.lower().split())

        for emotion, keywords in _EMOTION_WORDS.items():
            matches = words & keywords
            if matches:
                emotion_counter[emotion] += 1

    # Build recurring emotions
    recurring_emotions = [
        {"emotion": emotion, "frequency": count}
        for emotion, count in emotion_counter.most_common(5)
        if count >= 2
    ]

    # Word frequency for themes
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words("english"))
    except Exception:
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "me",
                      "my", "and", "or", "but", "in", "on", "at", "to", "for"}

    content_words = [w for w in all_words if w.isalpha()
                     and len(w) > 3 and w not in stop_words]
    word_freq = Counter(content_words)
    key_themes = [w for w, c in word_freq.most_common(7) if c >= 2]

    # Stress words
    stress_words = {"stress", "stressed", "overwhelmed", "pressure", "deadline",
                    "burnout", "exhausted", "tired", "anxious", "worried"}
    stressors = [w for w in key_themes if w in stress_words]

    # Positive words
    positive_words = {"happy", "grateful", "better", "improving", "hope",
                      "love", "calm", "peaceful", "excited", "progress"}
    positive_signals = [w for w, c in word_freq.most_common(20)
                        if w in positive_words and c >= 1]

    return {
        "recurring_emotions": recurring_emotions,
        "emotional_trend": "stable",
        "key_themes": key_themes,
        "stressors": stressors,
        "positive_signals": positive_signals,
        "entries_analyzed": len(entries),
        "confidence": 0.35
    }


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------
def store_verification_result(user_id: int, result: dict):
    """
    Stores the verification result in the verification_results table.

    Args:
        user_id (int): The user's database ID.
        result (dict): The verification analysis.
    """
    sql = """
        INSERT INTO verification_results (user_id, patterns, confidence)
        VALUES (%s, %s, %s);
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            user_id,
            json.dumps(result, default=str),
            result.get("confidence", 0.0)
        ))
        conn.commit()
    except Exception as error:
        conn.rollback()
        print(f"[verification_agent] store_verification_result error: {error}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("VERIFICATION AGENT TEST")
    print("=" * 60)
    print("Note: Requires existing journal entries in the database.")
    print("Run with a valid user_id that has journal entries.")
