"""
AquaTheater venue configuration for Wonder of the Seas.
"""

SHIP_CODE = "WN"
VENUE_NAME = "AquaTheater"

CONFIG = {
    "known_shows": [
        "inTENse", "Aqua80", "Aqua Back Up", "Movies On Deck", "Halloween Movies", "Movies"
    ],
    "renaming_map": {
        "InTENse: Maximum Performance": "inTENse",
        "inTENse: Maximum Performance": "inTENse",
        "BACK UP AQUA": "Aqua Back Up"
    },
    "default_durations": {
        "inTENse": 60
    },
    "doors_config": [
        {
            "match_types": ["show", "headliner"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "min_gap_minutes": 30
        }
    ],
    "prompt_section": """
AquaTheater is an outdoor water/dive show venue.
Look for: inTENse, Aqua80, Movie screenings
""",
    "cross_venue_sources": [],
    "cross_venue_import_policies": {}
}


def get_config():
    """Return the venue configuration for database seeding."""
    return {
        "ship_code": SHIP_CODE,
        "venue_name": VENUE_NAME,
        "config": CONFIG
    }
