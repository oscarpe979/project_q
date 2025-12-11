"""
GenAI Parser v2 - Multi-pass architecture for improved accuracy.
Uses structured extraction followed by LLM interpretation.
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional, Union, BinaryIO
import json
import io
from datetime import datetime, timedelta
import pypdfium2 as pdfium
import asyncio

from .content_extractor import ContentExtractor
from .parser_validator import ParserValidator


class GenAIParser:
    """Parse CD Grid PDFs/Excel using Google Gemini with multi-pass architecture."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.content_extractor = ContentExtractor()
        self.validator = ParserValidator()
    
    async def parse_cd_grid(
        self, 
        file_obj: Union[str, BinaryIO], 
        filename: str, 
        target_venue: str, 
        other_venues: List[str] = []
    ) -> Dict[str, Any]:
        """
        Multi-pass parsing pipeline for improved accuracy.
        
        Pipeline:
        1. Extract raw structure (deterministic)
        2. LLM Pass 1: Discover structure (header rows, venue columns)
        3. Filter to relevant columns (deterministic)
        4. LLM Pass 2: Interpret content (events, itinerary, highlights)
        5. Validate results
        6. Fall back to vision mode if structured extraction fails
        """
        print("DEBUG: Starting multi-pass parsing pipeline...")
        
        try:
            # Step 1: Extract raw structure
            print("DEBUG: Step 1 - Extracting raw structure...")
            raw_data = await asyncio.to_thread(
                self.content_extractor.extract, file_obj, filename
            )
            
            if len(raw_data.get("cells", [])) < 10:
                print("DEBUG: Insufficient structured data, falling back to vision mode...")
                return await self._parse_via_vision(file_obj, filename, target_venue, other_venues)
            
            print(f"DEBUG: Extracted {len(raw_data['cells'])} cells from {raw_data['type']} file")
            
            # Step 2: LLM discovers structure
            print("DEBUG: Step 2 - LLM structure discovery...")
            structure = await self._discover_structure(raw_data, target_venue, other_venues)
            
            print(f"DEBUG: Structure discovered: {json.dumps(structure, indent=2)}")
            
            if not structure.get("target_venue_column"):
                # Don't fall back to vision mode - it will hallucinate events for a non-existent venue
                error_msg = f"Venue '{target_venue}' not found in this CD Grid file. Available venues in header: check the file."
                print(f"DEBUG: {error_msg}")
                raise ValueError(error_msg)
            
            # Step 3: Filter to relevant columns
            print("DEBUG: Step 3 - Filtering to relevant columns...")
            filtered_data = self._filter_to_relevant_columns(raw_data, structure)
            
            # Step 4: LLM interprets content
            print("DEBUG: Step 4 - LLM content interpretation...")
            result = await self._interpret_schedule(filtered_data, structure, target_venue, other_venues)
            
            # Step 5: Validate and transform
            print("DEBUG: Step 5 - Validating results...")
            validation = self.validator.validate(
                result, raw_data, target_venue, other_venues
            )
            
            if validation.warnings:
                print(f"DEBUG: Validation warnings: {validation.warnings}")
            
            if not validation.is_valid:
                print(f"DEBUG: Validation failed: {validation.errors}")
                print("DEBUG: Falling back to vision mode...")
                return await self._parse_via_vision(file_obj, filename, target_venue, other_venues)
            
            # Transform to API format
            return self._transform_to_api_format(result)
            
        except Exception as e:
            print(f"DEBUG: Multi-pass pipeline failed ({e}), falling back to vision mode...")
            return await self._parse_via_vision(file_obj, filename, target_venue, other_venues)
    
    async def _discover_structure(
        self, 
        raw_data: Dict[str, Any], 
        target_venue: str,
        other_venues: List[str]
    ) -> Dict[str, Any]:
        """LLM Pass 1: Discover document structure."""
        
        # Format cells for LLM
        formatted = self.content_extractor.format_for_llm(raw_data, max_cells=100)
        
        other_venues_str = ", ".join(other_venues) if other_venues else "none"
        
        prompt = f"""Analyze this CD Grid spreadsheet structure.

{formatted}

Target venue to find: "{target_venue}"
Other venues to find: {other_venues_str}

CD GRID STRUCTURE (confirmed pattern across all files):
- Row 1: Metadata (Guest Count, Kid Count, etc.)
- Row 2: Column headers (DATE, DAY, then venue names like "ROYAL THEATER", "STUDIO B", "TWO70")
- Row 3+: Data blocks where EACH DAY spans multiple rows:
  * First row of day block: Date, Day number (Day 1, Day 2), Event titles for each venue
  * Second row of day block: Weekday, Port name, Times for each venue event
  * Additional rows: More events, more times, departure info, etc.

IMPORTANT: Events and times are STACKED VERTICALLY in the SAME column:
- Event title appears on one row
- Time for that event appears on the row BELOW it in the same column

Identify these elements and return as JSON:
{{
    "header_row": <int - row with venue column headers (usually row 2)>,
    "date_column": <int - column with dates like "21-Dec-25" (usually column 1)>,
    "day_column": <int - column with day numbers like "Day 1" (usually column 2)>,
    "port_column": <int - column with port names like "MIAMI", "HONG KONG" (usually column 2)>,
    "data_start_row": <int - first row with event data (usually row 3)>,
    "stacking_order": "title_first",
    "rows_per_day_block": <int - how many rows make up one day's data, typically 4-6>,
    "target_venue_column": <int or null - column number for "{target_venue}">,
    "other_venue_columns": {{"venue_name": column_number, ...}}
}}

HINTS:
- Look for venue names in row 2 (like "STUDIO B", "TWO70", "ROYAL THEATER")
- Match venue names flexibly - "STUDIO B" might appear as "Studio B" or "STUDIO B"
- Match "{target_venue}" to the closest matching column header
"""

        # Use JSON mode for compatible models, text mode for others
        response = await self.model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        
        return json.loads(response.text)
    
    def _filter_to_relevant_columns(
        self, 
        raw_data: Dict[str, Any], 
        structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter raw data to only relevant columns based on discovered structure."""
        
        relevant_cols = set()
        
        # Always include date column
        if structure.get("date_column"):
            relevant_cols.add(structure["date_column"])
        
        # Include day and port columns
        if structure.get("day_column"):
            relevant_cols.add(structure["day_column"])
        if structure.get("port_column"):
            relevant_cols.add(structure["port_column"])
        
        # Include target venue column
        if structure.get("target_venue_column"):
            relevant_cols.add(structure["target_venue_column"])
        
        # Include other venue columns (only if they're in the requested list)
        for venue, col in structure.get("other_venue_columns", {}).items():
            if col:
                relevant_cols.add(col)
        
        # Filter cells
        filtered_cells = [
            cell for cell in raw_data["cells"]
            if cell["col"] in relevant_cols or cell["row"] <= structure.get("data_start_row", 5)
        ]
        
        return {
            **raw_data,
            "cells": filtered_cells,
            "structure": structure
        }
    
    async def _interpret_schedule(
        self,
        filtered_data: Dict[str, Any],
        structure: Dict[str, Any],
        target_venue: str,
        other_venues: List[str]
    ) -> Dict[str, Any]:
        """LLM Pass 2: Interpret schedule content with comprehensive parsing rules."""
        
        # Build focused prompt with filtered data
        formatted = self.content_extractor.format_for_llm(filtered_data, max_cells=200)
        
        other_venues_prompt = ""
        if other_venues and structure.get("other_venue_columns"):
            other_venues_list = ", ".join(other_venues)
            venue_cols = structure["other_venue_columns"]
            other_venues_prompt = f"""
3. OTHER VENUE SHOWS (Focus on these columns: {other_venues_list}):
   Column mappings: {json.dumps(venue_cols)}
   - For each of these other venues, extract the **Main Evening Highlights** for each day.
   - Typically include major production shows, headliners, and movies (typical start time 6pm onwards).
   - You may extract multiple significant events if available (e.g. an early movie and a late production show).
   - Ignore minor activities (like 'Open Skating', 'Dance Class') unless they are the only significant evening event.
   - Ignore any 'Back Up' or 'Backup' shows.
   - Extract:
     - venue: The name of the venue. You MUST use one of the exact strings from this list: [{other_venues_list}]. Do NOT combine names.
     - date: String in YYYY-MM-DD format
     - title: The name of the show
     - time: The display time string (e.g. "8:00 pm & 10:00 pm" or "6:30 pm"). keep the format exactly as it appears in the grid.
"""
        
        prompt = f"""Extract schedule data from this CD Grid.
Analyze the data as a strict grid structure. Focus strictly on the column for {target_venue}. 
Extract every event listed in this column for each date.
When reading the table, ignore all formatting attributes such as text color (e.g., red) or cell background colors (e.g., yellow highlights). 
These are for human emphasis only and are not part of the data to be extracted.
Your only priority is the text content and its position within the defined column boundaries.
Do not allow any color or highlighting to influence which text you select.

Ignore Saliency: Treat red text, yellow highlights, and bold fonts as identical to standard black text. They carry no special meaning.
Focus: Your attention must be distributed evenly across the grid. Do not let colored text pull your focus away from the column structure.

{formatted}

STRUCTURE INFO:
- Header row: {structure.get('header_row', 2)}
- Date column: {structure.get('date_column', 1)}
- Day/Port column: {structure.get('day_column', 2)}
- Data starts at row: {structure.get('data_start_row', 3)}
- Rows per day block: {structure.get('rows_per_day_block', 4)}
- Target venue "{target_venue}" is in column: {structure.get('target_venue_column')}

**CRITICAL - HOW TO PAIR EVENTS WITH TIMES**:
In CD Grids, each venue column contains BOTH event titles AND their times, stacked vertically:

PATTERN (within any venue column):
- Row 3: Event Title (e.g., "Ice Spectacular 365")
- Row 4: Time for that event (e.g., "8:15 pm & 10:30 pm")
- Row 5: Next event title (e.g., "Laser Tag")  
- Row 6: Time for that event (e.g., "1:00 pm - 6:00 pm")

You MUST pair: Event on Row N with Time on Row N+1 (within the same column).

Example from Column 4 (STUDIO B):
- Row 3: "Private Ice Skating" 
- Row 4: "11:30am-12:30 pm"
Result: Event "Private Ice Skating" with start_time "11:30"

- Row 5: "Ice Spectacular 365"
- Row 6: "8:15 pm & 10:30 pm" 
Result: TWO events - "Ice Spectacular 365" at 20:15 AND "Ice Spectacular 365" at 22:30

Present the output as a JSON object with the following structure:

1. ITINERARY (one entry per day):
   - day_number: Integer (e.g., 1, 2, 3)
   - date: String in YYYY-MM-DD format
   - port: String (port name or "At Sea")
   - arrival_time: String (e.g., "07:00" or null if none/cruising)
   - departure_time: String (e.g., "18:00" or "00:00" for Midnight or null if none)

2. EVENTS (from the "{target_venue}" column only):
   - title: String (event name, excluding time information)
   - start_time: String in HH:MM format (24-hour)
   - end_time: String in HH:MM format (24-hour) or null if not specified
   - date: String in YYYY-MM-DD format (match to itinerary date)
   - category: String (Must be one of the allowed categories defined below)

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
- **Port Naming**: Normalize port names that indicate navigation (e.g., 'Cruising', 'At Sea', 'Sea', 'Sea Day', 'Crossing', 'Passage') to "At Sea".
- **At Sea Times**: For "At Sea" days, `arrival_time` and `departure_time` MUST be null.

RULES IN GENERAL:
- **Date Assignment**: Always use the date corresponding to the row where the event text is physically located.
- If the column "{target_venue}" DOES NOT EXIST, return an empty list `[]`.
- Ignore "Doors open" times; use the show start time.
- 'GO' followed by a time is the start time. Also, a time followed by a 'GO' is a start time.
- Skip empty cells or cells with just "-".
- 'Perfect Day' = 'Coco Cay'.
- Ignore numbers pax (passengers) for an event.

EVENT NAMES RULES:
- 'BOTS' = 'Battle of The Sexes'.
- 'RED' = 'RED: Nightclub Experience'.
- Format headliner event names as "Headliner: " followed by the event name.
- Remove 'Production Show' from the event name.
- Event names must be formatted as title case unless it's an acronym.
- Ignore dates in the event name like (10.21 - 12.11) or similar.

CATEGORIZATION RULES:
Assign a `category` to each event based on its type. Use ONLY these categories:
- **Production Shows** (category: "show"): e.g., "Cats", "Hairspray", "Mamma Mia!", "Saturday Night Fever", "We Will Rock You", "Grease", "The Wizard of Oz", "The Effectors", "The Effectors II: Crash 'n' Burn", "Flight", "Hiro", "inTENse", "1977", "Aqua80", "Aqua80Too", "Big Daddy's Hideaway Heist", "Blue Planet", "Live. Love. Legs.", "The Gift", "Sonic Odyssey", "Starwater", "Spectra's Cabaret", "Showgirl™", "Columbus The Musical", "Can't Stop the Rock", "Fast Forward", "Gallery of Dreams", "Jackpot", "Marquee", "Music in Pictures", "Now and Forever", "Once Upon A Time", "One Sky", "Piano Man", "Pure Country", "Sequins & Feathers", "Stage to Screen", "Tango Buenos Aires", "The Beautiful Dream", "The Fine Line", "The Silk Road™", "Vibeology", "Voices", "West End to Broadway", "Wild Cool & Swingin'", "iSkate 2.0", "Ice Games", "Ice Odyssey", "Invitation to Dance", "Ballroom Fever", "Broadway Rhythm & Rhyme", "City of Dreams", "Hot Ice!", "Oceanides".
- **Headliners** (category: "headliner"): e.g., events starting with "Headliner:".
- **Movies** (category: "movie").
- **Game Shows** (category: "game"): e.g., "Love & Marriage", "Battle of the Sexes", "The Quest", "Majority Rules", "Friendly Feud", "Who Wants to Be a Royal Caribbeanaire", "The Virtual Concert", "Late-Night DJ Music and Dancing", "NextStage", "The Voice".
- **Activities** (category: "activity"): e.g., "Trivia", "Dance Class", "Karaoke", "Laser Tags", "Ice Skating".
- **Music** (category: "music"): e.g., "Live Music", "Piano", "Band", "Live Concert", "Live Performance".
- **Comedy** (category: "comedy"): e.g., "Stand-up Comedy", "Comedian", "Comedy Show", "Adult Comedy Show".
- **Party** (category: "party"): e.g., "RED: Nightclub Experience", "Nightclub".
- **Other** (category: "other"): Rehearsals, Maintenance, or anything else.

Return ONLY valid JSON matching the schema."""

        response = await self.model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=self._get_interpretation_schema(),
                temperature=0.0
            )
        )
        
        result = json.loads(response.text)
        
        # Debug logging to inspect LLM response
        print(f"DEBUG: LLM Pass 2 returned {len(result.get('events', []))} events")
        print(f"DEBUG: LLM Pass 2 returned {len(result.get('itinerary', []))} itinerary items")
        if result.get('events'):
            print(f"DEBUG: First 3 events sample:")
            for i, event in enumerate(result.get('events', [])[:3]):
                print(f"DEBUG:   Event {i}: {json.dumps(event)}")
        
        return result
    
    def _get_interpretation_schema(self) -> Dict:
        """JSON schema for Pass 2 interpretation."""
        enum_values = [
            "show", "movie", "game", "activity", "music", 
            "party", "comedy", "headliner", "rehearsal", 
            "maintenance", "other"
        ]
        
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
                            "port": {"type": "string"},
                            "arrival_time": {"type": "string"},
                            "departure_time": {"type": "string"}
                        },
                        "required": ["day_number", "date", "port"]
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
                            "category": {"type": "string", "enum": enum_values}
                        },
                        "required": ["title", "start_time", "date", "category"]
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
    
    def _transform_to_api_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Transform parsed result to API response format."""
        
        # Process events
        raw_events = result.get("events", [])
        parsed_events = []
        
        for event in raw_events:
            parsed = self._parse_single_event(event)
            if parsed:
                parsed_events.append(parsed)
        
        # Sort by start time
        parsed_events.sort(key=lambda x: x['start_dt'])
        
        # Resolve durations
        final_events = self._resolve_event_durations(parsed_events)
        
        # Format for API
        formatted_events = [self._format_event_for_api(e) for e in final_events]
        
        return {
            "itinerary": result.get("itinerary", []),
            "events": formatted_events,
            "other_venue_shows": self._filter_other_venue_shows(
                result.get("other_venue_shows", [])
            )
        }
    
    def _parse_single_event(self, event: Dict) -> Optional[Dict]:
        """Parse a single raw event into intermediate structure."""
        try:
            date_str = event["date"]
            start_time_str = event['start_time']
            start_dt = datetime.fromisoformat(f"{date_str}T{start_time_str}:00")
            
            # Smart Date Shift for late-night events
            if start_dt.hour < 4:
                start_dt += timedelta(days=1)
            
            end_time_raw = event.get("end_time")
            end_time_str = None if (end_time_raw is None or end_time_raw == "null" or end_time_raw == "") else end_time_raw
            
            return {
                "title": event["title"],
                "start_dt": start_dt,
                "end_time_str": end_time_str,
                "venue": event.get("venue", ""),
                "raw_date": date_str,
                "category": event.get("category", "other")
            }
        except (ValueError, KeyError) as e:
            print(f"Skipping malformed event: {event}, error: {e}")
            return None
    
    def _resolve_event_durations(self, events: List[Dict]) -> List[Dict]:
        """Resolve end times for events."""
        resolved_events = []
        
        for i, event in enumerate(events):
            start_dt = event['start_dt']
            end_dt = None
            
            if event['end_time_str']:
                try:
                    end_dt = datetime.fromisoformat(f"{event['raw_date']}T{event['end_time_str']}:00")
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    
                    # Prevent overlap with next event
                    if i + 1 < len(events):
                        next_event = events[i + 1]
                        if next_event['start_dt'] < end_dt:
                            end_dt = next_event['start_dt']
                except ValueError:
                    end_dt = start_dt + timedelta(hours=1)
            else:
                default_end = start_dt + timedelta(hours=1)
                if i + 1 < len(events):
                    next_event = events[i + 1]
                    if next_event['start_dt'] < default_end:
                        end_dt = next_event['start_dt']
                    else:
                        end_dt = default_end
                else:
                    end_dt = default_end
            
            event['end_dt'] = end_dt
            resolved_events.append(event)
        
        return resolved_events
    
    def _format_event_for_api(self, event: Dict) -> Dict:
        """Format event for API response."""
        return {
            "title": event["title"],
            "start": event["start_dt"].isoformat(),
            "end": event["end_dt"].isoformat(),
            "type": event.get("category", "other"),
            "venue": event.get("venue", "")
        }
    
    def _filter_other_venue_shows(self, shows: List[Dict]) -> List[Dict]:
        """Ensure only one show per venue per day."""
        grouped = {}
        for show in shows:
            key = (show.get('venue', ''), show.get('date', ''))
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(show)
        
        filtered = []
        for key, venue_shows in grouped.items():
            # Take the first one (LLM should have already picked the main show)
            filtered.append(venue_shows[0])
        
        return filtered
    
    # ========== VISION FALLBACK (Original Implementation) ==========
    
    async def _parse_via_vision(
        self, 
        file_obj: Union[str, BinaryIO], 
        filename: str, 
        target_venue: str, 
        other_venues: List[str] = []
    ) -> Dict[str, Any]:
        """Fallback: Parse using vision mode (original implementation)."""
        print("DEBUG: Using vision fallback mode...")
        
        content_to_send = []
        upload_file_obj = None
        mime_type = None
        
        try:
            if filename.lower().endswith('.pdf'):
                print("DEBUG: Converting PDF to image for vision analysis...")
                try:
                    if isinstance(file_obj, str):
                        pdf_bytes = await asyncio.to_thread(lambda: open(file_obj, 'rb').read())
                    else:
                        if hasattr(file_obj, 'seek'):
                            file_obj.seek(0)
                        pdf_bytes = await asyncio.to_thread(file_obj.read)
                        if hasattr(file_obj, 'seek'):
                            file_obj.seek(0)
                    
                    image_bytes = await asyncio.to_thread(self._convert_pdf_to_image, pdf_bytes)
                    upload_file_obj = io.BytesIO(image_bytes)
                    mime_type = "image/png"
                except Exception as e:
                    print(f"Warning: PDF to Image conversion failed ({e})")
                    raise
            
            elif filename.lower().endswith(('.xls', '.xlsx')):
                print("DEBUG: Converting Excel to CSV for vision analysis...")
                try:
                    def convert_excel():
                        import pandas as pd
                        if isinstance(file_obj, str):
                            df = pd.read_excel(file_obj)
                        else:
                            if hasattr(file_obj, 'seek'):
                                file_obj.seek(0)
                            df = pd.read_excel(file_obj)
                            if hasattr(file_obj, 'seek'):
                                file_obj.seek(0)
                        
                        output = io.StringIO()
                        df.to_csv(output, index=False)
                        return output.getvalue().encode('utf-8')
                    
                    csv_bytes = await asyncio.to_thread(convert_excel)
                    upload_file_obj = io.BytesIO(csv_bytes)
                    mime_type = "text/csv"
                except Exception as e:
                    print(f"Warning: Excel to CSV conversion failed ({e})")
                    raise
            else:
                if isinstance(file_obj, str):
                    upload_file_obj = await asyncio.to_thread(lambda: open(file_obj, 'rb'))
                else:
                    upload_file_obj = file_obj
                
                if filename.lower().endswith('.png'):
                    mime_type = "image/png"
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = "image/jpeg"
                else:
                    mime_type = "image/png"
            
            uploaded_file = await asyncio.to_thread(
                genai.upload_file,
                upload_file_obj,
                mime_type=mime_type
            )
            content_to_send.append(uploaded_file)
            
            prompt = self._create_vision_prompt(target_venue, other_venues)
            content_to_send.append(prompt)
            
            response = await self.model.generate_content_async(
                content_to_send,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=self._get_interpretation_schema(),
                    temperature=0.0
                )
            )
            
            result = json.loads(response.text)
            
            return self._transform_to_api_format(result)
            
        finally:
            if upload_file_obj and hasattr(upload_file_obj, 'close') and upload_file_obj != file_obj:
                upload_file_obj.close()
    
    def _convert_pdf_to_image(self, pdf_bytes: bytes) -> bytes:
        """Convert first page of PDF to high-res image."""
        pdf = pdfium.PdfDocument(pdf_bytes)
        page = pdf[0]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    def _create_vision_prompt(self, venue: str, other_venues: List[str]) -> str:
        """Create prompt for vision-based parsing with comprehensive rules."""
        other_venues_prompt = ""
        if other_venues:
            other_venues_list = ", ".join(other_venues)
            other_venues_prompt = f"""
3. OTHER VENUE SHOWS (Focus on these columns: {other_venues_list}):
   - For each of these other venues, extract the **Main Evening Highlights** for each day.
   - Typically include major production shows, headliners, and movies (typical start time 6pm onwards).
   - You may extract multiple significant events if available (e.g. an early movie and a late production show).
   - Ignore minor activities unless they are the only significant evening event.
   - Ignore any 'Back Up' or 'Backup' shows.
   - Extract: venue, date (YYYY-MM-DD), title, time (display string like "8:00 pm & 10:00 pm")
"""
        
        return f"""Analyze this CD Grid schedule document.
Focus strictly on the column labeled "{venue}". Extract every event listed in this column for each date.
When reading the table, ignore all formatting attributes such as text color or cell background colors.
These are for human emphasis only. Your only priority is the text content.

Present the output as a JSON object with:

1. ITINERARY (one entry per day):
   - day_number: Integer (1, 2, 3...)
   - date: String in YYYY-MM-DD format
   - port: String (port name or "At Sea")
   - arrival_time: String (HH:MM 24-hour) or null
   - departure_time: String (HH:MM 24-hour, "00:00" for Midnight) or null

2. EVENTS (from "{venue}" column only):
   - title: String (event name, excluding time information)
   - start_time: String in HH:MM format (24-hour)
   - end_time: String in HH:MM format (24-hour) or null
   - date: String in YYYY-MM-DD format
   - category: One of [show, movie, game, activity, music, party, comedy, headliner, rehearsal, maintenance, other]

{other_venues_prompt}

RULES FOR TIME PARSING:
- **Midnight**: set `start_time` to "00:00"
- **Late**: record as "03:00" (3 AM)
- **Multiple Showtimes**: "7pm & 9pm" = TWO separate events
- **Missing End Time**: set `end_time` to null, do NOT fabricate
- **Port Naming**: Normalize "Cruising", "Sea Day" to "At Sea"

EVENT NAMES RULES:
- 'BOTS' = 'Battle of The Sexes'
- 'RED' = 'RED: Nightclub Experience'
- Format headliners as "Headliner: [Name]"
- Remove 'Production Show' from names
- Event names in title case unless acronym

CATEGORIZATION RULES:
- **show**: "Cats", "Hairspray", "Mamma Mia!", "Grease", "inTENse", "Flight", "Hiro", "The Effectors", "Starwater", "iSkate 2.0", etc.
- **headliner**: events starting with "Headliner:"
- **movie**: any movie screenings
- **game**: "Love & Marriage", "Battle of the Sexes", "The Quest", "Majority Rules", "Friendly Feud", "The Voice"
- **activity**: "Trivia", "Dance Class", "Karaoke", "Laser Tags", "Ice Skating"
- **music**: "Live Music", "Piano", "Band", "Live Concert"
- **comedy**: "Stand-up Comedy", "Comedian", "Comedy Show", "Adult Comedy Show"
- **party**: "RED: Nightclub Experience", "Nightclub"
- **other**: Rehearsals, Maintenance, anything else

Return JSON with: itinerary[], events[], other_venue_shows[]
"""

