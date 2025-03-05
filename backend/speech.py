import io
import os
import base64
import requests
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import gtts

router = APIRouter()

# Google API Key (Consider using an environment variable for security)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBIS4jpx3o9zVkKgxEIoDX6yrz1XqKOsLg")

class SpeechInput(BaseModel):
    audio_base64: str

class ChatQuery(BaseModel):
    query: str
    # Add a force_telugu flag that defaults to True
    force_telugu: bool = True

def decode_base64_audio(audio_base64):
    """Decode base64-encoded audio data and save it as a temporary WAV file."""
    try:
        audio_data = base64.b64decode(audio_base64)
        temp_audio_path = "temp_audio.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_data)
        return temp_audio_path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"🚨 Audio decoding error: {str(e)}")

def transcribe_with_google_speech(audio_file_path, language_code="te-IN"):
    """
    Transcribe audio using Google Speech-to-Text REST API.
    Always uses Telugu as the primary language.
    """
    try:
        # Read the audio file
        with open(audio_file_path, "rb") as audio_file:
            audio_content = base64.b64encode(audio_file.read()).decode("utf-8")

        # Prepare the request to Google Speech API
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={GOOGLE_API_KEY}"
        body = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": language_code,  # Default to Telugu
                "alternativeLanguageCodes": ["en-US"]  # Also accept English
            },
            "audio": {
                "content": audio_content
            }
        }

        # Send the request
        response = requests.post(url, json=body)
        
        if response.status_code != 200:
            # If Telugu fails, try English as a fallback
            if language_code == "te-IN":
                return transcribe_with_google_speech(audio_file_path, "en-US")
            raise HTTPException(
                status_code=500, 
                detail=f"Google Speech API error: {response.status_code}: {response.text}"
            )
        
        result = response.json()
        
        # Extract transcript
        if "results" in result and len(result["results"]) > 0:
            transcript = result["results"][0]["alternatives"][0]["transcript"]
            return transcript
        else:
            # If no Telugu detected, try English as fallback
            if language_code == "te-IN":
                return transcribe_with_google_speech(audio_file_path, "en-US")
            return "No speech detected"
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 Speech-to-text error: {str(e)}")

def generate_speech_with_gtts(text, language="te"):
    """
    Generate speech using gTTS (Google Text-to-Speech) library
    Always use Telugu for output.
    """
    try:
        # Create a BytesIO object to store the audio
        audio_buffer = io.BytesIO()
        
        # Generate the audio
        tts = gtts.gTTS(text=text, lang=language, slow=False)
        tts.write_to_fp(audio_buffer)
        
        # Get the audio content and encode to base64
        audio_buffer.seek(0)
        audio_content = audio_buffer.read()
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        return audio_base64
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 Text-to-speech error: {str(e)}")

@router.post("/speech-to-text")
def speech_to_text(audio: SpeechInput):
    """
    Convert speech (audio) to text.
    Always attempts to recognize as Telugu first.
    """
    # Process the audio file
    audio_path = decode_base64_audio(audio.audio_base64)
    # Try to recognize as Telugu first
    recognized_text = transcribe_with_google_speech(audio_path, "te-IN")
    
    return {"text": recognized_text}

@router.post("/text-to-speech")
def text_to_speech(chat_response: ChatQuery):
    """
    Convert text to speech and return base64-encoded audio.
    Always generates Telugu speech.
    """
    # Generate Telugu speech
    encoded_audio = generate_speech_with_gtts(chat_response.query, language="te")
    return {"audio_base64": encoded_audio}

# Alternative implementation for file upload if needed
@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Accept audio file upload and transcribe it.
    Always attempts to recognize as Telugu first.
    """
    try:
        # Save the uploaded file
        temp_file_path = f"temp_upload_{file.filename}"
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Try to recognize as Telugu first
        recognized_text = transcribe_with_google_speech(temp_file_path, "te-IN")
        
        # Clean up
        os.remove(temp_file_path)
        
        return {"text": recognized_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 File upload error: {str(e)}")