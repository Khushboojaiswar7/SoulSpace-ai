"""
SoulSpace LLM Provider Module
==============================
Modular LLM provider abstraction supporting Groq (cloud), Ollama (local),
and a fallback provider. Includes a JSON response parser that handles
common LLM output quirks (markdown-wrapped JSON, extra text, etc.).
"""

import os
import re
import json
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a text response from the LLM given a prompt.

        Args:
            prompt: The user prompt to send to the model.

        Returns:
            The model's text response, or an empty string on failure.
        """
        pass


class GroqProvider(BaseLLMProvider):
    """
    LLM provider using the Groq cloud REST API.

    Reads configuration from environment variables:
        - GROQ_API_KEY:  API key for authentication (required).
        - GROQ_MODEL:    Model identifier (default: openai/gpt-oss-120b).
    """

    API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    TIMEOUT_SECONDS = 30

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        if not self.api_key:
            print("[GroqProvider] WARNING: GROQ_API_KEY not set in environment.")

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the Groq API and return the model's response.

        Args:
            prompt: The user prompt.

        Returns:
            The model's text response, or empty string on any failure.
        """
        if not self.api_key:
            print("[GroqProvider] Cannot generate — GROQ_API_KEY is missing.")
            return ""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a mental health analysis assistant. "
                        "Always respond with valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        try:
            response = requests.post(
                self.API_ENDPOINT,
                headers=headers,
                json=body,
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            print(f"[GroqProvider] Request timed out after {self.TIMEOUT_SECONDS}s.")
            return ""
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if hasattr(e, "response") and e.response is not None else ""
            print(f"[GroqProvider] HTTP error: {e} | Details: {error_detail}")
            return ""
        except requests.exceptions.ConnectionError:
            print("[GroqProvider] Connection error — cannot reach Groq API.")
            return ""
        except (KeyError, IndexError) as e:
            print(f"[GroqProvider] Unexpected response structure: {e}")
            return ""
        except Exception as e:
            print(f"[GroqProvider] Unexpected error: {e}")
            return ""


class OllamaProvider(BaseLLMProvider):
    """
    LLM provider using a local Ollama instance.

    Reads configuration from environment variables:
        - OLLAMA_URL:    Base URL for the Ollama server (default: http://localhost:11434).
        - OLLAMA_MODEL:  Model identifier (default: llama3.1).
    """

    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the local Ollama server and return the response.

        Args:
            prompt: The user prompt.

        Returns:
            The model's text response, or empty string on any failure.
        """
        endpoint = f"{self.url}/api/generate"

        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(endpoint, json=body, timeout=120)
            response.raise_for_status()

            data = response.json()
            return data["response"]

        except requests.exceptions.ConnectionError:
            print(f"[OllamaProvider] Cannot connect to Ollama at {self.url}.")
            return ""
        except requests.exceptions.Timeout:
            print("[OllamaProvider] Request timed out.")
            return ""
        except requests.exceptions.HTTPError as e:
            print(f"[OllamaProvider] HTTP error: {e}")
            return ""
        except (KeyError, IndexError) as e:
            print(f"[OllamaProvider] Unexpected response structure: {e}")
            return ""
        except Exception as e:
            print(f"[OllamaProvider] Unexpected error: {e}")
            return ""


class FallbackProvider(BaseLLMProvider):
    """
    Fallback provider that always returns an empty string.
    Callers should implement their own fallback logic when they
    receive an empty response.
    """

    def generate(self, prompt: str) -> str:
        """Return an empty string — the caller handles fallback logic."""
        print("[FallbackProvider] No LLM provider available. Returning empty response.")
        return ""


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function that returns the appropriate LLM provider
    based on the LLM_PROVIDER environment variable.

    Supported values:
        - 'groq'     -> GroqProvider   (default)
        - 'ollama'   -> OllamaProvider
        - 'fallback' -> FallbackProvider

    Returns:
        An instance of a BaseLLMProvider subclass.
    """
    provider_name = os.getenv("LLM_PROVIDER", "groq").lower().strip()

    providers = {
        "groq": GroqProvider,
        "ollama": OllamaProvider,
        "fallback": FallbackProvider,
    }

    provider_class = providers.get(provider_name)

    if provider_class is None:
        print(
            f"[get_llm_provider] Unknown provider '{provider_name}'. "
            f"Falling back to GroqProvider."
        )
        provider_class = GroqProvider

    provider = provider_class()
    print(f"[get_llm_provider] Using LLM provider: {provider_class.__name__}")
    return provider


def parse_json_response(text: str) -> dict:
    """
    Robustly parse a JSON object from LLM-generated text.

    Tries the following strategies in order:
        1. Direct JSON parse of the entire text.
        2. Extract from markdown code blocks (```json ... ``` or ``` ... ```).
        3. Find the first '{' and last '}' and parse that substring.

    Args:
        text: Raw text output from an LLM.

    Returns:
        Parsed dict on success, or an empty dict if all strategies fail.
    """
    if not text or not text.strip():
        return {}

    text = text.strip()

    # Strategy 1: Direct parse
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: Extract from markdown code blocks
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            result = json.loads(match.strip())
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, TypeError):
            continue

    # Strategy 3: Find first { and last } and try to parse
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, TypeError):
            pass

    print(f"[parse_json_response] Failed to parse JSON from text: {text[:100]}...")
    return {}


if __name__ == "__main__":
    print("=" * 60)
    print("SoulSpace LLM Provider — Smoke Test")
    print("=" * 60)

    # Test factory
    provider = get_llm_provider()
    print(f"Provider type: {type(provider).__name__}")

    # Test JSON parser
    print("\n--- Testing parse_json_response ---")

    # Direct JSON
    raw1 = '{"sentiment": "positive", "score": 0.85}'
    print(f"Direct JSON:    {parse_json_response(raw1)}")

    # Markdown-wrapped JSON
    raw2 = '```json\n{"emotion": "happy", "intensity": 0.9}\n```'
    print(f"Markdown JSON:  {parse_json_response(raw2)}")

    # Surrounded by extra text
    raw3 = 'Here is the result: {"mood": "calm"} Hope that helps!'
    print(f"Embedded JSON:  {parse_json_response(raw3)}")

    # Invalid
    raw4 = "Sorry, I cannot process that."
    print(f"Invalid text:   {parse_json_response(raw4)}")

    # Test generation (only if API key is available)
    print("\n--- Testing LLM Generation ---")
    test_prompt = (
        'Analyze this journal entry and respond with JSON containing '
        '"sentiment" and "emotion" keys: "I had a wonderful day at the park."'
    )
    result = provider.generate(test_prompt)
    if result:
        print(f"Raw response:   {result[:200]}")
        parsed = parse_json_response(result)
        print(f"Parsed result:  {parsed}")
    else:
        print("No response received (check API key / provider config).")

    print("\nDone.")
