# utils/chat.py
# Reflection Coach — upgraded from the original rule-based chatbot.
#
# Instead of generic conversation, the Reflection Coach encourages
# journaling, self-reflection, and emotional awareness.
#
# If an LLM provider is configured, it generates contextual reflection
# questions. Otherwise, falls back to keyword-based responses.
#
# Usage:
#   from utils.chat import ChatService
#   reply = ChatService.get_reply("I feel so stressed about my exams")

import random
from utils.sentiment import analyze_sentiment


class ChatService:
    """
    Reflection Coach — encourages journaling and self-reflection.

    Detection priority:
        1. Crisis language detection (immediate supportive response)
        2. Keyword cluster matching (intent-based reflection prompts)
        3. LLM-powered contextual reflection (if available)
        4. Sentiment analysis fallback for borderline messages
        5. Default reflective response

    All logic lives here — the controller only calls get_reply().
    """

    # -----------------------------------------------------------------------
    # Crisis keywords — always take priority
    # -----------------------------------------------------------------------
    _CRISIS_KEYWORDS = {
        "kill myself", "want to die", "end my life", "suicide",
        "self harm", "self-harm", "don't want to live",
        "no reason to live", "better off dead"
    }

    _CRISIS_RESPONSE = (
        "I hear you, and I want you to know that you're not alone. 💙 "
        "What you're feeling is real, and it matters. Please reach out to "
        "someone who can help:\n\n"
        "• 988 Suicide & Crisis Lifeline: Call or text 988 (24/7)\n"
        "• Crisis Text Line: Text HOME to 741741\n"
        "• iCall (India): 9152987821\n"
        "• Vandrevala Foundation (India): 1860-2662-345 (24/7)\n\n"
        "You deserve support. Please talk to someone today. 🤍"
    )

    # -----------------------------------------------------------------------
    # Keyword clusters for reflection prompts
    # -----------------------------------------------------------------------

    _SADNESS_KEYWORDS = {
        "sad", "lonely", "depressed", "depression", "hopeless", "crying",
        "cry", "heartbroken", "miserable", "empty", "worthless", "unloved",
        "alone", "grief", "devastated", "lost"
    }

    _STRESS_KEYWORDS = {
        "stress", "stressed", "anxious", "anxiety", "exam", "exams", "test",
        "deadline", "deadlines", "work", "overwhelmed", "pressure", "burnout",
        "exhausted", "tired", "worried", "worry", "panic", "panicking",
        "assignment", "project", "boss", "job"
    }

    _HAPPY_KEYWORDS = {
        "happy", "happiness", "excited", "great", "amazing", "wonderful",
        "fantastic", "awesome", "joyful", "elated", "thrilled", "ecstatic",
        "good", "terrific", "brilliant", "cheerful", "content", "grateful"
    }

    _MOTIVATION_KEYWORDS = {
        "motivation", "motivate", "motivated", "inspire", "inspired",
        "inspiration", "goal", "goals", "purpose", "achieve", "ambition",
        "dream", "success", "focus", "discipline", "progress", "forward"
    }

    _JOURNAL_KEYWORDS = {
        "journal", "write", "writing", "entry", "wrote", "journaling",
        "diary", "reflect", "reflection", "thoughts", "feelings"
    }

    # -----------------------------------------------------------------------
    # Reflection response banks (upgraded from generic chatbot replies)
    # -----------------------------------------------------------------------

    _SADNESS_REFLECTIONS = [
        "It sounds like you're carrying something heavy right now. 💙 "
        "When you feel ready, try writing about what's on your mind in your journal. "
        "Sometimes putting feelings into words can bring a small sense of relief. "
        "What do you think is at the root of this feeling?",

        "I'm here with you. 💜 Sadness often has layers — "
        "have you noticed if this feeling is connected to something specific? "
        "Writing about it, even just a few lines, can help you see things more clearly.",

        "It takes courage to acknowledge how you feel. 🌧️ "
        "Try this: in your next journal entry, write about one moment today "
        "that felt even slightly okay — no matter how small. "
        "What's one thing that usually brings you comfort?",

        "Your feelings are valid, and they matter. 💙 "
        "Consider asking yourself: 'When did this feeling start?' "
        "and 'What would I tell a friend going through this?' "
        "Sometimes we're kinder to others than to ourselves."
    ]

    _STRESS_REFLECTIONS = [
        "Sounds like there's a lot on your plate. 🫧 "
        "Try this reflection exercise: write down everything that's stressing you, "
        "then circle the ONE thing you can act on today. "
        "What feels most urgent right now?",

        "When pressure builds, it helps to untangle your thoughts. 🌊 "
        "In your journal, try separating 'things I can control' from "
        "'things I can't.' Which category is taking up more of your energy?",

        "Your body often knows before your mind does. ☕ "
        "Pause for a moment — where are you holding tension? "
        "Jaw? Shoulders? Back? Write about what you notice. "
        "What would it look like to give yourself permission to rest?",

        "Stress often comes from trying to do everything at once. 💛 "
        "What if you focused on just one task for the next 25 minutes? "
        "After that, check in with yourself: how do you feel? "
        "Write about it in your journal."
    ]

    _HAPPY_REFLECTIONS = [
        "That's wonderful to hear! 🌟 Savor this feeling — you deserve it. "
        "Try this: write down exactly what contributed to this good feeling. "
        "On harder days, you can revisit this entry as a reminder. "
        "What specifically made the difference today?",

        "Your positive energy is beautiful. ✨ "
        "Take a moment to reflect: what choices did you make today that led here? "
        "Understanding what works helps you recreate it. "
        "Have you considered writing a gratitude entry?",

        "Love this for you! 🌈 "
        "Happiness is worth studying just as much as struggle. "
        "In your journal, try capturing this moment in detail — "
        "the sights, sounds, feelings. What are you most grateful for right now?",

        "Amazing! 🚀 Channel this energy into your journal — "
        "write about what's going right, who made you smile, "
        "or a goal you're excited about. "
        "What would you like to remember about today?"
    ]

    _MOTIVATION_REFLECTIONS = [
        "That spark you feel? That's the start of something. 🚀 "
        "Capture it in your journal before it fades. Write down: "
        "'My goal is ___, and the smallest step I can take today is ___.' "
        "What matters most to you right now?",

        "Purpose grows when you pay attention to it. 🌱 "
        "Try this reflection: 'Why does this goal matter to me personally?' "
        "Write freely — the 'why' is your fuel. "
        "What would achieving this mean for your future self?",

        "Progress isn't always visible, but it's happening. 💡 "
        "In your journal, list three things you've accomplished recently "
        "— even small ones count. "
        "What's one thing you're proud of this week?",

        "Your ambition is a strength. 🏅 "
        "Reflect on this: 'What's holding me back, and is it real or imagined?' "
        "Sometimes our biggest obstacles are the stories we tell ourselves."
    ]

    _JOURNAL_REFLECTIONS = [
        "Journaling is one of the most powerful tools for self-understanding. 📖 "
        "Here's a prompt for your next entry: "
        "'What emotion visited me most today, and what was it trying to tell me?'",

        "Every entry you write is a conversation with yourself. ✍️ "
        "Try this prompt: 'If I could change one thing about today, what would it be? "
        "And what would I keep exactly the same?'",

        "Writing regularly builds emotional clarity over time. 🌿 "
        "For your next entry, try: 'Three things I noticed about myself today — "
        "one thought, one feeling, one physical sensation.'",

        "Your journal is a safe space with no judgment. 💜 "
        "Try writing about something you haven't said out loud yet. "
        "What's been sitting quietly in the back of your mind?"
    ]

    _DEFAULT_REFLECTIONS = [
        "Thanks for sharing that with me. 🌿 "
        "I'm here to help you reflect. Tell me more — "
        "what's the strongest feeling you have right now? "
        "Sometimes naming it is the first step to understanding it.",

        "I hear you. 💛 Let's explore that together. "
        "If you had to describe your current emotional state in one word, "
        "what would it be? There's no wrong answer.",

        "That's interesting — let's dig deeper. 😊 "
        "What do you think triggered this feeling? "
        "Sometimes connecting a feeling to a moment brings clarity.",

        "I'm here with you. 🌸 "
        "Have you written about this in your journal yet? "
        "Putting it on paper often helps more than we expect. "
        "What would you want to tell your future self about today?"
    ]

    # -----------------------------------------------------------------------
    # LLM-powered reflection (optional enhancement)
    # -----------------------------------------------------------------------
    @staticmethod
    def _try_llm_reflection(message: str) -> str:
        """
        Attempts to generate a contextual reflection using the LLM.
        Returns empty string if LLM is unavailable.
        """
        try:
            from agents.llm_provider import get_llm_provider

            prompt = f"""You are a Reflection Coach in a mental wellness journaling app. A user just sent this message:

"{message}"

Respond with a warm, supportive message that:
1. Acknowledges their feeling
2. Asks a thoughtful self-reflection question
3. Gently encourages them to journal about it
4. Uses uncertain, non-diagnostic language

Keep your response to 3-4 sentences. Be warm and encouraging, not clinical.
Do NOT diagnose or use clinical labels. Do NOT say "I'm an AI" or "I'm a bot"."""

            provider = get_llm_provider()
            response = provider.generate(prompt)
            if response and len(response.strip()) > 20:
                return response.strip()
        except Exception as e:
            print(f"[ChatService] LLM reflection error (using fallback): {e}")

        return ""

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    @staticmethod
    def get_reply(message: str) -> str:
        """
        Returns a reflective, supportive reply for the given user message.

        The Reflection Coach prioritizes self-awareness, journaling
        encouragement, and emotional exploration over generic conversation.

        Args:
            message (str): The raw message string from the user.

        Returns:
            str: A contextual, reflective reply.
        """
        if not message or not message.strip():
            return random.choice(ChatService._DEFAULT_REFLECTIONS)

        message_lower = message.lower()

        # --- Priority 0: Crisis detection ---
        for phrase in ChatService._CRISIS_KEYWORDS:
            if phrase in message_lower:
                return ChatService._CRISIS_RESPONSE

        # Tokenise for keyword matching
        words = set(message_lower.split())

        # --- Priority 1: Keyword cluster detection ---
        if words & ChatService._JOURNAL_KEYWORDS:
            return random.choice(ChatService._JOURNAL_REFLECTIONS)

        if words & ChatService._SADNESS_KEYWORDS:
            return random.choice(ChatService._SADNESS_REFLECTIONS)

        if words & ChatService._STRESS_KEYWORDS:
            return random.choice(ChatService._STRESS_REFLECTIONS)

        if words & ChatService._HAPPY_KEYWORDS:
            return random.choice(ChatService._HAPPY_REFLECTIONS)

        if words & ChatService._MOTIVATION_KEYWORDS:
            return random.choice(ChatService._MOTIVATION_REFLECTIONS)

        # --- Priority 2: Try LLM-powered contextual reflection ---
        llm_reply = ChatService._try_llm_reflection(message)
        if llm_reply:
            return llm_reply

        # --- Priority 3: Sentiment-analysis fallback ---
        sentiment = analyze_sentiment(message)
        score = sentiment["score"]

        if score <= -0.3:
            return random.choice(ChatService._SADNESS_REFLECTIONS)
        elif score >= 0.3:
            return random.choice(ChatService._HAPPY_REFLECTIONS)

        # --- Priority 4: Warm reflective default ---
        return random.choice(ChatService._DEFAULT_REFLECTIONS)
