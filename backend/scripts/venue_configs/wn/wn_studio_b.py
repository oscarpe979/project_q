"""
Studio B venue configuration for Wonder of the Seas.
"""

SHIP_CODE = "WN"
VENUE_NAME = "Studio B"

CONFIG = {
    "known_shows": [
        "Ice Show: 365", "Battle of the Sexes", "Open Ice Skating", "Private Ice Skating",
        "Teens Skate", "Laser Tag", "Bingo", "Perfect Couple Game Show", "Top Tier",
        "RED: A Nightclub Experience", "Crazy Quest", "Nightclub", "Family Shush!",
        "Glow Party", "Red Party", "Port & Shopping", "Spa Bingo", "Cast Install", "Ice Melt"
    ],
    "renaming_map": {
        "Ice Spectacular 365": "Ice Show: 365",
        "Ice Spectacular": "Ice Show: 365",
        "Ice Show": "Ice Show: 365"
    },
    "default_durations": {
        "Ice Show: 365": 60,
        "Top Tier": 45,
        "Battle of the Sexes": 60
    },
    "doors_config": [
        {
            "match_titles": ["Ice Show: 365"],
            "offset_minutes": -45,
            "duration_minutes": 15,
            "min_gap_minutes": 45
        },
        {
            "match_titles": ["Family SHUSH!", "Family Shush!", "Bingo", "Royal Bingo", "Spa Bingo"],
            "offset_minutes": -15,
            "duration_minutes": 15,
            "min_gap_minutes": 15
        },
        {
            "match_types": ["game", "movie", "party"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "min_gap_minutes": 30
        },
        {
            "match_types": ["show", "headliner"],
            "offset_minutes": -45,
            "duration_minutes": 15,
            "min_gap_minutes": 45
        },
        {
            "match_types": ["toptier"],
            "offset_minutes": -15,
            "duration_minutes": 15,
            "min_gap_minutes": 15
        }
    ],
    "setup_config": [
        {
            "match_types": ["toptier"],
            "offset_minutes": -75,
            "duration_minutes": 60,
            "title_template": "Set Up Top Tier",
            "min_gap_minutes": 75
        },
        {
            "match_titles": ["Laser Tag"],
            "offset_minutes": -60,
            "duration_minutes": 60,
            "title_template": "Set Up Laser Tag"
        },
        {
            "match_titles": ["Battle of the Sexes", "Crazy Quest", "Glow Party"],
            "offset_minutes": -60,
            "duration_minutes": 30,
            "title_template": "Set Up {parent_title}",
            "min_gap_minutes": 60
        },
        {
            "match_titles": ["RED: Nightclub Experience", "RED: A Nightclub Experience",
                            "RED! Nightclub Experience", "RED Party", "RED! Party"],
            "offset_minutes": -60,
            "duration_minutes": 60,
            "title_template": "Set Up RED",
            "min_gap_minutes": 60
        },
        {
            "match_titles": ["Ice Skating", "Open Ice Skating", "Private Ice Skating",
                            "Teens Skate", "Teens Ice Skate", "Open Skate"],
            "offset_minutes": -30,
            "duration_minutes": 30,
            "title_template": "Set Up Skates",
            "first_per_day": True
        },
        {
            "match_titles": ["Family SHUSH!", "Family Shush!"],
            "offset_minutes": -60,
            "duration_minutes": 30,
            "title_template": "Set Up Family Shush!",
            "min_gap_minutes": 60
        },
        {
            "match_types": ["game", "party", "music"],
            "offset_minutes": -60,
            "duration_minutes": 30,
            "title_template": "Set Up {parent_title}",
            "min_gap_minutes": 60
        }
    ],
    "strike_config": [
        {
            "match_titles": ["Ice Show: 365"],
            "duration_minutes": 30,
            "title_template": "Strike & Ice Scrape",
            "last_per_day": True
        },
        {
            "match_titles": ["Ice Skating", "Open Ice Skating", "Private Ice Skating",
                            "Teens Skate", "Teens Ice Skate", "Open Skate"],
            "duration_minutes": 30,
            "title_template": "Strike Skates",
            "skip_if_next_matches": True
        },
        {
            "match_titles": ["Laser Tag"],
            "duration_minutes": 60,
            "title_template": "Strike Laser Tag"
        },
        {
            "match_titles": ["RED: Nightclub Experience", "RED: A Nightclub Experience",
                            "RED! Nightclub Experience", "RED Party", "RED! Party", "Nightclub"],
            "duration_minutes": 60,
            "title_template": "Strike RED"
        },
        {
            "match_titles": ["Battle of the Sexes", "Crazy Quest", "Glow Party"],
            "duration_minutes": 30,
            "title_template": "Strike {parent_title}"
        },
        {
            "match_types": ["game", "party"],
            "duration_minutes": 30,
            "title_template": "Strike {parent_title}"
        }
    ],
    "warm_up_config": [
        {
            "match_titles": ["Ice Show: 365"],
            "offset_minutes": -210,
            "duration_minutes": 90,
            "title_template": "Warm Up - Specialty Ice",
            "first_per_day": True
        },
        {
            "match_titles": ["Ice Show: 365"],
            "offset_minutes": -120,
            "duration_minutes": 30,
            "title_template": "Warm Up - Cast",
            "first_per_day": True
        }
    ],
    "preset_config": [
        {
            "match_titles": ["Ice Show: 365"],
            "offset_minutes": -240,
            "duration_minutes": 30,
            "title_template": "Ice Make",
            "type": "ice_make",
            "first_per_day": True
        },
        {
            "match_titles": ["Ice Show: 365"],
            "offset_minutes": -90,
            "duration_minutes": 30,
            "title_template": "Ice Make & Presets",
            "type": "preset",
            "first_per_day": True
        },
        {
            "match_titles": ["Ice Show: 365"],
            "offset_minutes": 0,
            "duration_minutes": 30,
            "title_template": "Ice Make & Presets",
            "type": "preset",
            "anchor": "end",
            "skip_last_per_day": True
        },
        {
            "match_titles": ["Ice Skating", "Open Ice Skating", "Private Ice Skating",
                            "Teens Skate", "Teens Ice Skate", "Open Skate"],
            "offset_minutes": -30,
            "duration_minutes": 30,
            "title_template": "Ice Make",
            "type": "ice_make",
            "min_gap_minutes": 30
        }
    ],
    "floor_requirements": {
        "floor": {
            "match_titles": ["Laser Tag", "RED: Nightclub Experience", "Nightclub",
                           "Family SHUSH!", "Family Shush!", "Battle of the Sexes",
                           "Crazy Quest", "Glow Party", "Top Tier"]
        },
        "ice": {
            "match_titles": ["Ice Show: 365", "Ice Skating", "Open Ice Skating",
                           "Private Ice Skating", "Teens Skate", "Ice Make", "Warm Up"]
        }
    },
    "floor_transition": {
        "duration_minutes": 60,
        "titles": {
            "floor_to_ice": "Strike Floor",
            "ice_to_floor": "Set Floor"
        },
        "type": "strike"
    },
    "late_night_config": {
        "cutoff_hour": 1,
        "end_hour": 6,
        "reschedule_hour": 9,
        "long_event_threshold_minutes": 60
    },
    "prompt_section": """
Studio B is an ice rink venue. Key patterns:
- Ice Skating sessions have duration notation like "(5+1hrs)"
- Multiple time slots under one header = multiple events
- Cast Install events = type "cast_install"
""",
    "cross_venue_sources": ["AquaTheater", "Royal Theater", "Royal Promenade"],
    "cross_venue_import_policies": {
        "AquaTheater": {
            "highlight_inclusions": ["show", "headliner", "movie", "game", "backup"],
            "custom_instructions": "For any movie related events, simplify the name to just Movie"
        },
        "Royal Theater": {
            "highlight_inclusions": ["show", "headliner", "comedy", "game", "movie"],
            "custom_instructions": "For any movie related events, simplify the name to just Movie"
        },
        "Royal Promenade": {
            "highlight_inclusions": ["party", "parade", "competition", "show", "class", "activity"],
            "merge_inclusions": ["Anchors Aweigh Parade"],
            "custom_instructions": "Extract ALL Parades, Street Parties, and Theme Activities like 'Thriller Dance Class'."
        }
    }
}


def get_config():
    """Return the venue configuration for database seeding."""
    return {
        "ship_code": SHIP_CODE,
        "venue_name": VENUE_NAME,
        "config": CONFIG
    }
