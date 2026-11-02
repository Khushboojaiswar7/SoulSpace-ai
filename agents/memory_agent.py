# agents/memory_agent.py
# Memory Agent — analyzes patterns across a user's last 10 journal entries.
#
# Instead of analyzing only today's journal, this agent retrieves recent
# entry analyses and identifies recurring emotions, stressors, trends,
# triggers, improvements, and negative changes.
#
# Usage:
#   from agents.memory_agent import analyze_patterns, store_memory_patterns
#   patterns = analyze_patterns(user_id=1, current_analysis={...})

import json
import traceback
from collections import Counter

from database import get_connection
from agents.llm_provider import get_llm_provider, parse_json_response


# ---------------------------------------------------------------------------
# Database helper — fetch recent analyses
# ---------------------------------------------------------------------------
def get_recent_analyses(user_id: int, limit: int = 10) -> list:
    """
    Retrieves the most recent entry analyses for a user.

    Args:
        user_id (int): The user's database ID.
        limit (int): Maximum number of analyses to retrieve (default: 10).

    Returns:
        list[dict]: Each dict contains sentiment, primary_emotion,
                    emotion_intensity, stress_level, keywords,
                    cognitive_distortions, confidence, risk_level,
                    and created_at.
    """
    sql = """
        SELECT ea.sentiment, ea.primary_emotion, ea.emotion_intensity,
               ea.stress_level, ea.keywords, ea.cognitive_distortions,
               ea.confidence, ea.risk_level, ea.created_at
        FROM   entry_analyses ea
        WHERE  ea.user_id = %s
        ORDER  BY ea.created_at DESC
        LIMIT  %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, limit))
        rows = cursor.fetchall()
        return [
            {
                "sentiment":             row[0],
                "primary_emotion":       row[1],
                "emotion_intensity":     row[2],
                "stress_level":          row[3],
                "keywords":              row[4] if row[4] else [],
                "cognitive_distortions": row[5] if row[5] else [],
                "confidence":            row[6],
                "risk_level":            row[7],
                "created_at":            str(row[8])
            }
            for row in rows
        ]
    except Exception as error:
        print(f"[memory_agent] get_recent_analyses error: {error}")
        return []
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# Main pattern analysis function
# ---------------------------------------------------------------------------
def analyze_patterns(user_id: int, current_analysis: dict = None) -> dict:
    """
    Analyzes emotional patterns across a user's recent journal entries.

    Retrieves the last 10 entry analyses and uses the LLM to identify
    recurring emotions, stressors, trends, triggers, improvements,
    and negative changes.

    Falls back to statistical aggregation if the LLM is unavailable.

    Args:
        user_id (int): The user's database ID.
        current_analysis (dict, optional): The analysis of the current entry
                                            (included for context).

    Returns:
        dict: Pattern analysis with keys:
            recurring_emotions, recurring_stressors, emotional_trends,
            recurring_triggers, positive_improvements, negative_changes,
            entries_analyzed, confidence
    """
    # Fetch recent analyses
    analyses = get_recent_analyses(user_id, limit=10)

    # Minimum threshold check
    if len(analyses) < 3:
        return {
            "insufficient_data": True,
            "entries_analyzed": len(analyses),
            "message": "Need at least 3 journal entries to identify patterns.",
            "confidence": 0.0
        }

    # Build context for the LLM
    entries_summary = []
    for i, a in enumerate(analyses):
        entries_summary.append(
            f"Entry {i+1} ({a['created_at']}):\n"
            f"  Sentiment: {a['sentiment']}, Emotion: {a['primary_emotion']} "
            f"(intensity: {a['emotion_intensity']})\n"
            f"  Stress: {a['stress_level']}, Risk: {a['risk_level']}\n"
            f"  Keywords: {', '.join(a['keywords']) if a['keywords'] else 'none'}\n"
            f"  Distortions: {', '.join(a['cognitive_distortions']) if a['cognitive_distortions'] else 'none'}"
        )

    entries_text = "\n\n".join(entries_summary)

    prompt = f"""Analyze these {len(analyses)} consecutive journal entry analyses from a single user and identify emotional patterns over time.

{entries_text}

