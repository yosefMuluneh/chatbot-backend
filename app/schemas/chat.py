from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class ChatSessionResponse(BaseModel):
    id: int
    name: str
    timestamp: str

class RenameSessionRequest(BaseModel):  # New model
    name: str