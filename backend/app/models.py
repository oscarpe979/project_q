from typing import Optional, List
from datetime import date, datetime, time
from sqlmodel import Field, Relationship, SQLModel

# --- Join Tables ---
class VenueCapability(SQLModel, table=True):
    venue_id: Optional[int] = Field(default=None, foreign_key="venue.id", primary_key=True)
    event_type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id", primary_key=True)

# --- Core Entities ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    full_name: str
    role: str = "scheduler"

class Ship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: str = Field(unique=True, index=True)
    
    venues: List["Venue"] = Relationship(back_populates="ship")
    voyages: List["Voyage"] = Relationship(back_populates="ship")

class Venue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ship_id: int = Field(foreign_key="ship.id")
    name: str
    capacity: int
    
    ship: Ship = Relationship(back_populates="venues")
    capabilities: List["EventType"] = Relationship(back_populates="venues", link_model=VenueCapability)
    schedule_items: List["ScheduleItem"] = Relationship(back_populates="venue")

class EventType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str # e.g., "Production Show", "Comedy"
    default_duration_minutes: int
    
    venues: List[Venue] = Relationship(back_populates="capabilities", link_model=VenueCapability)
    schedule_items: List["ScheduleItem"] = Relationship(back_populates="event_type")

# --- Voyage & Schedule ---

class Voyage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ship_id: int = Field(foreign_key="ship.id")
    start_date: date
    end_date: date
    voyage_number: str = Field(unique=True, index=True) # e.g., "WN-2023-11-23"
    
    ship: Ship = Relationship(back_populates="voyages")
    itineraries: List["VoyageItinerary"] = Relationship(back_populates="voyage")
    schedule_items: List["ScheduleItem"] = Relationship(back_populates="voyage")

class VoyageItinerary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    voyage_id: int = Field(foreign_key="voyage.id")
    day_number: int
    date: date
    location: str
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    
    voyage: Voyage = Relationship(back_populates="itineraries")

class ScheduleItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    voyage_id: int = Field(foreign_key="voyage.id")
    venue_id: int = Field(foreign_key="venue.id")
    event_type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id")
    
    title: str
    start_time: datetime
    end_time: datetime
    type: str # "Show", "Setup", "Strike", "Rehearsal", "Cast Install", "Cast Reblock"
    notes: Optional[str] = None
    
    voyage: Voyage = Relationship(back_populates="schedule_items")
    venue: Venue = Relationship(back_populates="schedule_items")
    event_type: Optional[EventType] = Relationship(back_populates="schedule_items")
