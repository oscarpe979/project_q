"""
GenAI Parser v2 - Multi-pass architecture for improved accuracy.
Uses structured extraction followed by LLM interpretation.
"""
from google import genai
from google.genai import types
from typing import Dict, Any, List, Optional, Union, BinaryIO
import json
import io
from datetime import datetime, timedelta, time as dt_time, date
import asyncio
import difflib
import os
import time

from .content_extractor import ContentExtractor
from .parser_validator import ParserValidator

# Venue Rules Configuration
from backend.app.config.venue_rules import get_source_venues, get_venue_rules

# Thinking budget for speed/quality tradeoff (0=off, -1=dynamic, 1-24576=fixed)
THINKING_BUDGET = 1024

# Retry configuration for transient API errors (503, 429, etc.)
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds


class GenAIParser:
    """Parse CD Grid PDFs/Excel using Google Gemini with multi-pass architecture."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.content_extractor = ContentExtractor()
        self.validator = ParserValidator()
    
    def _call_with_retry(self, config: types.GenerateContentConfig, prompt: str, pass_name: str = "LLM"):
        """Call LLM with retry logic for transient errors (503, 429)."""
        for attempt in range(MAX_RETRIES):
            try:
                return self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
            except Exception as e:
                error_str = str(e)
                # Check for retryable errors (503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED)
                if "503" in error_str or "429" in error_str or "UNAVAILABLE" in error_str or "overloaded" in error_str.lower():
                    if attempt < MAX_RETRIES - 1:
                        wait_time = INITIAL_BACKOFF * (2 ** attempt)
                        print(f"DEBUG: {pass_name} failed with transient error, retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(wait_time)
                        continue
                # Non-retryable error or max retries reached
                raise
    
    async def parse_cd_grid(
        self, 
        file_obj: Union[str, BinaryIO], 
        filename: str, 
        target_venue: str, 
        ship_code: str = None
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
        
        # Derive source venues from config based on ship_code and target_venue
        source_venues = get_source_venues(ship_code, target_venue) if ship_code else []
        venue_rules = get_venue_rules(ship_code, target_venue, source_venues) if ship_code else {}
        combined_other_venues = source_venues
        
        #Step 1: Extract raw structure
        print("DEBUG: Step 1 - Extracting raw structure...")
        raw_data = await asyncio.to_thread(
            self.content_extractor.extract, file_obj, filename
        )
        
        if len(raw_data.get("cells", [])) < 10:
             error_msg = "Insufficient structured data found in file. Vision fallback is disabled."
             print(f"DEBUG: {error_msg}")
             raise ValueError(error_msg)
        
        print(f"DEBUG: Extracted {len(raw_data['cells'])} cells from {raw_data['type']} file")
        
        # Initialize Token Usage Stats (including thinking tokens)
        usage_stats = {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "total_tokens": 0}
        
        # Step 2: LLM Structure Discovery (Pass 1)
        print("DEBUG: Step 2 - LLM structure discovery...")
        structure = await asyncio.to_thread(self._discover_structure, raw_data, target_venue, combined_other_venues, usage_stats)
        print(f"DEBUG: Structure discovered: {json.dumps(structure, indent=2)}")
        
        if not structure.get("target_venue_column"):
            error_msg = f"Venue '{target_venue}' not found in this CD Grid file. Available venues in header: check the file."
            print(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        
        # Step 3: Filter to relevant columns
        print("DEBUG: Step 3 - Filtering to relevant columns...")
        filtered_data = self._filter_to_relevant_columns(raw_data, structure)
        
        # Step 4: Interpret content (Pass 2)
        print("DEBUG: Step 4 - LLM content interpretation...")
        result = await asyncio.to_thread(self._interpret_schedule, filtered_data, structure, target_venue, combined_other_venues, venue_rules, usage_stats)
        
        # Log Token Usage (with thinking tokens breakdown)
        print(f"DEBUG: Token Usage Report:")
        print(f"DEBUG:   Input Tokens:    {usage_stats['input_tokens']}")
        print(f"DEBUG:   Output Tokens:   {usage_stats['output_tokens']}")
        print(f"DEBUG:   Thinking Tokens: {usage_stats['thinking_tokens']}")
        print(f"DEBUG:   Total Tokens:    {usage_stats['total_tokens']}")
        
        # Cost estimate (Gemini 2.5 Flash pricing - Dec 2024)
        # Source: https://ai.google.dev/gemini-api/docs/pricing
        # Input: $0.30 per 1M tokens (text/image/video)
        # Output (including thinking tokens): $2.50 per 1M tokens
        input_cost = (usage_stats['input_tokens'] / 1_000_000) * 0.30
        output_cost = ((usage_stats['output_tokens'] + usage_stats['thinking_tokens']) / 1_000_000) * 2.50
        total_cost = input_cost + output_cost
        print(f"DEBUG: Estimated Cost: ${total_cost:.6f} (Input: ${input_cost:.6f}, Output+Thinking: ${output_cost:.6f})")
        
        # Step 5: Validate and Repair (Deterministic)
        print("DEBUG: Step 5 - Validating results...")
        
        # Filter out events with null/missing start times (LLM sometimes returns "null" string)
        original_event_count = len(result.get("events", []))
        result["events"] = [
            e for e in result.get("events", [])
            if e.get("start_time") and str(e.get("start_time")).lower() != "null"
        ]
        filtered_count = original_event_count - len(result["events"])
        if filtered_count > 0:
            print(f"DEBUG: Filtered out {filtered_count} events with null/missing start times")
        
        validation = self.validator.validate(
            result, raw_data, target_venue, combined_other_venues
        )
        
        if validation.warnings:
            print(f"DEBUG: Validation warnings: {validation.warnings}")
        
        if not validation.is_valid:
            error_msg = f"Validation failed: {validation.errors}"
            print(f"DEBUG: {error_msg}")
            raise ValueError(error_msg)
        
        # Construct Master Duration & Metadata Maps
        # Merge self-policy and cross-venue policies
        master_duration_map = venue_rules.get("self_extraction_policy", {}).get("default_durations", {}).copy()
        metadata_rules = {} # Map of "Title" -> {type, color} or "SourceVenue" -> {type, color} (logic needed)
        
        # Add durations & metadata from merged venues (e.g. Parades)
        cross_policies = venue_rules.get("cross_venue_import_policies", {})
        for venue_name, policy in cross_policies.items():
            # Include durations from source venue if there are any merge_inclusions
            if policy.get("merge_inclusions"):
                master_duration_map.update(policy.get("default_durations", {}))
                
                # If this merge source has force settings, add them to metadata rules
                # We key them by the "venue_name" (Source) so we know which events to tag
                if policy.get("forced_type") or policy.get("custom_color"):
                    metadata_rules[venue_name] = {
                        "type": policy.get("forced_type"),
                        "color": policy.get("custom_color")
                    }
        
        # Step 6: Transform to API format
        # New Step: Pass standard renaming map for robustness against LLM misses
        renaming_map = venue_rules.get("self_extraction_policy", {}).get("renaming_map", {})
        derived_event_rules = venue_rules.get("derived_event_rules", {})
        
        # Floor transition config (only for venues like Studio B)
        floor_config = {
            "floor_requirements": venue_rules.get("self_extraction_policy", {}).get("floor_requirements"),
            "floor_transition": venue_rules.get("self_extraction_policy", {}).get("floor_transition"),
        }
        
        print("DEBUG: Step 6 - Formatting response...")
        return self._transform_to_api_format(result, master_duration_map, renaming_map, cross_policies, derived_event_rules, floor_config, venue_rules)
    
    def _discover_structure(
        self, 
        raw_data: Dict[str, Any], 
        target_venue: str,
        other_venues: List[str],
        usage_stats: Dict[str, int]
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
- STRICT COLUMN MATCHING: Map venues ONLY if the column header typically matches the venue name (e.g. "Royal Promenade" matches "Royal Promenade", "Promenade", "Royal Prom"). Do NOT map to unrelated headers like "Pool Deck" or "Activity" just because they are empty. If no text match is found, omit the venue.
"""

        # Use retry helper for transient error handling
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET)
        )
        response = self._call_with_retry(config, prompt, "Pass 1")
        
        
        # Update Usage Stats (including thinking tokens)
        if response.usage_metadata:
            print(f"DEBUG: Pass 1 usage_metadata: {response.usage_metadata}")
            usage_stats["input_tokens"] += response.usage_metadata.prompt_token_count or 0
            usage_stats["output_tokens"] += response.usage_metadata.candidates_token_count or 0
            
            # Calculate thinking tokens from total if available
            total = response.usage_metadata.total_token_count or 0
            if total > 0:
                thinking = total - (response.usage_metadata.prompt_token_count or 0) - (response.usage_metadata.candidates_token_count or 0)
                if thinking > 0:
                    usage_stats["thinking_tokens"] += thinking
                usage_stats["total_tokens"] += total
            else:
                usage_stats["total_tokens"] += (response.usage_metadata.prompt_token_count or 0) + (response.usage_metadata.candidates_token_count or 0)
            
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
    
    def _interpret_schedule(
        self,
        filtered_data: Dict[str, Any],
        structure: Dict[str, Any],
        target_venue: str,
        other_venues: List[str],
        venue_rules: Dict[str, Any],
        usage_stats: Dict[str, int]
    ) -> Dict[str, Any]:
        """LLM Pass 2: Interpret schedule content with comprehensive parsing rules."""
        
        # Build focused prompt with filtered data
        # Increase max_cells to 400 (sufficient for 35 rows * 10 cols) to avoid LLM stuttering
        formatted = self.content_extractor.format_for_llm(filtered_data, max_cells=400)
        print(f"DEBUG: Grid Snapshot sent to LLM:\n{formatted[:10000]}...")
        
        # Use venue_rules passed from parse_cd_grid
        other_venue_policies = venue_rules.get("cross_venue_import_policies", {})
        
        # Dynamically generate "Global/Self" prompt instructions from the structured map
        self_extraction = venue_rules.get("self_extraction_policy", {})
        self_renaming_map = self_extraction.get("renaming_map", {})
        known_shows = self_extraction.get("known_shows", [])
        
        custom_instructions = ""
        # Inject Known Shows (Knowledge Base)
        if known_shows:
            show_list_str = ", ".join(f'"{s}"' for s in known_shows)
            custom_instructions += f"- **KNOWN SHOWS**: This venue typically hosts: {show_list_str}. If you see text similar to these (e.g. typos), correct them to these titles.\n"

        for original, new_name in self_renaming_map.items():
            custom_instructions += f"- Rule: If you see '{original}', extract it as '{new_name}'.\n"
        
        other_venues_prompt = ""
        if other_venues and structure.get("other_venue_columns"):
            other_venues_list = ", ".join(other_venues)
            venue_cols = structure["other_venue_columns"]
            
        # Dynamically build "Other Venue" instructions based on policy
        highlight_instructions = ""
        main_import_instructions = ""
        category_instructions = ""
        
        # Split venues into "Highlights" vs "Main Event Imports"
        highlight_venues_list = []
        
        if other_venues and structure.get("other_venue_columns"):
            venue_cols = structure["other_venue_columns"]
            
            for venue in other_venues:
                policy = other_venue_policies.get(venue, {})
                inclusions = policy.get("highlight_inclusions", [])
                merge_inclusions = policy.get("merge_inclusions", [])
                
                # Check if this is a "merge all" policy ("*" in merge_inclusions)
                merge_all = "*" in merge_inclusions
                
                if merge_all:
                    # Logic for "Merged Imports" (e.g. ALL events from this venue go to main schedule)
                    col_num = venue_cols.get(venue, "unknown")
                    formatted_inclusions = ", ".join(inclusions).upper() if inclusions else "ALL EVENTS"
                    main_import_instructions += f"""
- CRITICAL IMPORT from {venue} (Column {col_num}):
  - The events in this column are run by the {target_venue} crew and MUST be added to the main 'events' list.
  - Look for events matching: {formatted_inclusions}
  - Provide them with venue="{venue}" (or "{target_venue}" if they are fully integrated).
  - Do NOT put these in 'other_venue_shows'.
"""
                    # Generate Category Rule if forced_type is set
                    forced_type = policy.get("forced_type")
                    if forced_type:
                        category_instructions += f"- **{venue} Events:** MUST be category = '{forced_type}'.\n"

                elif venue in other_venue_policies:
                    # Logic for "Highlights" (Sidebar) - ONLY if in policy
                    highlight_venues_list.append(venue)
                    if inclusions:
                        types_str = ", ".join(inclusions).upper()
                        highlight_instructions += f"\n   - STRICT RULE for {venue}: Extract events that match these types: {types_str}. If no Main Show exists, look for these fallback types."

            # If no specific policy found for a highlight venue, use defaults
            if not highlight_instructions and highlight_venues_list:
                 highlight_instructions = "\n   - Include major production shows and headliners."
            
            # Only generate the "OTHER VENUE SHOWS" block for actual highlight venues
            if highlight_venues_list:
                hl_list_str = ", ".join(highlight_venues_list)
                other_venues_prompt = f"""
3. OTHER VENUE SHOWS (Focus on these columns: {hl_list_str}):
   **CRITICAL - COLUMN BOUNDARIES:**
   {json.dumps(venue_cols, indent=3)}
   
   **STRICT COLUMN RULES - READ CAREFULLY:**
   - Each venue has ONE specific column. ONLY extract events from that EXACT column number.
   - Studio B = Column {venue_cols.get('Studio B', 'N/A')} ONLY. Do NOT read from any other column for Studio B.
   - AquaTheater = Column {venue_cols.get('AquaTheater', 'N/A')} ONLY. Do NOT read from any other column for AquaTheater.
   - Royal Promenade = Column {venue_cols.get('Royal Promenade', 'N/A')} ONLY. Do NOT read from any other column for Royal Promenade.
   - If you see an event in Column {venue_cols.get('AquaTheater', 'N/A')}, it belongs to AquaTheater, NOT Studio B.
   - NEVER assign an event to different venue based on event type or name similarity.
   **END COLUMN RULES**
   
   **EXTRACTION RULE: Extract ALL events from each venue column for each day.**
   - For EACH venue column, extract EVERY event that appears for EACH day.
   - Do NOT be selective - extract everything. Our backend algorithm will decide which one to highlight.
   - Even if there are multiple events per day for a venue, extract ALL of them.
   
   {highlight_instructions}
   - Extract:
     - venue: The name of the venue. You MUST use one of the exact strings from this list: [{hl_list_str}]. Do NOT combine names.
     - date: String in YYYY-MM-DD format
     - title: The name of the event (ONLY from the correct column for that venue)
     - category: One of [show, headliner, game, party, movie, activity, parade, backup, other]
     - time: The display time string (e.g. "8:00 pm & 10:00 pm" or "12:30 pm"). keep the format exactly as shown.

CRITICAL INSTRUCTIONS FOR TARGET VENUE ({target_venue}):
1. **NO GAP FILLING:** Do NOT assume an event ends when the next one begins.
   - If an event lists "8:00 pm" and the next one is "10:00 pm", the first event is "8:00 pm" (duration unknown or standard), NOT "8:00 pm - 10:00 pm".
   - Only extract an end time if it is EXPLICITLY printed (e.g. "8:00 pm - 9:00 pm").
   - If no end time is printed, leave the end time null.

2. **Stacking:** If multiple events are in the same cell stack, extract them as separate events.


"""
        prompt = f"""Extract schedule data from this CD Grid.
Analyze the data as a strict grid structure. Focus strictly on the column for {target_venue}. 

VENUE SPECIFIC CONTEXT ({target_venue}):
{custom_instructions}
{main_import_instructions}

FORMATTING RULES:
When reading the table, ignore all formatting attributes such as text color or cell background colors.
- Background Color: A dark or gray background does NOT mean the event is cancelled. It is just styling.
- Strikethrough: ONLY if the text has a visible line drawing through it (crossed out), treat it as CANCELLED.
- Mixed Cells: A cell may contain one active event and one crossed-out event. Extract the active one.
- Saliency: Treat red text, yellow highlights, and bold fonts as identical to standard black text.
Your priority is the text content and its position within the defined column boundaries.

{formatted}

STRUCTURE INFO:
- Header row: {structure.get('header_row', 2)}
- Date column: {structure.get('date_column', 1)}
- Day/Port column: {structure.get('day_column', 2)}
- Data starts at row: {structure.get('data_start_row', 3)}
- Rows per day block: {structure.get('rows_per_day_block', 4)}
- Target venue "{target_venue}" is in column: {structure.get('target_venue_column')}

HOW TO PAIR EVENTS WITH TIMES:
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

MULTI-SESSION EVENTS:
Sometimes an event header (like "Ice Skating (5+1hrs)") is followed by multiple time slots:
- Row 20: "Ice Skating (5+1hrs)"
- Row 21: "5:00 pm - 6:00 pm (1hr) TEENS"
- Row 22: "6:00 pm - 8:00 pm (2hrs)"
- Row 23: "8:30 pm - 11:30 pm (3hrs)"

Extract each time slot as a SEPARATE event using the header as the base title:
Result: THREE events:
1. "Teens Ice Skating" from 17:00 to 18:00 (TEENS modifier becomes part of title)
2. "Ice Skating" from 18:00 to 20:00
3. "Ice Skating" from 20:30 to 23:30

PERFORMER NAMES (Combine into one event title):
Sometimes an event is followed by a performer name on the next row:
- Row 41: "Adult Comedy LIVE! (18+) @ 10:15 PM"
- Row 42: "Simeon Kirkiles & Collin Moulton"

Combine them into ONE event with the performer in the title:
Result: ONE event - "Adult Comedy: Simeon Kirkiles & Collin Moulton" at 22:15
Do NOT create two separate events. The performer row has no time of its own.

OUTPUT FORMAT - Present as JSON with:

1. ITINERARY (one entry per day):
   - day_number: Integer (e.g., 1, 2, 3)
   - date: String in YYYY-MM-DD format
   - port: String (port name or "At Sea")
   - arrival_time: String (e.g., "07:00" or null if none/cruising)
   - departure_time: String (e.g., "18:00" or "00:00" for Midnight or null if none)

2. EVENTS (from the "{target_venue}" column only):
   Extract EVERY event in this column - both guest-facing and operational:
   - Guest shows: productions, movies, comedy, headliners
   - Technical events: Aerial Install, Tech Run, Rehearsal, Sound Check
   - Any text with times that reserves venue time
   
   **CRITICAL: ONLY extract items that have a clearly stated time (e.g., "7:30 pm", "10:00 am - 2:00 pm", etc.).**
   **SKIP informational notes or labels that don't have times (e.g., "New Cast on Muster 2.0", "Group Notes", dress codes).**
   
   Fields:
   - title: String (event name, excluding time information)
   - start_time: String in HH:MM format (24-hour)
   - end_time: String in HH:MM format (24-hour) or null if not specified
   - date: String in YYYY-MM-DD format (match to itinerary date)
   - category: String (Must be one of the allowed categories defined below)

{other_venues_prompt}

Please note the below rules:

RULES FOR TIME PARSING:
- **Midnight**: If the text says "Midnight", set `start_time` to "00:00".
- **Late**: If an end time is "Late", record it as "01:00" (1 AM).
- **Overnight**: If an event starts before midnight (e.g., 23:00) and ends after (e.g., 00:30), the start date is the current day.
- **24-Hour Format**: Convert all times to HH:MM 24-hour format.
- **Noon**: Convert "Noon" to "12:00".
- **Multiple Showtimes**: If an event lists multiple times separated by '&', 'and', or '/' (e.g., "7:00 pm & 9:00 pm"), you MUST create TWO separate event entries. EXCEPTION: If the times are followed by a duration in parentheses (e.g. "2:00 pm/4:30 pm (2.5hrs)"), treat it as a SINGLE event from Start to End.
- **Missing End Time**: If an event only lists a start time (e.g., "10:00 pm"), you MUST set `end_time` to `null`. Do NOT guess or fabricate an end time. NEVER use "00:00" as a default end time unless the text explicitly says "Midnight" or "12:00 am" for the end time.
- **Port Naming**: Normalize port names that indicate navigation (e.g., 'Cruising', 'At Sea', 'Sea', 'Sea Day', 'Crossing', 'Passage') to "At Sea".
- **At Sea Times**: For "At Sea" days, `arrival_time` and `departure_time` MUST be null.

RULES IN GENERAL:
- **Date Assignment**: Always use the date corresponding to the row where the event text is physically located.
  - **CRITICAL**: Use the "Row N" indicators in the input. A day's block ends ONLY when the NEXT date appears in Column 1 or 2.
  - If Day 5 starts at Row 20, and Day 6 starts at Row 26, then ANY event on Rows 20-25 BELONGS TO DAY 5.
  - Do NOT shift events to the next day just because they look like they belong there. Trust the Row numbers.
- If the column "{target_venue}" DOES NOT EXIST, return an empty list `[]`.
- Ignore "Doors open" times; use the show start time.
- 'GO' followed by a time is the start time. Also, a time followed by a 'GO' is a start time.
- Skip empty cells or cells with just "-".
- 'Perfect Day' = 'Coco Cay'.
- Ignore numbers pax (passengers) for an event.

EVENT NAMES RULES:
- 'BOTS' = 'Battle of The Sexes'.
- 'RED' = 'RED: Nightclub Experience'.
- **HEADLINER FORMAT RULES** (CRITICAL):
  - Headliner events MUST be formatted as "Headliner: [Act Name]" (with colon and space).
  - "Headliner Showtime" or just "Headliner" is a PLACEHOLDER LABEL, not the actual event name.
  
  **Multi-line Pattern A (Label → Time → Name)** - Common in CD Grids:
    * Row N: "Headliner Showtime" or "Headliner" (LABEL - ignore as title)
    * Row N+1: The TIME (e.g., "9:15 PM")
    * Row N+2: The ACTUAL ACT NAME (e.g., "Randy Cabral (Juggler)")
    * → Extract as: "Headliner: Randy Cabral" with start_time from Row N+1
  
  **Multi-line Pattern B (Label → Name → Time)**:
    * Row N: "Headliner" or "Headliner Show" (LABEL - ignore as title)
    * Row N+1: The ACTUAL ACT NAME (e.g., "John Smith")
    * Row N+2: The TIME (e.g., "8:00 PM")
    * → Extract as: "Headliner: John Smith" with start_time from Row N+2
  
  **Single-line format**: "Headliner John Smith" or "Headliner: John Smith" all on one row
    * → Extract as: "Headliner: John Smith"
  
  **How to detect which pattern**: Look at Row N+1. If it looks like a TIME (contains "pm", "am", ":", or numbers like "21:15"), use Pattern A. If it looks like a NAME (text without time indicators), use Pattern B.
  
  - The text "(Juggler - 7/20 - 8/17)" is metadata - REMOVE IT from the title.
  - Do NOT extract "Headliner Showtime" as the event title.
- Remove 'Production Show' from the event name.
- Event names must be formatted as title case unless it's an acronym.
- **Date Ranges**: If an event title contains a date range (e.g. "7/20 - 8/17"), REMOVE IT from the title string.
- **Parenthetical Metadata**: Remove act type descriptions in parentheses like "(Juggler)", "(Comedian)", "(Magician)" from the title.
- **Red Carpet Movie**: If an event starts with "Red Carpet Movie" followed by a dash and movie name (e.g., "Red Carpet Movie - Minecraft Movie"), extract it as just "Red Carpet Movie". The specific movie title changes weekly and should be stripped.

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
- **Parade** (category: "parade"): e.g., "Parade", "Anchors Aweigh Parade".
- **Top Tier Event** (category: "toptier"): e.g., "Top Tier Event", "Top Tier".
- **Other** (category: "other"): Rehearsals, Maintenance, or anything else.
{category_instructions}

Return ONLY valid JSON matching the schema."""

        # Use retry helper for transient error handling
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=self._get_interpretation_schema(),
            temperature=0.1,  # Small temp to help escape repetition loops
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET)
        )
        response = self._call_with_retry(config, prompt, "Pass 2")
        
        # Update Usage Stats (including thinking tokens)
        if response.usage_metadata:
            print(f"DEBUG: Pass 2 usage_metadata: {response.usage_metadata}")
            usage_stats["input_tokens"] += response.usage_metadata.prompt_token_count or 0
            usage_stats["output_tokens"] += response.usage_metadata.candidates_token_count or 0
            
            # Calculate thinking tokens from total if available
            total = response.usage_metadata.total_token_count or 0
            if total > 0:
                thinking = total - (response.usage_metadata.prompt_token_count or 0) - (response.usage_metadata.candidates_token_count or 0)
                if thinking > 0:
                    usage_stats["thinking_tokens"] += thinking
                usage_stats["total_tokens"] += total
            else:
                usage_stats["total_tokens"] += (response.usage_metadata.prompt_token_count or 0) + (response.usage_metadata.candidates_token_count or 0)
        
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"ERROR: LLM JSON Parse Failed: {e}")
            print(f"DEBUG: Broken JSON Snippet: {response.text[-500:]}") # Last 500 chars
            raise ValueError(f"LLM produced invalid JSON: {e}")
        
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
            "maintenance", "other", "parade", "toptier"
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
                            "time": {"type": "string"},
                            "category": {"type": "string", "enum": enum_values}
                        },
                        "required": ["venue", "date", "title", "time", "category"]
                    }
                }
            },
            "required": ["itinerary", "events"]
        }
    
    def _transform_to_api_format(self, result: Dict[str, Any], default_durations: Dict[str, int] = {}, renaming_map: Dict[str, str] = {}, cross_venue_policies: Dict = {}, derived_event_rules: Dict = {}, floor_config: Dict = {}, venue_rules: Dict = {}) -> Dict[str, Any]:
        """Transform parsed result to API response format."""
        
        # Process events
        raw_events = result.get("events", [])
        parsed_events = []
        
        for event in raw_events:
            # 1. Standardize Title (Force Renaming with Fuzzy Match)
            raw_title = event.get("title", "")
            event["title"] = self._apply_renaming_robust(raw_title, renaming_map)
            
            # 2. Normalize Title (Strip redundant text like "Game Show")
            event["title"] = self._normalize_title(event["title"])
            
            parsed = self._parse_single_event(event)
            if parsed:
                parsed_events.append(parsed)
        
        
        # SELECTIVE MERGE LOGIC (Crucial for split venues like Royal Promenade)
        # We need to process "other_venue_shows" and decide which ones move to "Main Events"
        # and which ones stay in "Footer", based on the Policy.
        
        raw_other_shows = result.get("other_venue_shows", [])
        print(f"DEBUG: Found {len(raw_other_shows)} raw other venue shows")
        print(f"DEBUG: Raw Other Shows Dump: {json.dumps(raw_other_shows, indent=2)}")
        final_other_shows = []
        
        for show in raw_other_shows:
            raw_venue = show.get('venue', '')
            
            # Clean Title (Headliner Prefix)
            import re
            raw_title_clean = show.get("title", "")
            if raw_title_clean:
                # Remove "Headliner:" prefix if present
                raw_title_clean = re.sub(r'(?i)^headliner:\s*', '', raw_title_clean)
                show["title"] = raw_title_clean
            
            # Normalize Venue Name to match Policy Keys (e.g. "Royal Prom" -> "Royal Promenade")
            matched_venue_key = raw_venue
            best_ratio = 0.0
            for policy_key in cross_venue_policies.keys():
                # Direct match
                if raw_venue.lower() == policy_key.lower():
                    matched_venue_key = policy_key
                    break
                # Substring match "Royal Prom" in "Royal Promenade"
                if raw_venue.lower() in policy_key.lower() or policy_key.lower() in raw_venue.lower():
                     matched_venue_key = policy_key
                # Fuzzy match
                ratio = difflib.SequenceMatcher(None, raw_venue.lower(), policy_key.lower()).ratio()
                if ratio > 0.8 and ratio > best_ratio:
                    best_ratio = ratio
                    matched_venue_key = policy_key
            
            # Update the show object with the correct canonical venue name
            show['venue'] = matched_venue_key
            policy = cross_venue_policies.get(matched_venue_key, {})
            
            # Check Merge Criteria based on merge_inclusions
            is_merged = False
            merge_inclusions = policy.get("merge_inclusions", [])
            
            # 1. Global Merge ("*" means all events from this venue go to Main)
            if "*" in merge_inclusions:
                is_merged = True
            
            # 2. Selective Merge (Specific titles go to Main)
            # e.g. "Royal Promenade" -> merge_inclusions: ["Anchors Aweigh Parade"]
            elif merge_inclusions:
                raw_title_other = show.get("title", "")
                # Check against whitelist
                for inclusion in merge_inclusions:
                    # Use fuzzy match or substring
                    if inclusion.lower() in raw_title_other.lower():
                        is_merged = True
                        break
            
            if is_merged:
                # Move to Main Events!
                # Apply Policy Renaming first
                renaming = policy.get('renaming_map', {})
                show['title'] = self._apply_renaming_robust(show.get('title', ''), renaming)
                
                # Apply Default Duration if set
                def_dur = policy.get('default_durations', {})
                # Try specific title match
                duration = def_dur.get(show['title'])
                
                # 3. Normalize Time (Highlights use 'time', Main uses 'start_time')
                raw_time = show.get("time", "")
                if not show.get("start_time") and raw_time:
                    # Clean clean time string
                    clean_time = raw_time.lower().replace(".", "").strip() # "12:30 p.m." -> "12:30 pm"
                    
                    found_time = False
                    # Format 1: "12:30 pm" / "12:30pm"
                    try:
                         # Manual split to handle "12:30pm" vs "12:30 pm"
                         if "pm" in clean_time or "am" in clean_time:
                             # Remove am/pm to get time part
                             t_part = clean_time.replace("pm", "").replace("am", "").strip()
                             is_pm = "pm" in clean_time
                             
                             t_obj = datetime.strptime(t_part, "%H:%M") # "12:30"
                             # Adjust 12-hour
                             if is_pm and t_obj.hour < 12:
                                 t_obj += timedelta(hours=12)
                             elif not is_pm and t_obj.hour == 12:
                                 t_obj = t_obj.replace(hour=0)
                             
                             show['start_time'] = t_obj.strftime("%H:%M")
                             found_time = True

                         if not found_time:
                             # Format 1.5: HH:MM:SS (Excel/ISO style) e.g. "12:30:00"
                             match_hms = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', clean_time)
                             if match_hms:
                                 hh = int(match_hms.group(1))
                                 mm = int(match_hms.group(2))
                                 # Assuming 24h format if no AM/PM provided and it looks like an ISO time
                                 if hh < 12 and "pm" in clean_time: hh += 12 # unlikely with this format but possible
                                 show['start_time'] = f"{hh:02d}:{mm:02d}"
                                 found_time = True

                         if not found_time:
                             match_simple = re.search(r'(\d{1,2}):(\d{2})', clean_time)
                             if match_simple:
                                # Heuristic: If > 12:00, it's 24h. If not, assume PM for evening events.
                                # But parade is 12:30. 12:30 is 12:30 PM.
                                hh = int(match_simple.group(1))
                                mm = int(match_simple.group(2))
                                
                                # Standard PM logic for ambiguous times if it's clearly afternoon/evening context?
                                # For now, just capture it.
                                show['start_time'] = f"{hh:02d}:{mm:02d}"
                                found_time = True
                             else:
                                 # Try pure 24h
                                 t_obj = datetime.strptime(clean_time, "%H:%M")
                                 show['start_time'] = t_obj.strftime("%H:%M")
                                 found_time = True
                    except ValueError:
                        print(f"DEBUG: Time parsing failed for '{raw_time}'")

                # Note: We rely on _resolve_event_durations later to set 'end_dt', 
                # but we need to ensure 'end_time' string is set if we know the duration now?
                # Actually _resolve_event use default_durations map.
                # So we just need to ensure title matches policy or we pass specific duration later?
                # Ideally, we update valid default_durations with our merged policy ones?
                # We already updated master_duration_map in Step 5.
                
                # Set category for merged event (important for coloring)
                # 1. Use policy's forced_type if specified
                # 2. Infer from title if contains known category keywords
                if not show.get("category"):
                    forced_type = policy.get("forced_type")
                    if forced_type:
                        show["category"] = forced_type
                    else:
                        # Infer from title
                        title_lower = show.get("title", "").lower()
                        if "parade" in title_lower:
                            show["category"] = "parade"
                        elif "party" in title_lower:
                            show["category"] = "party"
                        elif "movie" in title_lower:
                            show["category"] = "movie"
                        # else: will default to "other" in _parse_single_event
                
                parsed_main = self._parse_single_event(show)
                if parsed_main:
                    if policy.get("custom_color"):
                         parsed_main['color'] = policy.get("custom_color")
                    
                    # Mark as merged from another venue (for intervening event check)
                    parsed_main['is_merged'] = True
                    
                    parsed_events.append(parsed_main)
                    
                    # IMPORTANT: Merged events should ALSO appear in highlights!
                    # The parade goes to main schedule but should still show as a highlight for that venue/day
                    show['time'] = self._clean_time_string(show.get('time', ''))
                    final_other_shows.append(show)
                else:
                     # Failed to parse (bad time?) - Safe Fallback: Keep in Footer
                     print(f"DEBUG: Merge failed for '{show.get('title')}' (time parse error?), returning to Footer")
                     # Clean the time string for display (remove parens, fix seconds, etc.)
                     show['time'] = self._clean_time_string(show.get('time', ''))
                     final_other_shows.append(show)
            else:
                # Not merged - Clean and keep in Footer
                show['time'] = self._clean_time_string(show.get('time', ''))
                final_other_shows.append(show)

        # Sort by start time (Main Events + Merged Events)
        parsed_events.sort(key=lambda x: x['start_dt'])
        
        # Resolve durations (Main Events + Merged Events)
        final_events = self._resolve_event_durations(parsed_events, default_durations)
        
        # Apply derived event rules (doors, rehearsals, etc.)
        if derived_event_rules:
            final_events = self._apply_derived_event_rules(final_events, derived_event_rules)
        
        # Apply floor transition rules (Studio B only - ice/floor changes)
        if floor_config.get("floor_requirements"):
            final_events = self._apply_floor_transition_rules(final_events, floor_config)
        

        # FINAL MERGE: Combine any overlapping setup/strike/preset events
        # This handles cases like "Strike & Ice Scrape" overlapping with "Set Up Nightclub"
        final_events = self._merge_overlapping_operations(final_events)
        

        # RESOLVE OVERLAPS: Ensure no strike/setup overlaps with actual events
        # - Strikes get omitted if they overlap with actual events
        # - Setups bump earlier to not overlap with events
        final_events = self._resolve_operation_overlaps(final_events)
        

        # LATE NIGHT HANDLING: Handle derived events that start after midnight
        # - After voyage end: Remove completely  
        # - On/before last day: Reschedule to 9 AM same day, merge or drop if overlapping
        late_night_config = venue_rules.get("self_extraction_policy", {}).get("late_night_config")
        if late_night_config:
            # Get voyage end date from itinerary
            itinerary = result.get("itinerary", [])
            voyage_end_date = None
            if itinerary:
                # Find the last date in the itinerary
                dates = []
                for item in itinerary:
                    date_str = item.get("date")
                    if date_str:
                        try:
                            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                            dates.append(parsed_date)
                        except ValueError:
                            pass
                if dates:
                    voyage_end_date = max(dates)
            
            final_events = self._handle_late_night_derived_events(
                final_events, late_night_config, voyage_end_date
            )
        
        # Format for API
        formatted_events = [self._format_event_for_api(e) for e in final_events]
        

        # Filter other venue shows to Unique & Renamed
        footer_shows = self._filter_other_venue_shows(final_other_shows, cross_venue_policies)
        
        return {
            "itinerary": self._clean_itinerary(result.get("itinerary", [])),
            "events": formatted_events,
            "other_venue_shows": self._filter_other_venue_shows(
                final_other_shows, # Pass the filtered list
                cross_venue_policies
            )
        }
    
    
    def _clean_time_string(self, time_str: str) -> str:
        """Clean raw time strings for display (e.g. '6:30 pm (PG-13)' -> '6:30 pm')."""
        if not time_str:
            return ""
        
        import re
        # Lowercase and standard cleaning
        clean = time_str.lower().strip()
        
        # Remove parenthetical notes like (PG-13), (2.5hrs)
        clean = re.sub(r'\s*\(.*?\)', '', clean)
        
        # Normalize "midnight"
        if "midnight" in clean:
            clean = clean.replace("midnight", "12:00 am")
        
        
        # Normalize "midnight"
        if "midnight" in clean:
            clean = clean.replace("midnight", "12:00 am")
        
        # Normalize seconds: Remove ":00" if not followed by a digit (e.g. 12:30:00 -> 12:30)
        # Matches ":00" at end of string or followed by space/non-digit
        clean = re.sub(r':00(?!\d)', '', clean)
        
        # Normalize "5pm" to "5:00 pm" or "5:30pm" to "5:30 pm"
        # 1. "5pm" -> "5:00 pm"
        # Fix: Add (?<!:) to ensure we don't match minutes in "7:15 pm"
        clean = re.sub(r'(?<!:)\b(\d{1,2})\s*([ap]m)\b', r'\1:00 \2', clean)
        # 2. Add space if missing: "6:30pm" -> "6:30 pm"
        clean = re.sub(r'(\d{2})\s*([ap]m)\b', r'\1 \2', clean)
        
        # 3. Convert 24h "HH:MM" to 12h "H:MM pm" if no am/pm is present
        # Use a callback to handle multiple occurrences (e.g. "21:30 & 23:00")
        def to_12h(match):
            hh = int(match.group(1))
            mm = int(match.group(2))
            
            ampm = "am"
            if hh >= 12:
                ampm = "pm"
            
            hh_12 = hh
            if hh > 12:
                hh_12 = hh - 12
            elif hh == 0:
                hh_12 = 12
                
            return f"{hh_12}:{mm:02d} {ampm}"

        # Match "HH:MM" NOT followed by am/pm
        clean = re.sub(r'\b(\d{1,2}):(\d{2})\b(?!\s*[ap]m)', to_12h, clean)
        
        return clean.strip()
    
    def _apply_renaming_robust(self, raw_title: str, renaming_map: Dict[str, str]) -> str:
        """Apply renaming using robust fuzzy matching (SequenceMatcher)."""
        if not raw_title:
            return raw_title
            
        best_match = None
        best_ratio = 0.0
        
        # 1. Exact/Substring Case-Insensitive Match (Fast)
        for pattern, new_name in renaming_map.items():
            if pattern.lower() in raw_title.lower():
                return new_name
        
        # 2. Fuzzy Match (Slower, for typos)
        # Check against all patterns
        for pattern, new_name in renaming_map.items():
            ratio = difflib.SequenceMatcher(None, pattern.lower(), raw_title.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = new_name
        
        # Threshold: 0.8 (allows for ~1-2 wrong letters in a medium word)
        if best_ratio >= 0.8:
            return best_match
            
        return raw_title
    
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
    
    def _resolve_event_durations(self, events: List[Dict], default_durations: Dict[str, int]) -> List[Dict]:
        """Resolve end times for events."""
        resolved_events = []
        
        for i, event in enumerate(events):
            start_dt = event['start_dt']
            end_dt = None
            
            if event['end_time_str']:
                try:
                    # Parse explicit end time
                    end_dt = datetime.fromisoformat(f"{event['raw_date']}T{event['end_time_str']}:00")
                    # Handle crossing midnight
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    
                    # LOGIC FIX: If end time is EXACTLY Match start time (0 length) or suspiciously just 00:00 (Midnight)
                    # AND we have a better default duration, override it.
                    duration_min = (end_dt - start_dt).total_seconds() / 60
                    
                    # Check if we have a specific default override
                    best_match_minutes = None
                    for key, mm in default_durations.items():
                         if key.lower() in event.get("title", "").lower():
                             best_match_minutes = mm
                             break
                    
                    # Override if we have a match and the parsed duration is exactly midnight (probably a default)
                    # or if the duration seems excessive (> 3 hours) for a show.
                    if best_match_minutes and (event['end_time_str'] == "00:00" or duration_min > 180):
                         print(f"DEBUG: Overriding parsed duration ({duration_min}m) with default ({best_match_minutes}m) for {event['title']}")
                         end_dt = start_dt + timedelta(minutes=best_match_minutes)

                except ValueError:
                    # Fallback if invalid format
                    end_dt, end_is_late = self._calculate_default_end(start_dt, event.get("title", ""), default_durations)
                    event['end_is_late'] = end_is_late
            else:
                # No end time provided: Use Rule-based or Standard Duration
                end_dt, end_is_late = self._calculate_default_end(start_dt, event.get("title", ""), default_durations)
                event['end_is_late'] = end_is_late
            
            # Check if LLM returned 01:00 for end time (indicating "Late")
            if event.get('end_time_str') == '01:00' and not event.get('end_is_late'):
                # LLM converted "Late" to "01:00" - mark it as late
                event['end_is_late'] = True
            
            # Simple sanity check: If end_dt overlaps drastically with next start, maybe truncate?
            if i + 1 < len(events):
                next_event = events[i + 1]
                if next_event['start_dt'] < end_dt and next_event['start_dt'] > start_dt:
                    end_dt = next_event['start_dt']
            
            event['end_dt'] = end_dt
            resolved_events.append(event)
        
        return resolved_events

    def _calculate_default_end(self, start_dt: datetime, title: str, duration_map: Dict[str, int]) -> tuple:
        """
        Calculate end time based on title match or default 45 mins.
        Returns: (end_dt, is_late) - is_late is True if end time represents "Late"
        """
        title_lower = title.lower()
        
        # Special handling for RED party / Nightclub events - they end "late" (1 AM)
        if 'red' in title_lower and ('nightclub' in title_lower or 'party' in title_lower):
            # End at 1 AM next day - mark as "late"
            next_day = start_dt.date() + timedelta(days=1)
            return (datetime.combine(next_day, dt_time(1, 0)), True)
        
        # Find best matching duration
        minutes = 60 # Fallback
        
        # Exact or partial match in duration map
        # duration_map keys might be 'inTENse', 'Ice Spectacular'
        # title might be 'inTENse' (cleaned) or 'Ice Spectacular 365' (raw)
        for key, duration in duration_map.items():
            if key.lower() in title_lower:
                minutes = duration
                break
        
        return (start_dt + timedelta(minutes=minutes), False)
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize event title by stripping redundant text patterns.
        
        Examples:
            "Battle of the Sexes Game Show" -> "Battle of the Sexes"
            "Perfect Couple - Game Show" -> "Perfect Couple"
            "Game Show: Quiz Night" -> "Quiz Night" (if this pattern exists)
        """
        if not title:
            return title
        
        import re
        
        # Patterns to strip (case-insensitive)
        # Order matters - more specific patterns first
        patterns = [
            r'\s*-\s*Game Show$',   # " - Game Show" suffix
            r'\s+Game Show$',       # " Game Show" suffix
            r'^Game Show:\s*',      # "Game Show: " prefix
        ]
        
        normalized = title
        for pattern in patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        return normalized.strip()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DERIVED EVENT RULES ENGINE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _event_matches_rule(self, event: Dict, rule: Dict) -> bool:
        """
        Check if an event matches rule criteria (title or category).
        Uses fuzzy matching for title comparison to handle typos.
        
        Args:
            event: Event dict with 'title' and 'category' keys
            rule: Rule dict with optional 'match_titles', 'match_categories', and 'match_threshold'
        
        Returns:
            True if event matches any rule criteria
        """
        # Title match - fuzzy matching with similarity threshold
        if "match_titles" in rule:
            event_title = event.get("title", "").lower()
            match_threshold = rule.get("match_threshold", 0.8)  # Default 80% similarity
            
            for pattern in rule["match_titles"]:
                pattern_lower = pattern.lower()
                
                # First try exact substring match (fast path)
                if pattern_lower in event_title:
                    return True
                
                # Then try fuzzy matching on the full title
                similarity = difflib.SequenceMatcher(None, pattern_lower, event_title).ratio()
                if similarity >= match_threshold:
                    return True
                
                # Also check if pattern is similar to any word in the title
                # This helps match "Ice Skating" to "Open Ice Skatng Session"
                title_words = event_title.split()
                pattern_words = pattern_lower.split()
                
                # Check if all pattern words fuzzy-match words in title
                if len(pattern_words) > 1:
                    matched_words = 0
                    for p_word in pattern_words:
                        for t_word in title_words:
                            word_sim = difflib.SequenceMatcher(None, p_word, t_word).ratio()
                            if word_sim >= match_threshold:
                                matched_words += 1
                                break
                    if matched_words == len(pattern_words):
                        return True
        
        # Category match (broad) - exact match
        if "match_categories" in rule:
            event_category = event.get("category", "other")
            if event_category in rule["match_categories"]:
                # Check exclude_titles - if event matches any excluded title, skip this rule
                if "exclude_titles" in rule:
                    event_title = event.get("title", "").lower()
                    for excluded in rule["exclude_titles"]:
                        if excluded.lower() in event_title or event_title in excluded.lower():
                            return False
                return True
        
        return False
    
    def _create_derived_event(self, parent: Dict, rule: Dict) -> Optional[Dict]:
        """
        Create a derived event based on parent event and rule configuration.
        
        Args:
            parent: Parent event dict with 'start_dt', 'end_dt', 'title', etc.
            rule: Rule configuration with offset, duration, template, styling
        
        Returns:
            Derived event dict or None if creation fails
        """
        try:
            offset = timedelta(minutes=rule["offset_minutes"])
            duration = timedelta(minutes=rule["duration_minutes"])
            
            # Determine anchor point (start or end of parent event)
            anchor = rule.get("anchor", "start")
            if anchor == "end":
                base_time = parent["end_dt"]
            else:
                base_time = parent["start_dt"]
            
            derived_start = base_time + offset
            derived_end = derived_start + duration
            
            # Format title with template (supports {parent_title} placeholder)
            parent_title = parent.get("title", "")
            title = rule["title_template"].format(parent_title=parent_title)
            
            return {
                "title": title,
                "start_dt": derived_start,
                "end_dt": derived_end,
                "category": rule.get("type", "other"),
                "type": rule.get("type", "other"),
                "venue": parent.get("venue", ""),
                "raw_date": derived_start.strftime("%Y-%m-%d"),
                "is_derived": True,
                "parent_title": parent_title if parent_title else None,
                "styling": rule.get("styling", {})
            }
        except (KeyError, ValueError) as e:
            print(f"Error creating derived event: {e}")
            return None
    
    def _apply_derived_event_rules(
        self, 
        events: List[Dict], 
        derived_rules: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Generate derived events (doors, rehearsals, setup, strike) based on rules.
        
        Args:
            events: List of parsed events with 'start_dt', 'end_dt', 'title', 'category'
            derived_rules: Dict keyed by rule type ('doors', 'rehearsal', etc.)
        
        Returns:
            Original events + generated derived events, sorted by start time
        
        Note:
            Uses "first match wins" strategy - once an event matches a rule of a 
            particular type, it won't be matched by other rules of the same type.
            
            If a rule has "first_per_day": True, it only matches the earliest 
            occurrence of matching events per day.
        """
        if not derived_rules:
            return events
        
        derived_events = []
        
        for rule_type, rules in derived_rules.items():
            # Track which parent events have already been matched for this rule type
            matched_parent_keys = set()
            
            for rule in rules:
                # Check special per-day processing modes
                first_per_day = rule.get("first_per_day", False)
                skip_last_per_day = rule.get("skip_last_per_day", False)
                
                if first_per_day:
                    # Group matching events by date and only process the first of each day
                    # Note: first_per_day rules are INDEPENDENT - multiple rules CAN
                    # match the same parent event (e.g., Specialty Ice + Cast warm ups)
                    matching_by_date = {}
                    count_by_date = {}
                    
                    for parent_event in events:
                        if self._event_matches_rule(parent_event, rule):
                            event_date = parent_event.get('start_dt').date()
                            count_by_date[event_date] = count_by_date.get(event_date, 0) + 1
                            
                            if event_date not in matching_by_date:
                                matching_by_date[event_date] = parent_event
                            elif parent_event.get('start_dt') < matching_by_date[event_date].get('start_dt'):
                                matching_by_date[event_date] = parent_event
                    
                    # Check min_per_day requirement (e.g., only fire if 2+ shows)
                    min_per_day = rule.get("min_per_day", 1)
                    
                    # Process only the first matching event of each day (if min requirement met)
                    for event_date, parent_event in matching_by_date.items():
                        if count_by_date.get(event_date, 0) >= min_per_day:
                            parent_key = (parent_event.get('title'), parent_event.get('start_dt'))
                            derived = self._create_derived_event(parent_event, rule)
                            if derived:
                                derived_events.append(derived)
                
                elif rule.get("last_per_day", False):
                    # Fire after the LAST matching event of each CALENDAR DAY
                    # Optional: skip_if_next_matches - skip if the next venue event also matches this rule
                    skip_if_next = rule.get("skip_if_next_matches", False)
                    
                    # Only apply deduplication for category catch-all rules
                    is_catch_all = rule.get("match_categories") is not None and rule.get("match_titles") is None
                    
                    # Collect all matching events
                    matching_events = []
                    for parent_event in events:
                        if self._event_matches_rule(parent_event, rule):
                            parent_key = (parent_event.get('title'), parent_event.get('start_dt'))
                            if is_catch_all and parent_key in matched_parent_keys:
                                continue
                            matching_events.append(parent_event)
                    
                    if not matching_events:
                        continue
                    
                    # Sort by start time
                    matching_events.sort(key=lambda x: x.get('start_dt'))
                    
                    if skip_if_next:
                        # Skip if next venue event also matches this rule
                        # Get all venue events sorted by time (exclude derived and merged)
                        target_venue = matching_events[0].get('venue', '')
                        all_venue_events = [
                            e for e in events 
                            if e.get('venue') == target_venue
                            and not e.get('is_derived', False)
                            and not e.get('is_merged', False)
                        ]
                        all_venue_events.sort(key=lambda x: x.get('start_dt'))
                        
                        # For each matching event, check if the NEXT venue event also matches
                        for i, parent_event in enumerate(matching_events):
                            # Find this event's position in venue timeline
                            try:
                                venue_idx = next(
                                    idx for idx, e in enumerate(all_venue_events)
                                    if e.get('start_dt') == parent_event.get('start_dt')
                                    and e.get('title') == parent_event.get('title')
                                )
                            except StopIteration:
                                continue
                            
                            # Check if there's a next venue event
                            if venue_idx + 1 < len(all_venue_events):
                                next_venue_event = all_venue_events[venue_idx + 1]
                                # If next venue event matches this rule, skip
                                if self._event_matches_rule(next_venue_event, rule):
                                    continue  # Skip - next event is also a matching event
                            
                            # Fire derived event (no matching next event OR last in venue)
                            parent_key = (parent_event.get('title'), parent_event.get('start_dt'))
                            derived = self._create_derived_event(parent_event, rule)
                            if derived:
                                derived_events.append(derived)
                                matched_parent_keys.add(parent_key)
                    else:
                        # SIMPLE: Calendar-day based (default)
                        # Group by date, fire for last event of each date
                        events_by_date = {}
                        for evt in matching_events:
                            evt_date = evt.get('start_dt').date()
                            if evt_date not in events_by_date:
                                events_by_date[evt_date] = []
                            events_by_date[evt_date].append(evt)
                        
                        for date, day_events in events_by_date.items():
                            day_events.sort(key=lambda x: x.get('start_dt'))
                            last_event = day_events[-1]
                            parent_key = (last_event.get('title'), last_event.get('start_dt'))
                            derived = self._create_derived_event(last_event, rule)
                            if derived:
                                derived_events.append(derived)
                                matched_parent_keys.add(parent_key)
                
                elif skip_last_per_day:
                    # Fire for all matching events EXCEPT the LAST of each CALENDAR DAY
                    # Useful for presets between shows (no preset after final show)
                    
                    # Collect all matching events
                    matching_events = []
                    for parent_event in events:
                        if self._event_matches_rule(parent_event, rule):
                            matching_events.append(parent_event)
                    
                    if not matching_events:
                        continue
                    
                    # Check min_per_day requirement
                    min_per_day = rule.get("min_per_day", 1)
                    if len(matching_events) < min_per_day:
                        continue
                    
                    # Sort by start time
                    matching_events.sort(key=lambda x: x.get('start_dt'))
                    
                    # Group by date, fire for all except last of each date
                    events_by_date = {}
                    for evt in matching_events:
                        evt_date = evt.get('start_dt').date()
                        if evt_date not in events_by_date:
                            events_by_date[evt_date] = []
                        events_by_date[evt_date].append(evt)
                    
                    for date, day_events in events_by_date.items():
                        day_events.sort(key=lambda x: x.get('start_dt'))
                        # Fire for all except last of the day
                        for parent_event in day_events[:-1]:
                            derived = self._create_derived_event(parent_event, rule)
                            if derived:
                                derived_events.append(derived)
                
                elif rule.get("min_gap_minutes") is not None:
                    # Only fire if there's enough gap from previous event's end
                    # - If sessions are stacked (no gap), only fire before the first
                    # - If there's a gap >= min_gap_minutes, fire before each block
                    #
                    # check_all_events: If True, check gap from ANY preceding event (not just same-type)
                    # This is useful for doors - don't add doors if they'd overlap with any event
                    min_gap = rule.get("min_gap_minutes")
                    check_all = rule.get("check_all_events", False)
                    
                    # Only apply deduplication for category catch-all rules
                    is_catch_all = rule.get("match_categories") is not None and rule.get("match_titles") is None
                    
                    # Build list of all events by date for global gap checking
                    all_events_by_date = {}
                    if check_all:
                        for evt in events:
                            evt_date = evt.get('start_dt').date()
                            if evt_date not in all_events_by_date:
                                all_events_by_date[evt_date] = []
                            all_events_by_date[evt_date].append(evt)
                        # Sort each day's events
                        for d in all_events_by_date:
                            all_events_by_date[d] = sorted(all_events_by_date[d], key=lambda x: x.get('start_dt'))
                    
                    matching_by_date = {}
                    for parent_event in events:
                        if self._event_matches_rule(parent_event, rule):
                            event_date = parent_event.get('start_dt').date()
                            if event_date not in matching_by_date:
                                matching_by_date[event_date] = []
                            matching_by_date[event_date].append(parent_event)
                    
                    # Process each day's events
                    for event_date, day_events in matching_by_date.items():
                        # Sort by start time
                        sorted_events = sorted(day_events, key=lambda x: x.get('start_dt'))
                        
                        for parent_event in sorted_events:
                            # Skip if this is a category catch-all AND event was already matched by title rule
                            parent_key = (parent_event.get('title'), parent_event.get('start_dt'))
                            if is_catch_all and parent_key in matched_parent_keys:
                                continue
                            
                            current_start = parent_event.get('start_dt')
                            
                            # Find the closest preceding event end time
                            prev_end = None
                            if check_all and event_date in all_events_by_date:
                                # Check gap from ANY preceding event
                                for evt in all_events_by_date[event_date]:
                                    evt_end = evt.get('end_dt')
                                    if evt_end and evt_end <= current_start:
                                        if prev_end is None or evt_end > prev_end:
                                            prev_end = evt_end
                            else:
                                # Original logic: check gap from previous same-type event only
                                # (This is kept for backward compatibility with non-doors rules)
                                for evt in sorted_events:
                                    if evt.get('start_dt') < current_start:
                                        evt_end = evt.get('end_dt')
                                        if evt_end and (prev_end is None or evt_end > prev_end):
                                            prev_end = evt_end
                            
                            # Fire if: first of day OR gap from previous end >= min_gap_minutes
                            should_fire = False
                            if prev_end is None:
                                should_fire = True  # First event of day (no preceding events)
                            else:
                                gap_minutes = (current_start - prev_end).total_seconds() / 60
                                if gap_minutes >= min_gap:
                                    should_fire = True  # Sufficient gap, start new block
                            
                            if should_fire and check_all:
                                # ADDITIONAL CHECK: Verify derived event won't overlap with any running event
                                # Calculate where the derived event would be placed
                                offset_mins = rule.get("offset_minutes", 0)
                                derived_start = current_start + timedelta(minutes=offset_mins)
                                derived_date = derived_start.date()  # Use derived event's date (may differ for midnight crossover)
                                
                                # Check if this time falls INSIDE any event's range
                                # Need to check events from derived_date (not event_date) for midnight crossover
                                events_to_check = all_events_by_date.get(derived_date, [])
                                for evt in events_to_check:
                                    evt_start = evt.get('start_dt')
                                    evt_end = evt.get('end_dt')
                                    # If derived_start is inside an event's range (start < derived < end), don't fire
                                    if evt_start and evt_end and evt_start < derived_start < evt_end:
                                        should_fire = False
                                        print(f"DEBUG: Doors blocked - would overlap with '{evt.get('title')}' ({evt_start.strftime('%I:%M %p')} - {evt_end.strftime('%I:%M %p')})")
                                        break
                            
                            if should_fire:
                                derived = self._create_derived_event(parent_event, rule)
                                if derived:
                                    derived_events.append(derived)
                                    matched_parent_keys.add(parent_key)
                
                else:
                    # Standard processing - match all events
                    for parent_event in events:
                        parent_key = (parent_event.get('title'), parent_event.get('start_dt'))
                        
                        if parent_key in matched_parent_keys:
                            continue
                        
                        if self._event_matches_rule(parent_event, rule):
                            derived = self._create_derived_event(parent_event, rule)
                            if derived:
                                derived_events.append(derived)
                                matched_parent_keys.add(parent_key)
        
        # Combine and sort by start time
        all_events = events + derived_events
        all_events.sort(key=lambda x: x['start_dt'])
        
        return all_events
    
    def _apply_floor_transition_rules(
        self,
        events: List[Dict],
        floor_config: Dict
    ) -> List[Dict]:
        """
        Generate strike/set events when floor requirement changes.
        
        Only runs for venues with floor_requirements config (e.g., Studio B).
        
        Args:
            events: List of events with start_dt, end_dt, title
            floor_config: Dict containing floor_requirements and floor_transition config
        
        Returns:
            Original events + generated transition events, sorted by start time
        """
        # Skip if no floor config
        floor_requirements = floor_config.get("floor_requirements")
        transition_config = floor_config.get("floor_transition")
        
        if not floor_requirements or not transition_config:
            return events
        
        # Sort events chronologically
        sorted_events = sorted(events, key=lambda x: x.get('start_dt'))
        
        # Track floor state and transitions
        transition_events = []
        current_floor_state = None  # True = floor, False = ice, None = unknown
        prev_event_with_floor_need = None
        
        for event in sorted_events:
            # Skip derived events (setup, strike, doors, etc.) - only original events trigger floor transitions
            if event.get('is_derived'):
                continue
            
            floor_need = self._get_floor_need(event, floor_requirements)
            
            # Skip events that don't care about floor state
            if floor_need is None:
                continue
            
            # First event that cares - establish state, no transition
            if current_floor_state is None:
                current_floor_state = floor_need
                prev_event_with_floor_need = event
                continue
            
            # Check for transition
            if floor_need != current_floor_state:
                # TRANSITION DETECTED!
                transition = self._create_floor_transition(
                    prev_event_with_floor_need,
                    event,
                    current_floor_state,
                    floor_need,
                    transition_config
                )
                if transition:
                    transition_events.append(transition)
            
            # Update state
            current_floor_state = floor_need
            prev_event_with_floor_need = event
        
        # Check for overlaps and combine titles with existing events
        all_events = self._merge_floor_transitions_with_existing(events, transition_events)
        all_events.sort(key=lambda x: x['start_dt'])
        
        return all_events
    
    def _merge_floor_transitions_with_existing(
        self,
        events: List[Dict],
        transition_events: List[Dict]
    ) -> List[Dict]:
        """
        Merge floor transition events with existing events that overlap.
        
        If a floor transition overlaps with an existing strike event (like "Strike & Ice Scrape"),
        combine them into one event with a combined title.
        """
        if not transition_events:
            return events
        
        final_events = list(events)  # Copy to avoid modifying original
        
        for transition in transition_events:
            trans_start = transition.get('start_dt')
            trans_end = transition.get('end_dt')
            trans_title = transition.get('title', '')
            
            # Find overlapping events
            overlapping = None
            overlapping_idx = None
            
            for i, evt in enumerate(final_events):
                evt_start = evt.get('start_dt')
                evt_end = evt.get('end_dt')
                
                if not evt_start or not evt_end:
                    continue
                
                # Check for overlap OR adjacent (touching at same time point)
                # Events are combinable if they overlap OR one ends exactly when other starts
                # Original: not (trans_end <= evt_start or trans_start >= evt_end)
                # New: not (trans_end < evt_start or trans_start > evt_end)
                # This allows combining when trans_end == evt_start (adjacent)
                if not (trans_end < evt_start or trans_start > evt_end):
                    # Check if it's a strike/setup type event we can merge with
                    if evt.get('type') in ['strike', 'preset', 'setup']:
                        overlapping = evt
                        overlapping_idx = i
                        break
            
            if overlapping:
                # Combine titles
                existing_title = overlapping.get('title', '')
                if trans_title and trans_title not in existing_title:
                    combined_title = f"{existing_title} & {trans_title}"
                    final_events[overlapping_idx]['title'] = combined_title
                
                # Take earliest start time
                existing_start = overlapping.get('start_dt')
                existing_end = overlapping.get('end_dt')
                
                new_start = min(trans_start, existing_start)
                
                # Keep the LONGEST duration (not add durations)
                existing_duration = existing_end - existing_start
                trans_duration = trans_end - trans_start
                longest_duration = max(existing_duration, trans_duration)
                
                final_events[overlapping_idx]['start_dt'] = new_start
                final_events[overlapping_idx]['end_dt'] = new_start + longest_duration
            else:
                # No overlap - add as new event
                final_events.append(transition)
        
        return final_events
    
    def _merge_overlapping_operations(self, events: List[Dict]) -> List[Dict]:
        """
        Merge all overlapping operational events (setup, strike, preset).
        
        When events like "Strike & Ice Scrape" and "Set Up Nightclub" overlap,
        combine them into one event with combined title and longest duration.
        """
        if not events:
            return events
        
        # Sort by start time
        sorted_events = sorted(events, key=lambda x: x.get('start_dt'))
        merged = []
        
        for event in sorted_events:
            event_type = event.get('type', '')
            
            # Only merge operational events
            if event_type not in ['setup', 'strike', 'preset']:
                merged.append(event)
                continue
            
            evt_start = event.get('start_dt')
            evt_end = event.get('end_dt')
            evt_title = event.get('title', '')
            
            if not evt_start or not evt_end:
                merged.append(event)
                continue
            
            # Find overlapping operational event in merged list
            merge_target_idx = None
            for i in range(len(merged) - 1, -1, -1):  # Search backwards (recent first)
                target = merged[i]
                if target.get('type') not in ['setup', 'strike', 'preset']:
                    continue
                
                target_start = target.get('start_dt')
                target_end = target.get('end_dt')
                
                if not target_start or not target_end:
                    continue
                
                # Check for overlap OR adjacent (touching at same time point)
                if not (evt_end < target_start or evt_start > target_end):
                    merge_target_idx = i
                    break
            
            if merge_target_idx is not None:
                # Merge with existing event
                target = merged[merge_target_idx]
                target_title = target.get('title', '')
                target_start = target.get('start_dt')
                target_end = target.get('end_dt')
                
                # Combine titles (avoid duplicates)
                if evt_title and evt_title not in target_title:
                    merged[merge_target_idx]['title'] = f"{target_title} & {evt_title}"
                
                # Take earliest start, keep longest duration
                new_start = min(evt_start, target_start)
                target_duration = target_end - target_start
                evt_duration = evt_end - evt_start
                longest_duration = max(target_duration, evt_duration)
                
                merged[merge_target_idx]['start_dt'] = new_start
                merged[merge_target_idx]['end_dt'] = new_start + longest_duration
                
                # Preserve is_floor_transition flag - if either event is a floor transition,
                # the merged event should be treated as one (for late night handling)
                if event.get('is_floor_transition') or target.get('is_floor_transition'):
                    merged[merge_target_idx]['is_floor_transition'] = True
            else:
                # No overlap - add as new event
                merged.append(event)
        
        # Sort again after merging
        merged.sort(key=lambda x: x.get('start_dt'))
        return merged
    
    def _resolve_operation_overlaps(self, events: List[Dict]) -> List[Dict]:
        """
        Ensure no strike/setup overlaps with actual events.
        
        Rules:
        - If a strike overlaps with an event's start, defer to after ALL 
          overlapping events end, named after the LAST event
        - If a setup overlaps with an event, bump it earlier to merge with
          previous setups
        - Overlapping operations (setup/strike/preset) that conflict with 
          actual events get removed and replaced
        """
        if not events:
            return events
        
        # Separate actual events from operational events
        actual_events = [e for e in events if e.get('type') not in ['setup', 'strike', 'preset']]
        operations = [e for e in events if e.get('type') in ['setup', 'strike', 'preset']]
        
        if not operations or not actual_events:
            return events
        
        # Sort both lists by start time
        actual_events.sort(key=lambda x: x.get('start_dt'))
        operations.sort(key=lambda x: x.get('start_dt'))
        
        resolved_ops = []
        
        for op in operations:
            op_start = op.get('start_dt')
            op_end = op.get('end_dt')
            op_type = op.get('type')
            
            if not op_start or not op_end:
                resolved_ops.append(op)
                continue
            
            # Find all actual events this operation overlaps with
            overlapping_actuals = []
            for actual in actual_events:
                actual_start = actual.get('start_dt')
                actual_end = actual.get('end_dt')
                
                if not actual_start or not actual_end:
                    continue
                
                # Check for overlap (not adjacent)
                if not (op_end <= actual_start or op_start >= actual_end):
                    overlapping_actuals.append(actual)
            
            if not overlapping_actuals:
                # No overlap with actual events - keep as is
                resolved_ops.append(op)
            elif op_type == 'strike':
                # STRIKE: Check if overlapping with merged event (like Parade)
                merged_overlaps = [a for a in overlapping_actuals if a.get('is_merged')]
                non_merged_overlaps = [a for a in overlapping_actuals if not a.get('is_merged')]
                
                if non_merged_overlaps:
                    # Overlaps with actual (non-merged) event - drop the strike
                    pass
                elif merged_overlaps:
                    # Overlaps with merged event only - try to merge with next Setup
                    # Find the latest merged event end time
                    latest_merged = max(merged_overlaps, key=lambda x: x.get('end_dt'))
                    merged_end = latest_merged.get('end_dt')
                    op_date = op_start.date()
                    
                    # Find next Setup event that day (after merged event ends)
                    next_setups = [
                        s for s in operations 
                        if s.get('type') == 'setup' 
                        and s.get('start_dt') 
                        and s.get('start_dt').date() == op_date
                        and s.get('start_dt') >= merged_end
                    ]
                    
                    if next_setups:
                        # Merge strike title with the earliest next Setup
                        next_setup = min(next_setups, key=lambda x: x.get('start_dt'))
                        strike_title = op.get('title', '').replace('Strike ', '')
                        setup_title = next_setup.get('title', '')
                        
                        # Prepend "Strike X &" to setup title if not already there
                        if strike_title and strike_title not in setup_title:
                            next_setup['title'] = f"Strike {strike_title} & {setup_title}"
                        # Strike is now merged into setup - don't add it separately
                    else:
                        # No next Setup - schedule strike after merged event ends
                        duration = op_end - op_start
                        new_strike = dict(op)
                        new_strike['start_dt'] = merged_end
                        new_strike['end_dt'] = merged_end + duration
                        resolved_ops.append(new_strike)
                else:
                    # No overlaps at all (shouldn't reach here but be safe)
                    resolved_ops.append(op)
            elif op_type in ['setup', 'preset']:
                # SETUP: Bump earlier to not overlap
                # Find the earliest overlapping event
                earliest_overlap = min(overlapping_actuals, key=lambda x: x.get('start_dt'))
                earliest_start = earliest_overlap.get('start_dt')
                
                duration = op_end - op_start
                new_end = earliest_start  # Setup ends when event starts
                new_start = new_end - duration
                
                new_setup = dict(op)
                new_setup['start_dt'] = new_start
                new_setup['end_dt'] = new_end
                
                # Check if this new setup ALSO overlaps with earlier events
                overlaps_again = False
                for actual in actual_events:
                    actual_start = actual.get('start_dt')
                    actual_end = actual.get('end_dt')
                    if actual_start and actual_end:
                        if not (new_setup['end_dt'] <= actual_start or new_setup['start_dt'] >= actual_end):
                            overlaps_again = True
                            break
                
                if not overlaps_again:
                    resolved_ops.append(new_setup)
                # If still overlaps, drop (will merge with earlier setup)
        
        # Combine resolved operations with actual events
        result = actual_events + resolved_ops
        result.sort(key=lambda x: x.get('start_dt'))
        
        # Final merge pass on operations to combine any that now overlap
        return self._merge_overlapping_operations(result)
    
    def _handle_late_night_derived_events(
        self, 
        events: List[Dict], 
        late_night_config: Dict,
        voyage_end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Handle derived events that start in the late-night window (e.g., 1 AM - 9 AM).
        
        Rules:
        - Last day of cruise: Remove late-night derived events completely
        - Other days: Reschedule to reschedule_hour (e.g., 9 AM) same calendar day
          - Merge with other derived events if overlapping at that time
          - Remove if overlapping with actual events at that time
        """
        if not events or not late_night_config:
            return events
        
        cutoff_hour = late_night_config.get("cutoff_hour", 1)
        reschedule_hour = late_night_config.get("reschedule_hour", 9)
        
        # Separate actual events from derived events
        actual_events = [e for e in events if not e.get('is_derived', False)]
        derived_events = [e for e in events if e.get('is_derived', False)]
        
        if not derived_events:
            return events
        
        # Find late-night derived events (between cutoff_hour and reschedule_hour)
        # NOTE: Floor transitions are excluded - they handle their own timing based on parent event end time
        late_night_derived = []
        normal_derived = []
        
        for d in derived_events:
            # Floor transitions already handle late night scheduling in _create_floor_transition
            # based on parent event's end time, so skip them here
            if d.get('is_floor_transition'):
                normal_derived.append(d)
                continue
                
            start_dt = d.get('start_dt')
            end_dt = d.get('end_dt')
            if not start_dt:
                normal_derived.append(d)
                continue
            
            hour = start_dt.hour
            minute = start_dt.minute
            end_hour = late_night_config.get("end_hour", 6)
            
            # Late night if event starts AFTER midnight (00:00) but before end_hour (06:00)
            # - 00:00 exactly = midnight = NOT after midnight → OK to happen at night
            # - 00:01+ = after midnight → reschedule to morning
            is_after_midnight = (hour == 0 and minute > 0) or (hour > 0 and hour < end_hour)
            
            if is_after_midnight:
                late_night_derived.append(d)
            else:
                normal_derived.append(d)
        
        if not late_night_derived:
            return events
        
        # Process late-night derived events
        rescheduled = []
        merged_into_morning = []  # Track events we merged into morning ops
        
        for d in late_night_derived:
            start_dt = d.get('start_dt')
            event_date = start_dt.date()
            
            # Check if this is AFTER the last day of the cruise
            if voyage_end_date and event_date > voyage_end_date:
                # Last day - try to merge with existing morning operation instead of removing
                # Look for an operation at reschedule_hour on this date
                morning_ops = [
                    op for op in normal_derived 
                    if op.get('start_dt') 
                    and op.get('start_dt').date() == event_date
                    and op.get('start_dt').hour == reschedule_hour
                    and op.get('type') in ['strike', 'setup', 'preset']
                ]
                
                if morning_ops:
                    # Merge this late-night event's title into the morning operation
                    morning_op = morning_ops[0]
                    late_night_title = d.get('title', '').replace('Strike ', '').replace('Set Up ', '')
                    current_title = morning_op.get('title', '')
                    
                    if late_night_title and late_night_title not in current_title:
                        # Append to morning operation title
                        if 'Strike' in d.get('title', ''):
                            morning_op['title'] = f"{current_title} & Strike {late_night_title}"
                        else:
                            morning_op['title'] = f"{current_title} & {late_night_title}"
                    merged_into_morning.append(d)
                else:
                    # No morning operation to merge with - remove after voyage ends
                    pass
                continue
            
            # Reschedule to reschedule_hour same calendar day
            duration = d.get('end_dt') - d.get('start_dt')
            new_start = datetime.combine(event_date, dt_time(reschedule_hour, 0))
            new_end = new_start + duration
            
            new_event = dict(d)
            new_event['start_dt'] = new_start
            new_event['end_dt'] = new_end
            new_event['rescheduled_from_late_night'] = True
            rescheduled.append(new_event)
        
        if not rescheduled:
            # All late-night events were on last day - just remove them
            result = actual_events + normal_derived
            result.sort(key=lambda x: x.get('start_dt'))
            return result
        
        # Check for overlaps with actual events at the rescheduled time
        valid_rescheduled = []
        for r in rescheduled:
            r_start = r.get('start_dt')
            r_end = r.get('end_dt')
            
            overlaps_actual = False
            for a in actual_events:
                a_start = a.get('start_dt')
                a_end = a.get('end_dt')
                if a_start and a_end and r_start and r_end:
                    if not (r_end <= a_start or r_start >= a_end):
                        overlaps_actual = True
                        break
            
            if not overlaps_actual:
                valid_rescheduled.append(r)
            # If overlaps with actual event, remove it (drop)
        
        # Combine and merge
        all_derived = normal_derived + valid_rescheduled
        result = actual_events + all_derived
        result.sort(key=lambda x: x.get('start_dt'))
        
        # Merge overlapping derived events (at 9 AM there might be multiple)
        return self._merge_overlapping_operations(result)
    
    def _get_floor_need(self, event: Dict, floor_requirements: Dict) -> Optional[bool]:
        """
        Determine if an event needs the floor (True), ice (False), or doesn't care (None).
        """
        title = event.get('title', '')
        
        # Check floor events (needs_floor: True)
        floor_config = floor_requirements.get('floor', {})
        floor_titles = floor_config.get('match_titles', [])
        for match_title in floor_titles:
            if match_title.lower() in title.lower():
                return True
        
        # Check ice events (needs_floor: False)
        ice_config = floor_requirements.get('ice', {})
        ice_titles = ice_config.get('match_titles', [])
        for match_title in ice_titles:
            if match_title.lower() in title.lower():
                return False
        
        # Not in either list - doesn't care
        return None
    
    def _create_floor_transition(
        self,
        prev_event: Dict,
        next_event: Dict,
        prev_floor_state: bool,
        next_floor_state: bool,
        transition_config: Dict
    ) -> Optional[Dict]:
        """
        Create a floor transition event between two events.
        
        Timing:
        - If prev_event ends before midnight: anchor AFTER prev_event ends
        - If prev_event ends after midnight: anchor BEFORE next_event starts
        """
        duration = timedelta(minutes=transition_config.get('duration_minutes', 60))
        titles = transition_config.get('titles', {})
        event_type = transition_config.get('type', 'strike')
        
        # Determine title based on transition direction
        if prev_floor_state and not next_floor_state:
            # floor → ice
            title = titles.get('floor_to_ice', 'Strike Floor & Set Ice')
        else:
            # ice → floor
            title = titles.get('ice_to_floor', 'Strike Ice & Set Floor')
        
        prev_end = prev_event.get('end_dt')
        next_start = next_event.get('start_dt')
        
        if not prev_end or not next_start:
            return None
        
        # Check if prev_event ends AFTER midnight (not at midnight exactly)
        # - 00:00 exactly = midnight = NOT after midnight → transition can happen at night
        # - 00:01+ = after midnight → reschedule to morning (9 AM)
        is_after_midnight = (prev_end.hour == 0 and prev_end.minute > 0) or (prev_end.hour > 0 and prev_end.hour < 6)
        
        if is_after_midnight:
            # After midnight - prefer 9 AM for morning strikes
            # But if next event needs floor earlier, anchor before it
            preferred_9am = next_start.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # If next event starts before 10 AM, anchor 1 hour before it instead
            if next_start.hour < 10:
                transition_end = next_start
                transition_start = transition_end - duration
            else:
                # Use preferred 9 AM time
                transition_start = preferred_9am
                transition_end = transition_start + duration
        else:
            # Normal - anchor AFTER prev event ends
            transition_start = prev_end
            transition_end = transition_start + duration
        
        return {
            "title": title,
            "start_dt": transition_start,
            "end_dt": transition_end,
            "category": event_type,
            "type": event_type,
            "venue": prev_event.get("venue", ""),
            "raw_date": transition_start.strftime("%Y-%m-%d"),
            "is_derived": True,
            "is_floor_transition": True,
        }

    
    def _format_event_for_api(self, event: Dict) -> Dict:
        """Format event for API response."""
        formatted = {
            "title": event["title"],
            "start": event["start_dt"].isoformat(),
            "end": event["end_dt"].isoformat(),
            "type": event.get("type", event.get("category", "other")),
            "venue": event.get("venue", "")
        }
        
        # Include styling for derived events
        if event.get("styling"):
            formatted["styling"] = event["styling"]
        
        # Include derived event metadata
        if event.get("is_derived"):
            formatted["is_derived"] = True
            formatted["parent_title"] = event.get("parent_title")
        
        # Include end_is_late flag for "Late" display
        if event.get("end_is_late"):
            formatted["end_is_late"] = True
        
        return formatted
    
    def _filter_other_venue_shows(self, shows: List[Dict], policies: Dict = {}) -> List[Dict]:
        """
        Ensure only one show per venue per day, choosing the best highlight by priority.
        Priority: show (1) > headliner (2) > game (3) > party (4) > movie (5) > activity (6) > other (7) > backup (8)
        Also prefers afternoon/evening events over morning events.
        """
        grouped = {}
        for show in shows:
            # Apply Policy Renaming (Robust)
            venue = show.get('venue')
            policy = policies.get(venue, {})
            renaming = policy.get('renaming_map', {})
            
            raw_title = show.get('title', '')
            show['title'] = self._apply_renaming_robust(raw_title, renaming)
            
            key = (venue, show.get('date', ''))
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(show)
        
        filtered = []
    
        # Priority Map (Lower is better)
        PRIORITY_MAP = {
            "show": 1,
            "headliner": 2,
            "comedy": 2.5,
            "game": 3,
            "party": 4, 
            "movie": 5,
            "parade": 5,  # Parades are important events like movies
            "activity": 6,
            "other": 7,
            "backup": 8
        }
        
        def is_afternoon_or_evening(time_str: str) -> bool:
            """Check if time is after 1:00pm (preferred time band)."""
            if not time_str:
                return True  # No time = assume evening
            t = time_str.lower().strip()
            
            # Handle "noon" explicitly - it's 12pm, which is BEFORE 1pm cutoff
            if 'noon' in t:
                return False  # Noon = fallback
            
            # Handle multiple times (e.g., "7:45 pm & 10:00 pm")
            first_time = t.split('&')[0].strip()
            
            if 'pm' in first_time:
                # Extract hour
                try:
                    hour_part = first_time.split(':')[0].strip()
                    hour = int(''.join(c for c in hour_part if c.isdigit()))
                    # 12pm is noon = before 1pm cutoff, so fallback
                    # 1pm-11pm = afternoon/evening = preferred
                    return hour >= 1 and hour != 12
                except:
                    return True  # Default to preferred if parsing fails
            elif 'am' in first_time:
                return False  # Morning events = fallback
            return False  # Unknown time format = fallback (safer)
        
        for key, venue_shows in grouped.items():
            # Two-pass sorting:
            # 1. Prefer afternoon/evening events (after 1pm)
            # 2. Within same time band, sort by category priority
            venue_shows.sort(key=lambda x: (
                0 if is_afternoon_or_evening(x.get("time", "")) else 1,
                PRIORITY_MAP.get(x.get("category", "other").lower(), 99)
            ))
            
            # Identify the Winner (Top Priority)
            winner = venue_shows[0]
            
            # LOGIC FIX: Check for other events with the SAME Title as the winner (e.g. 2nd Showtime)
            # If found, merge their times into the winner's display string.
            # This handles the case where LLM splits "7:45 & 10:00" into two events.
            # BUT: Don't merge if times have ranges (dashes) or if it's an activity - creates messy strings.
            
            same_title_events = [s for s in venue_shows if s.get("title") == winner.get("title")]
            winner_category = winner.get("category", "").lower()
            first_time = winner.get("time", "")
            
            # Only merge if: multiple same-title events AND times are simple (no dash ranges)
            # AND category is not "activity" (activity sessions have complex time ranges)
            should_merge = (
                len(same_title_events) > 1 and
                winner_category != "activity" and
                "-" not in first_time  # Don't merge if first time is already a range
            )
            
            if should_merge:
                # Deduplicate times robustly
                unique_times_set = set()
                final_times_list = []
                
                for s in same_title_events:
                    t_str = s.get("time", "").strip()
                    if not t_str: continue
                    
                    # Skip times with ranges (dashes) - they're session times, not showtime slots
                    if "-" in t_str:
                        continue
                    
                    # Split by '&' to handle existing combined times
                    parts = [p.strip() for p in t_str.split('&')]
                    
                    for p in parts:
                        p_clean = p.lower()
                        if p_clean not in unique_times_set:
                            unique_times_set.add(p_clean)
                            final_times_list.append(p) # Keep original casing
                
                # Only update if we have clean times to merge
                if len(final_times_list) > 1:
                    winner['time'] = " & ".join(final_times_list)
                    print(f"DEBUG: Merged highlight times for {winner['title']}: {winner['time']}")
            
            # Clean up time string for display (remove ugly notations)
            winner['time'] = self._clean_highlight_time(winner.get('time', ''))
            
            filtered.append(winner)
        
        return filtered
    
    def _clean_highlight_time(self, time_str: str) -> str:
        """
        Clean up time string for highlight display.
        Removes duration notations like (1hr), (2hrs) and modifiers like TEENS, KIDS.
        Safe for any input - won't break on unexpected formats.
        """
        import re
        
        if not time_str or not isinstance(time_str, str):
            return time_str if time_str else ""
        
        cleaned = time_str
        
        # Remove duration notations: (1hr), (2 hrs), (1 hour), (2.5hrs), (6 hours)
        cleaned = re.sub(r'\s*\(\d+\.?\d*\s*(hrs?|hours?)\)', '', cleaned, flags=re.IGNORECASE)
        
        # Remove parenthetical modifiers: (TEENS), (KIDS), (Adults), (18+)
        cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', cleaned)
        
        # Remove trailing modifiers without parentheses: TEENS, KIDS, Adults
        cleaned = re.sub(r'\s*(TEENS|KIDS|ADULTS|18\+)\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up any trailing 'TEENS' etc that might be stuck to previous text
        cleaned = re.sub(r'(TEENS|KIDS|ADULTS)\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned

    def _clean_itinerary(self, itinerary: List[Dict]) -> List[Dict]:
        """Clean and normalize itinerary items."""
        for item in itinerary:
            port = item.get("port", "").lower()
            # Rule: If At Sea, times must be null
            if "sea" in port or "cruising" in port:
                item["arrival_time"] = None
                item["departure_time"] = None
            
            # Rule: "00:00" should often be treated as null if it makes no sense contextually, 
            # but usually At Sea is the main offender.
            if item.get("arrival_time") == "00:00":
                item["arrival_time"] = None
            if item.get("departure_time") == "00:00":
                item["departure_time"] = None
                
        return itinerary
    



