"""
Royal Theater venue configuration for Wonder of the Seas.
"""

SHIP_CODE = "WN"
VENUE_NAME = "Royal Theater"

CONFIG = {
    "known_shows": [
        "Voices", "The Effectors II", "Headliner Showtime", "Red Carpet Movie", "Movie", "Bingo",
        "Late Night Comedy", 'Price is Right', 'Adult Comedy', 'Captain Corner', 'Red Carpet Move',
        'Port and Shopping', 'Love and Marriage', 
    ],
    "renaming_map": {
        "The Effectors II: Crash & Burn": "The Effectors II",
        "Signature Production: Voices": "Voices"
    },
    "default_durations": {
        "Voices": 45,
        "Effectors II": 60,
        "Love and Marraige": 60,
        "Red Carpet Movie": 120,
        "Headliner": 60,
        "Captain's Corner": 60
    },
    "doors_config": [
        {
            "match_types": ["show", "headliner", "comedy", "movie", "game", "party"],
            "offset_minutes": -45,
            "duration_minutes": 15,
            "min_gap_minutes": 30
        }
    ],
    "preset_config": [
        {
            "match_titles": ["The Effectors II", "The Effectors: Crash and Burn"],
            "offset_minutes": -120,
            "duration_minutes": 15,
            "title_template": "Points Check & Bounce",
            "type": "preset",
            "first_per_day": True
        },
        {
            "match_titles": ["The Effectors II", "The Effectors: Crash and Burn"],
            "offset_minutes": -105,
            "duration_minutes": 30,
            "title_template": "Sound Check",
            "type": "preset",
            "first_per_day": True
        },
        {
            "match_titles": ["The Effectors II", "The Effectors: Crash and Burn"],
            "offset_minutes": -75,
            "duration_minutes": 30,
            "title_template": "Show Presets",
            "type": "preset",
            "first_per_day": True
        },
        {
            "match_titles": ["The Effectors II", "The Effectors: Crash and Burn", "Voices"],
            "offset_minutes": 0,
            "duration_minutes": 30,
            "title_template": "Show Presets",
            "type": "preset",
            "anchor": "end",
            "skip_last_per_day": True
        },
    ],
    "strike_config": [
        {
            "match_types": ['show', "game", "party", 'comedy', 'headliner'],
            "duration_minutes": 30,
            "title_template": "Strike {parent_title}",
            "last_per_day": True
        }
    ],
    "prompt_section": """
Royal Theater is the main theater venue.
Look for: Voices, The Effectors II, Headliners
""",
    "cross_venue_sources": ["AquaTheater", "Studio B", "Royal Promenade"],
    "cross_venue_import_policies": {
        "AquaTheater": {
            "highlight_inclusions": ["show", "headliner", "movie", "game", "backup"],
            "custom_instructions": "For any movie related events, simplify the name to just Movie"
        },
        "Studio B": {
            "highlight_inclusions": ["show", "headliner", "comedy", "game", "movie"],
            "custom_instructions": ""
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
