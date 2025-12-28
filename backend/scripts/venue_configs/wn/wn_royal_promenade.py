"""
Royal Promenade venue configuration for Wonder of the Seas.
"""

SHIP_CODE = "WN"
VENUE_NAME = "Royal Promenade"

CONFIG = {
    "known_shows": [
        "Anchors Aweigh Parade", "Bring The Beat Back",
        "Let's Dance", "Thriller Dance Class", "Balloon Drop"
    ],
    "renaming_map": {},
    "default_durations": {
        "Anchors Aweigh Parade": 30
    },
    "prompt_section": """
Royal Promenade is the main thoroughfare.
Look for: Parades, Street Parties
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
