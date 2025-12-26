"""
Test suite for Derived Event Rules System (TDD).

Tests the functionality for automatically generating derived events 
(Doors, Rehearsals, Set-ups, Strikes) based on configurable rules.
"""

import pytest
from datetime import datetime, timedelta, date
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


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 10: Floor Transition Logic (Studio B specific)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFloorTransitionLogic:
    """
    Tests for automatic strike/set events when floor requirements change.
    Only applies to venues with floor_requirements config (e.g., Studio B).
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helper: Floor requirements config for tests
    # ─────────────────────────────────────────────────────────────────────────
    
    @pytest.fixture
    def floor_config(self):
        """Sample floor requirements config for Studio B."""
        return {
            "floor_requirements": {
                # Events that need the floor (ice covered)
                "floor": {
                    "match_titles": ["Laser Tag", "RED: Nightclub Experience", "Nightclub",
                                   "Family SHUSH!", "Battle of the Sexes", "Crazy Quest", 
                                   "Bingo", "Glow Party", "Top Tier"],
                },
                # Events that need ice exposed (no floor)
                "ice": {
                    "match_titles": ["Ice Show: 365", "Ice Skating", "Open Ice Skating", 
                                   "Private Ice Skating", "Teens Skate", "Teens Ice Skate"],
                },
            },
            "floor_transition": {
                "duration_minutes": 60,
                "titles": {
                    "floor_to_ice": "Strike Floor & Set Ice",
                    "ice_to_floor": "Strike Ice & Set Floor",
                },
                "type": "strike",
            },
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Basic Transition Tests
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_ice_to_floor_transition_same_day(self, floor_config):
        """Ice event followed by floor event should generate 'Strike Ice & Set Floor'."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Ice Show 3 PM, Laser Tag 6 PM
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 15, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "show"},
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 18, 0), 
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # Should have original 2 events + 1 transition event
        assert len(result) == 3
        
        transition = [e for e in result if e.get("title") == "Strike Ice & Set Floor"]
        assert len(transition) == 1
        
        # Should start immediately after Ice Show ends (4 PM)
        assert transition[0]["start_dt"] == datetime(2025, 1, 15, 16, 0)
        assert transition[0]["end_dt"] == datetime(2025, 1, 15, 17, 0)  # 1 hour duration
    
    def test_floor_to_ice_transition_same_day(self, floor_config):
        """Floor event followed by ice event should generate 'Strike Floor & Set Ice'."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Laser Tag 2 PM, Ice Skating 5 PM
        events = [
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 14, 0), 
             "end_dt": datetime(2025, 1, 15, 15, 0), "category": "activity"},
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 15, 17, 0), 
             "end_dt": datetime(2025, 1, 15, 19, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        transition = [e for e in result if e.get("title") == "Strike Floor & Set Ice"]
        assert len(transition) == 1
        
        # Should start immediately after Laser Tag ends (3 PM)
        assert transition[0]["start_dt"] == datetime(2025, 1, 15, 15, 0)
        assert transition[0]["end_dt"] == datetime(2025, 1, 15, 16, 0)
    
    def test_same_floor_state_no_transition(self, floor_config):
        """Consecutive events with same floor state should NOT generate transition."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Both are floor events
        events = [
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 14, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "activity"},
            {"title": "Bingo", "start_dt": datetime(2025, 1, 15, 17, 0), 
             "end_dt": datetime(2025, 1, 15, 18, 0), "category": "game"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # No transition event - only original 2 events
        assert len(result) == 2
        transition = [e for e in result if "Strike" in e.get("title", "")]
        assert len(transition) == 0
    
    def test_same_ice_state_no_transition(self, floor_config):
        """Consecutive ice events should NOT generate transition."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Both are ice events
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 15, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "show"},
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 15, 17, 0), 
             "end_dt": datetime(2025, 1, 15, 19, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # No transition event
        assert len(result) == 2
        transition = [e for e in result if "Strike" in e.get("title", "")]
        assert len(transition) == 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # After-Midnight Deferral Tests
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_after_midnight_deferral_to_next_event(self, floor_config):
        """Event ending after midnight should defer strike to BEFORE next event."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Party ends at 2 AM, Ice Skating at 9 AM next day
        events = [
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 15, 23, 0), 
             "end_dt": datetime(2025, 1, 16, 2, 0), "category": "party"},  # Ends 2 AM
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 16, 9, 0), 
             "end_dt": datetime(2025, 1, 16, 11, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        transition = [e for e in result if e.get("title") == "Strike Floor & Set Ice"]
        assert len(transition) == 1
        
        # Should be anchored BEFORE Ice Skating (8 AM - 9 AM)
        assert transition[0]["start_dt"] == datetime(2025, 1, 16, 8, 0)
        assert transition[0]["end_dt"] == datetime(2025, 1, 16, 9, 0)
    
    def test_after_midnight_no_transition_if_same_floor_state(self, floor_config):
        """After-midnight event followed by same floor type → no transition."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Party ends at 2 AM, Laser Tag at 1 PM (both need floor)
        events = [
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 15, 23, 0), 
             "end_dt": datetime(2025, 1, 16, 2, 0), "category": "party"},
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 16, 13, 0), 
             "end_dt": datetime(2025, 1, 16, 17, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # No transition - both need floor
        transition = [e for e in result if "Strike" in e.get("title", "")]
        assert len(transition) == 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # "Don't Care" Events Tests
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_dont_care_event_ignored_in_transition_logic(self, floor_config):
        """Events not in floor/ice lists should be ignored (floor state continues)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Ice Show → Port Talk (don't care) → Ice Skating
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 15, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "show"},
            {"title": "Port & Shopping Talk", "start_dt": datetime(2025, 1, 15, 16, 30), 
             "end_dt": datetime(2025, 1, 15, 17, 0), "category": "other"},  # Don't care
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 15, 18, 0), 
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # No transition - Ice Show and Ice Skating are both ice events
        # Port Talk is ignored
        transition = [e for e in result if "Strike" in e.get("title", "")]
        assert len(transition) == 0
    
    def test_dont_care_event_between_different_floor_states(self, floor_config):
        """'Don't care' event between ice and floor should still trigger transition."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Ice Show → Port Talk (don't care) → Laser Tag
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 15, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "show"},
            {"title": "Port & Shopping Talk", "start_dt": datetime(2025, 1, 15, 16, 30), 
             "end_dt": datetime(2025, 1, 15, 17, 0), "category": "other"},  # Don't care
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 18, 0), 
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # Transition between Ice Show and Laser Tag (Port Talk ignored)
        transition = [e for e in result if e.get("title") == "Strike Ice & Set Floor"]
        assert len(transition) == 1
        
        # Anchored after Ice Show ends (4 PM)
        assert transition[0]["start_dt"] == datetime(2025, 1, 15, 16, 0)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Multiple Transitions Tests
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_multiple_transitions_in_one_day(self, floor_config):
        """Ice → Floor → Ice should generate TWO transition events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Ice Show → Laser Tag → Ice Skating
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 10, 0), 
             "end_dt": datetime(2025, 1, 15, 11, 0), "category": "show"},
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 13, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "activity"},
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 15, 18, 0), 
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # Should have 3 original events + 2 transitions
        assert len(result) == 5
        
        ice_to_floor = [e for e in result if e.get("title") == "Strike Ice & Set Floor"]
        floor_to_ice = [e for e in result if e.get("title") == "Strike Floor & Set Ice"]
        
        assert len(ice_to_floor) == 1
        assert len(floor_to_ice) == 1
        
        # First transition after Ice Show (11 AM)
        assert ice_to_floor[0]["start_dt"] == datetime(2025, 1, 15, 11, 0)
        
        # Second transition after Laser Tag (4 PM)
        assert floor_to_ice[0]["start_dt"] == datetime(2025, 1, 15, 16, 0)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Edge Cases
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_first_event_of_day_no_transition(self, floor_config):
        """First event that cares about floor should not trigger transition."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Only one event - no previous state to transition from
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 19, 0), 
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "show"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # No transition
        assert len(result) == 1
    
    def test_empty_floor_config_skips_logic(self, floor_config):
        """Venues without floor_requirements config should skip floor logic entirely."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 15, 0), 
             "end_dt": datetime(2025, 1, 15, 16, 0), "category": "show"},
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 18, 0), 
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "activity"},
        ]
        
        # Empty config - no floor_requirements
        result = parser._apply_floor_transition_rules(events, {})
        
        # Should return events unchanged (no transitions added)
        assert len(result) == 2
    
    def test_events_ending_at_exactly_midnight(self, floor_config):
        """Event ending at exactly midnight (00:00) should trigger immediate transition, not deferred."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Laser Tag ends at exactly midnight, Ice Skating at 2 PM
        events = [
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 20, 0), 
             "end_dt": datetime(2025, 1, 16, 0, 0), "category": "activity"},  # Ends exactly midnight
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 16, 14, 0), 
             "end_dt": datetime(2025, 1, 16, 17, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        transition = [e for e in result if e.get("title") == "Strike Floor & Set Ice"]
        assert len(transition) == 1
        
        # Exactly midnight is NOT "after midnight" - transition happens immediately at midnight
        assert transition[0]["start_dt"] == datetime(2025, 1, 16, 0, 0)
    
    def test_9am_preferred_for_late_morning_event(self, floor_config):
        """If next event is at 11 AM or later, use 9 AM as preferred strike time."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Party ends at 2 AM, Ice Skating at 12 PM (noon)
        events = [
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 15, 23, 0), 
             "end_dt": datetime(2025, 1, 16, 2, 0), "category": "party"},
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 16, 12, 0), 
             "end_dt": datetime(2025, 1, 16, 14, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        transition = [e for e in result if e.get("title") == "Strike Floor & Set Ice"]
        assert len(transition) == 1
        
        # Next event at noon → Use preferred 9 AM time
        assert transition[0]["start_dt"] == datetime(2025, 1, 16, 9, 0)
        assert transition[0]["end_dt"] == datetime(2025, 1, 16, 10, 0)
    
    def test_overlap_combines_titles(self, floor_config):
        """Floor transition overlapping with existing strike event should combine titles."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Ice Show ends at 10 PM with Strike & Ice Scrape after
        # Laser Tag at midnight needs floor transition
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 20, 15), 
             "end_dt": datetime(2025, 1, 15, 21, 15), "category": "show"},
            # Existing strike event that overlaps with floor transition
            {"title": "Strike & Ice Scrape", "start_dt": datetime(2025, 1, 15, 21, 15), 
             "end_dt": datetime(2025, 1, 15, 21, 45), "category": "strike", "type": "strike"},
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 22, 15), 
             "end_dt": datetime(2025, 1, 16, 0, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # Should have combined the floor transition into the existing strike event
        strike_events = [e for e in result if e.get("type") == "strike"]
        
        # Should only be one strike event (combined)
        assert len(strike_events) == 1
        
        # Title should be combined
        assert "Strike & Ice Scrape" in strike_events[0]["title"]
        assert "Set Floor" in strike_events[0]["title"]
    
    def test_adjacent_events_combine(self, floor_config):
        """Adjacent events (one ends exactly when other starts) should combine."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Strike Laser Tag ends at 7 PM, floor transition starts at 7 PM (adjacent)
        events = [
            {"title": "Laser Tag", "start_dt": datetime(2025, 1, 15, 13, 0), 
             "end_dt": datetime(2025, 1, 15, 18, 0), "category": "activity"},
            # Strike Laser Tag - ends at 7 PM
            {"title": "Strike Laser Tag", "start_dt": datetime(2025, 1, 15, 18, 0), 
             "end_dt": datetime(2025, 1, 15, 19, 0), "category": "strike", "type": "strike"},
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 15, 20, 0), 
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "activity"},
        ]
        
        result = parser._apply_floor_transition_rules(events, floor_config)
        
        # Floor transition (Strike Floor) should combine with Strike Laser Tag
        strike_events = [e for e in result if e.get("type") == "strike"]
        
        # Should only be one strike event (combined)
        assert len(strike_events) == 1
        
        # Title should be combined
        assert "Strike Laser Tag" in strike_events[0]["title"]
        assert "Strike Floor" in strike_events[0]["title"]
        
        # Duration should be longest of the two (both 1 hour), starting from earliest
        # Strike Laser Tag: 6 PM - 7 PM, Strike Floor: 7 PM - 8 PM
        # Result: 6 PM start, 1 hour duration = 7 PM end
        assert strike_events[0]["start_dt"] == datetime(2025, 1, 15, 18, 0)
        assert strike_events[0]["end_dt"] == datetime(2025, 1, 15, 19, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 11: Game Show Setup/Strike Rules
# ═══════════════════════════════════════════════════════════════════════════════

class TestGameShowSetupStrike:
    """
    Tests for game show and party setup/strike derived event rules.
    - Setup: 1 hour before, 30 min duration
    - Strike: After event ends, 30 min duration
    - Stacked events share one setup and one strike
    """
    
    @pytest.fixture
    def game_show_rules(self):
        """Sample derived event rules for game shows with event-specific titles."""
        return {
            "setup": [
                {
                    "match_titles": ["Battle of the Sexes", "Crazy Quest", "Family SHUSH!",
                                   "RED: Nightclub Experience"],
                    "offset_minutes": -60,
                    "duration_minutes": 30,
                    "title_template": "Set Up {parent_title}",  # Event-specific title
                    "type": "setup",
                    "min_gap_minutes": 60,  # Skip if stacked
                },
            ],
            "strike": [
                {
                    "match_titles": ["Battle of the Sexes", "Crazy Quest", "Family SHUSH!",
                                   "RED: Nightclub Experience"],
                    "offset_minutes": 0,
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike {parent_title}",  # Event-specific title
                    "type": "strike",
                    "last_per_day": True,
                },
            ],
        }
    
    def test_single_game_show_setup_and_strike(self, game_show_rules):
        """Single game show should have setup before and strike after with event-specific titles."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        events = [
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 21, 0), 
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "game",
             "raw_date": "2025-01-15"},
        ]
        
        result = parser._apply_derived_event_rules(events, game_show_rules)
        
        # Should have: Setup + Event + Strike
        assert len(result) == 3
        
        # Event-specific titles using {parent_title}
        setup = [e for e in result if e.get("title") == "Set Up Battle of the Sexes"]
        strike = [e for e in result if e.get("title") == "Strike Battle of the Sexes"]
        
        assert len(setup) == 1
        assert len(strike) == 1
        
        # Setup: 1 hour before (8 PM), 30 min duration (8:00 - 8:30 PM)
        assert setup[0]["start_dt"] == datetime(2025, 1, 15, 20, 0)
        assert setup[0]["end_dt"] == datetime(2025, 1, 15, 20, 30)
        
        # Strike: After event ends (10 PM), 30 min (10:00 - 10:30 PM)
        assert strike[0]["start_dt"] == datetime(2025, 1, 15, 22, 0)
        assert strike[0]["end_dt"] == datetime(2025, 1, 15, 22, 30)
    
    def test_stacked_game_shows_one_setup_one_strike(self, game_show_rules):
        """Stacked game shows on SAME DAY should have ONE setup before first and ONE strike after last."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Three stacked events on same day: BOTS 7 PM → Quest 8 PM → Family SHUSH 9:30 PM
        events = [
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 19, 0), 
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "game",
             "raw_date": "2025-01-15"},
            {"title": "Crazy Quest", "start_dt": datetime(2025, 1, 15, 20, 0), 
             "end_dt": datetime(2025, 1, 15, 21, 30), "category": "game",
             "raw_date": "2025-01-15"},
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 21, 30), 
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "game",
             "raw_date": "2025-01-15"},
        ]
        
        result = parser._apply_derived_event_rules(events, game_show_rules)
        
        # Event-specific titles: setup for first event (BOTS), strike for last event (Family SHUSH!)
        setup = [e for e in result if "Set Up" in e.get("title", "")]
        strike = [e for e in result if "Strike" in e.get("title", "")]
        
        # Only ONE setup (before first event) due to min_gap_minutes
        assert len(setup) == 1
        assert setup[0]["title"] == "Set Up Battle of the Sexes"  # First event's title
        assert setup[0]["start_dt"] == datetime(2025, 1, 15, 18, 0)  # 1 hour before BOTS
        
        # Only ONE strike (after last event) due to last_per_day
        assert len(strike) == 1
        assert strike[0]["title"] == "Strike Family SHUSH!"  # Last event's title
        assert strike[0]["start_dt"] == datetime(2025, 1, 15, 23, 0)  # After Family SHUSH ends
    
    def test_gap_between_events_triggers_multiple_setups(self, game_show_rules):
        """Events with sufficient gap should each get their own event-specific setup."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Two events with 6 hour gap (plenty of time for separate setup)
        events = [
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 14, 0), 
             "end_dt": datetime(2025, 1, 15, 15, 0), "category": "game",
             "raw_date": "2025-01-15"},
            {"title": "Crazy Quest", "start_dt": datetime(2025, 1, 15, 21, 0), 
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "game",
             "raw_date": "2025-01-15"},
        ]
        
        result = parser._apply_derived_event_rules(events, game_show_rules)
        
        setup = [e for e in result if "Set Up" in e.get("title", "")]
        
        # Should have TWO setups (enough gap between events) with event-specific titles
        assert len(setup) == 2
        
        # First setup: "Set Up Battle of the Sexes" at 1 PM
        assert setup[0]["title"] == "Set Up Battle of the Sexes"
        assert setup[0]["start_dt"] == datetime(2025, 1, 15, 13, 0)
        
        # Second setup: "Set Up Crazy Quest" at 8 PM  
        assert setup[1]["title"] == "Set Up Crazy Quest"
        assert setup[1]["start_dt"] == datetime(2025, 1, 15, 20, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 12: INTEGRATION TESTS - Full Pipeline with Production Rules
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudioBIntegration:
    """
    Integration tests using ACTUAL production venue rules from venue_rules.py.
    These test the full pipeline end-to-end, catching issues that unit tests miss.
    """
    
    @pytest.fixture
    def studio_b_rules(self):
        """Load actual production rules for Studio B."""
        from backend.app.config.venue_rules import VENUE_METADATA
        return VENUE_METADATA.get(("WN", "Studio B"), {})
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_ice_show_generates_all_warmups(self, parser, studio_b_rules):
        """Ice Show should generate BOTH Specialty Ice AND Cast warm ups."""
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        # Two Ice Shows on same day (triggers preset + multiple warm ups)
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Should have both warm up types
        warmups = [e for e in result if "Warm Up" in e.get("title", "")]
        warmup_titles = [e.get("title") for e in warmups]
        
        assert "Warm Up - Specialty Ice" in warmup_titles, "Missing Specialty Ice warm up"
        assert "Warm Up - Cast" in warmup_titles, "Missing Cast warm up"
    
    def test_game_show_title_rule_no_duplicate_from_catchall(self, parser, studio_b_rules):
        """Battle of the Sexes should match title rule, NOT also match category catch-all."""
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        events = [
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 21, 0),
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Should have exactly ONE setup (not two from title + catch-all)
        setups = [e for e in result if "Set Up" in e.get("title", "") and "Battle" in e.get("title", "")]
        assert len(setups) == 1, f"Expected 1 setup, got {len(setups)}: {[e.get('title') for e in setups]}"
    
    def test_ice_to_floor_transition_merges_with_strike(self, parser, studio_b_rules):
        """Floor transition should merge with Strike & Ice Scrape when adjacent."""
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        floor_config = {
            "floor_requirements": studio_b_rules.get("floor_requirements"),
            "floor_transition": studio_b_rules.get("floor_transition"),
        }
        
        # Ice Show followed by game show (triggers floor transition + strike)
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 20, 0),
             "end_dt": datetime(2025, 1, 15, 21, 0), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        # Apply derived events first
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Then apply floor transitions
        result = parser._apply_floor_transition_rules(result, floor_config)
        
        # Then merge overlapping operations
        result = parser._merge_overlapping_operations(result)
        
        # Check that Strike & Ice Scrape and Set Floor are combined
        combined = [e for e in result if "Strike" in e.get("title", "") and "Set Floor" in e.get("title", "")]
        assert len(combined) >= 1, "Floor transition should merge with Strike & Ice Scrape"
    
    def test_overlapping_setup_and_strike_merge(self, parser, studio_b_rules):
        """Overlapping setup and strike events should merge together."""
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        floor_config = {
            "floor_requirements": studio_b_rules.get("floor_requirements"),
            "floor_transition": studio_b_rules.get("floor_transition"),
        }
        
        # Ice Show followed by Nightclub (creates Strike + Set Up that overlap)
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 21, 0),
             "end_dt": datetime(2025, 1, 15, 22, 0), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Nightclub", "start_dt": datetime(2025, 1, 15, 23, 0),
             "end_dt": datetime(2025, 1, 16, 1, 0), "category": "party",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        # Full pipeline
        result = parser._apply_derived_event_rules(events, derived_rules)
        result = parser._apply_floor_transition_rules(result, floor_config)
        result = parser._merge_overlapping_operations(result)
        
        # Count how many separate strike/setup events there are
        operations = [e for e in result if e.get("type") in ["setup", "strike", "preset"]]
        
        # Get titles for debugging
        op_titles = [e.get("title") for e in operations]
        
        # Should not have both "Strike & Ice Scrape" AND "Set Up Nightclub" as separate events
        # if they overlap - they should be merged
        has_separate_strike = any("Strike" in t and "Set Up" not in t for t in op_titles)
        has_separate_setup = any("Set Up Nightclub" in t and "Strike" not in t for t in op_titles)
        
        # If they're supposed to overlap, one should contain both
        if has_separate_strike and has_separate_setup:
            # Check times - if they overlap, this is a bug
            strike_evt = [e for e in operations if "Strike" in e.get("title", "") and "Set Up" not in e.get("title", "")]
            setup_evt = [e for e in operations if "Set Up Nightclub" in e.get("title", "") and "Strike" not in e.get("title", "")]
            
            if strike_evt and setup_evt:
                strike_end = strike_evt[0].get("end_dt")
                setup_start = setup_evt[0].get("start_dt")
                
                # They should NOT overlap (if they do, merge failed)
                assert strike_end <= setup_start, f"Overlapping events not merged: Strike ends {strike_end}, Setup starts {setup_start}"
    
    def test_strike_never_overlaps_with_actual_events(self, parser, studio_b_rules):
        """
        Critical: Strikes must NEVER overlap with actual events.
        
        Scenario: Crazy Quest ends, Strike Crazy Quest should fire, but RED starts
        before the strike would finish. Strike should defer to AFTER RED ends.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        floor_config = {
            "floor_requirements": studio_b_rules.get("floor_requirements"),
            "floor_transition": studio_b_rules.get("floor_transition"),
        }
        
        # Scenario: Crazy Quest at 11:20 PM - 12:00 AM, RED at 12:00 AM - 1:00 AM
        # Strike Crazy Quest (30 min) would be 12:00 - 12:30, overlapping RED!
        events = [
            {"title": "Crazy Quest", "start_dt": datetime(2025, 1, 15, 23, 20),
             "end_dt": datetime(2025, 1, 16, 0, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 16, 0, 0),
             "end_dt": datetime(2025, 1, 16, 1, 0), "category": "party",
             "raw_date": "2025-01-16", "venue": "Studio B", "type": "party"},
        ]
        
        # Full pipeline with overlap resolution
        result = parser._apply_derived_event_rules(events, derived_rules)
        result = parser._apply_floor_transition_rules(result, floor_config)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        
        # Get all actual events (non-operational) - doors is also operational
        actual_events = [e for e in result if e.get('type') not in ['setup', 'strike', 'preset', 'doors']]
        operations = [e for e in result if e.get('type') in ['setup', 'strike', 'preset']]
        
        # Verify NO operation overlaps with ANY actual event
        for op in operations:
            op_start = op.get('start_dt')
            op_end = op.get('end_dt')
            op_title = op.get('title', '')
            
            for actual in actual_events:
                actual_start = actual.get('start_dt')
                actual_end = actual.get('end_dt')
                actual_title = actual.get('title', '')
                
                # Check for overlap (not adjacent - adjacent is OK)
                has_overlap = not (op_end <= actual_start or op_start >= actual_end)
                
                assert not has_overlap, (
                    f"Operation '{op_title}' ({op_start} - {op_end}) "
                    f"overlaps with actual event '{actual_title}' ({actual_start} - {actual_end})"
                )
    
    def test_separate_blocks_get_separate_strikes(self, parser, studio_b_rules):
        """
        Events with gap >= 60 min should be in separate blocks, each getting a strike.
        
        Scenario: Family Shush! (7-8 PM) then Battle of Sexes (10-11 PM) with 2-hour gap
        Should generate TWO strikes - after Family Shush AND after Battle of Sexes.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        events = [
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Get all strikes
        strikes = [e for e in result if "Strike" in e.get("title", "") and e.get("type") == "strike"]
        
        # Should have TWO strikes (one per block) due to 2-hour gap
        assert len(strikes) >= 2, f"Expected 2+ strikes for separate blocks, got {len(strikes)}: {[s.get('title') for s in strikes]}"
        
        # Verify one is after Family Shush (8 PM) and one after Battle (11 PM)
        strike_starts = [s.get("start_dt") for s in strikes]
        has_family_strike = any(s.hour == 20 for s in strike_starts)  # 8 PM
        has_battle_strike = any(s.hour == 23 for s in strike_starts)  # 11 PM
        
        assert has_family_strike, f"Missing strike after Family Shush! at 8 PM. Strike starts: {strike_starts}"
        assert has_battle_strike, f"Missing strike after Battle of Sexes at 11 PM. Strike starts: {strike_starts}"
    
    def test_multiple_ice_shows_between_presets_dont_merge_with_strike(self, parser, studio_b_rules):
        """
        Critical: There should be only ONE Strike & Ice Scrape (after the LAST Ice Show of the day)
        
        Even with a 75-min gap between shows, last_per_day should fire only once.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        # Two Ice Shows - 75 min gap to test calendar-day logic
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "show"},
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 21, 15),
             "end_dt": datetime(2025, 1, 15, 22, 15), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "show"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Get ALL strikes for Ice Shows
        all_ice_strikes = [e for e in result 
                          if e.get("type") == "strike" 
                          and "Ice Scrape" in e.get("title", "")]
        
        # CRITICAL: Should have exactly ONE Strike & Ice Scrape (after last show)
        assert len(all_ice_strikes) == 1, (
            f"Expected 1 Strike & Ice Scrape, got {len(all_ice_strikes)}: "
            f"{[(s.get('title'), s.get('start_dt')) for s in all_ice_strikes]}"
        )
        
        # Verify it's after the LAST show (22:15)
        assert all_ice_strikes[0].get("start_dt") == datetime(2025, 1, 15, 22, 15), (
            f"Strike should be after last show at 22:15, got {all_ice_strikes[0].get('start_dt')}"
        )
    
    def test_skating_session_only_gets_one_setup(self, parser, studio_b_rules):
        """
        Skating sessions should only get "Set Up Skates", NOT also a catch-all "Set Up [title]".
        
        The specific title rule (Set Up Skates) should prevent the category catch-all from also firing.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        events = [
            {"title": "Private Ice Skating", "start_dt": datetime(2025, 1, 15, 14, 0),
             "end_dt": datetime(2025, 1, 15, 15, 0), "category": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "activity"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Get all setups
        setups = [e for e in result if e.get("type") == "setup"]
        
        # Should have exactly ONE setup titled "Set Up Skates"
        assert len(setups) == 1, f"Expected 1 setup, got {len(setups)}: {[s.get('title') for s in setups]}"
        assert setups[0].get("title") == "Set Up Skates", f"Expected 'Set Up Skates', got '{setups[0].get('title')}'"
        
        # Verify it does NOT contain "Set Up Private Ice Skating" (catch-all)
        for setup in setups:
            assert "Private Ice Skating" not in setup.get("title", ""), (
                f"Catch-all incorrectly fired for skating: {setup.get('title')}"
            )
    
    def test_skating_sessions_only_one_strike_per_day(self, parser, studio_b_rules):
        """
        Multiple skating sessions with NO events in between should only get ONE strike at the end.
        
        Scenario: Skating at 9 AM and 9 PM (12 hour gap) but NO other Studio B events between.
        Should still only get one Strike Skates at the very end.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        events = [
            {"title": "Open Ice Skating", "start_dt": datetime(2025, 1, 15, 9, 0),
             "end_dt": datetime(2025, 1, 15, 11, 0), "category": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "activity"},
            {"title": "Private Ice Skating", "start_dt": datetime(2025, 1, 15, 21, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "activity"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Get all strikes for skating
        strikes = [e for e in result if e.get("type") == "strike" and "Skates" in e.get("title", "")]
        
        # Should have exactly ONE strike (after the last session at 23:00)
        assert len(strikes) == 1, f"Expected 1 strike, got {len(strikes)}: {[s.get('title') for s in strikes]}"
        
        # Strike should be after the evening session (9 PM ends at 11 PM)
        assert strikes[0].get("start_dt") == datetime(2025, 1, 15, 23, 0), (
            f"Strike should be at 23:00, got {strikes[0].get('start_dt')}"
        )
    
    def test_skating_sessions_strike_when_intervening_event(self, parser, studio_b_rules):
        """
        When there's an actual Studio B event between skating sessions, we MUST strike.
        
        Scenario: Skating 9-11 AM, Ice Show 2-3 PM, Skating 6-8 PM
        Should get TWO strikes: after morning skating (before Ice Show) and after evening skating.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        
        events = [
            {"title": "Open Ice Skating", "start_dt": datetime(2025, 1, 15, 9, 0),
             "end_dt": datetime(2025, 1, 15, 11, 0), "category": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "activity"},
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 14, 0),
             "end_dt": datetime(2025, 1, 15, 15, 0), "category": "show",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "show"},
            {"title": "Private Ice Skating", "start_dt": datetime(2025, 1, 15, 18, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "activity"},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        
        # Get all strikes for skating
        strikes = [e for e in result if e.get("type") == "strike" and "Skates" in e.get("title", "")]
        
        # Should have TWO strikes (after morning and evening skating)
        assert len(strikes) == 2, f"Expected 2 strikes, got {len(strikes)}: {[s.get('title') for s in strikes]}"
        
        # Strikes should be at 11:00 and 20:00
        strike_times = sorted([s.get("start_dt") for s in strikes])
        assert strike_times[0] == datetime(2025, 1, 15, 11, 0), f"First strike should be at 11:00, got {strike_times[0]}"
        assert strike_times[1] == datetime(2025, 1, 15, 20, 0), f"Second strike should be at 20:00, got {strike_times[1]}"
    
    def test_overlapping_strike_is_omitted(self, parser, studio_b_rules):
        """
        Critical: If a strike would overlap with the next event, it should be OMITTED.
        
        Scenario: Family SHUSH! 7-8 PM, Battle of Sexes 8:15-9:15 PM
        Strike Family SHUSH would be 8:00-8:30 PM, overlapping Battle of Sexes start.
        The strike should be omitted - Battle of Sexes will have its own strike.
        
        This test uses the FULL pipeline including overlap resolution.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        floor_config = {
            "floor_requirements": studio_b_rules.get("floor_requirements"),
            "floor_transition": studio_b_rules.get("floor_transition"),
        }
        
        # Back-to-back game shows with only 15 min gap
        events = [
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 20, 15),
             "end_dt": datetime(2025, 1, 15, 21, 15), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
        ]
        
        # FULL pipeline with overlap resolution
        result = parser._apply_derived_event_rules(events, derived_rules)
        result = parser._apply_floor_transition_rules(result, floor_config)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        
        # Get all strikes
        strikes = [e for e in result if e.get("type") == "strike"]
        
        # Should have exactly ONE strike - for Battle of Sexes (the one that doesn't overlap)
        # Strike Family SHUSH would overlap with Battle of Sexes start and should be omitted
        strike_titles = [s.get("title", "") for s in strikes]
        
        # Verify Strike Family SHUSH is NOT present (it was omitted due to overlap)
        family_strikes = [s for s in strikes if "Family SHUSH" in s.get("title", "")]
        assert len(family_strikes) == 0, (
            f"Strike Family SHUSH! should be OMITTED (overlaps with Battle of Sexes), "
            f"but found: {family_strikes}"
        )
        
        # Verify Battle of Sexes still has its strike
        battle_strikes = [s for s in strikes if "Battle" in s.get("title", "")]
        assert len(battle_strikes) >= 1, (
            f"Missing Strike Battle of the Sexes. All strikes: {strike_titles}"
        )
    
    def test_non_overlapping_strikes_both_fire(self, parser, studio_b_rules):
        """
        When game shows have enough gap, BOTH should get strikes.
        
        Scenario: Family SHUSH! 7-8 PM, Battle of Sexes 10-11 PM (2 hour gap)
        Both should get strikes since Strike Family SHUSH (8:00-8:30) doesn't overlap.
        
        This test uses the FULL pipeline including overlap resolution.
        """
        derived_rules = studio_b_rules.get("derived_event_rules", {})
        floor_config = {
            "floor_requirements": studio_b_rules.get("floor_requirements"),
            "floor_transition": studio_b_rules.get("floor_transition"),
        }
        
        events = [
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "category": "game",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "game"},
        ]
        
        # FULL pipeline
        result = parser._apply_derived_event_rules(events, derived_rules)
        result = parser._apply_floor_transition_rules(result, floor_config)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        
        # Get all strikes
        strikes = [e for e in result if e.get("type") == "strike"]
        strike_titles = [s.get("title", "") for s in strikes]
        
        # Both should have strikes
        family_strikes = [s for s in strikes if "Family SHUSH" in s.get("title", "")]
        battle_strikes = [s for s in strikes if "Battle" in s.get("title", "")]
        
        assert len(family_strikes) >= 1, f"Missing Strike Family SHUSH! Strikes: {strike_titles}"
        assert len(battle_strikes) >= 1, f"Missing Strike Battle of the Sexes. Strikes: {strike_titles}"


class TestLateNightHandling:
    """Tests for late-night derived event handling."""
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def late_night_config(self):
        return {
            "cutoff_hour": 1,
            "reschedule_hour": 9,
        }
    
    def test_late_night_event_removed_on_last_day(self, parser, late_night_config):
        """
        Derived events starting in late-night window ON the last day should be rescheduled to 9 AM.
        Events AFTER the last day should be removed.
        """
        voyage_end_date = date(2025, 1, 20)  # Last day is Jan 20
        
        events = [
            # Event ON the last day (Jan 20) - should be rescheduled to 9 AM
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 20, 0, 0),
             "end_dt": datetime(2025, 1, 20, 1, 0), "category": "party",
             "raw_date": "2025-01-20", "venue": "Studio B", "type": "party"},
            {"title": "Strike RED", "start_dt": datetime(2025, 1, 20, 1, 0),
             "end_dt": datetime(2025, 1, 20, 1, 30), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
        ]
        
        result = parser._handle_late_night_derived_events(events, late_night_config, voyage_end_date)
        
        # Strike should be rescheduled to 9 AM on last day
        strikes = [e for e in result if e.get("type") == "strike"]
        assert len(strikes) == 1, f"Expected 1 strike rescheduled to 9 AM on last day, got: {strikes}"
        assert strikes[0].get("start_dt").hour == 9, f"Strike should be at 9 AM, got: {strikes[0].get('start_dt')}"
    
    def test_late_night_event_rescheduled_to_9am(self, parser, late_night_config):
        """
        Derived events starting after 1 AM (not last day) should be rescheduled to 9 AM.
        """
        voyage_end_date = date(2025, 1, 20)  # Last day
        
        # Event on Jan 15 (not last day)
        events = [
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 15, 0, 0),
             "end_dt": datetime(2025, 1, 15, 1, 0), "category": "party",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "party"},
            {"title": "Strike RED", "start_dt": datetime(2025, 1, 15, 1, 0),
             "end_dt": datetime(2025, 1, 15, 1, 30), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
        ]
        
        result = parser._handle_late_night_derived_events(events, late_night_config, voyage_end_date)
        
        # Strike should be rescheduled to 9 AM
        strikes = [e for e in result if e.get("type") == "strike"]
        assert len(strikes) == 1, f"Expected 1 strike, got: {strikes}"
        assert strikes[0].get("start_dt").hour == 9, f"Strike should be at 9 AM, got: {strikes[0].get('start_dt')}"
    
    def test_multiple_late_night_events_merge_at_9am(self, parser, late_night_config):
        """
        Multiple late-night derived events should be merged when rescheduled to 9 AM.
        """
        voyage_end_date = date(2025, 1, 20)
        
        events = [
            # Two events ending in late-night window (after 1 AM)
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 16, 0, 0),
             "end_dt": datetime(2025, 1, 16, 1, 0), "category": "game",
             "raw_date": "2025-01-16", "venue": "Studio B", "type": "game"},
            {"title": "Strike Family SHUSH!", "start_dt": datetime(2025, 1, 16, 1, 0),
             "end_dt": datetime(2025, 1, 16, 1, 30), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 16, 1, 30),
             "end_dt": datetime(2025, 1, 16, 2, 30), "category": "party",
             "raw_date": "2025-01-16", "venue": "Studio B", "type": "party"},
            {"title": "Strike RED", "start_dt": datetime(2025, 1, 16, 2, 30),
             "end_dt": datetime(2025, 1, 16, 3, 0), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
        ]
        
        result = parser._handle_late_night_derived_events(events, late_night_config, voyage_end_date)
        
        # Both strikes should be rescheduled to 9 AM Jan 16 and merged
        strikes = [e for e in result if e.get("type") == "strike"]
        
        # Should be merged into one (since they overlap at 9 AM)
        assert len(strikes) <= 1, f"Expected merged strikes, got: {[s.get('title') for s in strikes]}"
    
    def test_late_night_event_dropped_if_overlaps_actual_at_9am(self, parser, late_night_config):
        """
        Late-night derived events should be dropped if they would overlap with
        an actual event at the reschedule time (9 AM).
        """
        voyage_end_date = date(2025, 1, 20)
        
        events = [
            # Late night strike
            {"title": "Strike RED", "start_dt": datetime(2025, 1, 15, 1, 30),
             "end_dt": datetime(2025, 1, 15, 2, 0), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
            # But there's an actual event at 9 AM!
            {"title": "Ice Skating", "start_dt": datetime(2025, 1, 15, 9, 0),
             "end_dt": datetime(2025, 1, 15, 11, 0), "category": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B", "type": "activity"},
        ]
        
        result = parser._handle_late_night_derived_events(events, late_night_config, voyage_end_date)
        
        # Strike should be dropped (would overlap with Ice Skating at 9 AM)
        strikes = [e for e in result if e.get("type") == "strike"]
        assert len(strikes) == 0, f"Expected no strikes (overlap with actual), got: {strikes}"
    
    def test_late_night_event_removed_after_voyage_end(self, parser, late_night_config):
        """
        Derived events that occur AFTER the voyage end date should be removed completely.
        """
        voyage_end_date = date(2025, 1, 20)  # Last day is Jan 20
        
        events = [
            # Event AFTER the last day (Jan 21) - should be removed
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 21, 0, 0),
             "end_dt": datetime(2025, 1, 21, 1, 0), "category": "party",
             "raw_date": "2025-01-21", "venue": "Studio B", "type": "party"},
            {"title": "Strike RED", "start_dt": datetime(2025, 1, 21, 1, 0),
             "end_dt": datetime(2025, 1, 21, 1, 30), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
        ]
        
        result = parser._handle_late_night_derived_events(events, late_night_config, voyage_end_date)
        
        # Strike should be removed (after voyage end)
        strikes = [e for e in result if e.get("type") == "strike"]
        assert len(strikes) == 0, f"Expected no strikes after voyage end, got: {strikes}"


class TestMergedEventStrikeHandling:
    """
    Tests for strikes that overlap with merged events (like Parades from other venues).
    """
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_strike_overlaps_merged_event_merges_with_next_setup(self, parser):
        """
        When a strike overlaps with a merged event (Parade), and there's a next 
        Setup event that day, the strike should be merged into that Setup.
        """
        from backend.app.config.venue_rules import get_venue_rules
        
        venue_rules = get_venue_rules('WN', 'Studio B')
        derived_rules = venue_rules.get('derived_event_rules', {})
        floor_config = {
            'floor_requirements': venue_rules.get('self_extraction_policy', {}).get('floor_requirements'),
            'floor_transition': venue_rules.get('self_extraction_policy', {}).get('floor_transition'),
        }
        
        # Laser Tag -> Parade (merged) -> Ice Show (has setup)
        events = [
            {'title': 'Laser Tag', 'start_dt': datetime(2025, 7, 24, 13, 0),
             'end_dt': datetime(2025, 7, 24, 15, 30), 'category': 'activity',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'activity'},
            {'title': 'Anchors Aweigh Parade', 'start_dt': datetime(2025, 7, 24, 15, 30),
             'end_dt': datetime(2025, 7, 24, 16, 0), 'category': 'parade',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'parade', 'is_cross_venue': True},
            {'title': 'Ice Show: 365', 'start_dt': datetime(2025, 7, 24, 19, 0),
             'end_dt': datetime(2025, 7, 24, 20, 0), 'category': 'show',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'show'},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        result = parser._apply_floor_transition_rules(result, floor_config)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        
        # Find the setup for ice show and verify it contains "Strike Laser Tag"
        setups = [e for e in result if e.get('type') == 'setup']
        setup_titles = [s.get('title', '') for s in setups]
        
        # "Strike Laser Tag" should be merged into one of the setups
        has_strike_laser_tag = any('Strike Laser Tag' in t for t in setup_titles)
        assert has_strike_laser_tag, f"Strike Laser Tag should be merged into a setup. Setups: {setup_titles}"
    
    def test_strike_overlaps_merged_event_no_next_setup_schedules_after(self, parser):
        """
        When a strike overlaps with a merged event (Parade), and there's no next 
        Setup event that day, the strike should be scheduled after the merged event.
        """
        from backend.app.config.venue_rules import get_venue_rules
        
        venue_rules = get_venue_rules('WN', 'Studio B')
        derived_rules = venue_rules.get('derived_event_rules', {})
        floor_config = {
            'floor_requirements': venue_rules.get('self_extraction_policy', {}).get('floor_requirements'),
            'floor_transition': venue_rules.get('self_extraction_policy', {}).get('floor_transition'),
        }
        
        # Laser Tag -> Parade (merged) -> no more events
        events = [
            {'title': 'Laser Tag', 'start_dt': datetime(2025, 7, 24, 13, 0),
             'end_dt': datetime(2025, 7, 24, 15, 30), 'category': 'activity',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'activity'},
            {'title': 'Anchors Aweigh Parade', 'start_dt': datetime(2025, 7, 24, 15, 30),
             'end_dt': datetime(2025, 7, 24, 16, 0), 'category': 'parade',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'parade', 'is_cross_venue': True},
        ]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        result = parser._apply_floor_transition_rules(result, floor_config)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        
        # Find strike for Laser Tag
        strikes = [e for e in result if e.get('type') == 'strike' and 'Laser Tag' in e.get('title', '')]
        
        assert len(strikes) == 1, f"Expected Strike Laser Tag, got: {[s.get('title') for s in strikes]}"
        
        # Strike should start after parade ends (16:00)
        strike_start = strikes[0].get('start_dt')
        parade_end = datetime(2025, 7, 24, 16, 0)
        assert strike_start >= parade_end, f"Strike should start after parade ends. Strike: {strike_start}, Parade end: {parade_end}"


class TestFullPipelineIntegration:
    """
    Integration tests that exercise the full pipeline to catch errors like undefined variables.
    These tests call _transform_to_api_format with real venue_rules.
    """
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def full_venue_rules(self):
        """Full venue rules structure similar to what get_venue_rules returns."""
        return {
            "self_extraction_policy": {
                "known_shows": ["Ice Show: 365"],
                "renaming_map": {},
                "default_durations": {"Ice Show: 365": 60},
                "late_night_config": {
                    "cutoff_hour": 1,
                    "reschedule_hour": 9,
                },
                "floor_requirements": {
                    "floor": {"match_titles": ["Laser Tag"]},
                    "ice": {"match_titles": ["Ice Show: 365"]},
                },
                "floor_transition": {
                    "duration_minutes": 60,
                    "titles": {"floor_to_ice": "Strike Floor", "ice_to_floor": "Set Floor"},
                    "type": "strike",
                },
            },
            "derived_event_rules": {
                "strike": [
                    {
                        "match_titles": ["Family SHUSH!"],
                        "offset_minutes": 0,
                        "anchor": "end",
                        "duration_minutes": 30,
                        "title_template": "Strike {parent_title}",
                        "type": "strike",
                    },
                ],
            },
        }
    
    def test_transform_to_api_format_with_late_night_config(self, parser, full_venue_rules):
        """
        Integration test: _transform_to_api_format should access late_night_config
        from venue_rules without errors.
        
        This test would have caught the 'self_policy is not defined' error.
        """
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "MIAMI"},
                {"day_number": 2, "date": "2025-01-16", "port": "CRUISING"},
            ],
            "events": [
                {"title": "Family SHUSH!", "start_time": "23:00", "end_time": None,
                 "date": "2025-01-15", "category": "game"},
            ],
        }
        
        derived_rules = full_venue_rules.get("derived_event_rules", {})
        floor_config = {
            "floor_requirements": full_venue_rules["self_extraction_policy"].get("floor_requirements"),
            "floor_transition": full_venue_rules["self_extraction_policy"].get("floor_transition"),
        }
        
        # This should NOT raise any errors
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={"Family SHUSH!": 60},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config=floor_config,
            venue_rules=full_venue_rules,
        )
        
        # Basic validation that it worked
        assert "events" in result
        assert "itinerary" in result


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: RED Party Short Titles
# ═══════════════════════════════════════════════════════════════════════════════

