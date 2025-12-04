from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import shutil
import os
import tempfile
from sqlmodel import Session
from ..services.parser import parse_venue_schedule_excel
from ..services.genai_parser import GenAIParser
from ..dependencies import get_genai_parser
from ..database import get_session
from ..models import User, Venue
from .auth import get_current_user

router = APIRouter()

@router.post("/upload/cd-grid")
async def upload_cd_grid(
    file: UploadFile = File(...),
    parser: GenAIParser = Depends(get_genai_parser),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Determine target venue from user
    target_venue = "STUDIO B" # Fallback
    if current_user.venue_id:
        venue = session.get(Venue, current_user.venue_id)
        if venue:
            target_venue = venue.name

    # Create a temporary file with the same extension as the uploaded file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        file_path = tmp_file.name
    
    try:
        if file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.xls', '.xlsx')):
            # Use GenAI Parser for CD Grid (PDF, Image, or Excel)
            try:
                # Fetch other venues for this ship to extract their main shows
                other_venues = []
                if current_user.ship_id:
                    # Get all venues for the ship, excluding the target venue
                    from sqlmodel import select
                    venues = session.exec(select(Venue).where(Venue.ship_id == current_user.ship_id)).all()
                    other_venues = [v.name for v in venues if v.name != target_venue]

                print(f"DEBUG: Parsing CD Grid with target_venue='{target_venue}', other_venues={other_venues}")
                result = await parser.parse_cd_grid(file_path, target_venue=target_venue, other_venues=other_venues)
                return result
            except Exception as e:
                print(f"GenAI parsing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")
        else:
            return {"message": "Unsupported file type", "events": [], "itinerary": []}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
