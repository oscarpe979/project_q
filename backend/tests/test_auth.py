from fastapi.testclient import TestClient
from backend.app.db.models import User

def test_login_success(client: TestClient, test_user: User):
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.username, "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
