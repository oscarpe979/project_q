"""
Studio B Venue Rules - Wonder of the Seas

Ice rink venue with custom logic for floor/ice transitions.
Configs are loaded from database; this class provides ice-specific algorithms.
"""

from typing import Dict, List
from datetime import timedelta

from ..base import VenueRules


class StudioBRules(VenueRules):
    """
    Studio B is an ice rink venue with unique requirements:
    - Floor/ice transitions when switching between floor and ice events
    - Ice Make events before shows and skating sessions
    - Warm ups for specialty ice and cast
    
    Configs (doors, setup, strike rules) come from the database.
    This class overrides methods that need ice-specific LOGIC.
    """
    
    # Ice-specific config properties not in base class (loaded from _config)
    @property
    def floor_requirements(self) -> Dict:
        return getattr(self, '_config', {}).get('floor_requirements', {})
    
    @property
    def floor_transition(self) -> Dict:
        return getattr(self, '_config', {}).get('floor_transition', {})
    
    def generate_derived_events(self, events: List[Dict]) -> List[Dict]:
        """
        Generate all derived events for Studio B.
        
        Overrides base to add ice-specific events after standard derivations.
        """
        # Only process non-derived events through each generator
        original_events = [e for e in events if not e.get('is_derived')]
        
        all_derived = []
        
        # Standard derived events from base class
        doors_result = self._generate_doors(original_events)
        all_derived.extend([e for e in doors_result if e.get('is_derived')])
        
        setup_result = self._generate_setup(original_events)
        all_derived.extend([e for e in setup_result if e.get('is_derived')])
        
        strike_result = self._generate_strike(original_events)
        all_derived.extend([e for e in strike_result if e.get('is_derived')])
        
        # Ice-specific derived events (using base class config-driven methods)
        warmup_result = self._generate_warm_up(original_events)
        all_derived.extend([e for e in warmup_result if e.get('is_derived')])
        
        preset_result = self._generate_preset(original_events)
        all_derived.extend([e for e in preset_result if e.get('is_derived')])
        
        # Combine events + derived for floor transitions (needs all events)
        all_events = events + all_derived
        
        # Ice-specific: Floor transitions (custom logic in this class)
        all_events = self._generate_floor_transitions(all_events)
        
        return all_events
    
    def _generate_floor_transitions(self, events: List[Dict]) -> List[Dict]:
        """
        Generate floor/ice transition events.
        
        When the venue switches between floor events (Laser Tag, RED Party)
        and ice events (Ice Show, Skating), we need transition events.
        """
        if not self.floor_requirements or not self.floor_transition:
            return events
        
        # Sort events chronologically
        sorted_events = sorted(events, key=lambda x: x.get('start_dt'))
        
        # Track floor state and transitions
        transition_events = []
        current_floor_state = None  # True = floor, False = ice, None = unknown
        prev_event_with_floor_need = None
        
        for event in sorted_events:
            # Skip derived events - only original events trigger floor transitions
            if event.get('is_derived'):
                continue
            
            floor_need = self._get_floor_need(event)
            
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
                transition = self._create_floor_transition(
                    prev_event_with_floor_need,
                    event,
                    current_floor_state,
                    floor_need
                )
                if transition:
                    transition_events.append(transition)
            
            # Update state
            current_floor_state = floor_need
            prev_event_with_floor_need = event
        
        # Merge transitions with existing events
        all_events = self._merge_floor_transitions_with_existing(events, transition_events)
        all_events.sort(key=lambda x: x['start_dt'])
        
        return all_events
    
    def _get_floor_need(self, event: Dict) -> bool:
        """Determine if an event needs the floor (True), ice (False), or doesn't care (None)."""
        title = event.get('title', '')
        
        # Check floor events (needs_floor: True)
        floor_config = self.floor_requirements.get('floor', {})
        floor_titles = floor_config.get('match_titles', [])
        for match_title in floor_titles:
            if match_title.lower() in title.lower():
                return True
        
        # Check ice events (needs_floor: False)
        ice_config = self.floor_requirements.get('ice', {})
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
        next_floor_state: bool
    ) -> Dict:
        """Create a floor transition event between two events."""
        transition_config = self.floor_transition
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
        is_after_midnight = (prev_end.hour == 0 and prev_end.minute > 0) or (prev_end.hour > 0 and prev_end.hour < 6)
        
        if is_after_midnight:
            # After midnight - prefer 9 AM for morning strikes
            preferred_9am = next_start.replace(hour=9, minute=0, second=0, microsecond=0)
            
            if next_start.hour < 10:
                transition_end = next_start
                transition_start = transition_end - duration
            else:
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
    
    def _merge_floor_transitions_with_existing(
        self,
        events: List[Dict],
        transition_events: List[Dict]
    ) -> List[Dict]:
        """Merge floor transition events with existing events that overlap."""
        if not transition_events:
            return events
        
        final_events = list(events)
        
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
                
                # Check for overlap OR adjacent
                if not (trans_end < evt_start or trans_start > evt_end):
                    if evt.get('type') in ['strike', 'preset', 'setup']:
                        overlapping = evt
                        overlapping_idx = i
                        break
            
            if overlapping:
                # Combine titles
                existing_title = overlapping.get('title', '')
                if trans_title and trans_title not in existing_title:
                    final_events[overlapping_idx]['title'] = f"{existing_title} & {trans_title}"
                
                # Take earliest start, keep longest duration
                existing_start = overlapping.get('start_dt')
                existing_end = overlapping.get('end_dt')
                new_start = min(trans_start, existing_start)
                existing_duration = existing_end - existing_start
                trans_duration = trans_end - trans_start
                longest_duration = max(existing_duration, trans_duration)
                
                final_events[overlapping_idx]['start_dt'] = new_start
                final_events[overlapping_idx]['end_dt'] = new_start + longest_duration
            else:
                final_events.append(transition)
        
        return final_events
    
    def build_prompt_section(self) -> str:
        """Studio B specific parsing instructions for LLM."""
        return self.prompt_section or """
Studio B is an ice rink venue. Key patterns:
- Ice Skating sessions have duration notation like "(5+1hrs)"
- Multiple time slots under one header = multiple events
- Cast Install events = type "cast_install"
"""
