from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
import os
from backend.app.services.parser import parse_venue_schedule_pdf, parse_cd_grid_pdf

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/cd-grid")
async def upload_cd_grid(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if file.filename.endswith('.pdf'):
            # Use GenAI Parser for CD Grid
            try:
                result = parse_cd_grid_pdf(file_path)
                
                # Debug Logging
                print("\n--- GenAI Parser Result ---")
                print(f"Itinerary Days: {len(result.get('itinerary', []))}")
                print(f"Events Found: {len(result.get('events', []))}")
                if result.get('events'):
                    print(f"Sample Event: {result['events'][0]}")
                print("---------------------------\n")
                
                return result
            except Exception as e:
                print(f"GenAI parsing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")
            
        elif file.filename.endswith(('.xls', '.xlsx')):
            from backend.app.services.parser import parse_venue_schedule_excel
            # Try Venue Schedule Parser first
            events = parse_venue_schedule_excel(file_path)
            # Return in new format with empty itinerary for now
            return {"events": events, "itinerary": []}
        else:
            return {"message": "Unsupported file type", "events": [], "itinerary": []}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Optional: Cleanup file
        if os.path.exists(file_path):
            os.remove(file_path)
