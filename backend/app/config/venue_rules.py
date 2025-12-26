"""
Venue Rules Configuration

Defines venue metadata and cross-venue import policies keyed by ship_code.
Ship codes are from Ship.code in database (e.g., "WN", "AL", "HM").
"""

from typing import Dict, List, Any


# ═══════════════════════════════════════════════════════════════════════════════
# VENUE METADATA - Keyed by (ship_code, venue_name)
# Contains: known_shows, renaming_map, default_durations
# ═══════════════════════════════════════════════════════════════════════════════

VENUE_METADATA: Dict[tuple, Dict[str, Any]] = {
    # ───────────────────────────────────────────────────────────────────────────
    # Wonder of the Seas (WN)
    # ───────────────────────────────────────────────────────────────────────────
    ("WN", "Studio B"): {
        "known_shows": [
            "Ice Show: 365", "Battle of the Sexes", "Open Ice Skating", "Private Ice Skating",
            "Teens Skate", "Laser Tag", "Bingo", "Perfect Couple Game Show", "Top Tier",
            "RED: A Nightclub Experience", "Crazy Quest", "Nightclub", "Family Shush!",
            "Glow Party", "Red Party", "Port & Shopping", "Spa Bingo", "Cast Install", "Ice Melt"
        ],
        "renaming_map": {
            "Ice Spectacular 365": "Ice Show: 365",
            "Ice Spectacular": "Ice Show: 365",
            "Ice Show": "Ice Show: 365",
        },
        "default_durations": {
            "Ice Show: 365": 60,
            "Top Tier": 45,
            "Battle of the Sexes": 60,
        },
        # Derived Event Rules - auto-generate events based on parent shows
        "derived_event_rules": {
            "warm_up": [
                # Specialty Ice Warm Up - 3.5 hours before first Ice Show of the night
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": -210,  # 3.5 hours before
                    "duration_minutes": 90,
                    "title_template": "Warm Up - Specialty Ice",
                    "type": "warm_up",
                    "first_per_day": True,
                },
                # Cast Warm Up - 2 hours before first Ice Show (right after Specialty Ice)
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": -120,  # 2 hours before
                    "duration_minutes": 30,
                    "title_template": "Warm Up - Cast",
                    "type": "warm_up",
                    "first_per_day": True,
                },
            ],
            "preset": [
                # Ice Make - 30 min before Specialty Ice Warm Up (4 hours before Ice Show)
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": -240,  # 4 hours before (30 min before Specialty Ice Warm Up)
                    "duration_minutes": 30,
                    "title_template": "Ice Make",
                    "type": "preset",
                    "first_per_day": True,
                },
                # Ice Make & Presets - 1.5 hours before first Ice Show
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": -90,  # 1.5 hours before
                    "duration_minutes": 30,
                    "title_template": "Ice Make & Presets",
                    "type": "preset",
                    "first_per_day": True,
                },
                # Between-show presets - After each show ends (except last show of day)
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": 0,  # Starts immediately after show ends
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Ice Make & Presets",
                    "type": "preset",
                    "skip_last_per_day": True,  # Fire after all shows except the last
                    "min_per_day": 2,  # Only when 2+ shows per day
                },
                # NOTE: Ice Make for skating sessions is in "ice_make" category below
            ],
            "doors": [
                # Specific: Ice Show doors
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": -45,
                    "duration_minutes": 15,
                    "title_template": "Doors",
                    "type": "doors",
                    "min_gap_minutes": 45,  # Skip if stacked with previous event
                    "check_all_events": True,  # Check gap against ALL events, not just same-type
                },
                # Specific: Family Shush & Bingo doors - only 15 mins before
                {
                    "match_titles": ["Family SHUSH!", "Family Shush!", "Bingo", "Royal Bingo", "Spa Bingo"],
                    "offset_minutes": -15,
                    "duration_minutes": 15,
                    "title_template": "Doors",
                    "type": "doors",
                    "min_gap_minutes": 15,
                    "check_all_events": True,
                },
                {
                    "match_categories": ["game", "movie", "party"],
                    "offset_minutes": -30,
                    "duration_minutes": 15,
                    "title_template": "Doors",
                    "type": "doors",
                    "min_gap_minutes": 30,  # Skip if stacked with previous event
                    "check_all_events": True,  # Check gap against ALL events, not just same-type
                },
                # Default: All shows and headliners get standard doors
                {
                    "match_categories": ["show", "headliner"],
                    "offset_minutes": -45,
                    "duration_minutes": 15,
                    "title_template": "Doors",
                    "type": "doors",
                    "min_gap_minutes": 45,  # Skip if stacked with previous event
                    "check_all_events": True,  # Check gap against ALL events, not just same-type
                },
                # Top Tier Event doors - 15 min before event
                {
                    "match_categories": ["toptier"],
                    "offset_minutes": -15,
                    "duration_minutes": 15,
                    "title_template": "Doors",
                    "type": "doors",
                    "min_gap_minutes": 15,
                    "check_all_events": True,  # Check gap against ALL events, not just same-type
                },
            ],
            "setup": [
                # Set Up - Top Tier: 1 hour setup, 15 min before doors (30 min before event)
                {
                    "match_categories": ["toptier"],
                    "offset_minutes": -75,  # 30 min before event + 60 min duration - 15 min overlap
                    "duration_minutes": 60,
                    "title_template": "Set Up Top Tier",
                    "type": "setup",
                    "min_gap_minutes": 75,  # Skip if stacked
                },
                # Set Up - Laser Tag: 1 hour before event, lasting 1 hour
                {
                    "match_titles": ["Laser Tag"],
                    "offset_minutes": -60,  # 1 hour before
                    "duration_minutes": 60,
                    "title_template": "Set Up Laser Tag",
                    "type": "setup",
                },
                # Set Up - Family SHUSH!: 45 mins before (doors only 15 mins before)
                {
                    "match_titles": ["Family SHUSH!", "Family Shush!"],
                    "offset_minutes": -45,  # 45 mins before (15 mins later than others)
                    "duration_minutes": 30,
                    "title_template": "Set Up Family Shush!",
                    "type": "setup",
                    "min_gap_minutes": 60,
                },
                # Set Up - RED Party: Use short title "RED" instead of full name
                {
                    "match_titles": ["RED: Nightclub Experience", "RED: A Nightclub Experience",
                                    "RED! Nightclub Experience", "RED Party", "RED! Party"],
                    "offset_minutes": -60,  # 1 hour before
                    "duration_minutes": 30,
                    "title_template": "Set Up RED",
                    "type": "setup",
                    "min_gap_minutes": 60,
                },
                # Set Up - Other Game Shows & Parties: 1 hour before, 30 min duration
                # Note: 'Nightclub' removed - it substring-matches 'RED: A Nightclub Experience'
                {
                    "match_titles": ["Battle of the Sexes", "Crazy Quest", "Glow Party"],
                    "offset_minutes": -60,  # 1 hour before
                    "duration_minutes": 30,
                    "title_template": "Set Up {parent_title}",
                    "type": "setup",
                    "min_gap_minutes": 60,  # Skip if stacked (only first of block gets setup)
                },
                # Set Up Skates - Only before the FIRST skating session of the day
                # MUST be before catch-all so specific rule matches first
                {
                    "match_titles": ["Ice Skating", "Open Ice Skating", "Private Ice Skating", 
                                    "Teens Skate", "Teens Ice Skate", "Open Skate"],
                    "offset_minutes": -30,  # 30 min before first session
                    "duration_minutes": 30,
                    "title_template": "Set Up Skates",
                    "type": "setup",
                    "first_per_day": True,  # Only before first skating session
                },
                # CATCH-ALL: Set Up for any game/party/music not matched above
                # Note: 'activity' excluded - skating has its own rule with first_per_day
                # Rules process in order; specific match_titles rules fire first
                # and add to matched_parent_keys, so catch-all skips those events
                {
                    "match_categories": ["game", "party", "music"],
                    "offset_minutes": -60,  # 1 hour before
                    "duration_minutes": 30,
                    "title_template": "Set Up {parent_title}",
                    "type": "setup",
                    "min_gap_minutes": 60,  # Skip if stacked
                },
            ],
            "ice_make": [
                # Ice Make - 30 min before EACH skating session (skips if back-to-back)
                {
                    "match_titles": ["Ice Skating", "Open Ice Skating", "Private Ice Skating", 
                                    "Teens Skate", "Teens Ice Skate", "Open Skate"],
                    "offset_minutes": -30,  # 30 min before session
                    "duration_minutes": 30,
                    "title_template": "Ice Make",
                    "type": "ice_make",  # Unique type - NOT merged with setup/strike/preset
                    "min_gap_minutes": 30,  # Skip if sessions are back-to-back
                },
            ],
            "strike": [
                # Strike & Ice Scrape - After the last Ice Show of the day
                {
                    "match_titles": ["Ice Show: 365"],
                    "offset_minutes": 0,  # Starts immediately after show ends
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike & Ice Scrape",
                    "type": "strike",
                    "last_per_day": True,  # Simply fires after the LAST Ice Show of the day
                },
                # Strike Skates - After each skating session
                # Skips if the next venue event is also a skating session (contiguous sessions)
                {
                    "match_titles": ["Ice Skating", "Open Ice Skating", "Private Ice Skating", 
                                    "Teens Skate", "Teens Ice Skate", "Open Skate"],
                    "offset_minutes": 0,  # Starts immediately after session ends
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike Skates",
                    "type": "strike",
                    "last_per_day": True,
                    "skip_if_next_matches": True,  # Skip if next venue event is also a skating session
                },
                # Strike - Laser Tag: After event ends, lasting 1 hour
                {
                    "match_titles": ["Laser Tag"],
                    "offset_minutes": 0,  # Starts immediately after event ends
                    "anchor": "end",
                    "duration_minutes": 60,
                    "title_template": "Strike Laser Tag",
                    "type": "strike",
                },
                # Strike - RED Party: Use short title "RED" instead of full name
                {
                    "match_titles": ["RED: Nightclub Experience", "RED: A Nightclub Experience",
                                    "RED! Nightclub Experience", "RED Party", "RED! Party", "Nightclub"],
                    "offset_minutes": 0,  # Starts immediately after event ends
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike RED",
                    "type": "strike",
                },
                # Strike - Game Shows & Parties: After EACH event ends, 30 min
                # Note: Overlap resolution will omit strikes that overlap with next event
                {
                    "match_titles": ["Battle of the Sexes", "Crazy Quest", "Family SHUSH!", "Family Shush!",
                                    "Glow Party"],
                    "offset_minutes": 0,  # Starts immediately after event ends
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike {parent_title}",
                    "type": "strike",
                },
                # CATCH-ALL: Strike for any game/party not matched above
                # Note: 'activity' excluded - skating has its own rule
                # Rules process in order; specific match_titles rules fire first
                # and add to matched_parent_keys, so catch-all skips those events
                {
                    "match_categories": ["game", "party"],
                    "offset_minutes": 0,  # Starts immediately after event ends
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike {parent_title}",
                    "type": "strike",
                },
            ],
        },
        # Floor transition config - for switching between ice and floor events
        "floor_requirements": {
            # Events that need the floor (ice covered)
            "floor": {
                "match_titles": ["Laser Tag", "RED: Nightclub Experience", "Nightclub",
                               "Family SHUSH!", "Family Shush!", "Battle of the Sexes", "Crazy Quest", 
                               "Glow Party", "Top Tier"],
            },
            # Events that need ice exposed (no floor)
            "ice": {
                "match_titles": ["Ice Show: 365", "Ice Skating", "Open Ice Skating", 
                               "Private Ice Skating", "Teens Skate", "Teens Ice Skate",
                               "Ice Make", "Warm Up"],
            },
        },
        "floor_transition": {
            "duration_minutes": 60,
            "titles": {
                "floor_to_ice": "Strike Floor",
                "ice_to_floor": "Set Floor",
            },
            "type": "strike",
        },
        # Late night handling - derived events in late-night window get rescheduled
        "late_night_config": {
            "cutoff_hour": 1,               # Events starting at 1 AM+ are always rescheduled
            "end_hour": 6,                  # Late night window ends at 6 AM
            "reschedule_hour": 9,           # Reschedule late-night events to 9 AM
            "long_event_threshold_minutes": 60,  # Events after midnight but >60min also reschedule
        },
    },
    ("WN", "AquaTheater"): {
        "known_shows": ["inTENse", "Aqua80", "Aqua Back Up", "Movies On Deck", "Halloween Movies", "Movies"],
        "renaming_map": {
            "InTENse: Maximum Performance": "inTENse",
            "inTENse: Maximum Performance": "inTENse",
            "Movies On Deck": "Movies On Deck",
            "BACK UP AQUA": "Aqua Back Up",
            "Back Up": "Aqua Back Up",
        },
        "default_durations": {"inTENse": 60},
    },
    ("WN", "Royal Theater"): {
        "known_shows": ["Voices", "The Effectors II", "Headliner Showtime", "Red Carpet Movie", "Movie", "Bingo"],
        "renaming_map": {
            "The Effectors II: Crash & Burn": "The Effectors II",
            "Signature Production: Voices": "Voices",
        },
        "default_durations": {"Voices": 45, "Effectors II": 60, "Love and Marraige": 60, "Red Carpet Movie": 120,
                                "Headliner": 60, "Captain's Corner": 60
        },
    },
    ("WN", "Royal Promenade"): {
        "known_shows": [
            "Anchors Aweigh Parade", "Bring The Beat Back",
            "Let's Dance", "Thriller Dance Class", "Balloon Drop"
        ],
        "renaming_map": {},
        "default_durations": {"Anchors Aweigh Parade": 30},
    },

    # ───────────────────────────────────────────────────────────────────────────
    # Add more ships as needed...
    # ───────────────────────────────────────────────────────────────────────────
}


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-VENUE POLICIES - Keyed by (ship_code, target_venue, source_venue)
# Contains: highlight_inclusions, custom_instructions, merge rules
# Does NOT contain known_shows (pulled from VENUE_METADATA automatically)
#
# MERGE RULES:
#   - merge_inclusions: [] or missing → highlights only (nothing merged to main schedule)
#   - merge_inclusions: ["Event A", "Event B"] → merge only these specific events
#   - merge_inclusions: ["*"] → merge ALL events from source venue
# ═══════════════════════════════════════════════════════════════════════════════

