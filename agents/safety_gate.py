# agents/safety_gate.py
# Safety Gate — only allows pattern disclosure when evidence is sufficient.
#
# This module ensures that emotional patterns are not disclosed to the user
# unless there is enough repeated evidence, sufficient confidence, and
# agreement between the Memory Agent and Verification Agent.
#
# Usage:
#   from agents.safety_gate import evaluate, store_safety_log
#   result = evaluate(memory_patterns, verification_result)
#   if result["disclosure_allowed"]:
#       # Safe to show patterns to user

import json
from database import get_connection


# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------
MIN_ENTRIES_THRESHOLD = 5       # Need at least 5 analyzed entries
MIN_CONFIDENCE_THRESHOLD = 0.6  # Combined confidence must exceed this
MIN_AGREEMENT_THRESHOLD = 0.5   # Agent agreement score must exceed this


# ---------------------------------------------------------------------------
# Main evaluation function
# ---------------------------------------------------------------------------
def evaluate(memory_patterns: dict, verification_result: dict) -> dict:
    """
    Evaluates whether emotional patterns should be disclosed to the user.

    Three checks must ALL pass for disclosure to be approved:
      1. Enough entries analyzed (>= MIN_ENTRIES_THRESHOLD)
      2. Combined confidence exceeds threshold
      3. Memory Agent and Verification Agent sufficiently agree

    Args:
        memory_patterns (dict): Output from the Memory Agent.
        verification_result (dict): Output from the Verification Agent.

    Returns:
        dict: {
            "disclosure_allowed": bool,
            "approved_patterns": dict (subset that passed),
            "rejected_patterns": list[str] (reasons for rejection),
            "agreement_score": float,
            "combined_confidence": float,
            "entries_analyzed": int,
            "reason": str
        }
    """
    rejected_reasons = []

    # --- Check for insufficient data ---
    if memory_patterns.get("insufficient_data") or verification_result.get("insufficient_data"):
        mem_count = memory_patterns.get("entries_analyzed", 0)
        ver_count = verification_result.get("entries_analyzed", 0)
        return {
            "disclosure_allowed": False,
            "approved_patterns": {},
            "rejected_patterns": ["Insufficient data from one or both agents"],
            "agreement_score": 0.0,
            "combined_confidence": 0.0,
            "entries_analyzed": max(mem_count, ver_count),
            "reason": f"Need at least {MIN_ENTRIES_THRESHOLD} entries. "
                      f"Memory Agent has {mem_count}, Verification has {ver_count}."
        }

    # --- Check 1: Minimum entries ---
    entries_analyzed = memory_patterns.get("entries_analyzed", 0)
    if entries_analyzed < MIN_ENTRIES_THRESHOLD:
        rejected_reasons.append(
            f"Only {entries_analyzed} entries analyzed "
            f"(minimum: {MIN_ENTRIES_THRESHOLD})"
        )

    # --- Check 2: Combined confidence ---
    memory_confidence = float(memory_patterns.get("confidence", 0.0))
    verification_confidence = float(verification_result.get("confidence", 0.0))
    combined_confidence = (memory_confidence + verification_confidence) / 2

    if combined_confidence < MIN_CONFIDENCE_THRESHOLD:
        rejected_reasons.append(
            f"Combined confidence {combined_confidence:.2f} below "
            f"threshold {MIN_CONFIDENCE_THRESHOLD}"
        )

    # --- Check 3: Agreement score ---
    agreement_score = _calculate_agreement(memory_patterns, verification_result)

    if agreement_score < MIN_AGREEMENT_THRESHOLD:
        rejected_reasons.append(
            f"Agent agreement score {agreement_score:.2f} below "
            f"threshold {MIN_AGREEMENT_THRESHOLD}"
        )

    # --- Final decision ---
    disclosure_allowed = len(rejected_reasons) == 0

    # Build approved patterns (only include patterns from memory that match)
    if disclosure_allowed:
        approved_patterns = _build_approved_patterns(
            memory_patterns, verification_result
        )
    else:
        approved_patterns = {}

    reason = (
        "All checks passed: sufficient evidence with agent agreement."
        if disclosure_allowed
        else "Disclosure blocked: " + "; ".join(rejected_reasons)
    )

    return {
        "disclosure_allowed": disclosure_allowed,
        "approved_patterns": approved_patterns,
        "rejected_patterns": rejected_reasons,
        "agreement_score": round(agreement_score, 3),
        "combined_confidence": round(combined_confidence, 3),
        "entries_analyzed": entries_analyzed,
        "reason": reason
    }


