#!/usr/bin/env python3
"""
Script to populate the database from the Royal Caribbean Production Managers CSV.
Usage: python -m backend.scripts.populate_db
"""

import csv
import os
from sqlmodel import Session, select
from backend.app.db.session import engine, create_db_and_tables
from backend.app.db.models import Ship, Venue, User
from backend.app.core.security import get_password_hash

CSV_FILE_PATH = "royal_caribbean_production_managers.csv"

def populate_database():
    # Ensure tables exist
    create_db_and_tables()

    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ Error: CSV file not found at {CSV_FILE_PATH}")
        return

    print(f"📂 Reading from {CSV_FILE_PATH}...")
    
    with Session(engine) as session:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            stats = {"ships": 0, "venues": 0, "users": 0}
            
            for row in reader:
                # 1. Ship
                ship_name = row['Ship Name'].strip()
                ship_code = row['Code'].strip()
                ship_class = row['Class'].strip()
                
                ship = session.exec(select(Ship).where(Ship.code == ship_code)).first()
                if not ship:
                    ship = Ship(name=ship_name, code=ship_code, ship_class=ship_class)
                    session.add(ship)
                    session.commit()
                    session.refresh(ship)
                    stats["ships"] += 1
                    print(f"  🚢 Created Ship: {ship.name} ({ship.code})")
                else:
                    # Update class if missing
                    if not ship.ship_class:
                        ship.ship_class = ship_class
                        session.add(ship)
                        session.commit()
                
                # 2. Venue
                venue_name = row['Venue'].strip()
                capacity_str = row['Est. Capacity'].replace(',', '').strip()
                capacity = int(capacity_str) if capacity_str.isdigit() else 0
                
                venue = session.exec(
                    select(Venue).where(Venue.ship_id == ship.id, Venue.name == venue_name)
                ).first()
                
                if not venue:
                    venue = Venue(name=venue_name, capacity=capacity, ship_id=ship.id)
                    session.add(venue)
                    session.commit()
                    session.refresh(venue)
                    stats["venues"] += 1
                    print(f"    🎭 Created Venue: {venue.name}")
                
                # 3. User (Production Manager)
                position_title = row['Production Manager'].strip()
                
                # Username Logic: code + "_" + venue (lowercase, no spaces)
                # e.g. "HM" + "_" + "Studio B" -> "hm_studiob"
                venue_slug = venue_name.replace(" ", "").lower()
                username = f"{ship_code.lower()}_{venue_slug}"
                
                user = session.exec(select(User).where(User.username == username)).first()
                
                if not user:
                    user = User(
                        username=username,
                        password_hash=get_password_hash("changeme123"),
                        full_name=position_title,
                        role="prod", # Production Manager
                        ship_id=ship.id,
                        venue_id=venue.id,
                        is_active=True
                    )
                    session.add(user)
                    session.commit()
                    stats["users"] += 1
                    print(f"      👤 Created User: {username} ({position_title})")
        
        print("\n" + "="*40)
        print("✅ Database Population Complete")
        print(f"  Ships Created: {stats['ships']}")
        print(f"  Venues Created: {stats['venues']}")
        print(f"  Users Created: {stats['users']}")
        print("="*40)

if __name__ == "__main__":
    populate_database()
