# agents/entry_analysis.py
# Entry Analysis Agent — powered by Groq LLM with TextBlob fallback.
#
# Replaces TextBlob as the main AI engine for journal analysis.
# Returns rich structured JSON with sentiment, emotion, stress,
# cognitive distortions, and risk assessment.
#
# Usage:
#   from agents.entry_analysis import analyze_entry, store_entry_analysis
#   result = analyze_entry("I feel overwhelmed with work...", preprocessed)
#   store_entry_analysis(journal_id=42, user_id=1, analysis=result)

import json
import traceback

from agents.llm_provider import get_llm_provider, parse_json_response
from database import get_connection


# ---------------------------------------------------------------------------
# Valid values for validation
# ---------------------------------------------------------------------------
VALID_SENTIMENTS = {"positive", "negative", "neutral", "mixed"}
VALID_EMOTIONS = {
    "anxiety", "sadness", "anger", "joy", "fear", "surprise",
    "disgust", "shame", "guilt", "love", "gratitude", "hope",
    "loneliness", "frustration", "calm", "excitement", "contentment",
    "confusion", "overwhelm", "relief"
}
VALID_STRESS_LEVELS = {"none", "low", "moderate", "high", "severe"}
VALID_RISK_LEVELS = {"none", "low", "moderate", "high"}
VALID_DISTORTIONS = {
    "catastrophizing", "black-and-white thinking", "overgeneralization",
    "mind-reading", "fortune-telling", "emotional-reasoning",
    "should-statements", "labeling", "personalization",
    "mental-filtering", "discounting-positives", "magnification"
}


# ---------------------------------------------------------------------------
# Default / empty analysis structure
# ---------------------------------------------------------------------------
def _empty_analysis() -> dict:
    """Returns a default empty analysis dict with all expected keys."""
    return {
        "sentiment": "neutral",
        "primary_emotion": "calm",
        "emotion_intensity": 0.0,
        "stress_level": "none",
        "keywords": [],
        "cognitive_distortions": [],
        "confidence": 0.0,
        "risk_level": "none"
    }


