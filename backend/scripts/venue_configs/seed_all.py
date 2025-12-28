"""
Seed All Venue Rules

Main entry point to seed all venue configurations to the database.
Imports configs from per-ship/per-venue modules and upserts to VenueRulesConfig table.

Usage:
    PYTHONPATH=. python -m backend.scripts.venue_configs.seed_all
    
Or from project root:
    PYTHONPATH=. python backend/scripts/venue_configs/seed_all.py
"""

from sqlmodel import Session, select
from backend.app.db.session import engine
from backend.app.db.models import VenueRulesConfig

# Import venue configs by ship
from backend.scripts.venue_configs.wn import (
    wn_studio_b,
    wn_aquatheater,
    wn_royal_theater,
    wn_royal_promenade
)


def get_all_configs():
    """Collect all venue configurations from all ships."""
    configs = []
    
    # Wonder of the Seas (WN)
    configs.append(wn_studio_b.get_config())
    configs.append(wn_aquatheater.get_config())
    configs.append(wn_royal_theater.get_config())
    configs.append(wn_royal_promenade.get_config())
    
    # Add more ships here as they're configured:
    # configs.append(sy_studio_b.get_config())  # Symphony of the Seas
    # configs.append(hr_studio_b.get_config())  # Harmony of the Seas
    
    return configs


def seed_venue_rules():
    """Seed all venue rules configurations to the database."""
    configs = get_all_configs()
    
    print(f"Seeding {len(configs)} venue rules configs...")
    
    with Session(engine) as session:
        for cfg in configs:
            ship_code = cfg["ship_code"]
            venue_name = cfg["venue_name"]
            config = cfg["config"]
            
            # Check if exists
            existing = session.exec(
                select(VenueRulesConfig).where(
                    VenueRulesConfig.ship_code == ship_code,
                    VenueRulesConfig.venue_name == venue_name
                )
            ).first()
            
            if existing:
                print(f"  Updating: {ship_code} - {venue_name}")
                existing.config = config
                existing.version += 1
            else:
                print(f"  Creating: {ship_code} - {venue_name}")
                session.add(VenueRulesConfig(
                    ship_code=ship_code,
                    venue_name=venue_name,
                    config=config
                ))
        
        session.commit()
    
    print("Seeding complete.")


if __name__ == "__main__":
    seed_venue_rules()
