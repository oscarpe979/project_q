from sqlmodel import Session, select
from backend.app.db.session import engine
from backend.app.db.models import User, Ship, Venue
from backend.app.core.security import get_password_hash

def seed_db():
    with Session(engine) as session:
        # Check if user exists
        user = session.exec(select(User).where(User.username == "testuser")).first()
        if not user:
            print("Creating test user...")
            
            # Ensure ship and venue exist
            ship = session.exec(select(Ship).where(Ship.code == "TEST")).first()
            if not ship:
                ship = Ship(code="TEST", name="Test Ship", ship_class="Oasis")
                session.add(ship)
                session.commit()
                session.refresh(ship)
            
            venue = session.exec(select(Venue).where(Venue.name == "Test Venue")).first()
            if not venue:
                venue = Venue(name="Test Venue", ship_id=ship.id, capacity=100)
                session.add(venue)
                session.commit()
                session.refresh(venue)

            user = User(
                username="testuser",
                password_hash=get_password_hash("password"),
                full_name="Test User",
                ship_id=ship.id,
                venue_id=venue.id,
                role="scheduler",
                is_active=True
            )
            session.add(user)
            session.commit()
            print("Test user created.")
        else:
            print("Test user already exists.")

if __name__ == "__main__":
    seed_db()
