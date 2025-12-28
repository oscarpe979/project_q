"""
Venue Rules Registry

Provides venue-specific rules for parsing and derived event generation.
Loads configs from database, selects venue-specific class for custom logic.
"""

from typing import Optional, Type
from sqlmodel import Session, select

from .base import VenueRules


# Registry of venue-specific classes (for venues with custom logic)
# Registry of venue-specific classes (for venues with custom logic)
VENUE_CLASS_REGISTRY = {
    # (ship_code, venue_name): VenueRulesSubclass
    ("WN", "Studio B"): "wn.wn_studio_b.StudioBRules",
    ("WN", "Royal Theater"): "wn.wn_royal_theater.RoyalTheaterRules",
    ("WN", "AquaTheater"): "wn.wn_aquatheater.AquaTheaterRules",
    ("WN", "Royal Promenade"): "wn.wn_royal_promenade.RoyalPromenadeRules",
}


def get_venue_rules(ship_code: str, venue_name: str, session: Session = None) -> VenueRules:
    """
    Get venue-specific rules for parsing.
    
    1. Load config from database (VenueRulesConfig table)
    2. Select appropriate class (venue-specific or base)
    3. Create instance with config
    
    Args:
        ship_code: Ship identifier (e.g., "WN")
        venue_name: Venue name (e.g., "Studio B")
        session: Optional database session
    
    Returns:
        VenueRules instance (always returns valid instance, never None)
    """
    ship_code = ship_code.upper() if ship_code else ""
    
    # Load config from database
    config = _load_config_from_db(ship_code, venue_name, session)
    
    # Get the appropriate class
    rules_class = _get_venue_class(ship_code, venue_name)
    
    # Create instance with config
    return rules_class.from_config(ship_code, venue_name, config)


def _load_config_from_db(ship_code: str, venue_name: str, session: Session = None) -> dict:
    """Load venue config from database. Returns empty dict if not found."""
    try:
        from backend.app.db.session import engine
        from backend.app.db.models import VenueRulesConfig
        
        if session:
            config_row = session.exec(
                select(VenueRulesConfig).where(
                    VenueRulesConfig.ship_code == ship_code,
                    VenueRulesConfig.venue_name == venue_name
                )
            ).first()
        else:
            with Session(engine) as new_session:
                config_row = new_session.exec(
                    select(VenueRulesConfig).where(
                        VenueRulesConfig.ship_code == ship_code,
                        VenueRulesConfig.venue_name == venue_name
                    )
                ).first()
        
        return config_row.config if config_row else {}
        
    except Exception as e:
        print(f"Warning: Could not load venue rules from DB: {e}")
        return {}


def _get_venue_class(ship_code: str, venue_name: str) -> Type[VenueRules]:
    """
    Get the appropriate VenueRules class for a venue.
    
    Returns venue-specific subclass if it exists, otherwise base class.
    """
    class_path = VENUE_CLASS_REGISTRY.get((ship_code, venue_name))
    
    if class_path:
        try:
            # Dynamically import the class
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(f"backend.app.venues.{module_path}", fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not load venue class {class_path}: {e}")
    
    # Fallback to base class
    return VenueRules