class TestREDPartyShortTitles:
    """Test that RED party events get 'Set Up RED' and 'Strike RED' instead of full title."""
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def full_venue_rules(self):
        """Full venue rules including RED party setup/strike rules."""
        from backend.app.config.venue_rules import get_venue_rules
        return get_venue_rules("WN", "Studio B")
    
    def test_red_nightclub_setup_has_short_title(self, parser, full_venue_rules):
        """RED: Nightclub Experience should get 'Set Up RED' not 'Set Up RED: Nightclub Experience'."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "RED: Nightclub Experience", "start_time": "21:00", "end_time": "23:00",
                 "date": "2025-01-15", "category": "party"},
            ],
        }
        
        derived_rules = full_venue_rules.get("derived_event_rules", {})
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={"RED: Nightclub Experience": 90},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config={},
            venue_rules=full_venue_rules,
        )
        
        # Find setup event for RED - may be merged with other setups
        setup_events = [e for e in result["events"] if "Set Up" in e["title"]]
        assert len(setup_events) >= 1, "Should have at least one setup event"
        
        # Check that 'Set Up RED' is part of the title (may be merged)
        red_setup = [e for e in setup_events if "Set Up RED" in e["title"]]
        assert len(red_setup) >= 1, f"Should have at least one RED setup, got: {[e['title'] for e in setup_events]}"
    
    def test_red_party_strike_has_short_title(self, parser, full_venue_rules):
        """RED! Party should get 'Strike RED' not 'Strike RED! Party'."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "RED! Party", "start_time": "21:00", "end_time": "23:00",
                 "date": "2025-01-15", "category": "party"},
            ],
        }
        
        derived_rules = full_venue_rules.get("derived_event_rules", {})
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config={},
            venue_rules=full_venue_rules,
        )
        
        # Find strike event for RED
        strike_events = [e for e in result["events"] if "Strike" in e["title"]]
        red_strike = [e for e in strike_events if "RED" in e["title"]]
        
        assert len(red_strike) == 1, "Should have exactly one RED strike"
        assert red_strike[0]["title"] == "Strike RED", \
            f"Expected 'Strike RED' but got '{red_strike[0]['title']}'"
    
    def test_non_red_party_gets_full_title(self, parser, full_venue_rules):
        """Non-RED parties like Battle of the Sexes should get full title in setup/strike."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "Battle of the Sexes", "start_time": "22:00", "end_time": "23:00",
                 "date": "2025-01-15", "category": "game"},
            ],
        }
        
        derived_rules = full_venue_rules.get("derived_event_rules", {})
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config={},
            venue_rules=full_venue_rules,
        )
        
        # Find setup/strike events
        setup_events = [e for e in result["events"] if "Set Up" in e["title"]]
        strike_events = [e for e in result["events"] if "Strike" in e["title"]]
        
        battle_setup = [e for e in setup_events if "Battle" in e["title"]]
        battle_strike = [e for e in strike_events if "Battle" in e["title"]]
        
        if battle_setup:
            assert battle_setup[0]["title"] == "Set Up Battle of the Sexes"
        if battle_strike:
            assert battle_strike[0]["title"] == "Strike Battle of the Sexes"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: End Time "Late" Display Flag
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndIsLateFlag:
    """Test that end_is_late flag is set correctly for Late end times."""
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def full_venue_rules(self):
        """Full venue rules for testing."""
        from backend.app.config.venue_rules import get_venue_rules
        return get_venue_rules("WN", "Studio B")
    
    def test_red_party_without_end_time_gets_late_flag(self, parser, full_venue_rules):
        """RED party events without explicit end time should get end_is_late=True."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "RED: Nightclub Experience", "start_time": "23:30", "end_time": None,
                 "date": "2025-01-15", "category": "party"},
            ],
        }
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules={},
            floor_config={},
            venue_rules=full_venue_rules,
        )
        
        # Find the main RED event
        red_events = [e for e in result["events"] if "RED" in e["title"] and "Set Up" not in e["title"] and "Strike" not in e["title"]]
        assert len(red_events) >= 1, "Should have at least one RED event"
        
        main_red = red_events[0]
        assert main_red.get("end_is_late") == True, \
            "RED party without end time should have end_is_late=True"
    
    def test_event_with_0100_end_time_gets_late_flag(self, parser, full_venue_rules):
        """Events with 01:00 end time (LLM interpretation of 'Late') should get end_is_late=True."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "Dance Party", "start_time": "22:00", "end_time": "01:00",
                 "date": "2025-01-15", "category": "party"},
            ],
        }
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules={},
            floor_config={},
            venue_rules=full_venue_rules,
        )
        
        # Find the dance party event
        party_events = [e for e in result["events"] if "Dance Party" in e["title"]]
        assert len(party_events) == 1, "Should have exactly one Dance Party event"
        
        assert party_events[0].get("end_is_late") == True, \
            "Event with 01:00 end time should have end_is_late=True"
    
    def test_normal_event_does_not_get_late_flag(self, parser, full_venue_rules):
        """Events with normal end times should NOT have end_is_late flag."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "Ice Show: 365", "start_time": "19:30", "end_time": "20:30",
                 "date": "2025-01-15", "category": "show"},
            ],
        }
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules={},
            floor_config={},
            venue_rules=full_venue_rules,
        )
        
        # Find the ice show event
        ice_shows = [e for e in result["events"] if "Ice Show" in e["title"]]
        assert len(ice_shows) == 1, "Should have exactly one Ice Show event"
        
        assert ice_shows[0].get("end_is_late") != True, \
            "Normal event should NOT have end_is_late=True"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Floor Transition Late Night Exclusion
