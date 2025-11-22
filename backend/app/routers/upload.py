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
            # Try Venue Schedule Parser first
            events = parse_venue_schedule_pdf(file_path)
            if not events:
                # Fallback to CD Grid Parser
                events = parse_cd_grid_pdf(file_path)
            return {"events": events}
            
        elif file.filename.endswith(('.xls', '.xlsx')):
            from backend.app.services.parser import parse_venue_schedule_excel
            # Try Venue Schedule Parser first
            events = parse_venue_schedule_excel(file_path)
            # TODO: Implement parse_cd_grid_excel if needed
            return {"events": events}
        else:
            # TODO: Implement Excel parser
            return {"message": "Excel parsing not yet implemented", "events": []}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup? Maybe keep for debugging for now
        pass
