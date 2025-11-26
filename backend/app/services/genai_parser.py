import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
import pypdfium2 as pdfium
import os


class GenAIParser:
    """Parse CD Grid PDFs using Google Gemini."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def parse_cd_grid(self, file_path: str, target_venue: str) -> Dict[str, Any]:
        """
        Parse CD Grid (PDF, Image, or Excel) and extract itinerary + events.
        
        Returns:
            {
                "itinerary": [...],
                "events": [...]
            }
        """
        # Determine file type and prepare content for Gemini
        content_to_send = []
        

        temp_files_to_cleanup = [] # Renamed from temp_images for clarity, as it can contain CSVs too
        upload_path = file_path # Default to original file path

        if file_path.lower().endswith('.pdf'):
            print("DEBUG: Converting PDF to image for better vision analysis...")
            try:
                # Convert first page to image (assuming grid is on page 1)
                image_path = self._convert_pdf_to_image(file_path)
                upload_path = image_path
                temp_files_to_cleanup.append(image_path)
            except Exception as e:
                print(f"Warning: PDF to Image conversion failed ({e}). Falling back to raw PDF.")
                upload_path = file_path
        
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            print("DEBUG: Converting Excel to CSV for Gemini analysis...")
            try:
                # Convert Excel to CSV
                import pandas as pd
                df = pd.read_excel(file_path)
                csv_path = file_path + ".csv"
                df.to_csv(csv_path, index=False)
                upload_path = csv_path
                temp_files_to_cleanup.append(csv_path) # Add to cleanup list
            except Exception as e:
                print(f"Warning: Excel to CSV conversion failed ({e}).")
                # If conversion fails, try uploading the raw Excel file.
                # Gemini might still be able to process it, or it will fail gracefully.
                upload_path = file_path
        else:
            # Assume Image or other direct uploadable file type
            upload_path = file_path

        try:
            print(f"DEBUG: Uploading {upload_path} to Gemini...")
            uploaded_file = genai.upload_file(upload_path)
            content_to_send.append(uploaded_file)

            # Create structured prompt
            prompt = self._create_parsing_prompt(target_venue)
            content_to_send.append(prompt)
            
            # Generate response with JSON schema
            response = self.model.generate_content(
                content_to_send,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=self._get_response_schema()
                )
            )
            
            # Parse and validate response
            result = json.loads(response.text)
            
            # Log debug info
            if "debug_info" in result:
                print(f"DEBUG INFO FROM LLM:\n{result['debug_info']}")
                
            return self._validate_and_transform(result)
            
        finally:
            # Cleanup temporary files
            for f in temp_files_to_cleanup:
                if os.path.exists(f):
                    os.remove(f)

    def _convert_pdf_to_image(self, pdf_path: str) -> str:
        """Convert the first page of a PDF to a high-res image."""
        pdf = pdfium.PdfDocument(pdf_path)
        page = pdf[0] # Load first page
        
        # Render to image (scale=2 for better resolution/OCR)
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        
        # Save to temp file
        base_name = os.path.splitext(pdf_path)[0]
        image_path = f"{base_name}_converted.png"
        pil_image.save(image_path)
        
        return image_path
    
    def _create_parsing_prompt(self, venue: str) -> str:
        return f"""
Analyze the uploaded file (PDF, Image, Excel/CSV) as a strict grid structure. Focus strictly on the column labeled {venue}. 
Extract every event listed in this column for each date.
When reading the table, ignore all formatting attributes such as text color (e.g., red) or cell background colors (e.g., yellow highlights). 
These are for human emphasis only and are not part of the data to be extracted.
Your only priority is the text content and its position within the defined column boundaries (e.g., the 'Studio B' column). 
Do not allow any color or highlighting to influence which text you select.

Ignore Saliency: Treat red text, yellow highlights, and bold fonts as identical to standard black text. They carry no special meaning.
Preprocessing: Before extracting any text, mentally convert the entire page to a high-contrast black-and-white image.
Focus: Your attention must be distributed evenly across the grid. Do not let colored text pull your focus away from the column structure.

Present the output as a JSON object with the following structure:

1. ITINERARY (one entry per day):
   - day_number: Integer (e.g., 1, 2, 3)
   - date: String in YYYY-MM-DD format
   - day_of_week: String (e.g., "Monday", "Tuesday")
   - port: String (port name or "CRUISING")
   - port_times: String (e.g., "7:00 am - 6:00 pm" or "Depart 4:30 pm" or empty)

2. EVENTS (from the "{venue}" column only):
   - title: String (event name, excluding time information)
   - start_time: String in HH:MM format (24-hour)
   - end_time: String in HH:MM format (24-hour) or null if not specified
   - date: String in YYYY-MM-DD format (match to itinerary date)
   - venue: String (always "{venue}")

Please note the below rules:

RULES FOR TIME PARSING:
- **Midnight**: If the text says "Midnight", set `start_time` to "00:00".
- **Late**: If an end time is "Late", record it as "03:00" (3 AM).
- **Overnight**: If an event starts before midnight (e.g., 23:00) and ends after (e.g., 00:30), the start date is the current day.
- **24-Hour Format**: Convert all times to HH:MM 24-hour format.
- **Noon**: Convert "Noon" to "12:00".
- **Multiple Showtimes**: If an event lists multiple times separated by '&', 'and', or '/' (e.g., "7:00 pm & 9:00 pm"), you MUST create TWO separate event entries. One event starting at 19:00 and another event starting at 21:00, both with the same title.
- **Missing End Time**: If an event only lists a start time (e.g., "10:00 pm"), you MUST set `end_time` to `null`. Do NOT guess or fabricate an end time.

