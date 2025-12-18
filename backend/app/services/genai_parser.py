"""
GenAI Parser v2 - Multi-pass architecture for improved accuracy.
Uses structured extraction followed by LLM interpretation.
"""
from google import genai
from google.genai import types
from typing import Dict, Any, List, Optional, Union, BinaryIO
import json
import io
from datetime import datetime, timedelta
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
            if policy.get("merge_into_schedule"):
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
        
        print("DEBUG: Step 6 - Formatting response...")
        return self._transform_to_api_format(result, master_duration_map, renaming_map, cross_policies)
    
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
                should_merge = policy.get("merge_into_schedule", False)
                
                if should_merge:
                    # Logic for "Merged Imports" (e.g. Parades run by this crew)
                    # These go into the MAIN 'events' list, NOT 'other_venue_shows'
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
   Column mappings: {json.dumps(venue_cols)}
   - For each of these other venues, extract the **Main Highlights** for each day.
   - Typically include major production shows, headliners, and movies.
   - **Time Rule**: While usually evening (6pm+), you MUST extract **Special Events** (like Parades) regardless of time (e.g. 12:30 PM).
   - **Time Rule**: While usually evening (6pm+), you MUST extract **Special Events** (like Parades) regardless of time (e.g. 12:30 PM).
   - You may extract multiple significant events if available.
   - Ignore minor activities (like 'Open Skating', 'Dance Class').
   - **Ignore**: "Aerial Install", "Tech Run", "Rehearsal", "Sound Check", "Private Event".
   {highlight_instructions}
   - Extract:
     - venue: The name of the venue. You MUST use one of the exact strings from this list: [{hl_list_str}]. Do NOT combine names.
     - date: String in YYYY-MM-DD format
     - title: The name of the show
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
Extract every event listed in this column for each date.

VENUE SPECIFIC CONTEXT ({target_venue}):
{custom_instructions}
{main_import_instructions}

When reading the table, ignore all formatting attributes such as text color or cell background colors.
    - **Background Color**: A dark or gray background does NOT mean the event is cancelled. It is just styling. Extract these events normally.
    - **Strikethrough**: ONLY if the text has a visible line drawing through it (crossed out), treat it as CANCELLED and do not extract it.
    - **Mixed Cells**: A cell may contain one active event and one crossed-out event. Extract the active one.
    
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
- **Parade** (category: "parade"): e.g., "Parade", "Muster Drill".
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
            "maintenance", "other", "parade"
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
    
    def _transform_to_api_format(self, result: Dict[str, Any], default_durations: Dict[str, int] = {}, renaming_map: Dict[str, str] = {}, cross_venue_policies: Dict = {}) -> Dict[str, Any]:
        """Transform parsed result to API response format."""
        
        # Process events
        raw_events = result.get("events", [])
        parsed_events = []
        
        for event in raw_events:
            # 1. Standardize Title (Force Renaming with Fuzzy Match)
            raw_title = event.get("title", "")
            event["title"] = self._apply_renaming_robust(raw_title, renaming_map)
            
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
            
            # Check Merge Criteria
            is_merged = False
            
            # 1. Global Merge (All events from this venue go to Main)
            if policy.get("merge_into_schedule") is True:
                is_merged = True
            
            # 2. Selective Merge (Specific titles go to Main)
            # e.g. "Royal Promenade" -> merge_inclusions: ["Anchors Aweigh Parade"]
            elif "merge_inclusions" in policy:
                raw_title_other = show.get("title", "")
                # Check against whitelist
                for inclusion in policy.get("merge_inclusions", []):
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
                
                parsed_main = self._parse_single_event(show)
                if parsed_main:
                    if policy.get("custom_color"):
                         parsed_main['color'] = policy.get("custom_color")
                    
                    parsed_events.append(parsed_main)
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
                    end_dt = self._calculate_default_end(start_dt, event.get("title", ""), default_durations)
            else:
                # No end time provided: Use Rule-based or Standard Duration
                end_dt = self._calculate_default_end(start_dt, event.get("title", ""), default_durations)
            
            # Simple sanity check: If end_dt overlaps drastically with next start, maybe truncate?
            if i + 1 < len(events):
                next_event = events[i + 1]
                if next_event['start_dt'] < end_dt and next_event['start_dt'] > start_dt:
                    end_dt = next_event['start_dt']
            
            event['end_dt'] = end_dt
            resolved_events.append(event)
        
        return resolved_events

    def _calculate_default_end(self, start_dt: datetime, title: str, duration_map: Dict[str, int]) -> datetime:
        """Calculate end time based on title match or default 45 mins."""
        # Find best matching duration
        minutes = 60 # Fallback
        
        # Exact or partial match in duration map
        # duration_map keys might be 'inTENse', 'Ice Spectacular'
        # title might be 'inTENse' (cleaned) or 'Ice Spectacular 365' (raw)
        for key, duration in duration_map.items():
            if key.lower() in title.lower():
                minutes = duration
                break
        
        return start_dt + timedelta(minutes=minutes)
    
    def _format_event_for_api(self, event: Dict) -> Dict:
        """Format event for API response."""
        return {
            "title": event["title"],
            "start": event["start_dt"].isoformat(),
            "end": event["end_dt"].isoformat(),
            "type": event.get("category", "other"),
            "venue": event.get("venue", "")
        }
    
    def _filter_other_venue_shows(self, shows: List[Dict], policies: Dict = {}) -> List[Dict]:
        """Ensure only one show per venue per day and apply renaming."""
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
            "game": 3,
            "party": 4, 
            "movie": 5,
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
            
            same_title_events = [s for s in venue_shows if s.get("title") == winner.get("title")]
            if len(same_title_events) > 1:
                # Deduplicate times robustly
                unique_times_set = set()
                final_times_list = []
                
                for s in same_title_events:
                    t_str = s.get("time", "").strip()
                    if not t_str: continue
                    
                    # Split by '&' to handle existing combined times
                    parts = [p.strip() for p in t_str.split('&')]
                    
                    for p in parts:
                        p_clean = p.lower()
                        if p_clean not in unique_times_set:
                            unique_times_set.add(p_clean)
                            final_times_list.append(p) # Keep original casing
                
                # Check if we should merge them
                if len(final_times_list) > 0:
                    winner['time'] = " & ".join(final_times_list)
                    print(f"DEBUG: Merged highlight times for {winner['title']}: {winner['time']}")
            
            filtered.append(winner)
        
        return filtered

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
    



