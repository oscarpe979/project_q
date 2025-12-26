import pytest
from sqlmodel import Session, select
from backend.app.db.models import EventType, ScheduleItem, Voyage, User, Venue, Ship
from datetime import datetime

def test_round_trip_type_persistence(client, auth_headers, session, test_user):
    # 1. Setup Data
    # Ensure standard types exist (conftest uses empty DB)
    game_type = EventType(name="game", default_duration_minutes=45, default_color="#f3b344")
    other_type = EventType(name="other", default_duration_minutes=60, default_color="#cccccc")
    session.add(game_type)
    session.add(other_type)
    session.commit()
    session.refresh(game_type)
    session.refresh(other_type)

    voyage_number = "VY-ROUND-TRIP"
    voyage = Voyage(voyage_number=voyage_number, start_date=datetime.now(), end_date=datetime.now(), ship_id=test_user.ship_id)
    session.add(voyage)
    session.commit()
    session.refresh(voyage)

    # 2. Create Initial ScheduleItem directly in DB linked to "game"
    item = ScheduleItem(
        voyage_id=voyage.id,
        venue_id=test_user.venue_id,
        event_type_id=game_type.id,
        title="Original Game",
        start_time=datetime(2025, 1, 1, 20, 0),
        end_time=datetime(2025, 1, 1, 21, 0),
        color="#f3b344"
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # 3. GET the schedule
    response = client.get(f"/api/schedules/{voyage_number}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    events = data["events"]
    assert len(events) == 1
    fetched_event = events[0]
    
    # CHECK 1: Does GET return the type?
    print(f"Fetched Event: {fetched_event}")
    if fetched_event.get("type") != "game":
        pytest.fail(f"GET failed to return type. Got: {fetched_event.get('type')}")

    # 4. POST the schedule back (simulate 'Save')
    # Use the fetching event mostly as-is
    payload = {
        "voyage_number": voyage_number,
        "events": [fetched_event], # Should include 'type': 'game'
        "itinerary": data["itinerary"]
    }
    
    response_post = client.post("/api/schedules/", json=payload, headers=auth_headers)
    assert response_post.status_code == 201

    # 5. Verify DB again
    # We might have deleted and recreated items, so fetch fresh
    items = session.exec(select(ScheduleItem).where(ScheduleItem.voyage_id == voyage.id)).all()
    assert len(items) == 1
    final_item = items[0]
    
    # CHECK 2: Is it still linked?
    assert final_item.event_type_id == game_type.id, f"Lost linkage! ID is {final_item.event_type_id}, expected {game_type.id}"
