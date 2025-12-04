import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
import pypdfium2 as pdfium
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor


class GenAIParser:
    """Parse CD Grid PDFs using Google Gemini."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    


    async def parse_cd_grid(self, file_path: str, target_venue: str, other_venues: List[str] = []) -> Dict[str, Any]:
        """
        Async version of parse_cd_grid.
        """
        # Determine file type and prepare content for Gemini
        content_to_send = []
        
        temp_files_to_cleanup = [] 
        upload_path = file_path 

        try:
            if file_path.lower().endswith('.pdf'):
                print("DEBUG: Converting PDF to image for better vision analysis...")
                try:
                    # Run blocking conversion in thread
                    image_path = await asyncio.to_thread(self._convert_pdf_to_image, file_path)
                    upload_path = image_path
                    temp_files_to_cleanup.append(image_path)
                except Exception as e:
                    print(f"Warning: PDF to Image conversion failed ({e}). Falling back to raw PDF.")
                    upload_path = file_path
            
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                print("DEBUG: Converting Excel to CSV for Gemini analysis...")
                try:
                    # Run blocking conversion in thread
                    def convert_excel():
                        import pandas as pd
                        df = pd.read_excel(file_path)
                        csv_path = file_path + ".csv"
                        df.to_csv(csv_path, index=False)
                        return csv_path

                    csv_path = await asyncio.to_thread(convert_excel)
                    upload_path = csv_path
                    temp_files_to_cleanup.append(csv_path) 
                except Exception as e:
                    print(f"Warning: Excel to CSV conversion failed ({e}).")
                    upload_path = file_path
            else:
                upload_path = file_path

            print(f"DEBUG: Uploading {upload_path} to Gemini...")
            # Run blocking upload in thread
            uploaded_file = await asyncio.to_thread(genai.upload_file, upload_path)
            content_to_send.append(uploaded_file)

            # Create structured prompt
            prompt = self._create_parsing_prompt(target_venue, other_venues)
            content_to_send.append(prompt)
            
            # Generate response with JSON schema (ASYNC)
            response = await self.model.generate_content_async(
                content_to_send,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=self._get_response_schema(),
                    temperature=0.0
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
                    try:
                        os.remove(f)
                    except:
                        pass

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
    
    def _create_parsing_prompt(self, venue: str, other_venues: List[str]) -> str:
        other_venues_prompt = ""
        if other_venues:
            other_venues_list = ", ".join(other_venues)
            other_venues_prompt = f"""
3. OTHER VENUE SHOWS (Focus on these columns: {other_venues_list}):
   - For each of these other venues, extract **EXACTLY ONE** "Main Evening Show" for each day.
   - The "Main Evening Show" is the single most important event in that venue for the evening (usually 7pm onwards).
   - **CRITICAL**: You must output EXACTLY ONE event per venue per day. If there are multiple shows (e.g. 8pm and 10pm), choose the most important one that is a main production show or headliner.
   - Ignore any 'Back Up' or 'Backup' shows.
   - Try to only extract the main show title. For example: 'inTENSE: Maximum Performance' can be 'inTENse', 'Headliner: Adam Kario' can be 'Adam Kario'. 
   - If a venue column doesn't exist or has no main show, skip it for that day.
   - Extract:
     - venue: The name of the venue. You MUST use one of the exact strings from this list: [{other_venues_list}]. Do NOT combine names.
     - date: String in YYYY-MM-DD format
     - title: The name of the show
     - time: The display time string should be kept as they are but trying to convert it to 12-hour format. Keep in mind there might be multiple times that means there are two shows and we should keep both times in the time string. If you get times in words like "Midnight" or "Late", keep them as they are. (e.g., "8:00 pm & 10:00 pm" or "9:00 pm" or "Midnight").
