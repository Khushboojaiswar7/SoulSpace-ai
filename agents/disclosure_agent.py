"""
Disclosure Agent — Converts validated patterns into supportive, non-clinical language.

This agent is the final step in the pattern-disclosure pipeline. It takes ONLY
patterns that have been approved by the Safety Gate and transforms them into
warm, encouraging reflections the user can read. It never diagnoses, never
uses clinical labels, and always uses uncertain language.
"""

import json
from agents.llm_provider import get_llm_provider, parse_json_response
from database import get_connection


# ---------------------------------------------------------------------------
# Template-based fallback responses
# ---------------------------------------------------------------------------
_NEGATIVE_EMOTION_TEMPLATE = (
    "It seems like {emotion} has been coming up frequently in your reflections. "
    "It's completely normal to feel this way sometimes. Consider taking a moment "
    "to explore what might be contributing to this feeling."
)

_STRESSOR_TEMPLATE = (
    "You've been mentioning {stressor} quite a bit. It might help to break this "
    "down into smaller, manageable steps."
)

_POSITIVE_TEMPLATE = (
    "There's something really encouraging here — {improvement}. "
    "Keep nurturing what's working for you!"
)

_GENERIC_ENCOURAGEMENT = (
    "Thank you for continuing to journal. Every entry is a step toward "
    "understanding yourself better. Keep going — you're doing great."
)

_GENERIC_SELF_CARE = (
    "Try setting aside 5–10 minutes today for something that brings you "
    "calm — a walk, deep breathing, or simply sitting quietly with a warm drink."
)

# Emotions generally considered negative for template selection
_NEGATIVE_EMOTIONS = {
    "sadness", "anxiety", "anger", "guilt", "fatigue", "confusion",
    "fear", "frustration", "loneliness", "stress", "overwhelm",
    "grief", "shame", "resentment", "hopelessness",
}


def _build_fallback_disclosure(approved_patterns: dict) -> dict:
    """
    Generate template-based disclosure when the LLM is unavailable.

    Uses simple string templates to produce supportive reflections for each
    category of approved patterns.

    Args:
        approved_patterns: The Safety-Gate-approved pattern dict.

    Returns:
        A disclosure result dict with reflections and encouragement.
    """
    pattern_reflections = []

    # Recurring emotions
    for item in approved_patterns.get("recurring_emotions", []):
        emotion = item.get("emotion", "") if isinstance(item, dict) else str(item)
        if emotion.lower() in _NEGATIVE_EMOTIONS:
            pattern_reflections.append({
                "pattern": f"Recurring feeling of {emotion}",
                "reflection": _NEGATIVE_EMOTION_TEMPLATE.format(emotion=emotion),
            })
        else:
            pattern_reflections.append({
                "pattern": f"Recurring feeling of {emotion}",
                "reflection": (
                    f"It looks like {emotion} has been present in your recent reflections. "
                    f"It can be helpful to notice and appreciate these moments."
                ),
            })

    # Stressors
    for stressor in approved_patterns.get("recurring_stressors", []):
        pattern_reflections.append({
            "pattern": f"Recurring stressor: {stressor}",
            "reflection": _STRESSOR_TEMPLATE.format(stressor=stressor),
        })

    # Positive improvements
    for improvement in approved_patterns.get("positive_improvements", []):
        pattern_reflections.append({
            "pattern": f"Positive signal: {improvement}",
            "reflection": _POSITIVE_TEMPLATE.format(improvement=improvement),
        })

    # Negative changes
    for change in approved_patterns.get("negative_changes", []):
        pattern_reflections.append({
            "pattern": f"Recent change: {change}",
            "reflection": (
                f"It seems like {change} has been on your mind recently. "
                f"Acknowledging changes is an important first step."
            ),
        })

    # Overall reflection from trend
    trends = approved_patterns.get("emotional_trends", {})
    direction = trends.get("direction", "") if isinstance(trends, dict) else ""

    if direction == "improving":
        overall = (
            "Looking at your recent entries, it appears your emotional well-being "
            "may be heading in a positive direction. That's a wonderful sign — "
            "keep paying attention to what's been helping you."
        )
    elif direction == "declining":
        overall = (
            "Your recent entries suggest you might be going through a tougher "
            "stretch. It's okay to not feel okay. Consider reaching out to "
            "someone you trust or trying a small act of self-care today."
        )
    else:
        overall = (
            "Your reflections show a range of experiences and emotions. "
            "Journaling itself is a meaningful practice — you're building "
            "self-awareness with every entry."
        )

    return {
        "overall_reflection": overall,
        "pattern_reflections": pattern_reflections,
        "encouragement": _GENERIC_ENCOURAGEMENT,
        "self_care_suggestion": _GENERIC_SELF_CARE,
    }


