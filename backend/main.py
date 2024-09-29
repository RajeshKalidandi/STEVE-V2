from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from rasa.core.agent import Agent
from rasa.core.interpreter import RasaNLUInterpreter
import asyncio

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

# Load Rasa model
model_path = "./rasa_model/models"
agent = Agent.load(model_path)

@app.get("/")
async def root():
    return {"message": "Hello, I'm STEVE!"}

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    response = await agent.handle_text(chat_message.message)
    return {"response": response[0]["text"] if response else "I'm not sure how to respond to that."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)