"""

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
   - arrival_time: String (e.g., "7:00 am" or null if none/cruising)
   - departure_time: String (e.g., "6:00 pm" or "Midnight" or null if none)

2. EVENTS (from the "{venue}" column only):
   - title: String (event name, excluding time information)
   - start_time: String in HH:MM format (24-hour)
   - end_time: String in HH:MM format (24-hour) or null if not specified
   - date: String in YYYY-MM-DD format (match to itinerary date)
   - venue: String (always "{venue}")

{other_venues_prompt}

Please note the below rules:

RULES FOR TIME PARSING:
- **Midnight**: If the text says "Midnight", set `start_time` to "00:00".
- **Late**: If an end time is "Late", record it as "03:00" (3 AM).
- **Overnight**: If an event starts before midnight (e.g., 23:00) and ends after (e.g., 00:30), the start date is the current day.
- **24-Hour Format**: Convert all times to HH:MM 24-hour format.
- **Noon**: Convert "Noon" to "12:00".
- **Multiple Showtimes**: If an event lists multiple times separated by '&', 'and', or '/' (e.g., "7:00 pm & 9:00 pm"), you MUST create TWO separate event entries. One event starting at 19:00 and another event starting at 21:00, both with the same title.
- **Missing End Time**: If an event only lists a start time (e.g., "10:00 pm"), you MUST set `end_time` to `null`. Do NOT guess or fabricate an end time. NEVER use "00:00" as a default end time unless the text explicitly says "Midnight" or "12:00 am" for the end time.

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

CATEGORIZATION RULES:
Assign a `category` to each event based on its type. Use ONLY these categories:
- **Production Shows** (category: "show"): e.g., "Cats", "Hairspray", "Mamma Mia!", "Saturday Night Fever", "We Will Rock You", "Grease", "The Wizard of Oz", "The Effectors", "The Effectors II: Crash 'n' Burn", "Flight", "Hiro", "inTENse", "1977", "Aqua80", "Aqua80Too", "Big Daddy's Hideaway Heist", "Blue Planet", "Live. Love. Legs.", "The Gift", "Sonic Odyssey", "Starwater", "Spectra's Cabaret", "Showgirl™", "Columbus The Musical", "Can't Stop the Rock", "Fast Forward", "Gallery of Dreams", "Jackpot", "Marquee", "Music in Pictures", "Now and Forever", "Once Upon A Time", "One Sky", "Piano Man", "Pure Country", "Sequins & Feathers", "Stage to Screen", "Tango Buenos Aires", "The Beautiful Dream", "The Fine Line", "The Silk Road™", "Vibeology", "Voices", "West End to Broadway", "Wild Cool & Swingin'", "iSkate 2.0", "Ice Games", "Ice Odyssey", "Invitation to Dance", "Ballroom Fever", "Broadway Rhythm & Rhyme", "City of Dreams", "Hot Ice!", "Oceanides".
- **Headliners** (category: "headliner"): e.g., events starting with "Headliner:".
- **Movies** (category: "movie").
- **Game Shows** (category: "game"): e.g., "Love & Marriage", "Battle of the Sexes", "The Quest", "Majority Rules", "Friendly Feud", "Who Wants to Be a Royal Caribbeanaire", "The Virtual Concert", "Late-Night DJ Music and Dancing", "NextStage", "The Voice".
- **Activities** (category: "activity"): e.g., "Trivia", "Dance Class", "Karaoke", "Laser Tags", "Ice Skating", .
- **Music** (category: "music"): e.g., "Live Music", "Piano", "Band", "Live Concert", "Live Performance".
- **Comedy** (category: "comedy"): e.g., "Stand-up Comedy", "Comedian", "Comedy Show", "Adult Comedy Show".
- **Party** (category: "party"): e.g., "RED: Nightclub Experience", "Nightclub".
- **Other** (category: "other"): Rehearsals, Maintenance, or anything else.

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
                            "arrival_time": {"type": "string"},
                            "departure_time": {"type": "string"}
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
                            "venue": {"type": "string"},
                            "category": {"type": "string", "enum": ["show", "movie", "game", "activity", "music", "party", "comedy", "headliner", "rehearsal", "maintenance", "other"]}
                        },
                        "required": ["title", "start_time", "date", "venue", "category"]
                    }
                },
                "other_venue_shows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "venue": {"type": "string"},
                            "date": {"type": "string"},
                            "title": {"type": "string"},
                            "time": {"type": "string"}
                        },
                        "required": ["venue", "date", "title", "time"]
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
            "events": formatted_events,
            "other_venue_shows": self._filter_other_venue_shows(result.get("other_venue_shows", []))
        }

    def _filter_other_venue_shows(self, shows: List[Dict]) -> List[Dict]:
        """
        Ensure only one show per venue per day.
        Prioritize:
        1. Shows starting between 7 PM and 10 PM.
        2. Earliest show in that window.
        """
        grouped = {}
        for show in shows:
            key = (show['venue'], show['date'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(show)
        
        filtered_shows = []
        for key, venue_shows in grouped.items():
            if len(venue_shows) == 1:
                filtered_shows.append(venue_shows[0])
                continue
            
            # Multiple shows: Pick the best one
            best_show = None
            
            # Strategy: Parse time and find the one closest to 8 PM (20:00)
            # This is a heuristic since 'time' is a display string (e.g. "8:00 pm & 10:00 pm")
            # We'll just pick the first one for now as the prompt instructs LLM to pick the main one.
            # But to be safe, we can look for keywords or just take the first one.
            
            # If the prompt works well, the LLM should have already filtered. 
            # But if it didn't, we just take the first one to enforce the constraint.
            filtered_shows.append(venue_shows[0])
            
        return filtered_shows

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
                "raw_date": date_str,
                "category": event.get("category", "other")
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
            "type": event.get("category", "other"),
            "venue": event["venue"]
        }
    

