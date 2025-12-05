from fastapi.testclient import TestClient

def test_get_schedules(client: TestClient, auth_headers: dict):
    response = client.get("/api/schedules/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
