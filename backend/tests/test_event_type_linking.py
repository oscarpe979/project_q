import pytest
from sqlmodel import Session, select
from backend.app.db.models import EventType, ScheduleItem, Voyage

def test_publish_schedule_links_event_type(client, auth_headers, session):
    # 1. Seed Event Types
    game_type = EventType(name="game", default_duration_minutes=45, default_color="#f3b344")
    other_type = EventType(name="other", default_duration_minutes=60, default_color="#cccccc")
    session.add(game_type)
    session.add(other_type)
    session.commit()
    session.refresh(game_type)
    
    # 2. Prepare Payload
    payload = {
        "voyage_number": "VY-TEST-LINK",
        "events": [
            {
                "title": "Test Game",
                "start": "2025-01-01T20:00:00",
                "end": "2025-01-01T21:00:00",
                "type": "game"  # This should trigger lookup
            },
            {
                "title": "Unknown Event",
                "start": "2025-01-01T22:00:00",
                "end": "2025-01-01T23:00:00",
                "type": "unknown_thing"  # Should fallback to 'other' or None (depending on logic) -> Logic is fallback to 'other'
            },
            {
                "title": "Colorless Game",
                "start": "2025-01-01T21:00:00",
                "end": "2025-01-01T22:00:00",
                "type": "game",
                "color": None # Should inherit #f3b344
            }
        ],
        "itinerary": [
            {"day": 1, "date": "2025-01-01", "location": "Port A"}
        ]
    }
    
    # 3. Call API
    response = client.post("/api/schedules/", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    
    # 4. Verify DB
    voyage = session.exec(select(Voyage).where(Voyage.voyage_number == "VY-TEST-LINK")).first()
    assert voyage is not None
    
    items = session.exec(select(ScheduleItem).where(ScheduleItem.voyage_id == voyage.id)).all()
    assert len(items) == 3
    
    # Sort items to verify specific ones
    # "Test Game" should be linked to game_type
    game_item = next(i for i in items if i.title == "Test Game")
    assert game_item.event_type_id == game_type.id
    
    # "Unknown Event" should be linked to other_type (based on fallback logic I implemented)
    unknown_item = next(i for i in items if i.title == "Unknown Event")
    assert unknown_item.event_type_id == other_type.id
    
    # "Colorless Game" should have inherited the default color
    colorless_item = next(i for i in items if i.title == "Colorless Game")
    assert colorless_item.event_type_id == game_type.id
    assert colorless_item.color == "#f3b344"
