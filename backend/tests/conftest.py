import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.app.main import app
from backend.app.db.session import get_session
from backend.app.db.models import User, Venue, Ship
from backend.app.core.security import get_password_hash

# Use in-memory SQLite for tests
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool 
)

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    # Create dependencies
    ship = Ship(code="TEST", name="Test Ship", ship_class="Oasis")
    session.add(ship)
    session.commit()
    session.refresh(ship)
    
    venue = Venue(name="Test Venue", ship_id=ship.id, capacity=100)
    session.add(venue)
    session.commit()
    session.refresh(venue)
    
    user = User(
        username="testuser",
        password_hash=get_password_hash("testpassword"),
        full_name="Test User",
        ship_id=ship.id,
        venue_id=venue.id,
        role="prod",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, test_user: User):
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
