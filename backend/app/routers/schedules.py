from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timezone, time

# Helper to parse a single time string with various formats
def parse_single_time_string(t_str: Optional[str]) -> Optional[time]:
    if not t_str:
        return None
    
    t_str = t_str.strip().lower().replace("midnight", "12:00 am")
    formats = [
        "%I:%M %p",  # 07:00 am
        "%I:%M%p",   # 07:00am
        "%H:%M",     # 19:00
        "%-I:%M %p", # 7:00 am
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(t_str, fmt).time()
        except ValueError:
            continue
    return None

# Helper to parse time string "7:00 am - 4:30 pm"
def parse_port_times(time_str: Optional[str]):
    if not time_str:
        return None, None
    
    # Normalize string: lowercase, remove extra spaces
    ts = time_str.lower().strip()
    
    # Handle "Midnight" special case (often used for departure)
    if "midnight" in ts:
        # If it's a range like "7:00 am - midnight"
        parts = ts.replace('midnight', '12:00 am').split('-')
    else:
        # Split by various dash types
        parts = ts.replace('–', '-').replace('—', '-').split('-')
        
    if len(parts) != 2:
        return None, None
    
    arrival = parse_single_time_string(parts[0])
    departure = parse_single_time_string(parts[1])
    
    return arrival, departure

# Helper to format time objects back to string
def format_port_times(arrival: Optional[time], departure: Optional[time]) -> str:
    if not arrival or not departure:
        return ""
    return f"{arrival.strftime('%-I:%M %p').lower()} - {departure.strftime('%-I:%M %p').lower()}"
from backend.app.database import get_session
from backend.app.models import (
    User, Voyage, VoyageItinerary, ScheduleItem, Venue, EventType
)
from backend.app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
    responses={404: {"description": "Not found"}},
)

# --- Pydantic Models for Request Body ---

class EventInput(BaseModel):
    title: str
    start: datetime
    end: datetime
    type: str # "show", "setup", etc.
    notes: Optional[str] = None
    color: Optional[str] = None # Not stored in DB currently, but good to accept

class ItineraryInput(BaseModel):
    day: int
    date: str # YYYY-MM-DD
    location: str
    time: Optional[str] = None # "7:00 am - 4:30 pm"
    arrival: Optional[str] = None
    departure: Optional[str] = None

class PublishScheduleRequest(BaseModel):
    voyage_number: str
    events: List[EventInput]
    itinerary: List[ItineraryInput]

# --- Endpoints ---