# ---------------------------------------------------------------------------
# Agreement calculation
# ---------------------------------------------------------------------------
def _calculate_agreement(memory_patterns: dict, verification_result: dict) -> float:
    """
    Calculates an agreement score between the Memory Agent and
    Verification Agent based on overlapping emotions.

    Compares the recurring emotions detected by both agents using
    case-insensitive matching.

    Returns:
        float: Agreement score between 0.0 (no overlap) and 1.0 (full match).
    """
    # Extract emotion names from both agents
    memory_emotions = set()
    for e in memory_patterns.get("recurring_emotions", []):
        if isinstance(e, dict):
            memory_emotions.add(str(e.get("emotion", "")).lower().strip())
        elif isinstance(e, str):
            memory_emotions.add(e.lower().strip())

    verification_emotions = set()
    for e in verification_result.get("recurring_emotions", []):
        if isinstance(e, dict):
            verification_emotions.add(str(e.get("emotion", "")).lower().strip())
        elif isinstance(e, str):
            verification_emotions.add(e.lower().strip())

    # Remove empty strings
    memory_emotions.discard("")
    verification_emotions.discard("")

    if not memory_emotions and not verification_emotions:
        return 0.0

    # Calculate Jaccard-like overlap
    overlap = memory_emotions & verification_emotions
    union = memory_emotions | verification_emotions

    if not union:
        return 0.0

    # Also check emotional trend agreement for bonus score
    memory_trend = memory_patterns.get("emotional_trends", {})
    if isinstance(memory_trend, dict):
        memory_trend_dir = memory_trend.get("overall", "stable").lower()
    else:
        memory_trend_dir = "stable"

    verification_trend = str(
        verification_result.get("emotional_trend", "stable")
    ).lower()

    trend_bonus = 0.15 if memory_trend_dir == verification_trend else 0.0

    base_score = len(overlap) / len(union)
    return min(1.0, base_score + trend_bonus)


# ---------------------------------------------------------------------------
# Build approved patterns
# ---------------------------------------------------------------------------
def _build_approved_patterns(memory_patterns: dict,
                              verification_result: dict) -> dict:
    """
    Builds the approved patterns dict by filtering Memory Agent patterns
    to only include emotions that the Verification Agent also found.
    Non-emotion patterns (stressors, trends, etc.) are included as-is
    since they provide context.
    """
    # Get verification emotions for filtering
    verification_emotions = set()
    for e in verification_result.get("recurring_emotions", []):
        if isinstance(e, dict):
            verification_emotions.add(str(e.get("emotion", "")).lower().strip())
        elif isinstance(e, str):
            verification_emotions.add(e.lower().strip())

    # Filter recurring emotions to only those verified
    approved_emotions = []
    for e in memory_patterns.get("recurring_emotions", []):
        if isinstance(e, dict):
            emotion_name = str(e.get("emotion", "")).lower().strip()
            if emotion_name in verification_emotions:
                approved_emotions.append(e)

    return {
        "recurring_emotions": approved_emotions,
        "recurring_stressors": memory_patterns.get("recurring_stressors", []),
        "emotional_trends": memory_patterns.get("emotional_trends", {}),
        "positive_improvements": memory_patterns.get("positive_improvements", []),
        "negative_changes": memory_patterns.get("negative_changes", [])
    }


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------
def store_safety_log(user_id: int, decision: str, reason: str,
                     memory_confidence: float, verification_confidence: float,
                     agreement_score: float):
    """
    Stores a safety gate decision in the safety_logs table.

    Args:
        user_id (int): The user's database ID.
        decision (str): "approved" or "rejected".
        reason (str): Human-readable explanation of the decision.
        memory_confidence (float): Memory Agent's confidence score.
        verification_confidence (float): Verification Agent's confidence.
        agreement_score (float): Agreement between the two agents.
    """
    sql = """
        INSERT INTO safety_logs (user_id, decision, reason,
                                  memory_confidence, verification_confidence,
                                  agreement_score)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            user_id, decision, reason,
            memory_confidence, verification_confidence, agreement_score
        ))
        conn.commit()
    except Exception as error:
        conn.rollback()
        print(f"[safety_gate] store_safety_log error: {error}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Quick test with mock data
    mock_memory = {
        "recurring_emotions": [
            {"emotion": "anxiety", "frequency": 5, "trend": "increasing"},
            {"emotion": "frustration", "frequency": 3, "trend": "stable"},
        ],
        "recurring_stressors": ["work deadlines", "sleep issues"],
        "emotional_trends": {"overall": "declining", "description": "Increasing stress"},
        "positive_improvements": ["exercise mentions increasing"],
        "negative_changes": ["sleep quality declining"],
        "entries_analyzed": 8,
        "confidence": 0.75
    }
    mock_verification = {
        "recurring_emotions": [
            {"emotion": "anxiety", "frequency": 4},
            {"emotion": "sadness", "frequency": 2},
        ],
        "emotional_trend": "declining",
        "key_themes": ["work", "sleep", "stress"],
        "stressors": ["deadlines"],
        "positive_signals": ["exercise"],
        "entries_analyzed": 8,
        "confidence": 0.70
    }

    result = evaluate(mock_memory, mock_verification)
    import json
    print(json.dumps(result, indent=2))
