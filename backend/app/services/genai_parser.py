import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta


class GenAIParser:
    """Parse CD Grid PDFs using Google Gemini."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def parse_cd_grid(self, pdf_path: str, target_venue: str) -> Dict[str, Any]:
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
   - end_time: String in HH:MM format (24-hour) or null if not specified
   - date: String in YYYY-MM-DD format (match to itinerary date)
   - venue: String (always "{venue}")

IMPORTANT GENERAL RULES:
- **CRITICAL**: You must ONLY extract events from the column explicitly labeled "{venue}".
- **CRITICAL**: If the column "{venue}" DOES NOT EXIST in the PDF, return an empty list `[]` for events. Do NOT try to guess or extract from other columns.
- Do NOT extract events from "Royal Theater", "Two70", "Music Hall", "AquaTheater", "Studio B", "Star Lounge", "Boleros", "Pool Deck", "Solarium", "Royal Esplanade", "Promenade", or any other column unless the target venue matches exactly.
- For events with multiple showtimes (e.g., "7:30 PM & 9:30 PM"), create SEPARATE events
- If only start time is given, return null for end_time. DO NOT GUESS OR CALCULATE END TIMES.
- Extract event title by removing time information from the cell content
- Times can be given like 'midngiht' or 'noon'.
- Start times are always earlier than end times. If the start time is later than the end time, you have to assume that the end time is the next day.
- If an event starts before midnight (for example 23:00) and ends after midnight (for example 00:30) that means that the date of the start event is the current day and the end time is the next day.
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
            start_dt = datetime.fromisoformat(f"{date_str}T{event['start_time']}:00")
            
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
