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
