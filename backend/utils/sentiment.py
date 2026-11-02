# utils/sentiment.py
# Provides NLP-based sentiment analysis for journal entries.
#
# Usage:
#   from utils.sentiment import analyze_sentiment
#   result = analyze_sentiment("I had a great day!")
#   # result → { "score": 0.8, "label": "positive" }

from textblob import TextBlob


def analyze_sentiment(text: str) -> dict:
    """
    Analyses the sentiment of the provided text using TextBlob.

    Args:
        text (str): The journal entry content to analyse.

    Returns:
        dict: {
            "score" (float): Polarity score in the range [-1.0, 1.0].
            "label" (str):   One of "positive", "negative", or "neutral".
        }

    Classification thresholds:
        score >  0.1  → "positive"
        score < -0.1  → "negative"
        otherwise     → "neutral"
    """
    if not text or not text.strip():
        return {"score": 0.0, "label": "neutral"}

    blob = TextBlob(text)
    score: float = round(blob.sentiment.polarity, 4)

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {"score": score, "label": label}
