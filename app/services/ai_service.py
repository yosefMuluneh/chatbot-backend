import requests
import logging
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HF_API_KEY = os.getenv("HF_API_KEY")
MODELS = {
    "blenderbot": "facebook/blenderbot-400M-distill",  # Light option
    "blenderbot-smart": "facebook/blenderbot-1B-distill"  # Smart option
}

def get_ai_response(prompt: str, model_name: str = "blenderbot") -> str:
    if not HF_API_KEY:
        logger.warning("API key missing, using fallback")
        return "No API key set—can’t chat right now!"
    
    if model_name not in MODELS:
        logger.warning(f"Invalid model {model_name}, defaulting to blenderbot")
        model_name = "blenderbot"
    
    API_URL = f"https://api-inference.huggingface.co/models/{MODELS[model_name]}"
    HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

    try:
        # BlenderBot models use "User: ... Bot:" format
        inputs = f"User: {prompt}\nBot:"

        payload = {
            "inputs": inputs,
            "parameters": {
                "max_length": 50,
                "temperature": 0.7,
                "top_k": 50,
                "top_p": 0.9,
                "repetition_penalty": 1.2  # Reduce repetition
            }
        }
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        generated_text = response.json()[0]["generated_text"]
        logger.info(f"Raw {model_name} output: {generated_text}")  # Debug raw response

        # Clean response (same for both BlenderBot models)
        bot_start = generated_text.find("Bot:") + 4
        clean_response = generated_text[bot_start:].strip() if bot_start > 3 else generated_text.strip()

        if not clean_response or clean_response == prompt:
            return "I’m stumped—try again?"

        prompt_lower = prompt.lower()
        if prompt_lower in ["hi", "hello", "hey"]:
            return "Hey there! What’s up?"
        if "weather" in prompt_lower:
            return "Can’t check the skies, but I hope it’s clear for you!"

        logger.info(f"Generated {model_name} response for prompt: {prompt}")
        return clean_response

    except Exception as e:
        logger.error(f"API error with {model_name}: {str(e)}")
        return "Oops, something broke—give me a sec to recover!"