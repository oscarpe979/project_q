from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import io

 

# Re-writing the test to be more robust with dependency override pattern
from backend.app.main import app
from backend.app.core.dependencies import get_genai_parser

def test_upload_valid_file_robust(client: TestClient, auth_headers: dict):
    mock_parser = AsyncMock()
    mock_parser.parse_cd_grid.return_value = {
        "events": [{"title": "Mock Event", "start": "2023-10-27T10:00:00", "end": "2023-10-27T11:00:00"}],
        "itinerary": []
    }
    
    app.dependency_overrides[get_genai_parser] = lambda: mock_parser
    
    file_content = b"dummy content"
    response = client.post(
        "/api/upload/cd-grid",
        files={"file": ("test_schedule.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers
    )
    
    app.dependency_overrides.pop(get_genai_parser, None)
    
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert data["events"][0]["title"] == "Mock Event"
