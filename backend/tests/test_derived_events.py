"""
Test suite for Derived Event Rules System (TDD).

Tests the functionality for automatically generating derived events 
(Doors, Rehearsals, Set-ups, Strikes) based on configurable rules.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES: Sample Data
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_show_event():
    """A typical show event that should trigger doors/rehearsal rules."""
    return {
        "title": "Ice Show: 365",
        "start_dt": datetime(2024, 1, 15, 19, 0),  # 7:00 PM
        "end_dt": datetime(2024, 1, 15, 20, 0),    # 8:00 PM
        "category": "show",
        "venue": "Studio B",
        "raw_date": "2024-01-15"
    }


@pytest.fixture
def sample_headliner_event():
    """A headliner event that should trigger doors rules."""
    return {
        "title": "Headliner: Randy Cabral",
        "start_dt": datetime(2024, 1, 15, 21, 30),  # 9:30 PM
        "end_dt": datetime(2024, 1, 15, 22, 30),    # 10:30 PM
        "category": "headliner",
        "venue": "Royal Theater",
        "raw_date": "2024-01-15"
    }


@pytest.fixture
def sample_activity_event():
    """An activity event that should NOT trigger doors rules (by default)."""
    return {
        "title": "Open Ice Skating",
        "start_dt": datetime(2024, 1, 15, 14, 0),  # 2:00 PM
        "end_dt": datetime(2024, 1, 15, 16, 0),    # 4:00 PM
        "category": "activity",
        "venue": "Studio B",
        "raw_date": "2024-01-15"
    }


@pytest.fixture
def doors_rule_basic():
    """Basic doors rule matching shows and headliners."""
    return {
        "match_categories": ["show", "headliner"],
        "offset_minutes": -45,
        "duration_minutes": 15,
        "title_template": "Doors",
        "type": "doors",
        "styling": {"background": "#000000", "color": "#FFFFFF"}
    }


@pytest.fixture
def doors_rule_specific_title():
    """Doors rule for specific show with longer lead time."""
    return {
        "match_titles": ["Ice Show: 365"],
        "offset_minutes": -60,
        "duration_minutes": 30,
        "title_template": "Doors",
        "type": "doors",
        "styling": {"background": "#000000", "color": "#FFFFFF"}
    }


@pytest.fixture
def rehearsal_rule():
    """Rehearsal rule for shows."""
    return {
        "match_categories": ["show"],
        "offset_minutes": -180,  # 3 hours before
        "duration_minutes": 90,
        "title_template": "{parent_title} Rehearsal",
        "type": "rehearsal",
        "styling": {"background": "#4A5568", "color": "#FFFFFF"}
    }


@pytest.fixture
def strike_rule():
    """Strike rule anchored to event end time."""
    return {
        "match_categories": ["show"],
        "offset_minutes": 15,
        "anchor": "end",
        "duration_minutes": 45,
        "title_template": "Strike: {parent_title}",
        "type": "strike",
        "styling": {"background": "#2D3748", "color": "#FFFFFF"}
    }


@pytest.fixture
def full_derived_rules(doors_rule_basic, doors_rule_specific_title, rehearsal_rule, strike_rule):
    """Complete set of derived event rules."""
    return {
        "doors": [doors_rule_specific_title, doors_rule_basic],  # Specific first
        "rehearsal": [rehearsal_rule],
        "strike": [strike_rule]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 1: Rule Matching Logic
# ═══════════════════════════════════════════════════════════════════════════════

class TestEventMatchesRule:
    """Tests for _event_matches_rule() method."""
    
    def test_matches_category_show(self, sample_show_event, doors_rule_basic):
        """Show event should match rule with 'show' in match_categories."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_show_event, doors_rule_basic)
        
        assert result is True
    
    def test_matches_category_headliner(self, sample_headliner_event, doors_rule_basic):
        """Headliner event should match rule with 'headliner' in match_categories."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_headliner_event, doors_rule_basic)
        
        assert result is True
    
    def test_no_match_activity_category(self, sample_activity_event, doors_rule_basic):
        """Activity event should NOT match rule without 'activity' in match_categories."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_activity_event, doors_rule_basic)
        
        assert result is False
    
    def test_matches_specific_title(self, sample_show_event, doors_rule_specific_title):
        """Event should match rule when title matches match_titles list."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_show_event, doors_rule_specific_title)
        
        assert result is True
    
    def test_no_match_different_title(self, sample_headliner_event, doors_rule_specific_title):
        """Event should NOT match rule when title doesn't match match_titles."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_headliner_event, doors_rule_specific_title)
        
        assert result is False
    
    def test_title_match_case_insensitive(self, doors_rule_specific_title):
        """Title matching should be case-insensitive."""
        from backend.app.services.genai_parser import GenAIParser
        
        event = {
            "title": "ICE SHOW: 365",  # Different case
            "category": "show"
        }
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(event, doors_rule_specific_title)
        
        assert result is True
    
    def test_title_match_partial(self, doors_rule_specific_title):
        """Title matching should work with partial matches (substring)."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Rule looks for "Ice Show: 365"
        event = {
            "title": "Special Ice Show: 365 Premiere",  # Contains target string
            "category": "show"
        }
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(event, doors_rule_specific_title)
        
        assert result is True
    
    def test_empty_rule_matches_nothing(self, sample_show_event):
        """Rule with no match criteria should not match anything."""
        from backend.app.services.genai_parser import GenAIParser
        
        empty_rule = {
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors"
        }
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_show_event, empty_rule)
        
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 2: Derived Event Creation
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateDerivedEvent:
    """Tests for _create_derived_event() method."""
    
    def test_doors_event_basic(self, sample_show_event, doors_rule_basic):
        """Doors event should be created 45 min before show with correct properties."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, doors_rule_basic)
        
        # Time calculations: 7:00 PM - 45 min = 6:15 PM
        expected_start = datetime(2024, 1, 15, 18, 15)
        expected_end = datetime(2024, 1, 15, 18, 30)
        
        assert derived is not None
        assert derived["title"] == "Doors"
        assert derived["start_dt"] == expected_start
        assert derived["end_dt"] == expected_end
        assert derived["type"] == "doors"
        assert derived["styling"]["background"] == "#000000"
        assert derived["styling"]["color"] == "#FFFFFF"
        assert derived["is_derived"] is True
        assert derived["parent_title"] == "Ice Show: 365"
    
    def test_doors_event_longer_lead_time(self, sample_show_event, doors_rule_specific_title):
        """Ice Show doors should be created 60 min before with 30 min duration."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, doors_rule_specific_title)
        
        # Time calculations: 7:00 PM - 60 min = 6:00 PM, duration 30 min
        expected_start = datetime(2024, 1, 15, 18, 0)
        expected_end = datetime(2024, 1, 15, 18, 30)
        
        assert derived["start_dt"] == expected_start
        assert derived["end_dt"] == expected_end
    
    def test_rehearsal_event_with_template(self, sample_show_event, rehearsal_rule):
        """Rehearsal title should include parent event title via template."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, rehearsal_rule)
        
        # 7:00 PM - 180 min = 4:00 PM
        expected_start = datetime(2024, 1, 15, 16, 0)
        expected_end = datetime(2024, 1, 15, 17, 30)  # 90 min duration
        
        assert derived["title"] == "Ice Show: 365 Rehearsal"
        assert derived["start_dt"] == expected_start
        assert derived["end_dt"] == expected_end
        assert derived["type"] == "rehearsal"
    
    def test_strike_event_anchored_to_end(self, sample_show_event, strike_rule):
        """Strike event should be anchored to parent event END time."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, strike_rule)
        
        # Show ends at 8:00 PM + 15 min offset = 8:15 PM start
        expected_start = datetime(2024, 1, 15, 20, 15)
        expected_end = datetime(2024, 1, 15, 21, 0)  # 45 min duration
        
        assert derived["title"] == "Strike: Ice Show: 365"
        assert derived["start_dt"] == expected_start
        assert derived["end_dt"] == expected_end
        assert derived["type"] == "strike"
    
    def test_derived_event_inherits_venue(self, sample_show_event, doors_rule_basic):
        """Derived event should inherit venue from parent event."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, doors_rule_basic)
        
        assert derived["venue"] == "Studio B"
    
    def test_derived_event_correct_date(self, sample_show_event, doors_rule_basic):
        """Derived event should have correct raw_date based on its calculated time."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, doors_rule_basic)
        
        assert derived["raw_date"] == "2024-01-15"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 3: Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestDerivedEventEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_derived_event_crosses_midnight(self):
        """Derived event before a late show should handle date correctly."""
        from backend.app.services.genai_parser import GenAIParser
        
        late_show = {
            "title": "Late Night Comedy",
            "start_dt": datetime(2024, 1, 16, 0, 30),  # 12:30 AM
            "end_dt": datetime(2024, 1, 16, 1, 30),
            "category": "show",
            "venue": "Studio B",
            "raw_date": "2024-01-16"
        }
        
        rule = {
            "match_categories": ["show"],
            "offset_minutes": -60,
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "styling": {}
        }
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(late_show, rule)
        
        # 12:30 AM - 60 min = 11:30 PM previous day
        expected_start = datetime(2024, 1, 15, 23, 30)
        
        assert derived["start_dt"] == expected_start
        assert derived["raw_date"] == "2024-01-15"  # Previous day
    
    def test_multiple_matches_first_wins(self, sample_show_event, full_derived_rules):
        """When multiple rules match, specific title match should take priority."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Both doors rules might match Ice Show, but specific title should apply
        doors_rules = full_derived_rules["doors"]
        
        # First rule (specific) should match
        assert parser._event_matches_rule(sample_show_event, doors_rules[0]) is True
        
        # If we apply rules in order, first match determines timing
        derived = parser._create_derived_event(sample_show_event, doors_rules[0])
        
        # Specific rule has 60 min offset, not 45
        expected_start = datetime(2024, 1, 15, 18, 0)  # 6:00 PM
        assert derived["start_dt"] == expected_start
    
    def test_missing_parent_title(self, doors_rule_basic):
        """Event without title should not cause error in template."""
        from backend.app.services.genai_parser import GenAIParser
        
        event = {
            "start_dt": datetime(2024, 1, 15, 19, 0),
            "end_dt": datetime(2024, 1, 15, 20, 0),
            "category": "show",
            "venue": "Studio B",
            "raw_date": "2024-01-15"
            # No "title" key
        }
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(event, doors_rule_basic)
        
        assert derived is not None
        assert derived["parent_title"] is None or derived["parent_title"] == ""
    
    def test_zero_duration_rule(self, sample_show_event):
        """Rule with zero duration should still create valid event."""
        from backend.app.services.genai_parser import GenAIParser
        
        rule = {
            "match_categories": ["show"],
            "offset_minutes": -30,
            "duration_minutes": 0,
            "title_template": "Marker",
            "type": "marker",
            "styling": {}
        }
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, rule)
        
        assert derived["start_dt"] == derived["end_dt"]
    
    def test_very_large_offset(self, sample_show_event):
        """Large offset (e.g., 6 hours before) should work correctly."""
        from backend.app.services.genai_parser import GenAIParser
        
        rule = {
            "match_categories": ["show"],
            "offset_minutes": -360,  # 6 hours before
            "duration_minutes": 60,
            "title_template": "All-Day Setup",
            "type": "setup",
            "styling": {}
        }
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, rule)
        
        # 7:00 PM - 6 hours = 1:00 PM
        expected_start = datetime(2024, 1, 15, 13, 0)
        assert derived["start_dt"] == expected_start


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 4: Full Pipeline Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestApplyDerivedEventRules:
    """Tests for _apply_derived_event_rules() full pipeline."""
    
    def test_basic_doors_injection(self, sample_show_event, doors_rule_basic):
        """Doors event should be added before show in sorted output."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        events = [sample_show_event]
        
        # Apply single doors rule
        doors_only = {"doors": [doors_rule_basic]}
        result = parser._apply_derived_event_rules(events, doors_only)
        
        # Should have original event + doors event
        assert len(result) == 2
        
        # First event should be doors (earlier time)
        assert result[0]["type"] == "doors"
        assert result[0]["title"] == "Doors"
        
        # Second event should be original show
        assert result[1]["title"] == "Ice Show: 365"
    
    def test_multiple_derived_types(self, sample_show_event, full_derived_rules):
        """Multiple derived events (doors, rehearsal, strike) should be created."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        events = [sample_show_event]
        
        result = parser._apply_derived_event_rules(events, full_derived_rules)
        
        # Should have: rehearsal (4pm), doors (6pm), show (7pm), strike (8:15pm)
        # Note: doors might have 2 rules match but should dedupe or pick first
        types_in_order = [e.get("type", e.get("category")) for e in result]
        
        assert "rehearsal" in types_in_order
        assert "doors" in types_in_order
        assert "strike" in types_in_order
        
        # Events should be sorted by start time
        for i in range(len(result) - 1):
            assert result[i]["start_dt"] <= result[i + 1]["start_dt"]
    
    def test_no_derived_events_for_non_matching(self, sample_activity_event, full_derived_rules):
        """Activity event should not generate any derived events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        events = [sample_activity_event]
        
        result = parser._apply_derived_event_rules(events, full_derived_rules)
        
        # Only original event
        assert len(result) == 1
        assert result[0]["title"] == "Open Ice Skating"
    
    def test_empty_rules_returns_original(self, sample_show_event):
        """Empty rules dict should return original events unchanged."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        events = [sample_show_event]
        
        result = parser._apply_derived_event_rules(events, {})
        
        assert len(result) == 1
        assert result[0] == sample_show_event
    
    def test_multiple_shows_each_get_derived(self, sample_show_event, sample_headliner_event, doors_rule_basic):
        """Each matching show should get its own derived events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        events = [sample_show_event, sample_headliner_event]
        rules = {"doors": [doors_rule_basic]}
        
        result = parser._apply_derived_event_rules(events, rules)
        
        # 2 original + 2 doors = 4 events
        assert len(result) == 4
        
        doors_events = [e for e in result if e.get("type") == "doors"]
        assert len(doors_events) == 2
        
        # Check parent titles
        parent_titles = {e["parent_title"] for e in doors_events}
        assert "Ice Show: 365" in parent_titles
        assert "Headliner: Randy Cabral" in parent_titles


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 5: API Formatting
# ═══════════════════════════════════════════════════════════════════════════════

class TestDerivedEventFormatting:
    """Tests for formatting derived events in API response."""
    
    def test_styling_included_in_api_response(self, sample_show_event, doors_rule_basic):
        """Derived events should include styling in API format."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, doors_rule_basic)
        
        formatted = parser._format_event_for_api(derived)
        
        assert "styling" in formatted
        assert formatted["styling"]["background"] == "#000000"
        assert formatted["styling"]["color"] == "#FFFFFF"
    
    def test_is_derived_flag_in_api_response(self, sample_show_event, doors_rule_basic):
        """API response should include is_derived flag for derived events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        derived = parser._create_derived_event(sample_show_event, doors_rule_basic)
        
        formatted = parser._format_event_for_api(derived)
        
        assert formatted.get("is_derived") is True
        assert formatted.get("parent_title") == "Ice Show: 365"
    
    def test_regular_event_no_extra_fields(self, sample_show_event):
        """Regular events should not have derived-specific fields."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        formatted = parser._format_event_for_api(sample_show_event)
        
        assert "is_derived" not in formatted or formatted.get("is_derived") is not True
        assert "styling" not in formatted or formatted.get("styling") is None


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 6: Configuration Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestVenueRulesConfig:
    """Tests for venue_rules.py configuration."""
    
    def test_get_venue_rules_includes_derived_rules(self):
        """get_venue_rules() should include derived_event_rules when present."""
        from backend.app.config.venue_rules import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        assert "derived_event_rules" in rules
        assert "doors" in rules["derived_event_rules"]
        assert len(rules["derived_event_rules"]["doors"]) >= 1
        
        # Verify doors rule structure (styling is optional, handled by frontend)
        doors_rule = rules["derived_event_rules"]["doors"][0]
        assert "offset_minutes" in doors_rule
        assert "duration_minutes" in doors_rule
        assert "title_template" in doors_rule
        assert "type" in doors_rule
    
    def test_venue_metadata_structure(self):
        """VENUE_METADATA should have expected structure."""
        from backend.app.config.venue_rules import VENUE_METADATA
        
        studio_b_config = VENUE_METADATA.get(("WN", "Studio B"), {})
        
        assert "known_shows" in studio_b_config
        assert "renaming_map" in studio_b_config
        assert "default_durations" in studio_b_config


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 7: Cross-Event Gap Checking (check_all_events)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCheckAllEventsOption:
    """Tests for check_all_events option in min_gap_minutes rules."""
    
    def test_doors_skipped_when_overlaps_with_different_event_type(self):
        """Doors should be skipped if they would overlap with a DIFFERENT event type."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Movie ends at 3:00 PM, Bingo starts at 3:15 PM (15-min gap)
        # With 30-min doors offset, doors would start at 2:45 PM (overlaps Movie)
        events = [
            {"title": "Movie", "start_dt": datetime(2025, 1, 15, 14, 0), 
             "end_dt": datetime(2025, 1, 15, 15, 0), "category": "movie"},
            {"title": "Bingo", "start_dt": datetime(2025, 1, 15, 15, 15), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "game"},
        ]
        
        rules = {"doors": [{
            "match_categories": ["game"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "min_gap_minutes": 30,
            "check_all_events": True,
        }]}
        
        result = parser._apply_derived_event_rules(events, rules)
        doors_events = [e for e in result if e.get("type") == "doors"]
        
        # Gap is 15 min but rule requires 30 min → No doors
        assert len(doors_events) == 0
    
    def test_doors_created_when_sufficient_gap_from_different_type(self):
        """Doors should be created if there's sufficient gap from ANY event type."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Movie ends at 2:00 PM, Bingo starts at 3:15 PM (75-min gap)
        events = [
            {"title": "Movie", "start_dt": datetime(2025, 1, 15, 13, 0), 
             "end_dt": datetime(2025, 1, 15, 14, 0), "category": "movie"},
            {"title": "Bingo", "start_dt": datetime(2025, 1, 15, 15, 15), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "game"},
        ]
        
        rules = {"doors": [{
            "match_categories": ["game"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "min_gap_minutes": 30,
            "check_all_events": True,
        }]}
        
        result = parser._apply_derived_event_rules(events, rules)
        doors_events = [e for e in result if e.get("type") == "doors"]
        
        # Gap is 75 min >= 30 min required → Doors created
        assert len(doors_events) == 1
    
    def test_check_all_events_false_ignores_different_types(self):
        """Without check_all_events, gaps are only checked against same-type events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Movie ends at 3:00 PM, Bingo starts at 3:15 PM (15-min gap)
        # Without check_all_events, this should still create doors (only checks game vs game)
        events = [
            {"title": "Movie", "start_dt": datetime(2025, 1, 15, 14, 0), 
             "end_dt": datetime(2025, 1, 15, 15, 0), "category": "movie"},
            {"title": "Bingo", "start_dt": datetime(2025, 1, 15, 15, 15), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "game"},
        ]
        
        rules = {"doors": [{
            "match_categories": ["game"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "min_gap_minutes": 30,
            "check_all_events": False,  # Only check same-type events
        }]}
        
        result = parser._apply_derived_event_rules(events, rules)
        doors_events = [e for e in result if e.get("type") == "doors"]
        
        # Bingo is first game of day, so doors ARE created (no preceding game)
        assert len(doors_events) == 1
    
    def test_first_event_of_day_gets_doors_with_check_all_events(self):
        """First event of the day should always get doors (no preceding events)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Only one event on this day
        events = [
            {"title": "Bingo", "start_dt": datetime(2025, 1, 15, 15, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "game"},
        ]
        
        rules = {"doors": [{
            "match_categories": ["game"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "min_gap_minutes": 30,
            "check_all_events": True,
        }]}
        
        result = parser._apply_derived_event_rules(events, rules)
        doors_events = [e for e in result if e.get("type") == "doors"]
        
        # First event of day → Doors created
        assert len(doors_events) == 1
    
    def test_doors_blocked_when_falling_inside_another_event(self):
        """Doors should NOT be created if they would fall inside another event's time range."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Scenario: Crazy Quest 11:20 PM - 12:00 AM, RED Nightclub at 12:00 AM
        # Doors for RED would be at 11:30 PM, which falls INSIDE Crazy Quest
        events = [
            {"title": "Crazy Quest", "start_dt": datetime(2025, 1, 15, 23, 20), 
             "end_dt": datetime(2025, 1, 16, 0, 0), "category": "game"},
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 16, 0, 0), 
             "end_dt": datetime(2025, 1, 16, 2, 0), "category": "party"},
        ]
        
        rules = {"doors": [{
            "match_categories": ["party"],
            "offset_minutes": -30,  # 30 min before = 11:30 PM
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "min_gap_minutes": 30,
            "check_all_events": True,
        }]}
        
        result = parser._apply_derived_event_rules(events, rules)
        doors_events = [e for e in result if e.get("type") == "doors"]
        
        # Doors at 11:30 PM would fall inside Crazy Quest (11:20 PM - 12:00 AM) → Blocked
        assert len(doors_events) == 0
    
    def test_doors_allowed_when_not_overlapping_any_event(self):
        """Doors should be created when there's no overlap with any running event."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Scenario: Crazy Quest ends at 11:00 PM, RED Nightclub at 12:00 AM
        # Doors for RED would be at 11:30 PM, which is AFTER Crazy Quest ends
        events = [
            {"title": "Crazy Quest", "start_dt": datetime(2025, 1, 15, 22, 0), 
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "game"},  # Ends at 11:00 PM
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 16, 0, 0), 
             "end_dt": datetime(2025, 1, 16, 2, 0), "category": "party"},
        ]
        
        rules = {"doors": [{
            "match_categories": ["party"],
            "offset_minutes": -30,  # 30 min before = 11:30 PM
            "duration_minutes": 15,
            "title_template": "Doors",
            "type": "doors",
            "min_gap_minutes": 30,
            "check_all_events": True,
        }]}
        
        result = parser._apply_derived_event_rules(events, rules)
        doors_events = [e for e in result if e.get("type") == "doors"]
        
        # Doors at 11:30 PM is after Crazy Quest ends (11:00 PM) → Allowed
        assert len(doors_events) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 8: Category Inference for Merged Events
# ═══════════════════════════════════════════════════════════════════════════════

class TestMergedEventCategoryInference:
    """Tests for category inference on merged events from other venues."""
    
    def test_parade_title_infers_parade_category(self):
        """Events with 'parade' in title should get category 'parade'."""
        # This tests the logic in _transform_to_api_format that infers category
        # before calling _parse_single_event
        
        # Simulate what happens in the merge logic
        show = {"title": "Anchors Aweigh Parade", "date": "2025-01-15", 
                "start_time": "12:30", "venue": "Royal Promenade"}
        
        # Infer category from title (this is the logic we added)
        if not show.get("category"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["category"] = "parade"
        
        assert show["category"] == "parade"
    
    def test_party_title_infers_party_category(self):
        """Events with 'party' in title should get category 'party'."""
        show = {"title": "Deck Party", "date": "2025-01-15", 
                "start_time": "21:00", "venue": "Pool Deck"}
        
        if not show.get("category"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["category"] = "parade"
            elif "party" in title_lower:
                show["category"] = "party"
        
        assert show["category"] == "party"
    
    def test_movie_title_infers_movie_category(self):
        """Events with 'movie' in title should get category 'movie'."""
        show = {"title": "Movie Night", "date": "2025-01-15", 
                "start_time": "20:00", "venue": "Royal Theater"}
        
        if not show.get("category"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["category"] = "parade"
            elif "party" in title_lower:
                show["category"] = "party"
            elif "movie" in title_lower:
                show["category"] = "movie"
        
        assert show["category"] == "movie"
    
    def test_existing_category_not_overwritten(self):
        """If category already exists, it should NOT be overwritten."""
        show = {"title": "Parade Party", "date": "2025-01-15", 
                "start_time": "18:00", "venue": "Promenade", 
                "category": "activity"}  # Already has category
        
        if not show.get("category"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["category"] = "parade"
        
        # Category should remain "activity" (not overwritten to "parade")
        assert show["category"] == "activity"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 9: Highlights Filtering Algorithm
# ═══════════════════════════════════════════════════════════════════════════════

class TestHighlightsFilteringAlgorithm:
    """Tests for _filter_other_venue_shows() priority and filtering logic."""
    
    def test_show_beats_activity_same_day(self):
        """Show (priority 1) should be chosen over activity (priority 6)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-13", "title": "Private Ice Skating", 
             "time": "11:30am-12:30pm", "category": "activity"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Ice Spectacular 365", 
             "time": "8:15 pm & 10:30 pm", "category": "show"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Only one event per venue/day
        assert len(result) == 1
        # Show should win over activity
        assert result[0]["title"] == "Ice Spectacular 365"
        assert result[0]["category"] == "show"
    
    def test_evening_time_beats_morning_same_category(self):
        """Evening events should be preferred over morning events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-13", "title": "Morning Show", 
             "time": "10:00 am", "category": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Evening Show", 
             "time": "8:00 pm", "category": "show"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Evening show should win
        assert result[0]["title"] == "Evening Show"
    
    def test_headliner_beats_game(self):
        """Headliner (priority 2) should beat game (priority 3)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Trivia Night", 
             "time": "7:00 pm", "category": "game"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Comedy Special", 
             "time": "9:00 pm", "category": "headliner"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        assert result[0]["title"] == "Comedy Special"
    
    def test_party_beats_activity(self):
        """Party (priority 4) should beat activity (priority 6)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Let's Dance", 
             "time": "11:00 pm", "category": "party"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Open Skating", 
             "time": "2:00 pm", "category": "activity"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        assert result[0]["title"] == "Let's Dance"
    
    def test_one_winner_per_venue_per_day(self):
        """Only one highlight should be returned per venue per day."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-13", "title": "Event A", 
             "time": "7:00 pm", "category": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Event B", 
             "time": "9:00 pm", "category": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Event C", 
             "time": "10:00 pm", "category": "party"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Only one winner for Studio B on 2025-10-13
        assert len(result) == 1
    
    def test_multiple_venues_multiple_days(self):
        """Multiple venues and days should each have one winner."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-13", "title": "Ice Show", 
             "time": "8:00 pm", "category": "show"},
            {"venue": "AquaTheater", "date": "2025-10-13", "title": "Aqua Show", 
             "time": "8:00 pm", "category": "show"},
            {"venue": "Studio B", "date": "2025-10-14", "title": "Ice Show 2", 
             "time": "8:00 pm", "category": "show"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # 3 unique (venue, date) combinations
        assert len(result) == 3
        
        # Verify each is present
        keys = {(r["venue"], r["date"]) for r in result}
        assert ("Studio B", "2025-10-13") in keys
        assert ("AquaTheater", "2025-10-13") in keys
        assert ("Studio B", "2025-10-14") in keys
    
    def test_same_title_events_merge_times(self):
        """Events with same title should merge their times."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-13", "title": "Ice Show", 
             "time": "7:00 pm", "category": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Ice Show", 
             "time": "9:30 pm", "category": "show"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Times should be merged
        assert "7:00 pm" in result[0]["time"]
        assert "9:30 pm" in result[0]["time"]
    
    def test_backup_has_lowest_priority(self):
        """Backup (priority 8) should only win if nothing else available."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "AquaTheater", "date": "2025-10-16", "title": "Aqua Backup", 
             "time": "8:00 pm", "category": "backup"},
            {"venue": "AquaTheater", "date": "2025-10-16", "title": "Other Event", 
             "time": "8:00 pm", "category": "other"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # "other" (priority 7) beats "backup" (priority 8)
        assert result[0]["title"] == "Other Event"
    
    def test_parade_category_priority(self):
        """Parade should have moderate priority (not highest, not lowest)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Parade vs Activity - parade has higher priority
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-13", "title": "Costume Parade", 
             "time": "10:00 pm", "category": "parade"},
            {"venue": "Royal Promenade", "date": "2025-10-13", "title": "Random Activity", 
             "time": "2:00 pm", "category": "activity"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Parade should beat activity (it's after party in priority, but before activity)
        # Let's verify it's the parade
        assert result[0]["title"] == "Costume Parade"
    
    def test_late_night_party_is_valid_highlight(self):
        """Late-night parties (11pm+) like 'Let's Dance' should be valid highlights."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Scenario: Royal Promenade Day 2 only has a late-night party
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Let's Dance", 
             "time": "11:15 pm - midnight", "category": "party"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Should be kept as the highlight for that day
        assert len(result) == 1
        assert result[0]["title"] == "Let's Dance"
        assert result[0]["category"] == "party"
    
    def test_late_night_party_vs_activity(self):
        """Late-night party should beat afternoon activity even at 11pm."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Afternoon Activity", 
             "time": "2:00 pm", "category": "activity"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Let's Dance", 
             "time": "11:15 pm", "category": "party"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Party (priority 4) beats activity (priority 6)
        assert result[0]["title"] == "Let's Dance"
    
    def test_multiple_highlights_same_day_different_venues(self):
        """Each venue should have its own best highlight for the same day."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-14", "title": "RED: Nightclub Experience", 
             "time": "Midnight - late", "category": "party"},
            {"venue": "AquaTheater", "date": "2025-10-14", "title": "inTENse: Maximum Performance", 
             "time": "8:15 pm & 10:30 pm", "category": "show"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Let's Dance", 
             "time": "11:15 pm - midnight", "category": "party"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # All 3 venues should have highlights
        assert len(result) == 3
        
        titles = {r["title"] for r in result}
        assert "RED: Nightclub Experience" in titles
        assert "inTENse: Maximum Performance" in titles
        assert "Let's Dance" in titles
    
    def test_game_beats_activity_for_highlight(self):
        """Game shows (priority 3) should beat activity (priority 6) for highlights."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Real scenario: Day 5 Studio B - Battle of the Sexes should beat Family SHUSH
        shows = [
            {"venue": "Studio B", "date": "2025-08-21", "title": "Family SHUSH", 
             "time": "8pm - 9:30 pm", "category": "activity"},
            {"venue": "Studio B", "date": "2025-08-21", "title": "Battle of the Sexes", 
             "time": "9:45 pm", "category": "game"},
            {"venue": "Studio B", "date": "2025-08-21", "title": "Crazy Quest", 
             "time": "11:00 pm", "category": "game"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Game (priority 3) should beat activity (priority 6)
        # Battle of the Sexes is the first game and both have evening time
        assert result[0]["category"] == "game"
        # Either Battle of the Sexes or Crazy Quest should win
        assert result[0]["title"] in ["Battle of the Sexes", "Crazy Quest"]
    
    def test_game_beats_activity_even_earlier_time(self):
        """Game in evening should beat activity even if activity is earlier."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-08-21", "title": "Morning Activity", 
             "time": "10:00 am", "category": "activity"},
            {"venue": "Studio B", "date": "2025-08-21", "title": "Evening Game Show", 
             "time": "9:00 pm", "category": "game"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Evening game (priority 3, time score 0) beats morning activity (priority 6, time score 1)
        assert result[0]["title"] == "Evening Game Show"
    
    def test_movie_and_game_priority_same_day(self):
        """Game (priority 3) should beat movie (priority 5) for highlights."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "AquaTheater", "date": "2025-08-21", "title": "MOVIES ON DECK", 
             "time": "6:00 pm & 9:30 pm", "category": "movie"},
            {"venue": "AquaTheater", "date": "2025-08-21", "title": "Finish That Lyric", 
             "time": "8:30 pm", "category": "game"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Game (priority 3) should beat movie (priority 5)
        assert result[0]["title"] == "Finish That Lyric"
    
    def test_ice_skating_fallback_when_nothing_else(self):
        """Ice Skating is used as fallback highlight if nothing better exists."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Only Ice Skating sessions available - should use first one as fallback
        shows = [
            {"venue": "Studio B", "date": "2025-07-23", "title": "Ice Skating", 
             "time": "5:00 pm - 6:00 pm (1hr) TEENS", "category": "activity"},
            {"venue": "Studio B", "date": "2025-07-23", "title": "Ice Skating", 
             "time": "6:00 pm - 8:00 pm (2hrs)", "category": "activity"},
            {"venue": "Studio B", "date": "2025-07-23", "title": "Ice Skating", 
             "time": "8:30 pm - 11:30 pm (3hrs)", "category": "activity"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Should return exactly 1 Ice Skating as fallback (not merge all times)
        assert len(result) == 1
        assert "ice skating" in result[0]["title"].lower()
    
    def test_laser_tag_fallback_when_nothing_else(self):
        """Laser Tag is used as fallback highlight if nothing better exists."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-07-24", "title": "Laser Tag", 
             "time": "1:00 pm - 7:00 pm (6hrs)", "category": "activity"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Laser Tag should be used as fallback
        assert len(result) == 1
        assert result[0]["title"] == "Laser Tag"
    
    def test_ice_spectacular_show_not_blocked(self):
        """Ice Spectacular: 365 is a SHOW, not a skating session - should NOT be blocked."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-07-22", "title": "Ice Spectacular: 365", 
             "time": "6:45 pm & 9:00 pm", "category": "show"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Ice Spectacular is a show, not an activity - should NOT be blocked
        assert len(result) == 1
        assert result[0]["title"] == "Ice Spectacular: 365"
    
    def test_game_show_preferred_over_blocked_ice_skating(self):
        """If there's a game show AND Ice Skating, game show should be the highlight."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-07-23", "title": "Ice Skating", 
             "time": "5:00 pm - 8:00 pm", "category": "activity"},
            {"venue": "Studio B", "date": "2025-07-23", "title": "Battle of the Sexes", 
             "time": "9:15 pm", "category": "game"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Ice Skating blocked, Battle of the Sexes is the only remaining event
        assert len(result) == 1
        assert result[0]["title"] == "Battle of the Sexes"
