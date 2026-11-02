"""
SoulSpace NLP Preprocessor Module
===================================
Text preprocessing pipeline for journal entries using spaCy and NLTK.
Provides cleaning, tokenization, lemmatization, and named entity recognition
with graceful fallback to basic NLTK processing when spaCy is unavailable.
"""

import re
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# ---------------------------------------------------------------------------
# Download required NLTK data (silent if already present)
# ---------------------------------------------------------------------------
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

# ---------------------------------------------------------------------------
# Load spaCy model
# ---------------------------------------------------------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print(
        "[nlp_preprocessor] spaCy model not found. "
        "Run: python -m spacy download en_core_web_sm"
    )
    nlp = None

# Cache English stopwords
STOP_WORDS = set(stopwords.words("english"))


def clean_text(text: str) -> str:
    """
    Clean raw journal text for downstream NLP processing.

    Operations applied:
        - Convert to lowercase
        - Remove URLs
        - Remove email addresses
        - Remove excessive punctuation (3+ repeated)
        - Strip special characters (keep letters, digits, basic punctuation, emoticons)
        - Normalize whitespace

    Args:
        text: Raw input text.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    cleaned = text.lower()

    # Remove URLs
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)

    # Remove email addresses
    cleaned = re.sub(r"\S+@\S+\.\S+", "", cleaned)

    # Reduce excessive punctuation (3+ repeated chars -> 1)
    cleaned = re.sub(r"([!?.]){3,}", r"\1", cleaned)

    # Remove special characters but keep letters, digits, basic punctuation,
    # whitespace, and common emoticon characters
    cleaned = re.sub(r"[^\w\s.,!?;:'\"-—()😀-🙏☀-⭐]", "", cleaned)

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def tokenize_and_lemmatize(text: str) -> dict:
    """
    Tokenize and lemmatize text, filtering out stop words.

    Uses spaCy for lemmatization when available, falling back to
    basic NLTK word tokenization otherwise.

    Args:
        text: Cleaned input text.

    Returns:
        Dict with keys:
            - tokens:  list of non-stopword tokens
            - lemmas:  list of lemmatized tokens (same as tokens if spaCy unavailable)
    """
    if not text:
        return {"tokens": [], "lemmas": []}

    if nlp is not None:
        doc = nlp(text)
        tokens = [
            token.text
            for token in doc
            if not token.is_stop
            and not token.is_punct
            and not token.is_space
            and len(token.text) > 1
        ]
        lemmas = [
            token.lemma_
            for token in doc
            if not token.is_stop
            and not token.is_punct
            and not token.is_space
            and len(token.text) > 1
        ]
        return {"tokens": tokens, "lemmas": lemmas}

    # Fallback: NLTK tokenization (no lemmatization)
    raw_tokens = word_tokenize(text)
    tokens = [
        t for t in raw_tokens
        if t.lower() not in STOP_WORDS
        and len(t) > 1
        and t.isalnum()
    ]
    return {"tokens": tokens, "lemmas": tokens}


def extract_entities(text: str) -> list:
    """
    Extract named entities from text using spaCy NER.

    Args:
        text: Input text to analyze.

    Returns:
        List of dicts, each with keys:
            - text:  the entity surface text
            - label: the entity type label (e.g. PERSON, DATE, ORG)
        Returns an empty list if spaCy is unavailable.
    """
    if not text or nlp is None:
        return []

    doc = nlp(text)
    entities = [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
    ]
    return entities


def preprocess(text: str) -> dict:
    """
    Full NLP preprocessing pipeline for a journal entry.

    Combines cleaning, tokenization, lemmatization, entity extraction,
    and sentence segmentation into a single call.

    Args:
        text: Raw journal entry text.

    Returns:
        Dict containing:
            - original_text:  the unmodified input
            - cleaned_text:   cleaned version of the input
            - tokens:         word tokens with stopwords removed
            - lemmas:         lemmatized tokens
            - entities:       named entities as list of {text, label} dicts
            - sentences:      list of individual sentences
            - sentence_count: number of sentences
            - word_count:     total word count of the cleaned text
    """
    if not text or not text.strip():
        return {
            "original_text": text or "",
            "cleaned_text": "",
            "tokens": [],
            "lemmas": [],
            "entities": [],
            "sentences": [],
            "sentence_count": 0,
            "word_count": 0,
        }

    cleaned = clean_text(text)

    # Tokenize and lemmatize
    tok_result = tokenize_and_lemmatize(cleaned)

    # Extract entities from original text (preserves casing for NER accuracy)
    entities = extract_entities(text)

    # Sentence segmentation
    if nlp is not None:
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    else:
        # Basic fallback: split on sentence-ending punctuation
        sentences = [
            s.strip()
            for s in re.split(r"[.!?]+", text)
            if s.strip()
        ]

    word_count = len(cleaned.split()) if cleaned else 0

    return {
        "original_text": text,
        "cleaned_text": cleaned,
        "tokens": tok_result["tokens"],
        "lemmas": tok_result["lemmas"],
        "entities": entities,
        "sentences": sentences,
        "sentence_count": len(sentences),
        "word_count": word_count,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("SoulSpace NLP Preprocessor — Smoke Test")
    print("=" * 60)

    sample_journal = (
        "Today was really tough. I had a meeting with Dr. Smith on Monday "
        "and she said my anxiety levels are still high. I couldn't sleep "
        "last night because I kept worrying about the presentation at work. "
        "I feel like nothing I do is ever good enough!!! "
        "Maybe I should try meditation again... Sarah suggested it last week. "
        "Email me at test@example.com or visit https://example.com for more. "
        "I'm grateful for my family though 😊"
    )

    print(f"\nOriginal text:\n  {sample_journal}\n")

    result = preprocess(sample_journal)

    print(f"Cleaned text:\n  {result['cleaned_text']}\n")
    print(f"Tokens ({len(result['tokens'])}):\n  {result['tokens']}\n")
    print(f"Lemmas ({len(result['lemmas'])}):\n  {result['lemmas']}\n")
    print(f"Entities:\n  {result['entities']}\n")
    print(f"Sentences ({result['sentence_count']}):")
    for i, sent in enumerate(result["sentences"], 1):
        print(f"  {i}. {sent}")
    print(f"\nWord count: {result['word_count']}")

    print("\nDone.")
