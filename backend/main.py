import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import asyncio
import subprocess
import threading
import json

# Try to import optional dependencies
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
except ImportError:
    print("Voice dependencies not found. Voice features will be disabled.")
    VOICE_ENABLED = False

try:
    from rasa.core.agent import Agent
    from rasa.core.tracker_store import InMemoryTrackerStore
    from rasa.core.lock_store import InMemoryLockStore
    RASA_ENABLED = True
except ImportError:
    print("Rasa not found. Using fallback responses.")
    RASA_ENABLED = False

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    session_id: str

# Use environment variables
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", 8000))
RASA_MODEL_PATH = os.getenv("RASA_MODEL_PATH", "./rasa_model/models")

# Load Rasa model if available
if RASA_ENABLED:
    try:
        tracker_store = InMemoryTrackerStore(domain=None)
        lock_store = InMemoryLockStore()
        agent = Agent.load(RASA_MODEL_PATH, tracker_store=tracker_store, lock_store=lock_store)
    except Exception as e:
        print(f"Error loading Rasa model: {str(e)}")
        print(f"Make sure you have trained a model and it's located at {RASA_MODEL_PATH}")
        RASA_ENABLED = False

# Fallback responses
FALLBACK_RESPONSES = {
    "greet": "Hello! How can I help you today?",
    "goodbye": "Goodbye! Have a great day!",
    "default": "I'm sorry, I didn't understand that. Could you please rephrase?"
}

@app.get("/")
async def root():
    return {"message": "Hello, I'm STEVE!"}

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    if RASA_ENABLED:
        response = await agent.handle_text(chat_message.message, sender_id=chat_message.session_id)
        return {"response": response[0]["text"] if response else FALLBACK_RESPONSES["default"]}
    else:
        # Simple keyword-based fallback
        if "hello" in chat_message.message.lower():
            return {"response": FALLBACK_RESPONSES["greet"]}
        elif "bye" in chat_message.message.lower():
            return {"response": FALLBACK_RESPONSES["goodbye"]}
        else:
            return {"response": FALLBACK_RESPONSES["default"]}

@app.get("/intents")
async def get_intents():
    if RASA_ENABLED:
        domain = agent.domain
        intents = list(domain.intents)
        return {"intents": intents}
    else:
        return {"intents": list(FALLBACK_RESPONSES.keys())}

if VOICE_ENABLED:
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    def listen_for_speech():
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that.")
                return None
            except sr.RequestError:
                print("Sorry, there was an error with the speech recognition service.")
                return None

    def speak(text):
        print(f"STEVE: {text}")
        engine.say(text)
        engine.runAndWait()

    def run_voice_assistant():
        try:
            speak("Hello, I'm STEVE. How can I help you?")
            
            while True:
                try:
                    user_input = listen_for_speech()
                    if user_input:
                        response = asyncio.run(chat(ChatMessage(message=user_input, session_id="voice")))
                        speak(response["response"])
                except Exception as e:
                    print(f"Error in voice assistant loop: {str(e)}")
                    speak("I'm sorry, I encountered an error. Please try again.")
        except Exception as e:
            print(f"Error initializing voice assistant: {str(e)}")
            print("Voice assistant functionality is not available.")

def run_fastapi():
    uvicorn.run(app, host=API_HOST, port=API_PORT)

if __name__ == "__main__":
    # Start the FastAPI server in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.start()

    if VOICE_ENABLED:
        try:
            # Start the voice assistant in the main thread
            run_voice_assistant()
        except Exception as e:
            print(f"Error starting voice assistant: {str(e)}")
            print("Running in API-only mode.")
    else:
        print("Running in API-only mode (voice features disabled).")
    
    # Keep the main thread alive
    fastapi_thread.join()