CROSS_VENUE_POLICIES: Dict[tuple, Dict[str, Any]] = {
    # ───────────────────────────────────────────────────────────────────────────
    # Wonder of the Seas (WN) - Studio B imports
    # ───────────────────────────────────────────────────────────────────────────
    ("WN", "Studio B", "AquaTheater"): {
        "highlight_inclusions": ["show", "headliner", "movie", "game", "backup"],
        "custom_instructions": "For any movie related events, simplify the name to just Movie",
    },
    ("WN", "Studio B", "Royal Theater"): {
        "highlight_inclusions": ["show", "headliner", "comedy", "game", "movie"],
        "custom_instructions": "For any movie related events, simplify the name to just Movie",
    },
    ("WN", "Studio B", "Royal Promenade"): {
        "highlight_inclusions": ["party", "parade", "competition", "show", "class", "activity"],
        "merge_inclusions": ["Anchors Aweigh Parade"],
        "custom_instructions": (
            "Extract ALL Parades, Street Parties, and Theme Activities like 'Thriller Dance Class'."
        ),
    },

    # ───────────────────────────────────────────────────────────────────────────
    # Wonder of the Seas (WN) - Royal Theater imports
    # ───────────────────────────────────────────────────────────────────────────
    ("WN", "Royal Theater", "AquaTheater"): {
        "highlight_inclusions": ["show", "headliner", "movie", "game", "backup"],
        "custom_instructions": "For any movie related events, simplify the name to just Movie",
    },
    ("WN", "Royal Theater", "Studio B"): {
        "highlight_inclusions": ["show", "headliner", "comedy", "game", "movie"],
        "custom_instructions": ""
    },
    ("WN", "Royal Theater", "Royal Promenade"): {
        "highlight_inclusions": ["party", "parade", "competition", "show", "class", "activity"],
        "merge_inclusions": ["Anchors Aweigh Parade"],
        "custom_instructions": (
            "Extract ALL Parades, Street Parties, and Theme Activities like 'Thriller Dance Class'."
        ),
    },

    # ───────────────────────────────────────────────────────────────────────────
    # Wonder of the Seas (WN) - AquaTheater imports
    # ───────────────────────────────────────────────────────────────────────────
    ("WN", "AquaTheater", "Royal Theater"): {
        "highlight_inclusions": ["show", "headliner", "movie", "game"],
        "custom_instructions": "For any movie related events, simplify the name to just Movie",
    },
    ("WN", "AquaTheater", "Studio B"): {
        "highlight_inclusions": ["show", "headliner", "comedy", "game", "movie"],
        "custom_instructions": ""
    },
    ("WN", "AquaTheater", "Royal Promenade"): {
        "highlight_inclusions": ["party", "parade", "competition", "show", "class", "activity"],
        "merge_inclusions": ["Anchors Aweigh Parade"],
        "custom_instructions": (
            "Extract ALL Parades, Street Parties, and Theme Activities like 'Thriller Dance Class'."
        ),
    },

    # ───────────────────────────────────────────────────────────────────────────
    # Add more ships/venues as needed...
    # ───────────────────────────────────────────────────────────────────────────
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_source_venues(ship_code: str, target_venue: str) -> List[str]:
    """
    Extract source venues by scanning CROSS_VENUE_POLICIES for entries
    matching (ship_code, target_venue, *).
    """
    if not ship_code:
        return []
    return [
        key[2]  # The third element is source_venue
        for key in CROSS_VENUE_POLICIES.keys()
        if key[0] == ship_code and key[1] == target_venue
    ]


def get_venue_rules(ship_code: str, target_venue: str, source_venues: List[str] = None) -> Dict[str, Any]:
    """
    Get complete parsing rules for a ship + venue combination.
    
    Returns:
        {
            "self_extraction_policy": {known_shows, renaming_map, default_durations},
            "cross_venue_import_policies": {
                "AquaTheater": {
                    "highlight_inclusions": [...],
                    "known_shows": [...],        # Pulled from VENUE_METADATA
                    "renaming_map": {...},       # Pulled from VENUE_METADATA
                    "custom_instructions": "...",
                },
                ...
            },
            "derived_event_rules": {
                "doors": [...],
                "rehearsal": [...],
                ...
            }
        }
    """
    if not ship_code:
        return {"self_extraction_policy": {}, "cross_venue_import_policies": {}, "derived_event_rules": {}}
    
    # If source_venues not provided, derive from config
    if source_venues is None:
        source_venues = get_source_venues(ship_code, target_venue)
    
    # Self extraction policy
    self_policy = VENUE_METADATA.get((ship_code, target_venue), {})
    
    # Extract derived event rules
    derived_rules = self_policy.get("derived_event_rules", {})
    
    # Cross-venue policies (merge source metadata with policy)
    cross_policies = {}
    for source_venue in source_venues:
        policy_key = (ship_code, target_venue, source_venue)
        policy = CROSS_VENUE_POLICIES.get(policy_key, {}).copy()
        
        # Get source venue's metadata
        source_metadata = VENUE_METADATA.get((ship_code, source_venue), {})
        
        # Merge: policy-specific rules + source venue's shared metadata
        policy["known_shows"] = source_metadata.get("known_shows", [])
        policy["renaming_map"] = source_metadata.get("renaming_map", {})
        policy["default_durations"] = source_metadata.get("default_durations", {})
        
        cross_policies[source_venue] = policy
    
    return {
        "self_extraction_policy": self_policy,
        "cross_venue_import_policies": cross_policies,
        "derived_event_rules": derived_rules,
    }
