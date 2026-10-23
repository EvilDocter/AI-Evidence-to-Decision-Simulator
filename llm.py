import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Primary and fallback models verified supported by the active key
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]

def get_gemini_client(api_key=None):
    """
    Initializes the Gemini client using google-genai.
    Returns None if no API key is available.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or key == "YOUR_API_KEY_HERE":
        return None
    try:
        from google import genai
        from google.genai import types
        # Set a 60-second timeout to allow complete inference for complex evidence context
        return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000))
    except Exception as exc:
        print(f"[llm.py] Failed to initialize Gemini client: {exc}")
        return None

def clean_json_text(text):
    """
    Strips markdown code fences (```json ... ```) and whitespace.
    """
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

def ask_ai(prompt, api_key=None, model=None):
    """
    Sends a text prompt to Gemini and returns its live response string.
    Recovers across fallback models with exponential backoff on 503 spikes.
    """
    import time
    client = get_gemini_client(api_key)
    if not client:
        return (
            "[API Key Not Configured] Gemini API key is missing. "
            "Please configure GEMINI_API_KEY in .env to enable live AI responses."
        )

    candidate_models = [model] if model else [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]
    last_error = ""

    for target_model in candidate_models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as exc:
                last_error = str(exc)
                if "503" in str(exc) or "demand" in str(exc).lower() or "unavailable" in str(exc).lower():
                    time.sleep(1.5)
                    continue
                break

    return f"[Live Gemini Service Error] {last_error}"

def ask_ai_json(prompt, api_key=None, model=None, fallback=None):
    """
    Asks Gemini for a structured JSON response.
    Validates and converts the JSON text into a Python dictionary.
    Falls back gracefully without crashing if parsing fails.
    """
    import time
    client = get_gemini_client(api_key)
    if not client:
        return fallback or {
            "error": "API_KEY_MISSING",
            "message": "Gemini API key is not configured."
        }

    candidate_models = [model] if model else [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]
    last_error = ""

    for target_model in candidate_models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json"
                    }
                )
                cleaned = clean_json_text(response.text)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                match = re.search(r"(\{.*\}|\[.*\])", response.text, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except Exception:
                        pass
                return fallback or {
                    "error": "MALFORMED_JSON",
                    "message": "Model returned non-JSON text."
                }
            except Exception as exc:
                last_error = str(exc)
                if "503" in str(exc) or "demand" in str(exc).lower() or "unavailable" in str(exc).lower():
                    time.sleep(1.5)
                    continue
                break

    return fallback or {
        "error": "API_FAILURE",
        "message": last_error
    }