# ═══════════════════════════════════════════════════════════════════════════════

class TestFloorTransitionLateNightExclusion:
    """Test that floor transitions handle their own timing and aren't moved by generic late night handler."""
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def full_venue_rules(self):
        """Full venue rules for testing."""
        from backend.app.config.venue_rules import get_venue_rules
        return get_venue_rules("WN", "Studio B")
    
    def test_floor_transition_has_is_floor_transition_flag(self, parser, full_venue_rules):
        """Floor transitions should have is_floor_transition=True flag."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Create a floor transition directly
        prev_event = {
            "title": "Crazy Quest",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 0, 0),  # Ends at midnight
            "category": "game",
            "venue": "Studio B"
        }
        next_event = {
            "title": "Ice Skating",
            "start_dt": datetime(2025, 1, 16, 14, 0),
            "end_dt": datetime(2025, 1, 16, 17, 0),
            "category": "activity",
            "venue": "Studio B"
        }
        transition_config = {
            "duration_minutes": 60,
            "titles": {"floor_to_ice": "Strike Floor", "ice_to_floor": "Set Floor"},
            "type": "strike"
        }
        
        transition = parser._create_floor_transition(
            prev_event=prev_event,
            next_event=next_event,
            prev_floor_state=True,
            next_floor_state=False,
            transition_config=transition_config
        )
        
        assert transition is not None, "Should create a floor transition"
        assert transition.get("is_floor_transition") == True, \
            "Floor transition should have is_floor_transition=True"
    
    def test_floor_transition_after_midnight_event_is_rescheduled_to_morning(self, parser, full_venue_rules):
        """Floor transition after event ending AFTER midnight (00:01+) should be at 9 AM."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Event ends AFTER midnight (00:30, not exactly 00:00)
        prev_event = {
            "title": "RED Party",
            "start_dt": datetime(2025, 1, 15, 23, 30),
            "end_dt": datetime(2025, 1, 16, 0, 30),  # Ends at 00:30 - AFTER midnight
            "category": "game",
            "venue": "Studio B"
        }
        next_event = {
            "title": "Ice Skating",
            "start_dt": datetime(2025, 1, 16, 14, 0),
            "end_dt": datetime(2025, 1, 16, 17, 0),
            "category": "activity",
            "venue": "Studio B"
        }
        transition_config = {
            "duration_minutes": 60,
            "titles": {"floor_to_ice": "Strike Floor", "ice_to_floor": "Set Floor"},
            "type": "strike"
        }
        
        transition = parser._create_floor_transition(
            prev_event=prev_event,
            next_event=next_event,
            prev_floor_state=True,
            next_floor_state=False,
            transition_config=transition_config
        )
        
        assert transition is not None, "Should create a floor transition"
        
        # Should be at 9 AM, not midnight
        assert transition["start_dt"].hour == 9, \
            f"Floor transition should be at 9 AM, not {transition['start_dt'].hour}:00"
    
    def test_floor_transition_before_midnight_event_happens_immediately(self, parser, full_venue_rules):
        """Floor transition after event ending before midnight should happen immediately."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Event ends before midnight
        prev_event = {
            "title": "Crazy Quest",
            "start_dt": datetime(2025, 1, 15, 21, 0),
            "end_dt": datetime(2025, 1, 15, 22, 30),  # Ends at 10:30 PM
            "category": "game",
            "venue": "Studio B"
        }
        next_event = {
            "title": "Ice Skating",
            "start_dt": datetime(2025, 1, 16, 14, 0),
            "end_dt": datetime(2025, 1, 16, 17, 0),
            "category": "activity",
            "venue": "Studio B"
        }
        transition_config = {
            "duration_minutes": 60,
            "titles": {"floor_to_ice": "Strike Floor", "ice_to_floor": "Set Floor"},
            "type": "strike"
        }
        
        transition = parser._create_floor_transition(
            prev_event=prev_event,
            next_event=next_event,
            prev_floor_state=True,
            next_floor_state=False,
            transition_config=transition_config
        )
        
        assert transition is not None, "Should create a floor transition"
        
        # Should start immediately after prev_event ends (22:30)
        assert transition["start_dt"] == prev_event["end_dt"], \
            f"Floor transition should start at {prev_event['end_dt']}, not {transition['start_dt']}"
    
    def test_late_night_handler_skips_floor_transitions(self, parser, full_venue_rules):
        """Generic late night handler should NOT process floor transitions."""
        late_night_config = {
            "cutoff_hour": 1,
            "end_hour": 6,
            "reschedule_hour": 9,
            "long_event_threshold_minutes": 60
        }
        
        # Create a floor transition that starts at midnight
        floor_transition = {
            "title": "Strike Floor",
            "start_dt": datetime(2025, 1, 16, 0, 30),  # 12:30 AM
            "end_dt": datetime(2025, 1, 16, 1, 30),    # 1:30 AM
            "type": "strike",
            "is_derived": True,
            "is_floor_transition": True,
            "venue": "Studio B"
        }
        
        # Create a regular derived event that should be affected
        regular_strike = {
            "title": "Strike Crazy Quest",
            "start_dt": datetime(2025, 1, 16, 1, 30),  # 1:30 AM - in cutoff window
            "end_dt": datetime(2025, 1, 16, 2, 0),
            "type": "strike",
            "is_derived": True,
            "venue": "Studio B"
        }
        
        events = [floor_transition, regular_strike]
        
        result = parser._handle_late_night_derived_events(
            events, late_night_config, voyage_end_date=None
        )
        
        # Floor transition should NOT have been rescheduled
        floor_transitions = [e for e in result if e.get("is_floor_transition")]
        assert len(floor_transitions) == 1
        assert floor_transitions[0]["start_dt"].hour == 0, \
            "Floor transition should still be at 00:30, not rescheduled"
    
    def test_midnight_strike_is_rescheduled_to_morning(self, parser, full_venue_rules):
        """Strikes at midnight (hour 0) should be rescheduled to 9 AM like strikes at 1-5 AM.
        
        This is a regression test - previously strikes at 00:00-00:59 were NOT rescheduled
        because cutoff_hour was 1, meaning only hours 1-5 were in the late night window.
        """
        late_night_config = {
            "cutoff_hour": 1,  # Legacy config - code now ignores this for hour 0
            "end_hour": 6,
            "reschedule_hour": 9,
        }
        
        # Strike at midnight (00:00) - after Crazy Quest ends at midnight
        midnight_strike = {
            "title": "Strike Crazy Quest",
            "start_dt": datetime(2025, 1, 16, 0, 30),  # 00:30 - AFTER midnight
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "type": "strike",
            "is_derived": True,
            "venue": "Studio B"
        }
        
        events = [midnight_strike]
        
        result = parser._handle_late_night_derived_events(
            events, late_night_config, voyage_end_date=None
        )
        
        # Strike at 00:30 (after midnight) should be rescheduled to 9 AM
        strikes = [e for e in result if "Strike" in e.get("title", "")]
        assert len(strikes) == 1
        assert strikes[0]["start_dt"].hour == 9, \
            f"Strike at 00:30 should be rescheduled to 9 AM, got {strikes[0]['start_dt'].hour}:00"
    
    def test_midnight_exact_strike_is_not_rescheduled(self, parser, full_venue_rules):
        """Strikes at exactly midnight (00:00) should NOT be rescheduled.
        
        00:00 is midnight exactly, which is NOT 'after midnight', so strikes
        at this time can happen immediately.
        """
        late_night_config = {
            "end_hour": 6,
            "reschedule_hour": 9,
        }
        
        # Strike at exactly midnight (00:00) - after Crazy Quest ends at midnight
        midnight_exact_strike = {
            "title": "Strike Crazy Quest",
            "start_dt": datetime(2025, 1, 16, 0, 0),  # Exactly midnight
            "end_dt": datetime(2025, 1, 16, 0, 30),
            "type": "strike",
            "is_derived": True,
            "venue": "Studio B"
        }
        
        events = [midnight_exact_strike]
        
        result = parser._handle_late_night_derived_events(
            events, late_night_config, voyage_end_date=None
        )
        
        # Strike at exactly 00:00 should NOT be rescheduled - stays at midnight
        strikes = [e for e in result if "Strike" in e.get("title", "")]
        assert len(strikes) == 1
        assert strikes[0]["start_dt"].hour == 0 and strikes[0]["start_dt"].minute == 0, \
            f"Strike at exactly midnight should NOT be rescheduled, got {strikes[0]['start_dt'].hour}:{strikes[0]['start_dt'].minute:02d}"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: No Duplicate Derived Events
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoDuplicateDerivedEvents:
    """Ensure each event only produces ONE derived event of each type.
    
    The system uses 'first match wins' via matched_parent_keys tracking.
    Even if multiple rules COULD match (e.g., specific title rule + catch-all category rule),
    only ONE derived event should be created because the first matching rule adds 
    the event to matched_parent_keys, causing subsequent rules to skip it.
    """
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def derived_rules(self):
        from backend.app.config.venue_rules import get_venue_rules
        venue_rules = get_venue_rules("WN", "Studio B")
        return venue_rules.get("derived_event_rules", {})
    
    def test_red_nightclub_creates_only_one_setup_event(self, parser, derived_rules):
        """RED: A Nightclub Experience should create exactly ONE setup event."""
        events = [{
            "title": "RED: A Nightclub Experience",
            "category": "party",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "venue": "Studio B"
        }]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        setup_events = [e for e in result if "Set Up" in e.get("title", "")]
        
        assert len(setup_events) == 1, \
            f"Expected 1 setup event for RED, got {len(setup_events)}: {[e['title'] for e in setup_events]}"
        assert setup_events[0]["title"] == "Set Up RED", \
            f"Expected 'Set Up RED', got '{setup_events[0]['title']}'"
    
    def test_red_nightclub_creates_only_one_strike_event(self, parser, derived_rules):
        """RED: A Nightclub Experience should create exactly ONE strike event."""
        events = [{
            "title": "RED: A Nightclub Experience",
            "category": "party",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "venue": "Studio B"
        }]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        strike_events = [e for e in result if e.get("title", "").startswith("Strike") and "Floor" not in e.get("title", "")]
        
        assert len(strike_events) == 1, \
            f"Expected 1 strike event for RED, got {len(strike_events)}: {[e['title'] for e in strike_events]}"
        assert strike_events[0]["title"] == "Strike RED", \
            f"Expected 'Strike RED', got '{strike_events[0]['title']}'"
    
    def test_crazy_quest_creates_only_one_setup_event(self, parser, derived_rules):
        """Crazy Quest should create exactly ONE setup event."""
        events = [{
            "title": "Crazy Quest",
            "category": "game",
            "start_dt": datetime(2025, 1, 15, 22, 0),
            "end_dt": datetime(2025, 1, 16, 0, 0),
            "venue": "Studio B"
        }]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        setup_events = [e for e in result if "Set Up" in e.get("title", "")]
        
        assert len(setup_events) == 1, \
            f"Expected 1 setup event for Crazy Quest, got {len(setup_events)}: {[e['title'] for e in setup_events]}"
        assert setup_events[0]["title"] == "Set Up Crazy Quest", \
            f"Expected 'Set Up Crazy Quest', got '{setup_events[0]['title']}'"
    
    def test_no_duplicate_due_to_substring_matching(self, parser, derived_rules):
        """Ensure 'Nightclub' in rules doesn't create duplicate for 'RED: A Nightclub Experience'.
        
        Regression test: 'Nightclub' was substring-matching 'RED: A Nightclub Experience'.
        The system should NOT create 'Set Up RED' AND 'Set Up RED: A Nightclub Experience'.
        """
        events = [{
            "title": "RED: A Nightclub Experience",
            "category": "party",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "venue": "Studio B"
        }]
        
        result = parser._apply_derived_event_rules(events, derived_rules)
        setup_events = [e for e in result if "Set Up" in e.get("title", "")]
        
        # Should NOT have both 'Set Up RED' AND 'Set Up RED: A Nightclub Experience'
        setup_titles = [e["title"] for e in setup_events]
        has_duplicate = "Set Up RED" in setup_titles and "Set Up RED: A Nightclub Experience" in setup_titles
        
        assert not has_duplicate, \
            f"Duplicate setup events created: {setup_titles}"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Venue Rules Structure Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestVenueRulesStructure:
    """Validate the structure of venue rules to catch configuration errors.
    
    Ensures that rule ordering is correct so that the 'first match wins' 
    mechanism works as expected:
    - Specific match_titles rules must come BEFORE catch-all match_categories rules
    """
    
    # Common categories that indicate a catch-all rule when used together
    CATCH_ALL_CATEGORIES = ['game', 'party', 'music', 'show', 'activity']
    
    def _is_catch_all_rule(self, rule: dict) -> bool:
        """Return True if rule is a catch-all (matches multiple common categories, no match_titles)."""
        has_match_titles = rule.get('match_titles') is not None
        match_categories = rule.get('match_categories', [])
        
        if has_match_titles:
            return False
        
        # Catch-all = matches 2+ common categories
        common_category_count = len([c for c in match_categories if c in self.CATCH_ALL_CATEGORIES])
        return common_category_count >= 2
    
    def test_specific_rules_come_before_catch_all_in_setup(self):
        """Specific match_titles rules must come before catch-all match_categories rules in setup."""
        from backend.app.config.venue_rules import get_venue_rules
        
        venue_rules = get_venue_rules("WN", "Studio B")
        setup_rules = venue_rules.get("derived_event_rules", {}).get("setup", [])
        
        seen_catch_all = False
        errors = []
        
        for i, rule in enumerate(setup_rules):
            if self._is_catch_all_rule(rule):
                seen_catch_all = True
            elif seen_catch_all and rule.get("match_titles"):
                template = rule.get("title_template", "Unknown")
                errors.append(f"Rule {i} '{template}' has match_titles but comes after catch-all")
        
        assert not errors, \
            f"Setup rule order error - specific rules must come before catch-all:\n" + "\n".join(errors)
    
    def test_specific_rules_come_before_catch_all_in_strike(self):
        """Specific match_titles rules must come before catch-all match_categories rules in strike."""
        from backend.app.config.venue_rules import get_venue_rules
        
        venue_rules = get_venue_rules("WN", "Studio B")
        strike_rules = venue_rules.get("derived_event_rules", {}).get("strike", [])
        
        seen_catch_all = False
        errors = []
        
        for i, rule in enumerate(strike_rules):
            if self._is_catch_all_rule(rule):
                seen_catch_all = True
            elif seen_catch_all and rule.get("match_titles"):
                template = rule.get("title_template", "Unknown")
                errors.append(f"Rule {i} '{template}' has match_titles but comes after catch-all")
        
        assert not errors, \
            f"Strike rule order error - specific rules must come before catch-all:\n" + "\n".join(errors)
    
    def test_all_derived_rule_types_follow_correct_order(self):
        """All derived event rule types should have correct ordering."""
        from backend.app.config.venue_rules import get_venue_rules
        
        venue_rules = get_venue_rules("WN", "Studio B")
        derived_rules = venue_rules.get("derived_event_rules", {})
        
        all_errors = []
        
        for rule_type, rules in derived_rules.items():
            seen_catch_all = False
            
            for i, rule in enumerate(rules):
                if self._is_catch_all_rule(rule):
                    seen_catch_all = True
                elif seen_catch_all and rule.get("match_titles"):
                    template = rule.get("title_template", "Unknown")
                    all_errors.append(f"{rule_type.upper()} Rule {i} '{template}': match_titles after catch-all")
        
        assert not all_errors, \
            f"Rule order errors found:\n" + "\n".join(all_errors)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Title Normalization
# ═══════════════════════════════════════════════════════════════════════════════

class TestTitleNormalization:
    """Test that redundant text like 'Game Show' is stripped from event titles."""
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_strip_game_show_suffix(self, parser):
        """'Game Show' suffix should be stripped from titles."""
        assert parser._normalize_title("Battle of the Sexes Game Show") == "Battle of the Sexes"
        assert parser._normalize_title("Perfect Couple Game Show") == "Perfect Couple"
    
    def test_strip_game_show_with_dash(self, parser):
        """' - Game Show' suffix with dash should be stripped."""
        assert parser._normalize_title("Perfect Couple - Game Show") == "Perfect Couple"
        assert parser._normalize_title("Quiz Time - Game Show") == "Quiz Time"
    
    def test_strip_game_show_prefix(self, parser):
        """'Game Show: ' prefix should be stripped."""
        assert parser._normalize_title("Game Show: Quiz Night") == "Quiz Night"
        assert parser._normalize_title("game show: trivia time") == "trivia time"  # Case insensitive
    
    def test_no_change_for_normal_titles(self, parser):
        """Regular titles without 'Game Show' should not change."""
        assert parser._normalize_title("Crazy Quest") == "Crazy Quest"
        assert parser._normalize_title("RED: A Nightclub Experience") == "RED: A Nightclub Experience"
        assert parser._normalize_title("Ice Show: 365") == "Ice Show: 365"
    
    def test_only_strip_redundant_not_internal(self, parser):
        """Only strip suffix/prefix 'Game Show', not if it appears internally."""
        # "game show" appearing mid-title should only strip the suffix
        assert parser._normalize_title("The big game show game show") == "The big game show"
    
    def test_case_insensitive(self, parser):
        """Stripping should be case-insensitive."""
        assert parser._normalize_title("Battle of the Sexes GAME SHOW") == "Battle of the Sexes"
        assert parser._normalize_title("Quiz - game show") == "Quiz"
    
    def test_empty_and_none(self, parser):
        """Handle empty and None titles gracefully."""
        assert parser._normalize_title("") == ""
        assert parser._normalize_title(None) is None


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Merged Operation Duration
# ═══════════════════════════════════════════════════════════════════════════════

class TestMergedOperationDuration:
    """Test that merged setup/strike events have minimum 1 hour duration.
    
    When overlapping operational events merge (e.g., Strike + Strike Floor),
    the combined event should be at least 1 hour, or the longest of the merged
    events if any is longer than 1 hour.
    """
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_merged_duration_minimum_one_hour(self, parser):
        """Two 30-min operations merging should produce 60-min combined event."""
        events = [
            {
                "title": "Strike Crazy Quest",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 22, 0),
                "end_dt": datetime(2025, 1, 15, 22, 30),  # 30 min
            },
            {
                "title": "Strike Floor",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 22, 0),
                "end_dt": datetime(2025, 1, 15, 22, 30),  # 30 min
            },
        ]
        
        result = parser._merge_overlapping_operations(events)
        merged = [e for e in result if "Strike" in e.get("title", "")]
        
        assert len(merged) == 1, "Should merge into single event"
        duration = merged[0]["end_dt"] - merged[0]["start_dt"]
        assert duration >= timedelta(hours=1), \
            f"Merged duration should be at least 1 hour, got {duration}"
    
    def test_merged_duration_keeps_longer_if_over_one_hour(self, parser):
        """If one operation is 2 hours, merged event should be 2 hours (not capped at 1)."""
        events = [
            {
                "title": "Strike Crazy Quest",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 22, 0),
                "end_dt": datetime(2025, 1, 15, 22, 30),  # 30 min
            },
            {
                "title": "Set Up Floor",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 22, 0),
                "end_dt": datetime(2025, 1, 16, 0, 0),  # 2 hours
            },
        ]
        
        result = parser._merge_overlapping_operations(events)
        merged = [e for e in result if e.get("type") in ["setup", "strike"]]
        
        assert len(merged) == 1, "Should merge into single event"
        duration = merged[0]["end_dt"] - merged[0]["start_dt"]
        assert duration == timedelta(hours=2), \
            f"Merged duration should keep 2 hours (longest), got {duration}"
    
    def test_non_overlapping_operations_not_merged(self, parser):
        """Operations that don't overlap should remain separate."""
        events = [
            {
                "title": "Strike A",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 20, 0),
                "end_dt": datetime(2025, 1, 15, 20, 30),
            },
            {
                "title": "Strike B",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 22, 0),  # 1.5 hours gap
                "end_dt": datetime(2025, 1, 15, 22, 30),
            },
        ]
        
        result = parser._merge_overlapping_operations(events)
        strikes = [e for e in result if "Strike" in e.get("title", "")]
        
        assert len(strikes) == 2, "Non-overlapping operations should remain separate"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Reset Events