RULES IN GENERAL:
- **Date Assignment**: Always use the date corresponding to the row where the event text is physically located.
- If the column "{venue}" DOES NOT EXIST, return an empty list `[]`.
- Ignore "Doors open" times; use the show start time.
- 'GO' followed by a time is the start time. Also, a time followed gy a 'GO' is a start time.
- Skip empty cells or cells with just "-".
- 'Perfect Day' = 'Coco Cay'.
- Ignore numbers pax (passangers) for an event.

EVENT NAMES RULES:
- 'BOTS' =  'Battle of The Sexes'.
- 'RED' = 'RED: Nightclub Experience'.
- Format headliner event names as "Headliner: " followed by the event name.
- Remove 'Production Show' from the event name.
- Event names must be formated as title case unless it's an acronym.
- Ignore dates in the event name like (10.21 - 12.11) or similar.

Return ONLY valid JSON matching the schema.
"""
    
    def _get_response_schema(self) -> Dict:
        """Define JSON schema for structured output."""
        return {
            "type": "object",
            "properties": {
                "itinerary": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "date": {"type": "string"},
                            "day_of_week": {"type": "string"},
                            "port": {"type": "string"},
                            "port_times": {"type": "string"}
                        },
                        "required": ["day_number", "date", "day_of_week", "port"]
                    }
                },
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "start_time": {"type": "string"},
                            "end_time": {"type": "string"},
                            "date": {"type": "string"},
                            "venue": {"type": "string"}
                        },
                        "required": ["title", "start_time", "date", "venue"]
                    }
                }
            },
            "required": ["itinerary", "events"]
        }
    
    def _validate_and_transform(self, result: Dict) -> Dict[str, Any]:
        """Validate and transform to API format."""
        raw_events = result.get("events", [])
        parsed_events = []

        # 1. Parse raw events into intermediate objects
        for event in raw_events:
            parsed = self._parse_single_event(event)
            if parsed:
                parsed_events.append(parsed)

        # 2. Sort by start time to handle sequential logic
        parsed_events.sort(key=lambda x: x['start_dt'])

        # 3. Resolve end times (smart duration)
        final_events = self._resolve_event_durations(parsed_events)

        # 4. Format for API response
        formatted_events = [self._format_event_for_api(e) for e in final_events]
        
        return {
            "itinerary": result.get("itinerary", []),
            "events": formatted_events
        }

    def _parse_single_event(self, event: Dict) -> Optional[Dict]:
        """Parse a single raw event into an intermediate structure."""
        try:
            date_str = event["date"]
            start_time_str = event['start_time']
            start_dt = datetime.fromisoformat(f"{date_str}T{start_time_str}:00")
            
            # Smart Date Shift:
            # If an event is in the grid row for Day X, but the time is 00:00 - 03:59,
            # it implies it's a late-night event belonging to Day X's night (which is technically Day X+1).
            # So we shift the date forward by 1 day.
            if start_dt.hour < 4:
                start_dt += timedelta(days=1)
            
            # Normalize end_time: convert string "null" to None
            end_time_raw = event.get("end_time")
            end_time_str = None if (end_time_raw is None or end_time_raw == "null" or end_time_raw == "") else end_time_raw
            
            return {
                "title": event["title"],
                "start_dt": start_dt,
                "end_time_str": end_time_str,
                "venue": event["venue"],
                "raw_date": date_str
            }
        except (ValueError, KeyError) as e:
            print(f"Skipping malformed event: {event}, error: {e}")
            return None

    def _resolve_event_durations(self, events: List[Dict]) -> List[Dict]:
        """Resolve end times, handling missing durations and overlaps."""
        resolved_events = []
        
        for i, event in enumerate(events):
            start_dt = event['start_dt']
            end_dt = None
            
            # Case 1: End time is explicitly provided
            if event['end_time_str']:
                try:
                    # Construct end datetime
                    # We assume it's on the same day initially
                    end_dt = datetime.fromisoformat(f"{event['raw_date']}T{event['end_time_str']}:00")
                    
                    # Handle overnight events (end time < start time)
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    
                    # Force Smart Duration: If ANY event overlaps with the next event, shorten it.
                    # This handles cases where LLM hallucinates durations (e.g. 2 hours) or defaults to 1 hour.
                    # We assume events in the same venue column do not overlap.
                    if i + 1 < len(events):
                        next_event = events[i + 1]
                        if next_event['start_dt'] < end_dt:
                            end_dt = next_event['start_dt']

                except ValueError:
                    # Fallback if parsing fails
                    end_dt = start_dt + timedelta(hours=1)
            
            # Case 2: End time is missing (Smart Duration Logic)
            else:
                default_end = start_dt + timedelta(hours=1)
                
                # Check next event for overlap
                if i + 1 < len(events):
                    next_event = events[i + 1]
                    # If next event starts before our default end, cut short
                    if next_event['start_dt'] < default_end:
                        end_dt = next_event['start_dt']
                    else:
                        end_dt = default_end
                else:
                    end_dt = default_end
            
            # Update event with calculated end_dt
            event['end_dt'] = end_dt
            resolved_events.append(event)
            
        return resolved_events

    def _format_event_for_api(self, event: Dict) -> Dict:
        """Format the resolved event for the API response."""
        return {
            "title": event["title"],
            "start": event["start_dt"].isoformat(),
            "end": event["end_dt"].isoformat(),
            "type": self._classify_event(event["title"]),
            "venue": event["venue"]
        }
    
    def _classify_event(self, title: str) -> str:
        """Simple event classification."""
        title_lower = title.lower()
        if any(keyword in title_lower for keyword in ['silk road', 'oceanaria', 'show girl', 'effectors']):
            return 'show'
        elif 'rehearsal' in title_lower:
            return 'rehearsal'
        elif 'maintenance' in title_lower or 'dark' in title_lower:
            return 'maintenance'
        return 'other'