Respond with ONLY a valid JSON object (no markdown, no explanation) containing:
{{
    "recurring_emotions": [
        {{"emotion": "emotion_name", "frequency": count_of_appearances, "trend": "increasing" or "stable" or "decreasing"}}
    ],
    "recurring_stressors": ["list of recurring stress sources identified from keywords"],
    "emotional_trends": {{
        "overall": "improving" or "stable" or "declining",
        "description": "brief 1-2 sentence description of the overall emotional trajectory"
    }},
    "recurring_triggers": ["list of recurring triggers or themes"],
    "positive_improvements": ["list of any positive patterns or improvements noticed"],
    "negative_changes": ["list of any concerning negative patterns"],
    "confidence": float between 0.0 and 1.0
}}"""

    try:
        provider = get_llm_provider()
        raw_response = provider.generate(prompt)

        if raw_response:
            patterns = parse_json_response(raw_response)
            if patterns:
                patterns["entries_analyzed"] = len(analyses)
                patterns.setdefault("recurring_emotions", [])
                patterns.setdefault("recurring_stressors", [])
                patterns.setdefault("emotional_trends", {"overall": "stable", "description": ""})
                patterns.setdefault("recurring_triggers", [])
                patterns.setdefault("positive_improvements", [])
                patterns.setdefault("negative_changes", [])
                patterns.setdefault("confidence", 0.6)
                return patterns

        # LLM failed — use statistical fallback
        print("[memory_agent] LLM response empty, using statistical fallback")
        return _statistical_fallback(analyses)

    except Exception as e:
        print(f"[memory_agent] LLM error, using fallback: {e}")
        traceback.print_exc()
        return _statistical_fallback(analyses)


# ---------------------------------------------------------------------------
# Statistical fallback (no LLM needed)
# ---------------------------------------------------------------------------
def _statistical_fallback(analyses: list) -> dict:
    """
    Generates pattern analysis from raw statistics when LLM is unavailable.

    Counts emotion frequencies, averages intensities, and identifies
    the most common keywords and stressors.
    """
    # Count emotions
    emotion_counter = Counter()
    stress_levels = []
    all_keywords = []
    intensities = []

    for a in analyses:
        emotion = a.get("primary_emotion", "unknown")
        emotion_counter[emotion] += 1
        stress_levels.append(a.get("stress_level", "none"))
        intensities.append(a.get("emotion_intensity", 0.0))
        keywords = a.get("keywords", [])
        if isinstance(keywords, list):
            all_keywords.extend(keywords)

    # Build recurring emotions
    recurring_emotions = [
        {"emotion": emotion, "frequency": count, "trend": "stable"}
        for emotion, count in emotion_counter.most_common(5)
        if count >= 2
    ]

    # Build recurring stressors from keywords
    keyword_counter = Counter(all_keywords)
    recurring_stressors = [
        kw for kw, cnt in keyword_counter.most_common(5) if cnt >= 2
    ]

    # Determine overall trend from intensity changes
    if len(intensities) >= 3:
        first_half_avg = sum(intensities[len(intensities)//2:]) / max(1, len(intensities)//2)
        second_half_avg = sum(intensities[:len(intensities)//2]) / max(1, len(intensities)//2)
        if second_half_avg > first_half_avg + 0.1:
            overall_trend = "declining"
            trend_desc = "Emotional intensity appears to be increasing over recent entries."
        elif second_half_avg < first_half_avg - 0.1:
            overall_trend = "improving"
            trend_desc = "Emotional intensity appears to be decreasing — a positive trend."
        else:
            overall_trend = "stable"
            trend_desc = "Emotional patterns appear relatively stable across recent entries."
    else:
        overall_trend = "stable"
        trend_desc = "Not enough data points to determine a clear trend."

    # Stress analysis
    stress_map = {"none": 0, "low": 1, "moderate": 2, "high": 3, "severe": 4}
    avg_stress = sum(stress_map.get(s, 0) for s in stress_levels) / max(1, len(stress_levels))

    negative_changes = []
    positive_improvements = []
    if avg_stress >= 2.5:
        negative_changes.append("Elevated stress levels across recent entries")
    if any(e["emotion"] in {"joy", "calm", "gratitude", "hope"} for e in recurring_emotions):
        positive_improvements.append("Positive emotions are present in recent entries")

    return {
        "recurring_emotions": recurring_emotions,
        "recurring_stressors": recurring_stressors,
        "emotional_trends": {
            "overall": overall_trend,
            "description": trend_desc
        },
        "recurring_triggers": recurring_stressors[:3],
        "positive_improvements": positive_improvements,
        "negative_changes": negative_changes,
        "entries_analyzed": len(analyses),
        "confidence": 0.45  # Lower confidence for statistical fallback
    }


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------
def store_memory_patterns(user_id: int, patterns: dict):
    """
    Stores the detected patterns in the memory_patterns table.

    Args:
        user_id (int): The user's database ID.
        patterns (dict): The full pattern analysis result.
    """
    sql = """
        INSERT INTO memory_patterns (user_id, patterns, entries_analyzed, confidence)
        VALUES (%s, %s, %s, %s);
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            user_id,
            json.dumps(patterns, default=str),
            patterns.get("entries_analyzed", 0),
            patterns.get("confidence", 0.0)
        ))
        conn.commit()
    except Exception as error:
        conn.rollback()
        print(f"[memory_agent] store_memory_patterns error: {error}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("MEMORY AGENT TEST")
    print("=" * 60)
    print("Note: Requires existing entry_analyses data in the database.")
    print("Run with a valid user_id that has journal entries analyzed.")
