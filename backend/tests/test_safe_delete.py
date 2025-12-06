import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from backend.app.db.models import User, Venue, Voyage, VenueSchedule, ScheduleItem
from backend.app.core.security import get_password_hash

def test_safe_delete_shared_schedule(client: TestClient, session: Session, auth_headers: dict, test_user: User):
    """
    Verify "Last Venue Standing" logic.
    User A (default test_user) and User B (new) both use Voyage "900".
    """
    
    # 1. Setup User B and Venue B
    ship_id = test_user.ship_id
    venue_b = Venue(name="Venue B", ship_id=ship_id, capacity=50)
    session.add(venue_b)
    session.commit()
    session.refresh(venue_b)

    user_b = User(
        username="user_b",
        password_hash=get_password_hash("testpassword"),
        full_name="User B",
        ship_id=ship_id,
        venue_id=venue_b.id,
        role="prod",
        is_active=True
    )
    session.add(user_b)
    session.commit()
    session.refresh(user_b)

    # Login User B
    resp = client.post(
        "/api/auth/login",
        data={"username": "user_b", "password": "testpassword"}
    )
    token_b = resp.json()["access_token"]
    auth_headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. User A creates Voyage "900" with some events
    payload = {
        "voyage_number": "900",
        "events": [
            {"title": "Event A", "start": "2025-01-01T10:00:00", "end": "2025-01-01T11:00:00", "type": "show"}
        ],
        "itinerary": [
             {"day": 1, "date": "2025-01-01", "location": "Miami", "time": "17:00"}
        ]
    }
    client.post("/api/schedules/", json=payload, headers=auth_headers)

    # Verify Voyage exists and link exists for A
    voyage = session.exec(select(Voyage).where(Voyage.voyage_number == "900")).first()
    assert voyage is not None
    link_a = session.exec(select(VenueSchedule).where(VenueSchedule.venue_id == test_user.venue_id, VenueSchedule.voyage_id == voyage.id)).first()
    assert link_a is not None

    # 3. User B "joins" Voyage "900" (Updates it/Publishes to it)
    # This should create a VenueSchedule link for Venue B
    payload_b = {
        "voyage_number": "900",
        "original_voyage_number": "900", # Safe Publish Update
        "events": [
            {"title": "Event B", "start": "2025-01-01T12:00:00", "end": "2025-01-01T13:00:00", "type": "show"}
        ],
        "itinerary": [] # Itinerary remains from A (shared)
    }
    client.post("/api/schedules/", json=payload_b, headers=auth_headers_b)

    # Verify link exists for B
    link_b = session.exec(select(VenueSchedule).where(VenueSchedule.venue_id == venue_b.id, VenueSchedule.voyage_id == voyage.id)).first()
    assert link_b is not None

    # Verify there are 2 events total (one for A, one for B)?
    # Actually ScheduleItem table stores events.
    items = session.exec(select(ScheduleItem).where(ScheduleItem.voyage_id == voyage.id)).all()
    assert len(items) == 2

    # 4. User A Deletes "900"
    resp = client.delete("/api/schedules/900", headers=auth_headers)
    assert resp.status_code == 200

    # 5. Check State (Partial Deletion)
    session.expire_all() # Refresh logic
    
    # Voyage should STILL EXIST (protected by B)
    voyage_check = session.exec(select(Voyage).where(Voyage.voyage_number == "900")).first()
    assert voyage_check is not None

    # Venue A Link GONE
    link_a_check = session.exec(select(VenueSchedule).where(VenueSchedule.venue_id == test_user.venue_id, VenueSchedule.voyage_id == voyage.id)).first()
    assert link_a_check is None

    # Venue B Link EXISTS
    link_b_check = session.exec(select(VenueSchedule).where(VenueSchedule.venue_id == venue_b.id, VenueSchedule.voyage_id == voyage.id)).first()
    assert link_b_check is not None

    # Venue A Events GONE
    items_a = session.exec(select(ScheduleItem).where(ScheduleItem.voyage_id == voyage.id, ScheduleItem.venue_id == test_user.venue_id)).all()
    assert len(items_a) == 0

    # Venue B Events EXIST
    items_b = session.exec(select(ScheduleItem).where(ScheduleItem.voyage_id == voyage.id, ScheduleItem.venue_id == venue_b.id)).all()
    assert len(items_b) == 1

    # 6. User B Deletes "900" (Final Cleanup)
    resp = client.delete("/api/schedules/900", headers=auth_headers_b)
    assert resp.status_code == 200

    # 7. Check State (Full Deletion)
    session.expire_all()
    
    # Voyage GONE
    voyage_final = session.exec(select(Voyage).where(Voyage.voyage_number == "900")).first()
    assert voyage_final is None
    
    # Venue B Link GONE
    link_b_final = session.exec(select(VenueSchedule).where(VenueSchedule.venue_id == venue_b.id, VenueSchedule.voyage_id == voyage.id)).first()
    assert link_b_final is None
