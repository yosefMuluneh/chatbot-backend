import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.db.database import get_db
from app.models.message import Base, ChatSession, Message

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency to use test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)

# Setup and teardown for tests
@pytest.fixture(scope="function", autouse=True)
def setup_database():
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    # Verify table creation
    inspector = inspect(engine)
    assert "chat_sessions" in inspector.get_table_names(), "chat_sessions table not created"
    assert "messages" in inspector.get_table_names(), "messages table not created"
    yield
    # Drop tables after each test
    Base.metadata.drop_all(bind=engine)

# Test POST /chat/new
@pytest.mark.asyncio
async def test_create_new_chat():
    response = client.post("/chat/new")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "timestamp" in data
    assert data["name"] == "New Chat"

# Test GET /chat/sessions
@pytest.mark.asyncio
async def test_get_sessions():
    client.post("/chat/new")
    response = client.get("/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "name" in data[0]
    assert "timestamp" in data[0]

# Test POST /chat/{session_id}
@pytest.mark.asyncio
async def test_send_message():
    new_session = client.post("/chat/new").json()
    session_id = new_session["id"]
    message_data = {"message": "Hello, world!"}
    response = client.post(f"/chat/{session_id}", json=message_data)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)

# Test GET /chat/{session_id}/history
@pytest.mark.asyncio
async def test_get_history():
    new_session = client.post("/chat/new").json()
    session_id = new_session["id"]
    client.post(f"/chat/{session_id}", json={"message": "Test message"})
    response = client.get(f"/chat/{session_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # User message + bot response
    assert "id" in data[0]
    assert "text" in data[0]
    assert "sender" in data[0]
    assert "timestamp" in data[0]

# Test PUT /chat/sessions/{session_id}
@pytest.mark.asyncio
async def test_rename_session():
    new_session = client.post("/chat/new").json()
    session_id = new_session["id"]
    rename_data = {"name": "Renamed Chat"}
    response = client.put(f"/chat/sessions/{session_id}", json=rename_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Renamed Chat"
    assert data["id"] == session_id

# Test DELETE /chat/sessions/{session_id}
@pytest.mark.asyncio
async def test_delete_session():
    new_session = client.post("/chat/new").json()
    session_id = new_session["id"]
    response = client.delete(f"/chat/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"Session {session_id} deleted"
    sessions = client.get("/chat/sessions").json()
    assert not any(session["id"] == session_id for session in sessions)

# Test DELETE /chat/{session_id}/history
@pytest.mark.asyncio
async def test_clear_chat_history():
    new_session = client.post("/chat/new").json()
    session_id = new_session["id"]
    client.post(f"/chat/{session_id}", json={"message": "Test message"})
    response = client.delete(f"/chat/{session_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"History for session {session_id} cleared"
    history = client.get(f"/chat/{session_id}/history").json()
    assert len(history) == 0

# Test invalid session_id (404)
@pytest.mark.asyncio
async def test_invalid_session_id():
    invalid_id = 9999
    response = client.get(f"/chat/{invalid_id}/history")
    assert response.status_code == 404
    assert "Chat session not found" in response.json()["detail"]