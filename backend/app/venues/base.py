"""
VenueRules Base Class

Defines the interface for venue-specific parsing rules.
"""

from typing import Dict, List
from datetime import datetime, timedelta


class VenueRules:
    """
    Base class for venue-specific rules.
    
    Loaded from database config via `from_config()`.
    """
    
    # Venue identification
    ship_code: str = ""
    venue_name: str = ""
    
    # Standard config
    known_shows: List[str] = []
    renaming_map: Dict[str, str] = {}
    default_durations: Dict[str, int] = {}
    
    # Derived event config
    doors_config: List[Dict] = []
    setup_config: List[Dict] = []
    strike_config: List[Dict] = []
    warm_up_config: List[Dict] = []
    preset_config: List[Dict] = []
    ice_make_config: List[Dict] = []
    
    # Cross-venue config
    cross_venue_sources: List[str] = []
    cross_venue_import_policies: Dict = {}
    
    # Late night config
    late_night_config: Dict = {}
    
    # Prompt customization
    prompt_section: str = ""
    
    @property
    def self_extraction_policy(self) -> Dict:
        """
        Return self extraction policy configuration.
        Constructed from individual attributes for compatibility.
        """
        return {
            "known_shows": self.known_shows,
            "renaming_map": self.renaming_map,
            "default_durations": self.default_durations
        }

    @property
    def derived_event_rules(self) -> Dict:
        """
        Return all derived event configs in the format expected by the parser.
        
        This allows the parser to use venue_rules_obj.derived_event_rules instead
        of loading from the old venue_rules.py file.
        """
        rules = {}
        if self.doors_config:
            rules['doors'] = self.doors_config
        if self.setup_config:
            rules['setup'] = self.setup_config
        if self.strike_config:
            rules['strike'] = self.strike_config
        if self.warm_up_config:
            rules['warm_up'] = self.warm_up_config
        if self.preset_config:
            rules['preset'] = self.preset_config
        if self.ice_make_config:
            rules['ice_make'] = self.ice_make_config
        return rules
    
    @classmethod
    def from_config(cls, ship_code: str, venue_name: str, config: Dict) -> 'VenueRules':
        """
        Factory method to create VenueRules from database config.
        """
        instance = cls()
        instance.ship_code = ship_code
        instance.venue_name = venue_name
        
        # Load common config values
        instance.known_shows = config.get('known_shows', [])
        instance.renaming_map = config.get('renaming_map', {})
        instance.default_durations = config.get('default_durations', {})
        instance.doors_config = config.get('doors_config', [])
        instance.setup_config = config.get('setup_config', [])
        instance.strike_config = config.get('strike_config', [])
        instance.warm_up_config = config.get('warm_up_config', [])
        instance.preset_config = config.get('preset_config', [])
        instance.ice_make_config = config.get('ice_make_config', [])
        instance.cross_venue_sources = config.get('cross_venue_sources', [])
        instance.cross_venue_import_policies = config.get('cross_venue_import_policies', {})
        instance.late_night_config = config.get('late_night_config', {})
        instance.prompt_section = config.get('prompt_section', '')
        
        # Store full config for subclasses to access venue-specific fields
        instance._config = config
        
        return instance
    
    def build_prompt_section(self) -> str:
        """
        Return venue-specific LLM prompt instructions.
        
        This is inserted into the base prompt template.
        Override to add venue-specific parsing hints.
        """
        return ""
    
    def get_cross_venue_instructions(self) -> str:
        """
        Instructions for extracting cross-venue highlights.
        Override to specify what to look for from other venues.
        """
        return ""
    
    def post_process_events(self, events: List[Dict]) -> List[Dict]:
        """
        Venue-specific post-processing after LLM parsing.
        
        Override for custom cleanup, renaming, etc.
        Default: apply renaming_map only.
        """
        for event in events:
            title = event.get('title', '')
            if title in self.renaming_map:
                event['title'] = self.renaming_map[title]
        return events
    
    def generate_derived_events(self, events: List[Dict]) -> List[Dict]:
        """
        Generate derived events (doors, setup, strike, etc.)
        
        Override to add venue-specific derived events.
        Default: basic doors and setup/strike using configs.
        """
        # Only process non-derived events through each generator
        original_events = [e for e in events if not e.get('is_derived')]
        
        all_derived = []
        
        # Generate doors from original events
        doors_result = self._generate_doors(original_events)
        all_derived.extend([e for e in doors_result if e.get('is_derived')])
        
        # Generate setup from original events
        setup_result = self._generate_setup(original_events)
        all_derived.extend([e for e in setup_result if e.get('is_derived')])
        
        # Generate strike from original events
        strike_result = self._generate_strike(original_events)
        all_derived.extend([e for e in strike_result if e.get('is_derived')])
        
        # Generate warm up from original events
        warm_up_result = self._generate_warm_up(original_events)
        all_derived.extend([e for e in warm_up_result if e.get('is_derived')])
        
        # Generate preset from original events
        preset_result = self._generate_preset(original_events)
        all_derived.extend([e for e in preset_result if e.get('is_derived')])
        
        return events + all_derived
    
    # =========================================================================
    # Utility methods - Config-driven, venues just set config values
    # =========================================================================
    
    def _generate_doors(self, events: List[Dict]) -> List[Dict]:
        """Generate door events based on doors_config."""
        if not self.doors_config:
            return events
        
        derived = []
        # Track events that already have doors to prevent duplicates
        matched_event_keys = set()
        
        # Sort events chronologically for gap checking
        sorted_events = sorted(events, key=lambda x: x.get('start_dt') or datetime.min)
        
        for config in self.doors_config:
            match_types = config.get('match_types', [])
            match_titles = config.get('match_titles', [])
            offset_minutes = config.get('offset_minutes', -30)
            duration_minutes = config.get('duration_minutes', 15)
            min_gap_minutes = config.get('min_gap_minutes')
            
            for event in sorted_events:
                # Create unique key for event
                event_key = (event.get('title'), event.get('start_dt'))
                
                # Skip if this event already has doors
                if event_key in matched_event_keys:
                    continue
                
                if not self._matches_rule(event, match_types, match_titles):
                    continue
                
                # min_gap_minutes: Skip doors if not enough gap before this event
                if min_gap_minutes:
                    event_start = event.get('start_dt')
                    if event_start:
                        # Check gap against ALL previous events (including contiguous)
                        skip_doors = False
                        for prev_event in sorted_events:
                            if prev_event == event:
                                continue  # Skip self
                            prev_end = prev_event.get('end_dt')
                            if prev_end and prev_end <= event_start:
                                gap = (event_start - prev_end).total_seconds() / 60
                                if gap < min_gap_minutes:
                                    skip_doors = True
                                    break
                        if skip_doors:
                            continue
                
                door_event = self._create_derived_event(
                    parent=event,
                    title="Doors",
                    event_type="doors",
                    offset_minutes=offset_minutes,
                    duration_minutes=duration_minutes
                )
                derived.append(door_event)
                matched_event_keys.add(event_key)
        
        return events + derived
    
    def _generate_setup(self, events: List[Dict]) -> List[Dict]:
        """Generate setup events based on setup_config."""
        if not self.setup_config:
            return events
        
        derived = []
        # Track events that already have setup to prevent duplicates
        matched_event_keys = set()
        # Track first match per day for first_per_day rules
        first_per_day_rules_fired = {}  # rule_index -> set of dates
        
        # Sort events chronologically for proper ordering
        sorted_events = sorted(events, key=lambda x: x.get('start_dt') or datetime.min)
        
        for rule_idx, config in enumerate(self.setup_config):
            match_types = config.get('match_types', [])
            match_titles = config.get('match_titles', [])
            offset_minutes = config.get('offset_minutes', -60)
            duration_minutes = config.get('duration_minutes', 30)
            title_template = config.get('title_template', 'Set Up {parent_title}')
            first_per_day = config.get('first_per_day', False)
            min_gap_minutes = config.get('min_gap_minutes')
            
            prev_matching_event = None
            
            for event in sorted_events:
                # Create unique key for event
                event_key = (event.get('title'), event.get('start_dt'))
                
                # Skip if this event already has setup from another rule
                if event_key in matched_event_keys:
                    continue
                
                if not self._matches_rule(event, match_types, match_titles):
                    continue
                
                # first_per_day: Only fire for first matching event each day
                if first_per_day:
                    event_date = event.get('start_dt').date() if event.get('start_dt') else None
                    if rule_idx not in first_per_day_rules_fired:
                        first_per_day_rules_fired[rule_idx] = set()
                    if event_date in first_per_day_rules_fired[rule_idx]:
                        continue  # Already fired for this day
                    first_per_day_rules_fired[rule_idx].add(event_date)
                
                # min_gap_minutes: Skip if previous matching event is too close
                if min_gap_minutes and prev_matching_event:
                    prev_end = prev_matching_event.get('end_dt')
                    curr_start = event.get('start_dt')
                    if prev_end and curr_start:
                        gap = (curr_start - prev_end).total_seconds() / 60
                        if gap < min_gap_minutes:
                            prev_matching_event = event
                            continue  # Gap too small, skip
                
                title = title_template.replace('{parent_title}', event.get('title', ''))
                setup_event = self._create_derived_event(
                    parent=event,
                    title=title,
                    event_type="setup",
                    offset_minutes=offset_minutes,
                    duration_minutes=duration_minutes
                )
                derived.append(setup_event)
                matched_event_keys.add(event_key)
                prev_matching_event = event
        
        return events + derived
    
    def _generate_strike(self, events: List[Dict]) -> List[Dict]:
        """Generate strike events based on strike_config."""
        if not self.strike_config:
            return events
        
        derived = []
        # Track events that already have strike to prevent duplicates
        matched_event_keys = set()
        
        # Sort events chronologically for proper ordering
        sorted_events = sorted(events, key=lambda x: x.get('start_dt') or datetime.min)
        
        # Pre-calculate venue timeline for "skip_if_next_matches" logic
        # We need the sequence of "Real" venue events (excluding derived and import highlights)
        # to determine if the "next thing" is the same type of event.
        # Note: We filter out derived events so that "Ice Make" (derived) doesn't break the continuity of Skating sessions.
        venue_timeline = [
            e for e in sorted_events 
            if not e.get('is_derived') and not e.get('is_cross_venue')
        ]
        
        for config in self.strike_config:
            match_types = config.get('match_types', [])
            match_titles = config.get('match_titles', [])
            duration_minutes = config.get('duration_minutes', 30)
            title_template = config.get('title_template', 'Strike {parent_title}')
            last_per_day = config.get('last_per_day', False)
            skip_if_next_matches = config.get('skip_if_next_matches', False)
            
            for event in sorted_events:
                # 1. Check if event matches this rule
                if not self._matches_rule(event, match_types, match_titles):
                    continue

                # Create unique key for event
                event_key = (event.get('title'), event.get('start_dt'))
                
                # Skip if this event already has strike from another rule
                if event_key in matched_event_keys:
                    continue
                
                # 2. Check "last_per_day" Logic
                if last_per_day:
                    event_date = event.get('start_dt').date() if event.get('start_dt') else None
                    # Check if there's another matching event on the same day after this one
                    # We can look at venue_timeline or just sorted_events? 
                    # Strictly speaking, we should only care about events that MATCH THE RULE.
                    # So we iterate sorted_events found *after* this one.
                    has_later_same_day = False
                    current_idx = -1
                    try:
                        current_idx = sorted_events.index(event)
                    except ValueError:
                        continue # Should not happen

                    for later_event in sorted_events[current_idx+1:]:
                         if self._matches_rule(later_event, match_types, match_titles):
                            later_date = later_event.get('start_dt').date() if later_event.get('start_dt') else None
                            if later_date == event_date:
                                has_later_same_day = True
                                break
                    
                    if has_later_same_day:
                        continue  # Not the last one today
                
                # 3. Check "skip_if_next_matches" Logic
                # This logic is critical: We want to skip strike if the NEXT "real" event
                # in the venue is ALSO a matching event (continuing the session).
                # This ignores gaps (even large ones) and ignores derived events (like Ice Make).
                # But it correctly STRIKES if the next event is DIFFERENT (e.g. Laser Tag).
                if skip_if_next_matches:
                    try:
                        # Find current event in timeline
                        # Note: 'event' might be in sorted_events but NOT in venue_timeline if it's derived?
                        # But wait, we are iterating sorted_events which includes derived.
                        # Strike rules usually apply to Real events (Skating).
                        # If 'event' is derived (e.g. we striking a Setup?), it won't be in timeline.
                        # Assuming strike rules target known_shows (real events).
                        timeline_idx = venue_timeline.index(event)
                        
                        # Check next event in timeline
                        if timeline_idx + 1 < len(venue_timeline):
                            next_venue_event = venue_timeline[timeline_idx + 1]
                            
                            # Does the next event match THIS rule?
                            if self._matches_rule(next_venue_event, match_types, match_titles):
                                continue # SKIP STRIKE: Next event is compatible (e.g. Skating -> Skating)
                    except ValueError:
                        # Event not in timeline (maybe logic applied to derived event?), treat as "no next match"
                        pass
                
                # If we get here, generate the strike
                title = title_template.replace('{parent_title}', event.get('title', ''))
                strike_event = self._create_derived_event(
                    parent=event,
                    title=title,
                    event_type="strike",
                    offset_minutes=0,  # After event
                    duration_minutes=duration_minutes,
                    anchor="end"
                )
                derived.append(strike_event)
                matched_event_keys.add(event_key)
        
        return events + derived
    
    def _generate_warm_up(self, events: List[Dict]) -> List[Dict]:
        """Generate warm up events based on warm_up_config."""
        if not self.warm_up_config:
            return events
        
        derived = []
        # Group events by date for first_per_day logic
        events_by_date = {}
        for event in events:
            date_key = event.get('start_dt').date() if event.get('start_dt') else None
            if date_key:
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)
        
        for config in self.warm_up_config:
            match_titles = config.get('match_titles', [])
            offset_minutes = config.get('offset_minutes', -120)
            duration_minutes = config.get('duration_minutes', 30)
            title_template = config.get('title_template', 'Warm Up')
            first_per_day = config.get('first_per_day', False)
            
            processed_dates = set()
            
            for event in events:
                if self._matches_rule(event, [], match_titles):
                    event_date = event.get('start_dt').date() if event.get('start_dt') else None
                    
                    # Skip if first_per_day and already processed this date
                    if first_per_day and event_date in processed_dates:
                        continue
                    
                    title = title_template.replace('{parent_title}', event.get('title', ''))
                    warm_up_event = self._create_derived_event(
                        parent=event,
                        title=title,
                        event_type="warm_up",
                        offset_minutes=offset_minutes,
                        duration_minutes=duration_minutes
                    )
                    derived.append(warm_up_event)
                    
                    if first_per_day and event_date:
                        processed_dates.add(event_date)
        
        return events + derived
    
    def _generate_preset(self, events: List[Dict]) -> List[Dict]:
        """Generate preset/ice make events based on preset_config."""
        if not self.preset_config:
            return events
        
        derived = []
        # Group events by date for first_per_day and skip_last_per_day logic
        events_by_date = {}
        for event in events:
            date_key = event.get('start_dt').date() if event.get('start_dt') else None
            if date_key:
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)
        
        # Sort events chronologically for min_gap_minutes logic
        sorted_events = sorted(events, key=lambda x: x.get('start_dt') or datetime.min)
        
        for config in self.preset_config:
            match_titles = config.get('match_titles', [])
            offset_minutes = config.get('offset_minutes', -90)
            duration_minutes = config.get('duration_minutes', 30)
            title_template = config.get('title_template', 'Ice Make & Presets')
            event_type = config.get('type', 'preset')
            first_per_day = config.get('first_per_day', False)
            skip_last_per_day = config.get('skip_last_per_day', False)
            min_gap_minutes = config.get('min_gap_minutes')
            anchor = config.get('anchor', 'start')
            
            processed_dates = set()
            prev_matching_event = None
            
            for event in sorted_events:
                if self._matches_rule(event, [], match_titles):
                    event_date = event.get('start_dt').date() if event.get('start_dt') else None
                    
                    # Skip if first_per_day and already processed this date
                    if first_per_day and event_date in processed_dates:
                        continue
                    
                    # Skip if skip_last_per_day and this is the last matching event of the day
                    if skip_last_per_day:
                        day_events = events_by_date.get(event_date, [])
                        matching_events = [e for e in day_events if self._matches_rule(e, [], match_titles)]
                        if matching_events and event == matching_events[-1]:
                            continue
                    
                    # min_gap_minutes: Skip if previous matching event is too close
                    if min_gap_minutes and prev_matching_event:
                        prev_end = prev_matching_event.get('end_dt')
                        curr_start = event.get('start_dt')
                        if prev_end and curr_start:
                            gap = (curr_start - prev_end).total_seconds() / 60
                            if gap < min_gap_minutes:
                                prev_matching_event = event
                                continue  # Gap too small, skip ice make
                    
                    title = title_template.replace('{parent_title}', event.get('title', ''))
                    preset_event = self._create_derived_event(
                        parent=event,
                        title=title,
                        event_type=event_type,
                        offset_minutes=offset_minutes,
                        duration_minutes=duration_minutes,
                        anchor=anchor
                    )
                    derived.append(preset_event)
                    prev_matching_event = event
                    
                    if first_per_day and event_date:
                        processed_dates.add(event_date)
        
        return events + derived
    
    # =========================================================================
    # Helper methods
    # =========================================================================
    
    def _matches_rule(
        self, 
        event: Dict, 
        match_types: List[str], 
        match_titles: List[str]
    ) -> bool:
        """Check if an event matches a rule's criteria."""
        event_type = event.get('type', '')
        event_title = event.get('title', '')
        
        # Check type match
        if match_types and event_type in match_types:
            return True
        
        # Check title match
        if match_titles:
            for match_title in match_titles:
                if match_title.lower() in event_title.lower():
                    return True
        
        return False
    
    def _create_derived_event(
        self,
        parent: Dict,
        title: str,
        event_type: str,
        offset_minutes: int,
        duration_minutes: int,
        anchor: str = "start"
    ) -> Dict:
        """Create a derived event relative to a parent event."""
        if anchor == "end":
            base_time = parent.get('end_dt')
        else:
            base_time = parent.get('start_dt')
        
        if not base_time:
            return {}
        
        start_dt = base_time + timedelta(minutes=offset_minutes)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        return {
            'title': title,
            'type': event_type,
            'start_dt': start_dt,
            'end_dt': end_dt,
            'is_derived': True,
            'parent_title': parent.get('title', ''),
        }
