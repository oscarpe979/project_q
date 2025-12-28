
import pytest
from datetime import datetime
from backend.app.venues.base import VenueRules

class TestStrikeLogicRegression:
    """
    Regression tests for strike logic, specifically the 'last_per_day' rule.
    """

    @pytest.fixture
    def venue_rules(self):
        """Standard venue rules with a last_per_day strike rule."""
        rules = VenueRules()
        # Rule matches "show" or "game"
        rules.strike_config = [{
            "match_types": ["show", "game"],
            "duration_minutes": 30,
            "title_template": "Strike {parent_title}",
            "last_per_day": True,
            "type": "strike"
        }]
        return rules

    def test_different_titles_do_not_suppress_each_other(self, venue_rules):
        """
        Scenario: 'Show A' followed by 'Show B'.
        Both match the rule (type='show').
        Old Logic: Show B suppresses Show A's strike (because it's a 'later matching event').
        New Logic: Show B does NOT suppress Show A's strike (because titles differ).
        """
        events = [
            {
                "title": "The Effectors II",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
                "type": "show",
                "venue": "Royal Theater",
                "raw_date": "2025-01-15"
            },
            {
                "title": "Voices",
                "start_dt": datetime(2025, 1, 15, 21, 0),
                "end_dt": datetime(2025, 1, 15, 22, 0),
                "type": "show",  # Same type
                "venue": "Royal Theater",
                "raw_date": "2025-01-15"
            }
        ]

        result = venue_rules.generate_derived_events(events)
        
        # We expect TWO strikes:
        # 1. Strike The Effectors II (at 20:00)
        # 2. Strike Voices (at 22:00)
        strikes = [e for e in result if e.get('type') == 'strike']
        
        strike_titles = sorted([e['title'] for e in strikes])
        expected_titles = sorted(["Strike The Effectors II", "Strike Voices"])
        
        assert len(strikes) == 2, f"Expected 2 strikes, got {len(strikes)}: {strike_titles}"
        assert strike_titles == expected_titles

    def test_same_titles_do_suppress_each_other(self, venue_rules):
        """
        Scenario: 'Show A' followed by 'Show A'.
        New Logic: The second Show A SHOULD suppress the first one's strike.
        """
        events = [
            {
                "title": "The Effectors II",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
                "type": "show",
                "venue": "Royal Theater",
                "raw_date": "2025-01-15"
            },
            {
                "title": "The Effectors II",
                "start_dt": datetime(2025, 1, 15, 21, 0),
                "end_dt": datetime(2025, 1, 15, 22, 0),
                "type": "show",
                "venue": "Royal Theater",
                "raw_date": "2025-01-15"
            }
        ]

        result = venue_rules.generate_derived_events(events)
        
        # We expect ONE strike:
        # Only after the second show
        strikes = [e for e in result if e.get('type') == 'strike']
        
        assert len(strikes) == 1, f"Expected 1 strike, got {len(strikes)}: {[e['title'] for e in strikes]}"
        assert strikes[0]['title'] == "Strike The Effectors II"
        # Ensure it's the later one (starts at 22:00)
        assert strikes[0]['start_dt'] == datetime(2025, 1, 15, 22, 0)
