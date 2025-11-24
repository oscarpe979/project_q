import google.generativeai as genai
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta


class GenAIParser:
    """Parse CD Grid PDFs using Google Gemini."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def parse_cd_grid(self, pdf_path: str, target_venue: str = "STUDIO B") -> Dict[str, Any]:
        """
        Parse CD Grid PDF and extract itinerary + events.
        
        Returns:
            {
                "itinerary": [...],
                "events": [...]
            }
        """
        # Upload PDF to Gemini
        pdf_file = genai.upload_file(pdf_path)
        
        # Create structured prompt
        prompt = self._create_parsing_prompt(target_venue)
        
        # Generate response with JSON schema
        response = self.model.generate_content(
            [pdf_file, prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=self._get_response_schema()
            )
        )
        
        # Parse and validate response
        result = json.loads(response.text)
        return self._validate_and_transform(result)
    
    def _create_parsing_prompt(self, venue: str) -> str:
        return f"""
You are parsing a cruise ship Grid schedule PDF. Extract the following information:

1. ITINERARY (one entry per day):
   - day_number: Integer (e.g., 1, 2, 3)
   - date: String in YYYY-MM-DD format
   - day_of_week: String (e.g., "Monday", "Tuesday")
   - port: String (port name or "CRUISING")
   - port_times: String (e.g., "7:00 am - 6:00 pm" or "Depart 4:30 pm" or empty)

2. EVENTS (from the "{venue}" column only):
   - title: String (event name, excluding time information)
   - start_time: String in HH:MM format (24-hour)
   - end_time: String in HH:MM format (24-hour)
   - date: String in YYYY-MM-DD format (match to itinerary date)
   - venue: String (always "{venue}")

IMPORTANT GENERAL RULES:
- Make sure you only extract events from the "{venue}" column. Avoid extracting events from other columns.
- For events with multiple showtimes (e.g., "7:30 PM & 9:30 PM"), create SEPARATE events
- If only start time is given, assume 1-hour duration. Be aware of the end dates when an event starts between 23:00 and 23:59.
- Extract event title by removing time information from the cell content
- Times can be given like 'midngiht' or 'noon'.
- Start times are always earlier than end times. If the start time is later than the end time, you have to assume that the end time is the next day.
- If an event starts before midnight (for example 23:00) and ends after midnight (for example 00:30) that means that the date of the start event is the current day and the end time is the next day.
- If an event starts between 23:00 and 23:59 and has no ending time, you have to assume the event is 1 hour and the end date is the next day.
- If an ending time says 'late' assume 2am as ending time.
- If an event makes reference to 'Doors open' or 'Doors open at' ignore that time and look for the next time information for the event start time.
- Convert all times to 24-hour format
- Skip empty cells or cells with just "-"
- Port times can be ranges, single times, or "Depart/Arrive" statements
- Sometimes in the "Day" column there is an annotation like '1 Hour Forward' or '1 Hour back'. If you see that, ignore it for now.
- 'Perfect Day' as a port means the island of Coco Cay.


Return ONLY valid JSON matching the schema. No explanations.
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
                        "required": ["title", "start_time", "end_time", "date", "venue"]
                    }
                }
            },
            "required": ["itinerary", "events"]
        }
    
    def _validate_and_transform(self, result: Dict) -> Dict[str, Any]:
        """Validate and transform to API format."""
        # Transform events to include full datetime
        events = []
        for event in result.get("events", []):
            try:
                # Combine date and time
                date_str = event["date"]
                start_dt = datetime.fromisoformat(f"{date_str}T{event['start_time']}:00")
                end_dt = datetime.fromisoformat(f"{date_str}T{event['end_time']}:00")
                
                # Handle overnight events (end time is next day)
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                
                events.append({
                    "title": event["title"],
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "type": self._classify_event(event["title"]),
                    "venue": event["venue"]
                })
            except (ValueError, KeyError) as e:
                # Log and skip malformed events
                print(f"Skipping malformed event: {event}, error: {e}")
                continue
        
        return {
            "itinerary": result.get("itinerary", []),
            "events": events
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