# ---------------------------------------------------------------------------
# LLM-powered analysis
# ---------------------------------------------------------------------------
def analyze_entry(text: str, preprocessed_data: dict = None) -> dict:
    """
    Analyses a journal entry using the configured LLM provider.

    The LLM is prompted to return structured JSON with sentiment,
    emotion, stress level, keywords, cognitive distortions, and risk.

    If the LLM is unavailable or fails, falls back to TextBlob-based
    heuristic analysis.

    Args:
        text (str): The raw journal entry content.
        preprocessed_data (dict, optional): Pre-computed NLP data from
                                             nlp_preprocessor.preprocess().

    Returns:
        dict: Structured analysis with keys:
            sentiment, primary_emotion, emotion_intensity, stress_level,
            keywords, cognitive_distortions, confidence, risk_level
    """
    if not text or not text.strip():
        return _empty_analysis()

    # Build context from preprocessed NLP data
    nlp_context = ""
    if preprocessed_data:
        entities = preprocessed_data.get("entities", [])
        lemmas = preprocessed_data.get("lemmas", [])
        if entities:
            entity_strs = [f"{e['text']} ({e['label']})" for e in entities[:10]]
            nlp_context += f"\nDetected entities: {', '.join(entity_strs)}"
        if lemmas:
            nlp_context += f"\nKey lemmas: {', '.join(lemmas[:20])}"

    # Build the LLM prompt
    prompt = f"""Analyze this journal entry for emotional content and mental wellness indicators.

JOURNAL ENTRY:
\"\"\"{text}\"\"\"
{nlp_context}

Respond with ONLY a valid JSON object (no markdown, no explanation) containing:
{{
    "sentiment": one of "positive", "negative", "neutral", "mixed",
    "primary_emotion": the dominant emotion (e.g. "anxiety", "sadness", "joy", "frustration", "calm", "loneliness", "hope", "anger", "gratitude", "fear", "excitement", "overwhelm", "guilt", "shame", "love", "relief", "contentment", "confusion", "surprise", "disgust"),
    "emotion_intensity": float between 0.0 (very mild) and 1.0 (very intense),
    "stress_level": one of "none", "low", "moderate", "high", "severe",
    "keywords": array of 3-7 important keywords from the text,
    "cognitive_distortions": array of any cognitive distortions detected from this list: ["catastrophizing", "black-and-white thinking", "overgeneralization", "mind-reading", "fortune-telling", "emotional-reasoning", "should-statements", "labeling", "personalization", "mental-filtering", "discounting-positives", "magnification"]. Return empty array if none detected,
    "confidence": float between 0.0 and 1.0 indicating how confident you are,
    "risk_level": one of "none", "low", "moderate", "high"
}}"""

    try:
        provider = get_llm_provider()
        raw_response = provider.generate(prompt)

        if raw_response:
            analysis = parse_json_response(raw_response)
            if analysis:
                return _validate_analysis(analysis)

        # LLM returned empty or unparseable — use fallback
        print("[entry_analysis] LLM response empty or unparseable, using fallback")
        return _fallback_analysis(text)

    except Exception as e:
        print(f"[entry_analysis] LLM error, using fallback: {e}")
        traceback.print_exc()
        return _fallback_analysis(text)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _validate_analysis(analysis: dict) -> dict:
    """
    Validates and normalizes an analysis dict, filling defaults for any
    missing or invalid fields.
    """
    result = _empty_analysis()

    # Sentiment
    sent = str(analysis.get("sentiment", "neutral")).lower().strip()
    result["sentiment"] = sent if sent in VALID_SENTIMENTS else "neutral"

    # Primary emotion
    emotion = str(analysis.get("primary_emotion", "calm")).lower().strip()
    result["primary_emotion"] = emotion if emotion in VALID_EMOTIONS else emotion

    # Emotion intensity
    try:
        intensity = float(analysis.get("emotion_intensity", 0.0))
        result["emotion_intensity"] = max(0.0, min(1.0, intensity))
    except (ValueError, TypeError):
        result["emotion_intensity"] = 0.5

    # Stress level
    stress = str(analysis.get("stress_level", "none")).lower().strip()
    result["stress_level"] = stress if stress in VALID_STRESS_LEVELS else "none"

    # Keywords
    keywords = analysis.get("keywords", [])
    if isinstance(keywords, list):
        result["keywords"] = [str(k).strip() for k in keywords[:10] if k]
    else:
        result["keywords"] = []

    # Cognitive distortions
    distortions = analysis.get("cognitive_distortions", [])
    if isinstance(distortions, list):
        result["cognitive_distortions"] = [
            str(d).strip() for d in distortions if str(d).strip()
        ]
    else:
        result["cognitive_distortions"] = []

    # Confidence
    try:
        conf = float(analysis.get("confidence", 0.5))
        result["confidence"] = max(0.0, min(1.0, conf))
    except (ValueError, TypeError):
        result["confidence"] = 0.5

    # Risk level
    risk = str(analysis.get("risk_level", "none")).lower().strip()
    result["risk_level"] = risk if risk in VALID_RISK_LEVELS else "none"

    return result


# ---------------------------------------------------------------------------
# Fallback analysis (TextBlob + keyword heuristics)
# ---------------------------------------------------------------------------
# Emotion keyword banks for heuristic detection
_EMOTION_KEYWORDS = {
    "joy":         {"happy", "joy", "excited", "amazing", "wonderful", "great", "fantastic", "love", "blessed", "grateful"},
    "sadness":     {"sad", "unhappy", "depressed", "miserable", "heartbroken", "crying", "tears", "grief", "sorrow", "lonely"},
    "anxiety":     {"anxious", "worried", "nervous", "panic", "scared", "fear", "terrified", "dread", "uneasy", "restless"},
    "anger":       {"angry", "furious", "mad", "frustrated", "annoyed", "irritated", "rage", "livid", "outraged", "resentful"},
    "frustration": {"frustrated", "stuck", "overwhelmed", "exhausted", "tired", "burnout", "stressed", "drained", "can't", "impossible"},
    "calm":        {"calm", "peaceful", "relaxed", "serene", "content", "tranquil", "centered", "balanced", "steady", "mindful"},
    "hope":        {"hope", "hopeful", "optimistic", "looking forward", "excited", "bright", "positive", "better", "improving"},
    "loneliness":  {"alone", "lonely", "isolated", "nobody", "no one", "abandoned", "disconnected", "forgotten"},
    "gratitude":   {"thankful", "grateful", "appreciate", "blessed", "fortunate", "lucky"},
}


