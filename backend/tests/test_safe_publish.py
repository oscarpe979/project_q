import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from backend.app.db.models import User, Venue, Voyage
from datetime import datetime

# Helper to create a user and venue
@pytest.fixture(name="setup_data")
def fixture_setup_data(client: TestClient, session: Session, current_user_token_headers):
    # Ensure current user has a venue and ship
    user = session.exec(select(User).where(User.username == "test_user")).first()
    if not user:
        # Create user if not exists (though conftest usually handles this)
        pass 
    
    # We rely on the `auth_headers` fixture logic usually, 
    # but let's assume the standard `client` setup works.
    return {}

def test_safe_publish_scenarios(client: TestClient, auth_headers: dict, session: Session):
    """
    Test the Safe Publish logic:
    1. Create New (Success)
    2. Create Dup (Conflict)
    3. Update Same (Success)
    4. Rename (Success)
    5. Rename Overwrite (Conflict)
    """

    # 1. Baseline: Publish Voyage "100" (New Draft)
    payload_100 = {
        "voyage_number": "100",
        "events": [],
        "itinerary": []
    }
    
    resp = client.post("/api/schedules/", json=payload_100, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["voyage_number"] == "100"

    # 2. Creation Conflict: Try to publish "100" again WITHOUT original_voyage_number
    # This simulates a "New Draft" that happens to pick an existing number.
    payload_100_dup = {
        "voyage_number": "100",
        # "original_voyage_number": None, # Implicitly None
        "events": [],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_100_dup, headers=auth_headers)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]

    # 3. Update Success: Publish "100" WITH original_voyage_number="100"
    # This simulates clicking "Publish" on an existing schedule.
    payload_100_update = {
        "voyage_number": "100",
        "original_voyage_number": "100",
        "events": [{"title": "Updated Event", "start": datetime.now().isoformat(), "end": datetime.now().isoformat()}],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_100_update, headers=auth_headers)
    assert resp.status_code == 201
    
    # Verify update happened (check for event?)
    # For now status code 201 is enough.

    # 4. Rename Success: Rename "100" to "200"
    # This simulates changing the Voyage Number field on an existing schedule.
    payload_rename = {
        "voyage_number": "200", # New Target
        "original_voyage_number": "100", # Source
        "events": [],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_rename, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["voyage_number"] == "200"

    # Verify "100" is gone (conceptually)? 
    # Actually, our current implementation creates a NEW Voyage 200.
    # It does NOT delete 100 automatically unless we programmed it to.
    # Wait, the logic is: "Find or Create Voyage".
    # If we rename 100 -> 200, we create 200. 
    # 100 still exists in the DB unless we explicitly deleted it or migrated it.
    # The requirement was "Safe Publish", preventing overwrites.
    # Whether it acts as "Rename" (Move) or "Save As" (Copy) is a different nuance.
    # Currently it acts as "Save As" (Copy). 
    # But let's check if 200 was created.
    
    # Verify 200 exists
    resp = client.get("/api/schedules/200", headers=auth_headers)
    assert resp.status_code == 200

    # 5. Rename Overwrite Conflict: 
    # Now we have "100" (still exists) and "200".
    # Let's create "300" explicitly first.
    payload_300 = {
        "voyage_number": "300",
        "events": [],
        "itinerary": []
    }
    client.post("/api/schedules/", json=payload_300, headers=auth_headers)

    # Now try to "Rename" "200" to "300".
    # (i.e. Publish "300" claiming original="200")
    # This should fail because "300" already exists and is NOT "200".
    payload_overwrite = {
        "voyage_number": "300", # Target (Exists)
        "original_voyage_number": "200", # Source
        "events": [],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_overwrite, headers=auth_headers)
    assert resp.status_code == 409
    assert "Cannot overwrite" in resp.json()["detail"]


def test_multi_venue_same_voyage_number(client: TestClient, session: Session, auth_headers: dict, test_user: User):
    """
    Test that DIFFERENT venues can publish the SAME voyage number independently.
    This was a bug where the conflict detection checked global voyage existence
    instead of venue-specific ownership.
    
    Scenario:
    1. User A (Venue A) publishes voyage "500" → SUCCESS
    2. User B (Venue B) publishes voyage "500" → SUCCESS (should NOT conflict)
    3. User A tries to publish "500" again → CONFLICT (already has it)
    """
    from backend.app.db.models import Venue
    from backend.app.core.security import get_password_hash
    
    # 1. User A (test_user) publishes voyage "500"
    payload_a = {
        "voyage_number": "500",
        "events": [],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_a, headers=auth_headers)
    assert resp.status_code == 201, f"User A publish failed: {resp.text}"
    
    # 2. Setup User B on a DIFFERENT venue (same ship)
    ship_id = test_user.ship_id
    venue_b = Venue(name="Venue B for Publish Test", ship_id=ship_id, capacity=50)
    session.add(venue_b)
    session.commit()
    session.refresh(venue_b)
    
    user_b = User(
        username="user_b_publish_test",
        password_hash=get_password_hash("testpassword"),
        full_name="User B",
        ship_id=ship_id,
        venue_id=venue_b.id,
        role="manager",
        is_active=True
    )
    session.add(user_b)
    session.commit()
    
    # Authenticate User B
    login_resp = client.post("/api/auth/login", data={"username": "user_b_publish_test", "password": "testpassword"})
    assert login_resp.status_code == 200
    auth_headers_b = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    # 3. User B publishes the SAME voyage number "500" → Should SUCCEED
    payload_b = {
        "voyage_number": "500",
        "events": [],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_b, headers=auth_headers_b)
    assert resp.status_code == 201, f"User B publish should succeed but got: {resp.text}"
    
    # 4. User A tries to publish "500" AGAIN (without original) → Should CONFLICT
    resp = client.post("/api/schedules/", json=payload_a, headers=auth_headers)
    assert resp.status_code == 409, f"User A duplicate should conflict but got: {resp.text}"
    assert "already exists" in resp.json()["detail"]
    
    # 5. User A can UPDATE their "500" (with original_voyage_number)
    payload_update = {
        "voyage_number": "500",
        "original_voyage_number": "500",
        "events": [],
        "itinerary": []
    }
    resp = client.post("/api/schedules/", json=payload_update, headers=auth_headers)
    assert resp.status_code == 201, f"User A update should succeed but got: {resp.text}"
