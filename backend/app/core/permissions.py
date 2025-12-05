from fastapi import HTTPException, status
from backend.app.db.models import User

def check_venue_access(user: User, target_venue_id: int):
    """
    Check if the user has access to the target venue.
    Raises 403 Forbidden if access is denied.
    """
    # Admin has access to everything
    if user.role == "admin":
        return True
    
    # Users can only access their assigned venue
    if user.venue_id != target_venue_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this venue."
        )
    
    return True
