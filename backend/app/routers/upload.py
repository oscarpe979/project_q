from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
import os
import tempfile
from ..services.parser import parse_venue_schedule_excel
from ..services.genai_parser import GenAIParser
from ..dependencies import get_genai_parser
from fastapi import Depends

router = APIRouter()

@router.post("/upload/cd-grid")
async def upload_cd_grid(
    file: UploadFile = File(...),
    parser: GenAIParser = Depends(get_genai_parser)
):
    # Create a temporary file with the same extension as the uploaded file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        file_path = tmp_file.name
    
    try:
        if file.filename.endswith('.pdf'):
            # Use GenAI Parser for CD Grid
            try:
                result = parser.parse_cd_grid(file_path)
                return result
            except Exception as e:
                print(f"GenAI parsing failed: {e}")
                raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")
            
        elif file.filename.endswith(('.xls', '.xlsx')):
            from ..services.parser import parse_venue_schedule_excel
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
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
