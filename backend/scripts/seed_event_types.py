from sqlmodel import Session, select
from backend.app.db.session import engine
from backend.app.db.models import EventType

def seed_event_types():
    """Seed the EventType table with standard types and colors."""
    # Standard types with colors from frontend/src/utils/eventColors.ts
    STANDARD_TYPES = [
        {"name": "show", "default_duration_minutes": 45, "default_color": "#963333ff"},
        {"name": "headliner", "default_duration_minutes": 45, "default_color": "#84f0e6"},
        {"name": "game", "default_duration_minutes": 45, "default_color": "#f3b344ff"},
        {"name": "party", "default_duration_minutes": 60, "default_color": "#a5e1f8ff"},
        {"name": "movie", "default_duration_minutes": 120, "default_color": "#E1BEE7"},
        {"name": "activity", "default_duration_minutes": 60, "default_color": "#BBDEFB"},
        {"name": "music", "default_duration_minutes": 45, "default_color": "#9bfa9e"},
        {"name": "comedy", "default_duration_minutes": 45, "default_color": "#f5ff9bff"},
        {"name": "parade", "default_duration_minutes": 30, "default_color": "#b3ff51ff"},
        {"name": "backup", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "other", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "setup", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "strike", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "warm_up", "default_duration_minutes": 30, "default_color": "#A3FEFF"},
        {"name": "rehearsal", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "maintenance", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "preset", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "toptier", "default_duration_minutes": 60, "default_color": "#ff7979ff"},
        {"name": "ice_make", "default_duration_minutes": 60, "default_color": "#dcf0fa"},
        {"name": "cast_install", "default_duration_minutes": 60, "default_color": "#e3ded3"},
        {"name": "doors", "default_duration_minutes": 15, "default_color": "#000000"},
    ]

    print(f"Seeding {len(STANDARD_TYPES)} event types...")
    
    with Session(engine) as session:
        for type_data in STANDARD_TYPES:
            # Check if exists
            existing = session.exec(select(EventType).where(EventType.name == type_data["name"])).first()
            if not existing:
                print(f"Creating: {type_data['name']}")
                event_type = EventType(**type_data)
                session.add(event_type)
            else:
                # Update defaults
                # print(f"Updating: {type_data['name']}")
                existing.default_duration_minutes = type_data["default_duration_minutes"]
                existing.default_color = type_data["default_color"]
                session.add(existing)
        
        session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    seed_event_types()
