from fastapi import APIRouter, Depends, HTTPException
from app.schemas import ChatRequest, ChatResponse, ChatSessionResponse, RenameSessionRequest
from app.services.ai_service import get_ai_response
from app.db.database import get_db
from app.models.message import ChatSession, Message
from sqlalchemy.orm import Session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/new", response_model=ChatSessionResponse)
async def create_new_chat(db: Session = Depends(get_db)):
    try:
        new_session = ChatSession()
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        logger.info(f"Created new session: {new_session.id}")
        return {"id": new_session.id, "name": new_session.name, "timestamp": new_session.timestamp.isoformat()}
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create new chat")

@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.timestamp.desc()).all()
    return [{"id": s.id, "name": s.name, "timestamp": s.timestamp.isoformat()} for s in sessions]

@router.post("/{session_id}", response_model=ChatResponse)
async def chat(session_id: int, request: ChatRequest, model: str = "blenderbot", db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    user_msg = Message(text=request.message, sender="user", session_id=session_id)
    db.add(user_msg)
    db.commit()
    ai_response = get_ai_response(request.message, model)
    bot_msg = Message(text=ai_response, sender="bot", session_id=session_id)
    db.add(bot_msg)
    db.commit()
    return ChatResponse(response=ai_response)

@router.get("/{session_id}/history")
async def get_history(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.asc()).all()
    return [{"id": m.id, "text": m.text, "sender": m.sender, "timestamp": m.timestamp.isoformat()} for m in messages]

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def rename_session(session_id: int, request: RenameSessionRequest, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        session.name = request.name
        db.commit()
        db.refresh(session)
        logger.info(f"Renamed session {session_id} to {request.name}")
        return {"id": session.id, "name": session.name, "timestamp": session.timestamp.isoformat()}
    except Exception as e:
        logger.error(f"Error renaming session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to rename session")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        db.query(Message).filter(Message.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        logger.info(f"Deleted session {session_id}")
        return {"message": f"Session {session_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.delete("/{session_id}/history")
async def clear_chat_history(session_id: int, db: Session = Depends(get_db)):
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        db.query(Message).filter(Message.session_id == session_id).delete()
        db.commit()
        logger.info(f"Cleared history for session {session_id}")
        return {"message": f"History for session {session_id} cleared"}
    except Exception as e:
        logger.error(f"Error clearing history for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")