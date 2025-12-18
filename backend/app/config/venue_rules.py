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
            "Glow Party", "Red Party", "Port & Shopping", "Spa Bingo"
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
            }
        }
    """
    if not ship_code:
        return {"self_extraction_policy": {}, "cross_venue_import_policies": {}}
    
    # If source_venues not provided, derive from config
    if source_venues is None:
        source_venues = get_source_venues(ship_code, target_venue)
    
    # Self extraction policy
    self_policy = VENUE_METADATA.get((ship_code, target_venue), {})
    
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
    }
