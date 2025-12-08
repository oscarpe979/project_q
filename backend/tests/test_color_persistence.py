from fastapi.testclient import TestClient
from datetime import datetime, timedelta

def test_publish_and_retrieve_color(client: TestClient, auth_headers: dict):
    # Data
    voyage_number = "COLOR_TEST_001"
    event_color = "#123456"
    
    payload = {
        "voyage_number": voyage_number,
        "events": [
            {
                "title": "Color Test Event",
                "start": datetime.now().isoformat(),
                "end": (datetime.now() + timedelta(hours=1)).isoformat(),
                "color": event_color
            }
        ],
        "itinerary": []
    }
    
    # 1. Publish
    response = client.post("/api/schedules/", json=payload, headers=auth_headers)
    assert response.status_code == 201, f"Publish failed: {response.text}"
    
    # 2. Retrieve
    response = client.get(f"/api/schedules/{voyage_number}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    # 3. Verify
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["color"] == event_color
    assert event["title"] == "Color Test Event"
    
    # Cleanup (Optional, but good practice if safe_delete is implemented)
    client.delete(f"/api/schedules/{voyage_number}", headers=auth_headers)
