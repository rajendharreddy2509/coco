import io
import os
import requests
import gtts
import asyncio
from fastapi import APIRouter, Response
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Load API key from environment variable
GOOGLE_API_KEY = os.getenv("google_api_key")

router = APIRouter()

# Farming Keywords (English & Telugu)
FARMING_KEYWORDS = [
    "coconut", "farming", "soil", "irrigation", "fertilizer", "diseases", "weather", "pest control",
    "నారికేళం", "వ్యవసాయం", "మట్టి", "నీటిపారుదల", "ఎరువులు", "వ్యాధులు", "వాతావరణం", "కీటకాల నియంత్రణ"
]

class Query(BaseModel):
    text: str

# Global variable to store last AI response (for speech)
last_response_text = ""


def translate_text(text, source_lang="auto", target_lang="te"):
    """Translate text using Google Translate API."""
    url = "https://translation.googleapis.com/language/translate/v2"
    payload = {
        "q": text,
        "target": target_lang,
        "source": source_lang if source_lang != "auto" else None,
        "format": "text",
        "key": GOOGLE_API_KEY
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            result = response.json()
            return result["data"]["translations"][0]["translatedText"]
        else:
            print(f"Translation error: {response.status_code}")
            return text  # Return original text if translation fails
    except Exception as e:
        print(f"Translation exception: {str(e)}")
        return text


def detect_language(text):
    """Detect language using Google Translate API."""
    url = "https://translation.googleapis.com/language/translate/v2/detect"
    payload = {
        "q": text,
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            result = response.json()
            return result["data"]["detections"][0][0]["language"]
        else:
            print(f"Language detection error: {response.status_code}")
            return "en"  # Default to English if detection fails
    except Exception as e:
        print(f"Language detection exception: {str(e)}")
        return "en"


def is_farming_related(user_query, translated_query=None):
    """Check if the query contains farming-related keywords."""
    query_lower = user_query.lower()
    
    if translated_query:
        translated_lower = translated_query.lower()
        return any(keyword in query_lower for keyword in FARMING_KEYWORDS) or \
               any(keyword in translated_lower for keyword in FARMING_KEYWORDS)
    else:
        return any(keyword in query_lower for keyword in FARMING_KEYWORDS)


def generate_ai_response(user_query):
    """Fetch AI-generated response using Google Gemini API and ensure it's in Telugu."""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": user_query}]}]}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return f"🚨 API Error: {response.status_code} - {response.text}"

        data = response.json()
        if "candidates" in data and data["candidates"]:
            ai_response = data["candidates"][0]["content"]["parts"][0].get("text", "⚠️ AI could not generate a response.")
        else:
            ai_response = "⚠️ AI Response is empty."

        # ✅ Always translate response to Telugu
        translated_response = translate_text(ai_response, source_lang="auto", target_lang="te")
        return translated_response

    except requests.exceptions.RequestException as e:
        return f"🚨 API Request Error: {str(e)}"
    except ValueError:
        return "🚨 AI Error: Invalid JSON response from API."


async def stream_ai_response(user_query):
    """Stream AI response text in chunks."""
    global last_response_text
    response_text = generate_ai_response(user_query)
    last_response_text = response_text  # Store for speech response

    async def generate_stream():
        for word in response_text.split():
            yield word + " "  # Send word-by-word for a typing effect
            await asyncio.sleep(0.1)  # Adjust speed as needed

    return StreamingResponse(generate_stream(), media_type="text/plain")


def generate_audio(text):
    """Convert AI response text to speech (Telugu) and return an audio buffer."""
    tts = gtts.gTTS(text, lang="te")
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer


@router.post("/chat")
async def chatbot_response(query: Query):
    """Handle chatbot response and store the last AI response for speech generation."""
    global last_response_text
    user_query = query.text.strip()

    # Detect language
    detected_lang = detect_language(user_query)
    
    # Translate query if needed
    if detected_lang == "en":
        translated_query = translate_text(user_query, source_lang="en", target_lang="te")
    else:
        translated_query = translate_text(user_query, source_lang="te", target_lang="en")

    # Check if query is related to farming
    if is_farming_related(user_query, translated_query):
        return await stream_ai_response(user_query)
    else:
        return StreamingResponse(iter(["⚠️ I can only answer coconut farming-related questions."]), media_type="text/plain")


@router.get("/audio")
async def get_audio():
    """Generate AI response as speech (Telugu) and stream it."""
    global last_response_text
    if not last_response_text:
        return Response(status_code=204)  # No content

    audio_buffer = generate_audio(last_response_text)
    return StreamingResponse(audio_buffer, media_type="audio/mp3")