def generate_disclosure(approved_patterns: dict, user_id: int = None) -> dict:
    """
    Convert Safety-Gate-approved patterns into supportive, non-clinical language.

    This is the core function of the Disclosure Agent. It:
    1. Returns generic encouragement if no patterns were approved.
    2. Sends approved patterns to the LLM with strict non-clinical rules.
    3. Falls back to template-based responses if the LLM fails.
    4. Stores the disclosure in the disclosure_history table.

    Args:
        approved_patterns: The approved pattern dict from the Safety Gate.
        user_id: Optional user ID for persistence.

    Returns:
        A dict with overall_reflection, pattern_reflections, encouragement,
        and self_care_suggestion.
    """
    # ---- Empty / no patterns guard ----
    if not approved_patterns or _is_empty_patterns(approved_patterns):
        result = {
            "overall_reflection": (
                "Thanks for checking in! Keep journaling regularly — "
                "over time, your entries will help paint a clearer picture "
                "of your emotional journey."
            ),
            "pattern_reflections": [],
            "encouragement": _GENERIC_ENCOURAGEMENT,
            "self_care_suggestion": _GENERIC_SELF_CARE,
        }
        if user_id:
            store_disclosure(user_id, {}, result["overall_reflection"])
        return result

    # ---- Build LLM prompt ----
    patterns_json = json.dumps(approved_patterns, indent=2)

    prompt = f"""You are a supportive mental wellness companion. Based on the following emotional patterns detected from a user's journal entries, generate a kind, supportive reflection.

STRICT RULES:
- NEVER diagnose any mental health condition
- NEVER use clinical labels (depression, anxiety disorder, PTSD, etc.)
- ALWAYS use uncertain language ("It seems like...", "You might be experiencing...", "It appears that...")
- Use encouraging, warm language
- Keep each reflection to 2-3 sentences maximum
- NEVER claim certainty about the user's mental state
- Focus on observations, not conclusions
- Suggest gentle self-care actions when appropriate

Detected Patterns:
{patterns_json}

Respond with valid JSON only — no markdown, no commentary:
{{
    "overall_reflection": "A 2-3 sentence overall supportive reflection",
    "pattern_reflections": [
        {{"pattern": "what was observed", "reflection": "supportive message about it"}}
    ],
    "encouragement": "A short encouraging closing message",
    "self_care_suggestion": "One actionable self-care suggestion"
}}"""

    # ---- Call LLM ----
    try:
        llm = get_llm_provider()
        raw_response = llm.generate(prompt)
        parsed = parse_json_response(raw_response)

        if parsed is None:
            raise ValueError("LLM returned unparseable response")

        # Validate structure
        result = {
            "overall_reflection": str(parsed.get("overall_reflection", "")),
            "pattern_reflections": [],
            "encouragement": str(parsed.get("encouragement", _GENERIC_ENCOURAGEMENT)),
            "self_care_suggestion": str(parsed.get("self_care_suggestion", _GENERIC_SELF_CARE)),
        }

        # Validate pattern_reflections list
        for item in parsed.get("pattern_reflections", []):
            if isinstance(item, dict) and "pattern" in item and "reflection" in item:
                result["pattern_reflections"].append({
                    "pattern": str(item["pattern"]),
                    "reflection": str(item["reflection"]),
                })

        # Safety check: reject if clinical terms slipped through
        clinical_terms = [
            "depression", "anxiety disorder", "ptsd", "bipolar",
            "schizophrenia", "diagnosis", "diagnosed", "clinical",
            "disorder", "mental illness", "therapy", "medication",
        ]
        full_text = json.dumps(result).lower()
        for term in clinical_terms:
            if term in full_text:
                print(f"[DisclosureAgent] Clinical term '{term}' detected — using fallback")
                raise ValueError(f"Clinical language detected: {term}")

    except Exception as e:
        print(f"[DisclosureAgent] LLM disclosure failed, using fallback: {e}")
        result = _build_fallback_disclosure(approved_patterns)

    # ---- Persist ----
    if user_id:
        store_disclosure(user_id, approved_patterns, result.get("overall_reflection", ""))

    return result


def _is_empty_patterns(patterns: dict) -> bool:
    """
    Check if an approved_patterns dict is effectively empty.

    Args:
        patterns: The approved patterns dict to check.

    Returns:
        True if all pattern lists/dicts are empty.
    """
    if not patterns:
        return True

    return (
        not patterns.get("recurring_emotions")
        and not patterns.get("recurring_stressors")
        and not patterns.get("emotional_trends")
        and not patterns.get("positive_improvements")
        and not patterns.get("negative_changes")
    )


def store_disclosure(user_id: int, disclosed_patterns: dict, disclosure_text: str) -> None:
    """
    Persist a disclosure record to the disclosure_history table.

    Args:
        user_id: The user this disclosure is for.
        disclosed_patterns: The patterns that were disclosed (as dict).
        disclosure_text: The overall reflection text shown to the user.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO disclosure_history (user_id, disclosed_patterns, disclosure_text)
            VALUES (%s, %s, %s)
            """,
            (
                user_id,
                json.dumps(disclosed_patterns),
                disclosure_text,
            ),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[DisclosureAgent] Error storing disclosure: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Manual testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Disclosure Agent — Manual Test")
    print("=" * 60)

    # Simulated approved patterns from Safety Gate
    mock_approved = {
        "recurring_emotions": [
            {"emotion": "anxiety", "frequency": 5},
            {"emotion": "sadness", "frequency": 3},
        ],
        "recurring_stressors": ["work deadlines"],
        "emotional_trends": {"direction": "improving"},
        "positive_improvements": ["better sleep routine"],
        "negative_changes": ["increased work pressure"],
    }

    print("\n--- Test 1: With approved patterns ---")
    result = generate_disclosure(mock_approved, user_id=1)
    print(json.dumps(result, indent=2))

    print("\n--- Test 2: Empty patterns (generic) ---")
    result2 = generate_disclosure({}, user_id=1)
    print(json.dumps(result2, indent=2))

    print("\n--- Test 3: Fallback generation ---")
    fallback = _build_fallback_disclosure(mock_approved)
    print(json.dumps(fallback, indent=2))
