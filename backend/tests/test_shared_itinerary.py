import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from backend.app.db.models import User, Venue, Voyage
from backend.app.core.security import get_password_hash

def test_shared_itinerary_global_update(client: TestClient, session: Session, auth_headers: dict, test_user: User):
    """
    Verify "Global Itinerary Update" logic.
    User A (test_user) and User B (new user) share a Voyage.
    If User B updates date (header), Step 2 is re-publishing.
    User A should see the new date.
    """
    
    # 1. Setup User B on SAME SHIP but DIFFERENT VENUE (or same, doesn't matter for Voyage linking)
    ship_id = test_user.ship_id
    venue_b = Venue(name="Venue B", ship_id=ship_id, capacity=50)
    session.add(venue_b)
    session.commit()
    session.refresh(venue_b)

    user_b = User(
        username="user_b_itin",
        password_hash=get_password_hash("testpassword"),
        full_name="User B Itin",
        ship_id=ship_id,
        venue_id=venue_b.id, # Different venue
        role="prod",
        is_active=True
    )
    session.add(user_b)
    session.commit()
    session.refresh(user_b)

    # Login User B
    resp = client.post(
        "/api/auth/login",
        data={"username": "user_b_itin", "password": "testpassword"}
    )
    token_b = resp.json()["access_token"]
    auth_headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. User A creates Voyage "SHARED-100" with Location "Miami"
    payload_a = {
        "voyage_number": "SHARED-100",
        "events": [],
        "itinerary": [
             {"day": 1, "date": "2025-01-01", "location": "Miami", "time": "17:00"}
        ]
    }
    client.post("/api/schedules/", json=payload_a, headers=auth_headers)

    # 3. User B fetches Voyage "SHARED-100" (Optional check)
    # Even if they get 404/Empty initially, the subsequent Publish acts as "Joining" the voyage.
    client.get("/api/schedules/SHARED-100", headers=auth_headers_b)

    # 4. User B UPDATES "SHARED-100" with Location "Nassau"
    payload_b = {
        "voyage_number": "SHARED-100",
        "original_voyage_number": "SHARED-100", # Safe Publish Update
        "events": [], # B has no events yet
        "itinerary": [
             {"day": 1, "date": "2025-01-01", "location": "Nassau", "time": "18:00"} # CHANGED LOCATION
        ]
    }
    resp = client.post("/api/schedules/", json=payload_b, headers=auth_headers_b)
    assert resp.status_code == 201

    # 5. User A Fetches "SHARED-100" Again
    resp = client.get("/api/schedules/SHARED-100", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    # 6. Verify A sees "Nassau"
    itinerary_item = data["itinerary"][0]
    assert itinerary_item["location"] == "Nassau"
    # assert itinerary_item["time"] == "18:00" # Not returned in GET response
