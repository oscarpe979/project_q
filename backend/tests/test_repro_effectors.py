import pytest
from datetime import datetime, time, timedelta
from backend.app.venues.base import VenueRules

class TestReproEffectors:
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
        # Mimic wn_royal_theater.py configuration for Effectors
        rules.preset_config = [
            # Rule 1: Points Check (Offset -120)
            {
                "match_titles": ["The Effectors II"],
                "offset_minutes": -120,
                "duration_minutes": 15,
                "title_template": "Points Check",
                "type": "preset",
                "first_per_day": True
            },
            # Rule 2: Sound Check (Offset -105)
            {
                "match_titles": ["The Effectors II"],
                "offset_minutes": -105,
                "duration_minutes": 30,
                "title_template": "Sound Check",
                "type": "preset",
                "first_per_day": True
            },
            # Rule 3: Show Presets (Offset -75) -> THE ONE MISSING
            {
                "match_titles": ["The Effectors II"],
                "offset_minutes": -75,
                "duration_minutes": 30,
                "title_template": "Show Presets",
                "type": "preset",
                "first_per_day": True
            },
            # Rule 4: Show Presets (End Anchor, Exclude Tech Run)
            {
                "match_titles": ["The Effectors II"],
                "exclude_types": ["tech_run"],
                "offset_minutes": 0,
                "duration_minutes": 30,
                "title_template": "Show Presets",
                "type": "preset",
                "anchor": "end",
                "skip_last_per_day": True
            }
        ]
        
        rules.tech_run_config = [{
            "match_titles": ["The Effectors II"],
            "title_template": "Tech Run {parent_title}",
            "type": "tech_run"
        }]
        return rules

    @pytest.fixture
    def evening_show(self):
        return {
            "title": "The Effectors II",
            "start_dt": datetime(2024, 1, 1, 19, 30),  # 7:30 PM
            "end_dt": datetime(2024, 1, 1, 20, 30),
            "type": "show",
            "venue": "Royal Theater"
        }

    def test_effectors_presets_with_evening_show(self, rules, evening_show):
        """
        Scenario: Day 6 has both an Evening Show (7:30 PM) and we generate a Tech Run (10 AM).
        Ensure the Tech Run's start-anchored presets are NOT blocked by the Evening Show's quota.
        """
        events = [evening_show]
        result = rules.generate_derived_events(events)
        
        presets = [e for e in result if e.get('type') == 'preset']
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        
        print("\nGenerated Events:")
        for e in result:
            print(f"- {e['title']} ({e['type']}) at {e['start_dt']}")
        
        # Ensure Tech Run was generated
        assert len(tech_runs) == 1, f"Expected 1 Tech Run, got {len(tech_runs)}"
        
        # Check for 'Show Presets' (Rule 3) at ~8:45 AM (from Tech Run at 10 AM)
        show_presets = [p for p in presets if p['title'] == 'Show Presets' and p['start_dt'].hour < 12]
        
        # THIS SHOULD PASS - If it fails, then the bug is confirmed.
        assert len(show_presets) >= 1, f"Missing 'Show Presets' (Rule 3) for Tech Run! Got: {[p['title'] for p in presets]}"
        
        presets = [e for e in result if e.get('type') == 'preset']
        
        print("\nGenerated Presets:")
        for p in presets:
            print(f"- {p['title']} at {p['start_dt']}")
            
        titles = [p['title'] for p in presets]
        
        # Expectation:
        # 1. Points Check (8:00)
        # 2. Sound Check (8:15)
        # 3. Show Presets (8:45) -> THIS IS THE ONE USER SAYS IS MISSING
        
        assert "Points Check" in titles
        assert "Sound Check" in titles
        assert "Show Presets" in titles, "Missing 'Show Presets' (Rule 3) for Tech Run"
        
        # Ensure Rule 4 (End Anchored) did NOT fire (due to exclude_types)
        # It would be at 11:00 AM if it fired.
        end_presets = [p for p in presets if p['title'] == "Show Presets" and p['start_dt'].hour == 11]
        assert len(end_presets) == 0, "Rule 4 incorrectly fired for Tech Run"
