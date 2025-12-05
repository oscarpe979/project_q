#!/usr/bin/env python3
"""
Script to create user accounts for venue managers.
Usage: python -m backend.scripts.create_user
"""

from sqlmodel import Session, select
from backend.app.db.session import engine
from backend.app.db.models import User, Ship, Venue
from backend.app.core.security import get_password_hash
from getpass import getpass

def list_ships(session: Session):
    """List all available ships."""
    statement = select(Ship)
    ships = session.exec(statement).all()
    if not ships:
        print("\n⚠️  No ships found in database. Please add ships first.")
        return []
    
    print("\n📋 Available Ships:")
    for i, ship in enumerate(ships, 1):
        print(f"  {i}. {ship.name} ({ship.code}) - {ship.ship_class} class")
    return ships

def list_venues(session: Session, ship_id: int):
    """List all venues for a specific ship."""
    statement = select(Venue).where(Venue.ship_id == ship_id)
    venues = session.exec(statement).all()
    if not venues:
        print("\n⚠️  No venues found for this ship. Please add venues first.")
        return []
    
    print("\n🎭 Available Venues:")
    for i, venue in enumerate(venues, 1):
        print(f"  {i}. {venue.name} (Capacity: {venue.capacity})")
    return venues

def create_user():
    """Interactive user creation."""
    print("\n" + "="*60)
    print("🎬 VenueSched - User Creation Script")
    print("="*60)
    
    with Session(engine) as session:
        # Step 1: Select Ship
        ships = list_ships(session)
        if not ships:
            return
        
        ship_choice = int(input("\nSelect ship number: ")) - 1
        if ship_choice < 0 or ship_choice >= len(ships):
            print("❌ Invalid selection")
            return
        selected_ship = ships[ship_choice]
        
        # Step 2: Select Venue
        venues = list_venues(session, selected_ship.id)
        if not venues:
            return
        
        venue_choice = int(input("\nSelect venue number: ")) - 1
        if venue_choice < 0 or venue_choice >= len(venues):
            print("❌ Invalid selection")
            return
        selected_venue = venues[venue_choice]
        
        # Step 3: User Details
        print("\n" + "-"*60)
        print("👤 User Details")
        print("-"*60)
        
        username = input("Username (e.g., hmstudiob): ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return
        
        # Check if username already exists
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            print(f"❌ Username '{username}' already exists")
            return
        
        full_name = input("Position Title (e.g., Studio B Production Manager): ").strip()
        if not full_name:
            print("❌ Position title cannot be empty")
            return
        
        print("\n📝 Available Roles:")
        print("  1. admin - Full system access")
        print("  2. spro - Stage Production Manager")
        print("  3. prod - Production Manager")
        print("  4. view_only - Read-only access")
        
        role_map = {"1": "admin", "2": "spro", "3": "prod", "4": "view_only"}
        role_choice = input("\nSelect role number: ").strip()
        role = role_map.get(role_choice)
        if not role:
            print("❌ Invalid role selection")
            return
        
        password = getpass("Password: ")
        password_confirm = getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match")
            return
        
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            return
        
        # Step 4: Create User
        print("\n" + "-"*60)
        print("📝 Creating user...")
        print("-"*60)
        
        user = User(
            username=username,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=role,
            ship_id=selected_ship.id,
            venue_id=selected_venue.id,
            is_active=True
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print("\n✅ User created successfully!")
        print(f"\n📋 User Details:")
        print(f"  Username: {user.username}")
        print(f"  Position: {user.full_name}")
        print(f"  Ship: {selected_ship.name} ({selected_ship.code})")
        print(f"  Venue: {selected_venue.name}")
        print(f"  Role: {user.role}")
        print(f"  Active: {user.is_active}")
        print("\n" + "="*60)

if __name__ == "__main__":
    try:
        create_user()
    except KeyboardInterrupt:
        print("\n\n❌ User creation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
