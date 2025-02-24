from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.db.database import engine
from app.models.message import Base

app = FastAPI(
    title="Chatbot API",
    description="A scalable AI-powered chatbot backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])

# Create tables on startup
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Chatbot API is running"}