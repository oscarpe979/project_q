
import pytest
from sqlmodel import Session, select
from datetime import date, datetime
from backend.app.services.search import SearchService
from backend.app.db.models import Voyage, ScheduleItem, VenueSchedule, Ship, Venue, EventType

def create_test_dependencies(session: Session):
    ship = Ship(name="Test Ship", code="TS", ship_class="Test")
    session.add(ship)
    session.commit()
    
    venue = Venue(name="Test Venue", ship_id=ship.id, capacity=100)
    session.add(venue)
    session.commit()
    
    return ship, venue

def test_fuzzy_search_short_token_exclusion(session: Session):
    """
    Regression Test: Ensure that searching for "install" does NOT match short tokens like "in".
    It SHOULD match "installation".
    """
    ship, venue = create_test_dependencies(session)
    venue_id = venue.id
    
    # 1. Setup: Create voyages
    # Voyage A: Has "installation" in notes -> Should match "install"
    voyage_a = Voyage(voyage_number="A100", start_date=date(2025, 1, 1), end_date=date(2025, 1, 7), ship_id=ship.id)
    session.add(voyage_a)
    
    # Voyage B: Has " in " in notes -> Should NOT match "install"
    voyage_b = Voyage(voyage_number="B200", start_date=date(2025, 2, 1), end_date=date(2025, 2, 7), ship_id=ship.id)
    session.add(voyage_b)
    
    session.commit()
    session.refresh(voyage_a)
    session.refresh(voyage_b)
    
    # Link to venue
    session.add(VenueSchedule(venue_id=venue_id, voyage_id=voyage_a.id))
    session.add(VenueSchedule(venue_id=venue_id, voyage_id=voyage_b.id))
    
    # Add items with text
    item_a = ScheduleItem(
        voyage_id=voyage_a.id, 
        venue_id=venue_id,
        title="Setup",
        notes="Complete installation of equipment", # Contains "installation"
        date=date(2025, 1, 2),
        start_time=datetime(2025, 1, 2, 10, 0),
        end_time=datetime(2025, 1, 2, 11, 0)
    )
    session.add(item_a)
    
    item_b = ScheduleItem(
        voyage_id=voyage_b.id, 
        venue_id=venue_id,
        title="Meeting",
        notes="Check in with team", # Contains "in"
        date=date(2025, 2, 2),
        start_time=datetime(2025, 2, 2, 10, 0),
        end_time=datetime(2025, 2, 2, 11, 0)
    )
    session.add(item_b)
    
    session.commit()
    
    # 2. Execute Search
    service = SearchService(session)
    results = service.search_schedules("install", venue_id=venue_id)
    
    # 3. Assertions
    result_ids = [v.id for v in results]
    
    assert voyage_a.id in result_ids, "Should match 'installation'"
    assert voyage_b.id not in result_ids, "Should NOT match 'in' for query 'install'"

def test_fuzzy_search_typo_tolerance(session: Session):
    """
    Verify fuzzy matching handles typos like 'Tokio' -> 'Tokyo'.
    """
    ship, venue = create_test_dependencies(session)
    venue_id = venue.id
    
    voyage = Voyage(voyage_number="T100", start_date=date(2025, 1, 1), end_date=date(2025, 1, 7), ship_id=ship.id)
    session.add(voyage)
    session.commit()
    session.refresh(voyage)
    
    session.add(VenueSchedule(venue_id=venue_id, voyage_id=voyage.id))
    
    # Add item with "Tokyo"
    session.add(ScheduleItem(
        voyage_id=voyage.id,
        venue_id=venue_id,
        title="Port Visit",
        notes="Arrive in Tokyo",
        date=date(2025, 1, 1),
        start_time=datetime(2025, 1, 1, 8, 0),
        end_time=datetime(2025, 1, 1, 18, 0)
    ))
    session.commit()
    
    service = SearchService(session)
    
    # Search for "Tokio"
    results = service.search_schedules("Tokio", venue_id=venue_id)
    assert len(results) == 1
    assert results[0].id == voyage.id

def test_pagination_exact_boundary(session: Session):
    ship, unique_venue = create_test_dependencies(session)
    # Create 21 voyages
    # V0 to V20.
    # Voyage numbers: V001...V021
    from backend.app.db.models import Voyage, VenueSchedule
    from datetime import datetime, timedelta
    
    voyages = []
    for i in range(21):
        v = Voyage(
            ship_id=1, 
            voyage_number=f"V{i:03d}", # V000 to V020
            start_date=datetime.now().date(),
            end_date=datetime.now().date(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(v)
        voyages.append(v)
    session.commit()
    
    for v in voyages:
        vs = VenueSchedule(venue_id=unique_venue.id, voyage_id=v.id)
        session.add(vs)
    session.commit()
    
    service = SearchService(session)
    
    # Page 1: Skip 0, Limit 20. Should get 20 items.
    # Order desc: V020 ... V001
    results_p1 = service.search_schedules("", unique_venue.id, skip=0, limit=20)
    assert len(results_p1) == 20
    assert results_p1[0].voyage_number == "V020"
    assert results_p1[19].voyage_number == "V001"
    
    # Page 2: Skip 20, Limit 20. Should get 1 item (V000).
    results_p2 = service.search_schedules("", unique_venue.id, skip=20, limit=20)
    assert len(results_p2) == 1
    assert results_p2[0].voyage_number == "V000"
