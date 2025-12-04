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
    username: str = Field(unique=True, index=True)
    password_hash: str
    full_name: str  # Position title (e.g., "Studio B Production Manager")
    role: str  # Job codes: "admin", "spro", "prod", "view_only"
    ship_id: Optional[int] = Field(default=None, foreign_key="ship.id")
    venue_id: Optional[int] = Field(default=None, foreign_key="venue.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    
    ship: Optional["Ship"] = Relationship(back_populates="users")
    venue: Optional["Venue"] = Relationship(back_populates="users")

class Ship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: str = Field(unique=True, index=True)
    ship_class: str  # e.g., "Oasis", "Quantum", "Freedom", "Voyager"
    
    venues: List["Venue"] = Relationship(back_populates="ship")
    voyages: List["Voyage"] = Relationship(back_populates="ship")
    users: List["User"] = Relationship(back_populates="ship")

class Venue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ship_id: int = Field(foreign_key="ship.id")
    name: str
    capacity: int
    
    ship: Ship = Relationship(back_populates="venues")
    capabilities: List["EventType"] = Relationship(back_populates="venues", link_model=VenueCapability)
    schedule_items: List["ScheduleItem"] = Relationship(back_populates="venue")
    users: List["User"] = Relationship(back_populates="venue")
    highlights: List["VenueHighlight"] = Relationship(back_populates="source_venue", sa_relationship_kwargs={"foreign_keys": "VenueHighlight.source_venue_id"})
    schedules: List["VenueSchedule"] = Relationship(back_populates="venue")

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
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    ship: Ship = Relationship(back_populates="voyages")
    itineraries: List["VoyageItinerary"] = Relationship(back_populates="voyage", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    schedule_items: List["ScheduleItem"] = Relationship(back_populates="voyage", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    highlights: List["VenueHighlight"] = Relationship(back_populates="voyage", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    venue_schedules: List["VenueSchedule"] = Relationship(back_populates="voyage", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

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
    time_display: Optional[str] = None # Custom time label (e.g. "Doors Open 7pm")
    notes: Optional[str] = None
    
    voyage: Voyage = Relationship(back_populates="schedule_items")
    venue: Venue = Relationship(back_populates="schedule_items")
    event_type: Optional[EventType] = Relationship(back_populates="schedule_items")

class VenueHighlight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # SCOPING FIELDS (Strictly tied to Ship/Voyage and Venue)
    voyage_id: int = Field(foreign_key="voyage.id")
    source_venue_id: int = Field(foreign_key="venue.id") # The venue that "owns" this highlight list
    
    # CONTENT FIELDS (Extracted from PDF)
    date: date
    highlight_venue_name: str  # e.g., "Royal Theater" (The venue being highlighted)
    title: str                 # e.g., "Ice Spectacular"
    time_text: str             # e.g., "8:00 pm & 10:00 pm"
    
    # FUTURE-PROOFING FIELDS ("Smart Link")
    linked_venue_id: Optional[int] = Field(default=None, foreign_key="venue.id")
    linked_event_id: Optional[int] = Field(default=None, foreign_key="scheduleitem.id")
    
    # Relationships
    voyage: Voyage = Relationship(back_populates="highlights")
    source_venue: Venue = Relationship(back_populates="highlights", sa_relationship_kwargs={"foreign_keys": "VenueHighlight.source_venue_id"})

class VenueSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    venue_id: int = Field(foreign_key="venue.id")
    voyage_id: int = Field(foreign_key="voyage.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    venue: Venue = Relationship(back_populates="schedules")
    voyage: Voyage = Relationship(back_populates="venue_schedules")
