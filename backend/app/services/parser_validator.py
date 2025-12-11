"""
Parser Validator for GenAI extraction results.
Validates extracted data to catch hallucinations and ensure quality.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_data: Optional[Dict[str, Any]] = None


class ParserValidator:
    """Validate extracted schedule data for accuracy and consistency."""
    
    def __init__(self, valid_types: List[str] = None):
        self.valid_types = valid_types or [
            "show", "movie", "game", "activity", "music", 
            "party", "comedy", "headliner", "rehearsal", 
            "maintenance", "other"
        ]
    
    def validate(
        self, 
        result: Dict[str, Any], 
        raw_data: Dict[str, Any] = None,
        target_venue: str = None,
        other_venues: List[str] = None
    ) -> ValidationResult:
        """
        Validate extraction result.
        
        Checks:
        - Event count reasonable vs data row count
        - No duplicate start times on same date
        - All dates within itinerary date range
        - Venue names match target and other_venues list
        - No cross-venue contamination
        - Event types are valid enum values
        """
        errors = []
        warnings = []
        
        events = result.get("events", [])
        itinerary = result.get("itinerary", [])
        other_venue_shows = result.get("other_venue_shows", [])
        
        # Validate events
        event_errors, event_warnings = self._validate_events(
            events, target_venue, itinerary
        )
        errors.extend(event_errors)
        warnings.extend(event_warnings)
        
        # Validate itinerary
        itin_errors, itin_warnings = self._validate_itinerary(itinerary)
        errors.extend(itin_errors)
        warnings.extend(itin_warnings)
        
        # Validate other venue shows
        if other_venues:
            ovs_errors, ovs_warnings = self._validate_other_venue_shows(
                other_venue_shows, other_venues, itinerary
            )
            errors.extend(ovs_errors)
            warnings.extend(ovs_warnings)
        
        # Cross-validate with raw data if provided
        if raw_data:
            raw_warnings = self._cross_validate_with_raw(events, raw_data)
            warnings.extend(raw_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_events(
        self, 
        events: List[Dict], 
        target_venue: str,
        itinerary: List[Dict]
    ) -> tuple:
        """Validate event list."""
        errors = []
        warnings = []
        
        if not events:
            warnings.append("No events extracted")
            return errors, warnings
        
        # Get date range from itinerary
        itinerary_dates = set()
        for item in itinerary:
            if "date" in item:
                itinerary_dates.add(item["date"])
        
        # Track for duplicate detection
        seen_times = {}  # date -> set of start times
        
        for i, event in enumerate(events):
            # Check required fields
            if not event.get("title"):
                errors.append(f"Event {i}: Missing title")
            
            # Check for start_time (LLM response format) or start (API format)
            start_time = event.get("start_time") or event.get("start")
            if not start_time:
                errors.append(f"Event {i}: Missing start time")
            
            # Validate event type/category (LLM uses 'category', API uses 'type')
            event_type = event.get("category") or event.get("type", "other")
            if event_type not in self.valid_types:
                warnings.append(f"Event {i}: Unknown type '{event_type}', defaulting to 'other'")
            
            # Check venue assignment (skip if not in raw LLM response)
            if target_venue and event.get("venue"):
                if event["venue"].lower() != target_venue.lower():
                    errors.append(
                        f"Event {i} '{event.get('title')}': "
                        f"Wrong venue '{event['venue']}', expected '{target_venue}'"
                    )
            
            # Check for duplicate times
            if start_time:
                try:
                    # Handle both HH:MM format and ISO format
                    if "T" in str(start_time):
                        start_dt = datetime.fromisoformat(start_time)
                    else:
                        # HH:MM format - combine with date
                        date_str = event.get("date", "2025-01-01")
                        start_dt = datetime.fromisoformat(f"{date_str}T{start_time}:00")
                    
                    date_key = start_dt.strftime("%Y-%m-%d")
                    time_key = start_dt.strftime("%H:%M")
                    
                    if date_key not in seen_times:
                        seen_times[date_key] = {}
                    
                    if time_key in seen_times[date_key]:
                        warnings.append(
                            f"Duplicate start time {time_key} on {date_key}: "
                            f"'{event.get('title')}' and '{seen_times[date_key][time_key]}'"
                        )
                    else:
                        seen_times[date_key][time_key] = event.get("title", "Unknown")
                    
                    # Check if date is within itinerary
                    if itinerary_dates and date_key not in itinerary_dates:
                        warnings.append(
                            f"Event '{event.get('title')}' date {date_key} "
                            f"not in itinerary dates"
                        )
                except (ValueError, TypeError) as e:
                    errors.append(f"Event {i}: Invalid start time format - {start_time}")
        
        return errors, warnings
    
    def _validate_itinerary(self, itinerary: List[Dict]) -> tuple:
        """Validate itinerary list."""
        errors = []
        warnings = []
        
        if not itinerary:
            warnings.append("No itinerary extracted")
            return errors, warnings
        
        seen_days = set()
        seen_dates = set()
        
        for i, item in enumerate(itinerary):
            # Check required fields
            if "day_number" not in item:
                errors.append(f"Itinerary {i}: Missing day_number")
            else:
                if item["day_number"] in seen_days:
                    warnings.append(f"Duplicate day_number: {item['day_number']}")
                seen_days.add(item["day_number"])
            
            if not item.get("date"):
                errors.append(f"Itinerary {i}: Missing date")
            else:
                if item["date"] in seen_dates:
                    warnings.append(f"Duplicate date: {item['date']}")
                seen_dates.add(item["date"])
            
            if not item.get("port"):
                warnings.append(f"Itinerary {i}: Missing port/location")
        
        return errors, warnings
    
    def _validate_other_venue_shows(
        self, 
        shows: List[Dict], 
        other_venues: List[str],
        itinerary: List[Dict]
    ) -> tuple:
        """Validate other venue shows."""
        errors = []
        warnings = []
        
        valid_venues_lower = [v.lower() for v in other_venues]
        itinerary_dates = set(item.get("date") for item in itinerary if item.get("date"))
        
        for i, show in enumerate(shows):
            # Check venue is in allowed list
            venue = show.get("venue", "")
            if venue.lower() not in valid_venues_lower:
                warnings.append(
                    f"Other venue show {i}: Unknown venue '{venue}', "
                    f"expected one of {other_venues}"
                )
            
            # Check required fields
            if not show.get("title"):
                errors.append(f"Other venue show {i}: Missing title")
            
            if not show.get("date"):
                errors.append(f"Other venue show {i}: Missing date")
            elif itinerary_dates and show["date"] not in itinerary_dates:
                warnings.append(
                    f"Other venue show '{show.get('title')}' date {show['date']} "
                    f"not in itinerary dates"
                )
            
            if not show.get("time"):
                warnings.append(f"Other venue show {i}: Missing time")
        
        return errors, warnings
    
    def _cross_validate_with_raw(
        self, 
        events: List[Dict], 
        raw_data: Dict[str, Any]
    ) -> List[str]:
        """Cross-validate extracted events against raw cell data."""
        warnings = []
        
        total_data_cells = len(raw_data.get("cells", []))
        event_count = len(events)
        
        # Heuristic: if we have very few events compared to cells, might be missing data
        if total_data_cells > 50 and event_count < 5:
            warnings.append(
                f"Low event count ({event_count}) relative to data cells ({total_data_cells}). "
                f"Some events may have been missed."
            )
        
        return warnings