def _fallback_analysis(text: str) -> dict:
    """
    Fallback analysis using TextBlob sentiment and keyword-based
    emotion detection. Used when the LLM is unavailable.

    Args:
        text (str): The journal entry text.

    Returns:
        dict: Analysis with the same structure as LLM output,
              but with lower confidence (0.3-0.5).
    """
    result = _empty_analysis()

    # TextBlob sentiment
    try:
        from textblob import TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            result["sentiment"] = "positive"
        elif polarity < -0.1:
            result["sentiment"] = "negative"
        else:
            result["sentiment"] = "neutral"

        # Map polarity to emotion intensity (absolute value)
        result["emotion_intensity"] = round(min(abs(polarity) * 1.2, 1.0), 2)

    except Exception:
        result["sentiment"] = "neutral"
        result["emotion_intensity"] = 0.3

    # Keyword-based emotion detection
    text_lower = text.lower()
    words = set(text_lower.split())
    emotion_scores = {}

    for emotion, keywords in _EMOTION_KEYWORDS.items():
        matches = words & keywords
        if matches:
            emotion_scores[emotion] = len(matches)

    if emotion_scores:
        result["primary_emotion"] = max(emotion_scores, key=emotion_scores.get)
    else:
        # Default based on sentiment
        if result["sentiment"] == "positive":
            result["primary_emotion"] = "joy"
        elif result["sentiment"] == "negative":
            result["primary_emotion"] = "sadness"
        else:
            result["primary_emotion"] = "calm"

    # Stress level based on stress keywords
    stress_words = {"stress", "stressed", "overwhelmed", "pressure", "deadline",
                    "burnout", "exhausted", "can't cope", "too much", "overloaded"}
    stress_count = len(words & stress_words)
    if stress_count >= 3:
        result["stress_level"] = "high"
    elif stress_count >= 2:
        result["stress_level"] = "moderate"
    elif stress_count >= 1:
        result["stress_level"] = "low"
    else:
        result["stress_level"] = "none"

    # Extract basic keywords (most frequent non-stopword tokens)
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words("english"))
    except Exception:
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "me",
                      "my", "and", "or", "but", "in", "on", "at", "to", "for",
                      "of", "with", "that", "this", "it", "he", "she", "they"}

    content_words = [w for w in text_lower.split() if w.isalpha()
                     and len(w) > 3 and w not in stop_words]
    # Get top keywords by frequency
    from collections import Counter
    word_freq = Counter(content_words)
    result["keywords"] = [w for w, _ in word_freq.most_common(5)]

    # Confidence is lower for fallback
    result["confidence"] = 0.35
    result["risk_level"] = "none"

    return result


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------
def store_entry_analysis(journal_id: int, user_id: int, analysis: dict):
    """
    Stores the structured analysis in the entry_analyses table.

    Args:
        journal_id (int): The journal entry's database ID.
        user_id (int): The user's database ID.
        analysis (dict): The analysis result from analyze_entry().
    """
    sql = """
        INSERT INTO entry_analyses (journal_id, user_id, sentiment,
                                     primary_emotion, emotion_intensity,
                                     stress_level, keywords,
                                     cognitive_distortions, confidence,
                                     risk_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            journal_id,
            user_id,
            analysis.get("sentiment", "neutral"),
            analysis.get("primary_emotion", "calm"),
            analysis.get("emotion_intensity", 0.0),
            analysis.get("stress_level", "none"),
            json.dumps(analysis.get("keywords", [])),
            json.dumps(analysis.get("cognitive_distortions", [])),
            analysis.get("confidence", 0.0),
            analysis.get("risk_level", "none")
        ))
        conn.commit()
    except Exception as error:
        conn.rollback()
        print(f"[entry_analysis] store_entry_analysis error: {error}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Quick test
    test_text = (
        "I've been feeling really overwhelmed with work lately. "
        "The deadlines keep piling up and I can't sleep well. "
        "But I'm trying to exercise more which helps a bit."
    )
    print("=" * 60)
    print("ENTRY ANALYSIS TEST")
    print("=" * 60)
    result = analyze_entry(test_text)
    print(json.dumps(result, indent=2))