@router.post("/", status_code=status.HTTP_201_CREATED)
def publish_schedule(
    request: PublishScheduleRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.venue_id:
        raise HTTPException(status_code=400, detail="User must be assigned to a venue to publish a schedule.")
    
    if not current_user.ship_id:
        raise HTTPException(status_code=400, detail="User must be assigned to a ship to publish a schedule.")

    # 1. Find or Create Voyage
    voyage = session.exec(select(Voyage).where(Voyage.voyage_number == request.voyage_number)).first()
    
    if not voyage:
        # Infer start/end date from itinerary if available, else use today (fallback)
        start_date = datetime.now().date()
        end_date = datetime.now().date()
        
        if request.itinerary:
            try:
                sorted_itinerary = sorted(request.itinerary, key=lambda x: x.day)
                start_date = datetime.strptime(sorted_itinerary[0].date, "%Y-%m-%d").date()
                end_date = datetime.strptime(sorted_itinerary[-1].date, "%Y-%m-%d").date()
            except ValueError:
                pass # Keep defaults if parsing fails

        voyage = Voyage(
            ship_id=current_user.ship_id,
            voyage_number=request.voyage_number,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(voyage)
        session.commit()
        session.refresh(voyage)
    else:
        voyage.updated_at = datetime.now()
        session.add(voyage)
        session.commit()

    # 2. Update Itinerary (Global for the Voyage)
    # Strategy: Delete existing for this voyage and re-insert. 
    # NOTE: This might affect other venues if they rely on the same itinerary. 
    # For now, we assume the itinerary is shared and the latest publish wins/updates it.
    # To be safe, we could check if itinerary items exist and only update if different, 
    # but deleting and re-inserting is cleaner for "publishing" the source of truth.
    
    # Check if we should update itinerary. Only if provided.
    if request.itinerary:
        existing_itineraries = session.exec(select(VoyageItinerary).where(VoyageItinerary.voyage_id == voyage.id)).all()
        for item in existing_itineraries:
            session.delete(item)
        
        for item in request.itinerary:
            if item.arrival or item.departure:
                # Use provided structured times
                arrival_time = parse_single_time_string(item.arrival)
                departure_time = parse_single_time_string(item.departure)
            else:
                # Fallback to parsing the 'time' string
                arrival_time, departure_time = parse_port_times(item.time)
            
            itinerary_entry = VoyageItinerary(
                voyage_id=voyage.id,
                day_number=item.day,
                date=datetime.strptime(item.date, "%Y-%m-%d").date(),
                location=item.location.title(),
                arrival_time=arrival_time,
                departure_time=departure_time
            )
            session.add(itinerary_entry)

    # 3. Update Schedule Items (Scoped to Venue)
    # Delete existing items for this venue and voyage
    existing_items = session.exec(
        select(ScheduleItem)
        .where(ScheduleItem.voyage_id == voyage.id)
        .where(ScheduleItem.venue_id == current_user.venue_id)
    ).all()
    
    for item in existing_items:
        session.delete(item)
        
    # Insert new items
    for event in request.events:
        # Find or create EventType? 
        # For MVP, we might just store the type string if we don't strictly enforce EventType table yet
        # But ScheduleItem requires event_type_id (Optional).
        # Let's try to find an EventType by name, if not found, maybe leave null or create?
        # Model: event_type_id is Optional.
        
        # We need to map frontend 'type' to backend 'type' field in ScheduleItem
        
        new_item = ScheduleItem(
            voyage_id=voyage.id,
            venue_id=current_user.venue_id,
            title=event.title,
            start_time=event.start,
            end_time=event.end,
            type=event.type,
            notes=event.notes
        )
        session.add(new_item)

    session.commit()
    return {"message": "Schedule published successfully", "voyage_number": voyage.voyage_number}

@router.get("/latest")
def get_latest_schedule(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.venue_id:
        raise HTTPException(status_code=400, detail="User must be assigned to a venue.")
    
    if not current_user.ship_id:
        raise HTTPException(status_code=400, detail="User must be assigned to a ship.")

    # Find most recent voyage for this ship AND venue
    # We look for the ScheduleItem with the highest ID for this venue, 
    # as items are re-inserted on publish (so higher ID = later publish).
    latest_item_id = session.exec(
        select(ScheduleItem.voyage_id)
        .where(ScheduleItem.venue_id == current_user.venue_id)
        .order_by(ScheduleItem.id.desc())
    ).first()
    
    if not latest_item_id:
        return {"events": [], "itinerary": []}
        
    voyage = session.exec(select(Voyage).where(Voyage.id == latest_item_id)).first()
    
    if not voyage:
        return {"events": [], "itinerary": []}

    # Get Itinerary
    itinerary_items = session.exec(
        select(VoyageItinerary)
        .where(VoyageItinerary.voyage_id == voyage.id)
        .order_by(VoyageItinerary.day_number)
    ).all()
    
    # Get Schedule Items for user's venue
    schedule_items = session.exec(
        select(ScheduleItem)
        .where(ScheduleItem.voyage_id == voyage.id)
        .where(ScheduleItem.venue_id == current_user.venue_id)
    ).all()
    
    # Format response
    formatted_itinerary = [
        {
            "day": item.day_number,
            "date": item.date.isoformat(),
            "location": item.location,
            "port_times": format_port_times(item.arrival_time, item.departure_time)
        }
        for item in itinerary_items
    ]
    
    formatted_events = [
        {
            "title": item.title,
            "start": item.start_time.isoformat(),
            "end": item.end_time.isoformat(),
            "type": item.type,
            "notes": item.notes
        }
        for item in schedule_items
    ]
    
    return {
        "voyage_number": voyage.voyage_number,
        "events": formatted_events,
        "itinerary": formatted_itinerary
    }

@router.delete("/{voyage_number}")
def delete_schedule(
    voyage_number: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.venue_id:
        raise HTTPException(status_code=400, detail="User must be assigned to a venue.")
        
    voyage = session.exec(select(Voyage).where(Voyage.voyage_number == voyage_number)).first()
    if not voyage:
        raise HTTPException(status_code=404, detail="Voyage not found")
        
    # Delete Schedule Items for this venue
    items_to_delete = session.exec(
        select(ScheduleItem)
        .where(ScheduleItem.voyage_id == voyage.id)
        .where(ScheduleItem.venue_id == current_user.venue_id)
    ).all()
    
    count = len(items_to_delete)
    for item in items_to_delete:
        session.delete(item)
        
    session.commit() # Commit deletion of items first to check remaining
    
    # Check if any schedule items remain for this voyage (any venue)
    remaining_items = session.exec(
        select(ScheduleItem).where(ScheduleItem.voyage_id == voyage.id)
    ).all()
    
    if not remaining_items:
        # No items left, delete the Voyage and its Itinerary
        itineraries = session.exec(
            select(VoyageItinerary).where(VoyageItinerary.voyage_id == voyage.id)
        ).all()
        for it in itineraries:
            session.delete(it)
            
        session.delete(voyage)
        session.commit()
        return {"message": f"Deleted {count} schedule items and the Voyage {voyage_number} as it is now empty."}
    
    return {"message": f"Deleted {count} schedule items for voyage {voyage_number}"}