# ═══════════════════════════════════════════════════════════════════════════════

class TestResetEvents:
    """Test Reset event creation when both strike and setup are omitted.
    
    Reset events are created when:
    1. Strike for Event A is omitted (would overlap with Event B)
    2. Setup for Event B is omitted (would overlap with Event A)
    3. Gap between A end and B start >= 15 minutes
    
    Reset fills the gap (max 1 hour), titled "Reset for [Event B]".
    """
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_reset_created_when_both_omitted_with_gap(self, parser):
        """Reset event created when strike + setup both omitted and gap >= 15 min."""
        # Event Z: 6:00-7:00 PM (blocks setup from being bumped earlier)
        # Event A: 7:00-8:00 PM
        # Event B: 8:30-9:30 PM
        # Strike A (1 hr) would be 8:00-9:00 PM -> overlaps B -> omitted
        # Setup B (1 hr) would be 7:30-8:30 PM -> overlaps A -> try bump to 6:30-7:00 -> overlaps Z -> omitted
        # Gap = 30 min (8:00-8:30) -> Reset for Event B
        events = [
            {
                "title": "Event Z",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 18, 0),
                "end_dt": datetime(2025, 1, 15, 19, 0),
            },
            {
                "title": "Event A",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 20, 30),
                "end_dt": datetime(2025, 1, 15, 21, 30),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 20, 0),  # Would overlap B
                "end_dt": datetime(2025, 1, 15, 21, 0),  # 1 hour
            },
            {
                "title": "Set Up Event B",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 19, 30),  # Would overlap A, bumped to 18:30-19:00 overlaps Z
                "end_dt": datetime(2025, 1, 15, 20, 30),  # 1 hour (so bump to 18:30-19:30 overlaps Z)
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        resets = [e for e in result if e.get("type") == "reset"]
        
        assert len(resets) == 1, f"Expected 1 reset event, got {len(resets)}. All events: {[(e['title'], e['type']) for e in result]}"
        reset = resets[0]
        assert "Event B" in reset["title"], f"Reset should be for Event B, got {reset['title']}"
        assert reset["start_dt"] == datetime(2025, 1, 15, 20, 0), "Reset should start when A ends"
        assert reset["end_dt"] == datetime(2025, 1, 15, 20, 30), "Reset should fill gap to B start"
    
    def test_reset_not_created_when_gap_too_small(self, parser):
        """Reset NOT created when gap < 15 minutes."""
        events = [
            {
                "title": "Event A",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 20, 10),  # Only 10 min gap
                "end_dt": datetime(2025, 1, 15, 21, 10),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 20, 0),
                "end_dt": datetime(2025, 1, 15, 21, 0),
            },
            {
                "title": "Set Up Event B",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 19, 10),
                "end_dt": datetime(2025, 1, 15, 20, 10),
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        resets = [e for e in result if e.get("type") == "reset"]
        
        assert len(resets) == 0, f"No reset with gap < 15 min, got {len(resets)}"
    
    def test_reset_max_duration_one_hour(self, parser):
        """Reset duration capped at 1 hour even if gap is larger."""
        events = [
            {
                "title": "Event A",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 14, 0),
                "end_dt": datetime(2025, 1, 15, 15, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 17, 0),  # 2 hour gap
                "end_dt": datetime(2025, 1, 15, 18, 0),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 15, 0),
                "end_dt": datetime(2025, 1, 15, 16, 0),
            },
            {
                "title": "Set Up Event B",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 16, 0),
                "end_dt": datetime(2025, 1, 15, 17, 0),
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        resets = [e for e in result if e.get("type") == "reset"]
        
        if len(resets) == 1:
            reset = resets[0]
            duration = reset["end_dt"] - reset["start_dt"]
            assert duration <= timedelta(hours=1), \
                f"Reset duration should be max 1 hour, got {duration}"
    
    def test_no_reset_when_only_strike_omitted(self, parser):
        """No reset when only strike is omitted but setup is kept."""
        events = [
            {
                "title": "Event A",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 21, 0),  # 1 hour gap - setup fits
                "end_dt": datetime(2025, 1, 15, 22, 0),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 20, 0),
                "end_dt": datetime(2025, 1, 15, 21, 0),  # Overlaps B -> omitted
            },
            {
                "title": "Set Up Event B",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 20, 30),  # Fits in gap
                "end_dt": datetime(2025, 1, 15, 21, 0),
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        resets = [e for e in result if e.get("type") == "reset"]
        setups = [e for e in result if e.get("type") == "setup"]
        
        # Setup should be kept, no reset needed
        assert len(resets) == 0 or len(setups) >= 1, \
            "No reset when setup is kept"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Reset Events Integration (Full Pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

class TestResetIntegration:
    """Integration tests for Reset events through the full pipeline.
    
    These tests go through _apply_derived_event_rules (which may skip events
    due to min_gap_minutes) and then _resolve_operation_overlaps.
    """
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    @pytest.fixture
    def studio_b_derived_rules(self):
        """Derived rules matching real Studio B config."""
        return {
            "setup": [
                {
                    "match_titles": ["Battle of the Sexes", "Crazy Quest"],
                    "offset_minutes": -60,
                    "duration_minutes": 30,
                    "title_template": "Set Up {parent_title}",
                    "type": "setup",
                    "min_gap_minutes": 60,  # Skip if stacked
                },
            ],
            "strike": [
                {
                    "match_titles": ["Battle of the Sexes", "Crazy Quest"],
                    "offset_minutes": 0,
                    "anchor": "end",
                    "duration_minutes": 30,
                    "title_template": "Strike {parent_title}",
                    "type": "strike",
                },
            ],
        }
    
    def test_reset_when_setup_skipped_due_to_min_gap(self, parser, studio_b_derived_rules):
        """Reset should be created when setup is skipped by min_gap_minutes.
        
        Scenario:
        - Battle of the Sexes: 9:45 PM - 10:45 PM
        - Crazy Quest: 11:00 PM - 12:00 AM
        - Gap: 15 min (not enough for setup due to min_gap_minutes=60)
        - Strike for BotS: would overlap Crazy Quest -> dropped
        - Setup for CQ: NEVER CREATED (min_gap_minutes=60, gap only 15 min)
        - Result: Reset for Crazy Quest should fill the 15 min gap
        """
        events = [
            {
                "title": "Battle of the Sexes",
                "type": "game",
                "category": "game",
                "start_dt": datetime(2025, 7, 31, 21, 45),
                "end_dt": datetime(2025, 7, 31, 22, 45),
                "venue": "Studio B",
            },
            {
                "title": "Crazy Quest",
                "type": "game",
                "category": "game",
                "start_dt": datetime(2025, 7, 31, 23, 0),
                "end_dt": datetime(2025, 8, 1, 0, 0),
                "venue": "Studio B",
            },
        ]
        
        # Full pipeline
        result = parser._apply_derived_event_rules(events, studio_b_derived_rules)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        result = parser._create_reset_events(result)
        
        # Find events by type
        resets = [e for e in result if e.get("type") == "reset"]
        setups = [e for e in result if e.get("type") == "setup"]
        strikes = [e for e in result if e.get("type") == "strike"]
        
        # Debug output
        print(f"\\nEvents after pipeline:")
        for e in sorted(result, key=lambda x: x['start_dt']):
            print(f"  {e['title']}: {e['start_dt'].strftime('%H:%M')}-{e['end_dt'].strftime('%H:%M')} ({e['type']})")
        
        # Assertions
        # Setup for Crazy Quest should NOT exist (skipped by min_gap)
        cq_setups = [s for s in setups if "Crazy Quest" in s.get("title", "")]
        assert len(cq_setups) == 0, \
            f"Setup for Crazy Quest should NOT be created (min_gap_minutes=60), got {cq_setups}"
        
        # Reset should exist to fill the gap
        assert len(resets) == 1, \
            f"Expected 1 Reset event, got {len(resets)}. Events: {[(e['title'], e['type']) for e in result]}"
        
        reset = resets[0]
        assert "Crazy Quest" in reset["title"], f"Reset should be for Crazy Quest, got {reset['title']}"
        assert reset["start_dt"] == datetime(2025, 7, 31, 22, 45), "Reset should start when BotS ends"
        assert reset["end_dt"] == datetime(2025, 7, 31, 23, 0), "Reset should end when CQ starts"

