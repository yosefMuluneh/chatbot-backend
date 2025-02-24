from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"  # Correct name
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="New Chat")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    text = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)