# agents/report_agent.py
import json
import traceback

from database import get_connection
from agents.llm_provider import get_llm_provider, parse_json_response

def get_all_analyses(user_id: int, limit: int = 100) -> list:
    """
    Retrieves up to 'limit' entry analyses for a user, sorted chronologically (oldest first).

    SAFETY CONSTRAINT: Any journal entries associated with a crisis_events record
    for this user are EXCLUDED from the result set. This applies to all users, not
    just study participants — crisis-flagged content must never reach an ungated LLM call.
    """
    sql = """
        SELECT ea.sentiment, ea.primary_emotion, ea.emotion_intensity,
               ea.stress_level, ea.keywords, ea.cognitive_distortions,
               ea.created_at, j.content
        FROM   entry_analyses ea
        JOIN   journals j ON ea.journal_id = j.id
        WHERE  ea.user_id = %s
          AND  ea.journal_id NOT IN (
                   SELECT DISTINCT journal_id
                   FROM   crisis_events
                   WHERE  user_id = %s
                     AND  journal_id IS NOT NULL
               )
        ORDER  BY ea.created_at ASC
        LIMIT  %s;
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, user_id, limit))
        rows = cursor.fetchall()
        return [
            {
                "sentiment":             row[0],
                "primary_emotion":       row[1],
                "emotion_intensity":     row[2],
                "stress_level":          row[3],
                "keywords":              row[4] if row[4] else [],
                "cognitive_distortions": row[5] if row[5] else [],
                "created_at":            str(row[6]),
                "content":               row[7][:200] + "..." if len(row[7]) > 200 else row[7]
            }
            for row in rows
        ]
    except Exception as error:
        print(f"[report_agent] get_all_analyses error: {error}")
        return []
    finally:
        cursor.close()
        conn.close()

def generate_report(user_id: int) -> dict:
    """
    Generates a comprehensive emotional journey report for the user.
    """
    analyses = get_all_analyses(user_id, limit=100)
    
    if len(analyses) == 0:
        return {
            "has_data": False,
            "message": "Not enough journal entries to generate a report. Start journaling!"
        }

    # Build context for the LLM
    entries_summary = []
    for i, a in enumerate(analyses):
        entries_summary.append(
            f"Date: {a['created_at']}\n"
            f"Emotion: {a['primary_emotion']} (Stress: {a['stress_level']})\n"
            f"Keywords: {', '.join(a['keywords']) if a['keywords'] else 'none'}\n"
            f"Distortions: {', '.join(a['cognitive_distortions']) if a['cognitive_distortions'] else 'none'}\n"
            f"Snippet: \"{a['content']}\""
        )
    
    entries_text = "\n\n".join(entries_summary)

    prompt = f"""You are a compassionate, expert mental health AI. Below are the journal entry analyses for a user from their very first entry to their latest.

{entries_text}

Analyze the user's entire journey and generate a comprehensive Emotional Journey Report. 

Respond with ONLY a valid JSON object containing:
{{
    "journey_summary": "A compassionate, 2-3 paragraph narrative describing how their emotions, behaviors, and mindset have evolved from the beginning to now.",
    "major_emotion_month": "The defining emotion of their recent month.",
    "major_emotion_week": "The defining emotion of their recent week.",
    "behavioral_trends": [
        "A list of 3-5 key behavioral or emotional trends observed (e.g., 'You tend to experience higher stress when discussing work keywords like deadline')."
    ],
    "remedies": [
        "A list of 3-5 specific, actionable coping strategies and remedies tailored exactly to their unique cognitive distortions, stressors, and text."
    ],
    "system_support": "A warm, affirming 1-paragraph statement on how this journaling system supports them and acknowledges their growth."
}}"""

    try:
        provider = get_llm_provider()
        raw_response = provider.generate(prompt)

        if raw_response:
            report = parse_json_response(raw_response)
            if report:
                report["has_data"] = True
                report["entries_analyzed"] = len(analyses)
                return report

        # Fallback if parsing fails
        return {
            "has_data": True,
            "entries_analyzed": len(analyses),
            "journey_summary": "We couldn't generate the full AI report right now, but you have logged several entries. Keep journaling to build your emotional map!",
            "major_emotion_month": "Various",
            "major_emotion_week": "Various",
            "behavioral_trends": ["Keep logging to see trends!"],
            "remedies": ["Take a deep breath", "Go for a short walk", "Practice mindfulness for 5 minutes"],
            "system_support": "SoulSpace is always here for you."
        }
    except Exception as e:
        print(f"[report_agent] LLM error: {e}")
        traceback.print_exc()
        return {"has_data": False, "message": "Failed to generate report."}
