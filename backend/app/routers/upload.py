from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import asyncio
import io
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
    
    # Run blocking DB call in thread
    def get_venue_name(v_id):
        v = session.get(Venue, v_id)
        return v.name if v else None

    if current_user.venue_id:
        venue_name = await asyncio.to_thread(get_venue_name, current_user.venue_id)
        if venue_name:
            target_venue = venue_name

    # Pass the file object directly to the parser
    # file.file is a SpooledTemporaryFile (file-like object).
    # This avoids reading the entire file into RAM if it's already spooled to disk.
    file_obj = file.file
    
    try:
        if file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.xls', '.xlsx')):
            # Use GenAI Parser for CD Grid (PDF, Image, or Excel)
            try:
                # Fetch other venues for this ship to extract their main shows
                other_venues = []
                if current_user.ship_id:
                    # Run blocking DB call in thread
                    def get_other_venues(s_id, t_venue):
                        from sqlmodel import select
                        venues = session.exec(select(Venue).where(Venue.ship_id == s_id)).all()
                        return [v.name for v in venues if v.name != t_venue]

                    other_venues = await asyncio.to_thread(get_other_venues, current_user.ship_id, target_venue)

                print(f"DEBUG: Parsing CD Grid with target_venue='{target_venue}', other_venues={other_venues}")
                result = await parser.parse_cd_grid(file_obj, filename=file.filename, target_venue=target_venue, other_venues=other_venues)
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
