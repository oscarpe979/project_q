from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class EventInput(BaseModel):
    title: str
    start: datetime
    end: datetime
    color: Optional[str] = None
    time_display: Optional[str] = None
    notes: Optional[str] = None
    type: Optional[str] = None

class ItineraryInput(BaseModel):
    day: int
    date: str # YYYY-MM-DD
    location: str
    time: Optional[str] = None # "7:00 am - 4:30 pm"
    arrival: Optional[str] = None
    departure: Optional[str] = None
    
class OtherVenueShowInput(BaseModel):
    venue: str
    date: str
    title: str
    time: str

class PublishScheduleRequest(BaseModel):
    voyage_number: str
    original_voyage_number: Optional[str] = None
    events: List[EventInput]
    itinerary: List[ItineraryInput]
    other_venue_shows: Optional[List[OtherVenueShowInput]] = None
