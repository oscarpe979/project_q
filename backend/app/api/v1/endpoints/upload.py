from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import asyncio
import io
from sqlmodel import Session
from backend.app.services.parser import parse_venue_schedule_excel
from backend.app.services.genai_parser import GenAIParser
from backend.app.core.dependencies import get_genai_parser
from backend.app.db.session import get_session
from backend.app.db.models import User, Venue
from backend.app.api.v1.endpoints.auth import get_current_user

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
                # Get ship code for venue rules lookup
                ship_code = None
                if current_user.ship_id:
                    from backend.app.db.models import Ship
                    ship = session.get(Ship, current_user.ship_id)
                    ship_code = ship.code if ship else None

                print(f"DEBUG: Parsing CD Grid with target_venue='{target_venue}', ship_code='{ship_code}'")
                result = await parser.parse_cd_grid(
                    file_obj, 
                    filename=file.filename, 
                    target_venue=target_venue, 
                    ship_code=ship_code
                )
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
