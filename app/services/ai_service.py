import requests
import logging
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from app.models.message import Message

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODELS = {
    "gemini-1.5-flash": "gemini-1.5-flash",
    "gemini-2.0-flash": "gemini-2.0-flash"
}


def get_ai_response(prompt: str, model_name: str = "gemini-1.5-flash", session_id: int = None, db: Session = None) -> str:
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key missing, using fallback")
        return "No API key set—can’t chat right now!"
    
    if model_name not in MODELS:
        logger.warning(f"Invalid model {model_name}, defaulting to gemini-1.5-flash")
        model_name = "gemini-1.5-flash"
    
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELS[model_name]}:generateContent?key={GEMINI_API_KEY}"
    HEADERS = {
        "Content-Type": "application/json"
    }

    # Build conversation history from the database if session_id and db are provided
    conversation_history = []
    if session_id and db:
        messages = (db.query(Message)
                    .filter(Message.session_id == session_id)
                    .order_by(Message.timestamp.asc())
                    .all())
        for msg in messages:
            role = "user" if msg.sender == "user" else "model"
            conversation_history.append({
                "role": role,
                "parts": [{"text": msg.text}]
            })

    # Add the current user prompt to the history
    conversation_history.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    try:
        payload = {
            "contents": conversation_history,
            "generationConfig": {
                "maxOutputTokens": 500,
                "temperature": 0.7,
                "topP": 0.9,
                "topK": 50
            }
        }
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        generated_text = response.json()
        logger.info(f"Raw {model_name} output: {generated_text}")

        # Extract the raw response
        content = generated_text["candidates"][0]["content"]["parts"][0]["text"]
        
        # Clean the response: remove Markdown symbols and preserve paragraph structure
        cleaned_content = content.replace("**", "").replace("*", "").strip()
        # Split by double newlines to preserve paragraphs, then join with single newlines
        paragraphs = [p.strip() for p in cleaned_content.split("\n\n") if p.strip()]
        cleaned_content = "\n".join(paragraphs)

        logger.info(f"Generated {model_name} response for prompt: {prompt} in session {session_id}")
        return cleaned_content

    except Exception as e:
        logger.error(f"API error with {model_name} for session {session_id}: {str(e)}")
        return "Oops, something broke—give me a sec to recover!"