# agents/crisis_detector.py
# Crisis Detection module — runs BEFORE all other agents.
#
# Detects severe self-harm or suicide language in journal entries.
# If crisis is detected, the pipeline bypasses all reasoning agents
# and returns supportive crisis resources instead.
#
# Usage:
#   from agents.crisis_detector import detect_crisis
#   result = detect_crisis("I feel so hopeless...")
#   if result["is_crisis"]:
#       return result["resources"]

import json
from database import get_connection


# ---------------------------------------------------------------------------
# Crisis keyword/phrase patterns, organized by severity
# ---------------------------------------------------------------------------
CRISIS_PATTERNS = {
    "severe": [
        "kill myself", "want to die", "end my life", "suicide",
        "suicidal", "don't want to live", "no reason to live",
        "better off dead", "can't go on", "end it all",
        "take my own life", "not worth living",
        "want to disappear forever", "planning to end",
        "goodbye forever", "final goodbye", "last note"
    ],
    "moderate": [
        "self harm", "self-harm", "cutting myself", "hurt myself",
        "harming myself", "punish myself", "starving myself",
        "don't want to be here", "nobody cares", "hopeless",
        "nothing matters", "can't take it anymore", "give up",
        "no point in living", "wish i wasn't here",
        "wish i was dead", "rather be dead", "want to hurt myself"
    ],
    "low": [
        "feeling worthless", "feel worthless", "hate myself",
        "i'm a burden", "i am a burden", "everyone hates me",
        "no one understands", "so alone", "completely alone",
        "lost all hope", "no hope left", "can't do this anymore",
        "everything is my fault", "world without me",
        "i'm nothing", "i am nothing"
    ]
}


# ---------------------------------------------------------------------------
# Crisis resources — returned when crisis is detected
# ---------------------------------------------------------------------------
CRISIS_RESOURCES = {
    "message": (
        "I can see you're going through an incredibly difficult time. "
        "Your feelings are valid, and you don't have to face this alone. "
        "Please reach out to a professional who can help."
    ),
    "resources": [
        {
            "name": "988 Suicide & Crisis Lifeline (US)",
            "contact": "Call or text 988",
            "available": "24/7"
        },
        {
            "name": "Crisis Text Line (US)",
            "contact": "Text HOME to 741741",
            "available": "24/7"
        },
        {
            "name": "iCall (India)",
            "contact": "9152987821",
            "available": "Mon-Sat, 8am-10pm"
        },
        {
            "name": "Vandrevala Foundation (India)",
            "contact": "1860-2662-345",
            "available": "24/7"
        },
        {
            "name": "AASRA (India)",
            "contact": "91-22-27546669",
            "available": "24/7"
        }
    ],
    "safety_message": (
        "Remember: This is a moment, not your whole story. "
        "You are worthy of support and care."
    )
}

# Severity ranking for comparison
_SEVERITY_RANK = {"none": 0, "low": 1, "moderate": 2, "severe": 3}


# ---------------------------------------------------------------------------
# Main detection function
# ---------------------------------------------------------------------------
def detect_crisis(text: str) -> dict:
    """
    Scans journal text for crisis-related language.

    The detector checks for keyword/phrase matches across three severity
    tiers (severe, moderate, low). It returns the HIGHEST severity found.

    Args:
        text (str): The raw journal entry text.

    Returns:
        dict: {
            "is_crisis": bool,
            "severity": "none" | "low" | "moderate" | "severe",
            "matched_patterns": list[str],
            "resources": dict | None
        }
    """
    if not text or not text.strip():
        return {
            "is_crisis": False,
            "severity": "none",
            "matched_patterns": [],
            "resources": None
        }

    text_lower = text.lower()
    matched_patterns = []
    highest_severity = "none"

    # Check each severity tier
    for severity, patterns in CRISIS_PATTERNS.items():
        for pattern in patterns:
            if pattern in text_lower:
                matched_patterns.append(pattern)
                # Keep track of highest severity found
                if _SEVERITY_RANK[severity] > _SEVERITY_RANK[highest_severity]:
                    highest_severity = severity

    is_crisis = highest_severity != "none"

    return {
        "is_crisis": is_crisis,
        "severity": highest_severity,
        "matched_patterns": matched_patterns,
        "resources": CRISIS_RESOURCES if is_crisis else None
    }


# ---------------------------------------------------------------------------
# Database storage helper
# ---------------------------------------------------------------------------
def store_crisis_event(user_id: int, journal_id: int, severity: str,
                       matched_patterns: list, response_text: str):
    """
    Stores a crisis detection event in the crisis_events table.

    Args:
        user_id (int): The user's database ID.
        journal_id (int): The journal entry's database ID.
        severity (str): One of 'low', 'moderate', 'severe'.
        matched_patterns (list): The phrases that matched.
        response_text (str): The crisis message shown to the user.
    """
    sql = """
        INSERT INTO crisis_events (user_id, journal_id, severity,
                                    matched_patterns, response_given)
        VALUES (%s, %s, %s, %s, %s);
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            user_id,
            journal_id,
            severity,
            json.dumps(matched_patterns),
            response_text
        ))
        conn.commit()
    except Exception as error:
        conn.rollback()
        print(f"[crisis_detector] store_crisis_event error: {error}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Quick tests
    test_cases = [
        "I had a great day at work today!",
        "I feel so alone and hopeless",
        "I want to end my life, nothing matters anymore",
        "Feeling a bit stressed about exams",
    ]
    for text in test_cases:
        result = detect_crisis(text)
        status = f"⚠️ CRISIS ({result['severity']})" if result["is_crisis"] else "✅ Safe"
        print(f"{status}: \"{text[:50]}...\"")
        if result["matched_patterns"]:
            print(f"   Matched: {result['matched_patterns']}")
        print()
