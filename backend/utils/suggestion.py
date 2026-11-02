# utils/suggestion.py
# Rule-based suggestion engine for SoulSpace journal entries.
#
# Usage:
#   from utils.suggestion import SuggestionService
#   suggestion = SuggestionService.generate(
#       sentiment_score=-0.7,
#       sentiment_label="negative",
#       mood_label="Anxious"
#   )

import random


class SuggestionService:
    """
    Generates a personalised wellness suggestion based on sentiment analysis
    results and the user-selected mood label.

    All logic lives here – controllers stay clean.
    """

    # -----------------------------------------------------------------------
    # Suggestion banks per sentiment tier
    # -----------------------------------------------------------------------

    _VERY_NEGATIVE = [
        "It sounds like today was really tough. 💙 Try a simple box-breathing "
        "exercise: inhale for 4 counts, hold for 4, exhale for 4, hold for 4. "
        "Repeat 3–4 times. Your feelings are valid — be gentle with yourself.",

        "When emotions feel overwhelming, grounding yourself can help. "
        "Try the 5-4-3-2-1 technique: name 5 things you can see, 4 you can touch, "
        "3 you can hear, 2 you can smell, 1 you can taste. You are safe. 🌿",

        "You've been carrying a lot. 💙 Consider taking a short walk outside — "
        "even 10 minutes of fresh air can gently shift your mood. "
        "You don't have to fix everything today.",

        "It's okay not to be okay. 💜 Place one hand on your heart and take "
        "three slow, deep breaths. Remind yourself: 'This feeling is temporary. "
        "I am doing my best.' That's enough for right now.",
    ]

    _MILDLY_NEGATIVE = [
        "It seems like today was a little heavy. 🌧️ Take a few minutes to "
        "write down one small thing that went okay today — no matter how tiny. "
        "Shifting focus gently can create space for relief.",

        "Stress has a way of building up quietly. 🫧 Try a quick 'brain dump': "
        "write everything on your mind on paper (or here!) without filtering. "
        "Getting it out of your head is the first step.",

        "Feeling drained is a signal worth listening to. 💛 Ask yourself: "
        "'What's one small boundary I could set today to protect my energy?' "
        "Rest is productive — you're allowed to recharge.",

        "When things feel off, routine can be a quiet anchor. ☕ "
        "Make yourself a warm drink, take a short break, and revisit your tasks "
        "with fresh eyes. Small resets matter.",
    ]

    _NEUTRAL = [
        "You're navigating the in-between — and that's completely valid. 🌤️ "
        "A short mindfulness moment: close your eyes, focus on your breathing "
        "for 60 seconds, and notice how you feel without judgment.",

        "Balance is often found in small habits. 🌱 "
        "Consider scheduling a 5-minute 'check-in' with yourself each day — "
        "just ask: 'How am I really doing?' Awareness is the start of well-being.",

        "Steady days build resilience. 🌊 Celebrate maintaining equilibrium — "
        "it's not boring, it's sustainable. What's one thing you'd like to "
        "look forward to this week?",
    ]

    _POSITIVE = [
        "That's a lovely reflection! 🌟 You're doing well — keep nurturing "
        "what's working for you. Write down one thing you're proud of today "
        "to remember this feeling.",

        "Positive moments are worth anchoring. ✨ Spend 2 minutes noting: "
        "'What specifically made today feel good?' Revisiting these notes "
        "on harder days can be a great boost.",

        "Great energy today! 💛 Channel this into something you've been putting "
        "off — even 15 focused minutes can create real momentum. You've got this!",
    ]

    _VERY_POSITIVE = [
        "Amazing! You're radiating good vibes today. 🎉 "
        "Celebrate this fully — tell someone you appreciate them, or take "
        "a moment to savour what made today great. Joy compounds! 🌈",

        "This is wonderful to read! 🌟 Your positivity is a real asset. "
        "Consider using this energy to help someone else, start a creative project, "
        "or simply enjoy the moment — you've earned it.",

        "You're absolutely thriving! 🚀 Keep this momentum going by setting "
        "one micro-goal for tomorrow while you're feeling this confident. "
        "Small steps taken in good spirits go a long way!",
    ]

    # -----------------------------------------------------------------------
    # Mood-specific add-on phrases
    # -----------------------------------------------------------------------

    _MOOD_ADDONS = {
        "Anxious":  " Remember: anxiety is just your mind trying to protect you — "
                    "not a prediction of what will happen. 💙",
        "Angry":    " It's okay to feel anger — it often hides hurt or unmet needs. "
                    "Try journalling what's underneath that feeling. 🔥",
        "Sad":      " Sadness asks to be felt, not fixed. Allow yourself some "
                    "compassion today. 💜",
        "Happy":    " Keep spreading that joy — it's contagious! 😊",
        "Calm":     " Calm is a superpower. Notice what helped you get there "
                    "and try to recreate it tomorrow. 🌿",
    }

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @staticmethod
    def generate(
        sentiment_score: float,
        sentiment_label: str,
        mood_label: str = None
    ) -> str:
        """
        Returns a supportive, personalised suggestion string.

        Args:
            sentiment_score  (float) : TextBlob polarity score [-1.0, 1.0].
            sentiment_label  (str)   : 'positive', 'negative', or 'neutral'.
            mood_label       (str)   : Human-readable mood (e.g. 'Anxious').
                                       Can be None if no mood was selected.

        Returns:
            str: A single suggestion message.
        """
        # --- Select bank based on score tiers ---
        if sentiment_score <= -0.5:
            bank = SuggestionService._VERY_NEGATIVE
        elif sentiment_score < 0:
            bank = SuggestionService._MILDLY_NEGATIVE
        elif sentiment_label == "neutral":
            bank = SuggestionService._NEUTRAL
        elif sentiment_score <= 0.5:
            bank = SuggestionService._POSITIVE
        else:
            bank = SuggestionService._VERY_POSITIVE

        suggestion = random.choice(bank)

        # --- Optionally append a mood-specific add-on ---
        if mood_label and mood_label in SuggestionService._MOOD_ADDONS:
            suggestion += SuggestionService._MOOD_ADDONS[mood_label]

        return suggestion
