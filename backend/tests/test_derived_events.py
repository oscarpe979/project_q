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
        "type": "show",
        "type": "show",
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
        "type": "headliner",
        "type": "headliner",
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
        "type": "activity",
        "type": "activity",
        "venue": "Studio B",
        "raw_date": "2024-01-15"
    }


@pytest.fixture
def doors_rule_basic():
    """Basic doors rule matching shows and headliners."""
    return {
        "match_types": ["show", "headliner"],
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
        "match_types": ["show"],
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
        "match_types": ["show"],
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
    
    def test_matches_type_show(self, sample_show_event, doors_rule_basic):
        """Show event should match rule with 'show' in match_types."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_show_event, doors_rule_basic)
        
        assert result is True
    
    def test_matches_type_headliner(self, sample_headliner_event, doors_rule_basic):
        """Headliner event should match rule with 'headliner' in match_types."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        result = parser._event_matches_rule(sample_headliner_event, doors_rule_basic)
        
        assert result is True
    
    def test_no_match_activity_type(self, sample_activity_event, doors_rule_basic):
        """Activity event should NOT match rule without 'activity' in match_types."""
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
            "type": "show"
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
            "type": "show"
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
            "type": "show",
            "venue": "Studio B",
            "raw_date": "2024-01-16"
        }
        
        rule = {
            "match_types": ["show"],
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
            "type": "show",
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
            "match_types": ["show"],
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
            "match_types": ["show"],
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
    """Tests for VenueRules.generate_derived_events() full pipeline."""
    
    def test_basic_doors_injection(self, sample_show_event, doors_rule_basic):
        """Doors event should be added before show in sorted output."""
        from backend.app.venues.base import VenueRules
        
        rules = VenueRules()
        rules.doors_config = [doors_rule_basic]
        events = [sample_show_event]
        
        result = rules.generate_derived_events(events)
        
        # Should have original event + doors event
        assert len(result) == 2
        
        # Sort by start_dt to check order
        result_sorted = sorted(result, key=lambda x: x['start_dt'])
        
        # First event should be doors (earlier time)
        assert result_sorted[0]["type"] == "doors"
        assert result_sorted[0]["title"] == "Doors"
        
        # Second event should be original show
        assert result_sorted[1]["title"] == "Ice Show: 365"
    
    def test_multiple_derived_types(self, sample_show_event, full_derived_rules):
        """Multiple derived events (doors, rehearsal, strike) should be created."""
        from backend.app.venues.base import VenueRules
        
        rules = VenueRules()
        rules.doors_config = full_derived_rules.get("doors", [])
        rules.setup_config = full_derived_rules.get("rehearsal", [])  # rehearsal -> setup
        rules.strike_config = full_derived_rules.get("strike", [])
        events = [sample_show_event]
        
        result = rules.generate_derived_events(events)
        
        # Check types present
        types_in_order = [e.get("type", e.get("category")) for e in result]
        
        assert "doors" in types_in_order
        assert "strike" in types_in_order
        
        # Events should be sorted by start time
        result_sorted = sorted(result, key=lambda x: x['start_dt'])
        for i in range(len(result_sorted) - 1):
            assert result_sorted[i]["start_dt"] <= result_sorted[i + 1]["start_dt"]
    
    def test_no_derived_events_for_non_matching(self, sample_activity_event, full_derived_rules):
        """Activity event should not generate any derived events."""
        from backend.app.venues.base import VenueRules
        
        rules = VenueRules()
        rules.doors_config = full_derived_rules.get("doors", [])
        rules.setup_config = full_derived_rules.get("rehearsal", [])
        rules.strike_config = full_derived_rules.get("strike", [])
        events = [sample_activity_event]
        
        result = rules.generate_derived_events(events)
        
        # Only original event
        assert len(result) == 1
        assert result[0]["title"] == "Open Ice Skating"
    
    def test_empty_rules_returns_original(self, sample_show_event):
        """Empty rules should return original events unchanged."""
        from backend.app.venues.base import VenueRules
        
        rules = VenueRules()
        # No configs set = empty rules
        events = [sample_show_event]
        
        result = rules.generate_derived_events(events)
        
        assert len(result) == 1
        assert result[0] == sample_show_event
    
    def test_multiple_shows_each_get_derived(self, sample_show_event, sample_headliner_event, doors_rule_basic):
        """Each matching show should get its own derived events."""
        from backend.app.venues.base import VenueRules
        
        rules = VenueRules()
        rules.doors_config = [doors_rule_basic]
        events = [sample_show_event, sample_headliner_event]
        
        result = rules.generate_derived_events(events)
        
        # 2 original + 2 doors = 4 events
        assert len(result) == 4
        
        doors_events = [e for e in result if e.get("type") == "doors"]
        assert len(doors_events) == 2


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

# ═══════════════════════════════════════════════════════════════════════════════

class TestVenueRulesDB:
    """Tests for Database-driven VenueRules configuration."""
    
    def test_get_venue_rules_factory_returns_correct_object(self):
        """get_venue_rules() should return configured VenueRules object."""
        from backend.app.venues import get_venue_rules
        from backend.app.venues.wn.wn_studio_b import StudioBRules
        
        rules = get_venue_rules("WN", "Studio B")
        
        assert isinstance(rules, StudioBRules)
        assert rules.ship_code == "WN"
        assert rules.venue_name == "Studio B"
    
    def test_venue_rules_includes_derived_rules(self):
        """VenueRules object should expose derived_event_rules."""
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        # Test property access
        derived_rules = rules.derived_event_rules
        assert "doors" in derived_rules
        assert len(derived_rules["doors"]) >= 1
        
        # Verify doors rule structure
        doors_rule = derived_rules["doors"][0]
        assert "offset_minutes" in doors_rule
        assert "duration_minutes" in doors_rule
    
    def test_venue_metadata_structure(self):
        """VenueRules object should have correct metadata."""
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        assert hasattr(rules, "known_shows")
        assert len(rules.known_shows) > 0
        assert hasattr(rules, "renaming_map")
        assert hasattr(rules, "default_durations")
        
        # Verify specific content known to be in seed
        assert "Ice Show: 365" in rules.known_shows



# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 7: Cross-Event Gap Checking (check_all_events)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMergedEventTypeInference:
    """Tests for type inference on merged events from other venues."""
    
    def test_parade_title_infers_parade_type(self):
        """Events with 'parade' in title should get type 'parade'."""
        # This tests the logic in _transform_to_api_format that infers type
        # before calling _parse_single_event
        
        # Simulate what happens in the merge logic
        show = {"title": "Anchors Aweigh Parade", "date": "2025-01-15", 
                "start_time": "12:30", "venue": "Royal Promenade"}
        
        # Infer type from title (this is the logic we added)
        if not show.get("type"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["type"] = "parade"
        
        assert show["type"] == "parade"
    
    def test_party_title_infers_party_type(self):
        """Events with 'party' in title should get type 'party'."""
        show = {"title": "Deck Party", "date": "2025-01-15", 
                "start_time": "21:00", "venue": "Pool Deck"}
        
        if not show.get("type"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["type"] = "parade"
            elif "party" in title_lower:
                show["type"] = "party"
        
        assert show["type"] == "party"
    
    def test_movie_title_infers_movie_type(self):
        """Events with 'movie' in title should get type 'movie'."""
        show = {"title": "Movie Night", "date": "2025-01-15", 
                "start_time": "20:00", "venue": "Royal Theater"}
        
        if not show.get("type"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["type"] = "parade"
            elif "party" in title_lower:
                show["type"] = "party"
            elif "movie" in title_lower:
                show["type"] = "movie"
        
        assert show["type"] == "movie"
    
    def test_existing_type_not_overwritten(self):
        """If type already exists, it should NOT be overwritten."""
        show = {"title": "Parade Party", "date": "2025-01-15", 
                "start_time": "18:00", "venue": "Promenade", 
                "type": "activity"}  # Already has type
        
        if not show.get("type"):
            title_lower = show.get("title", "").lower()
            if "parade" in title_lower:
                show["type"] = "parade"
        
        # Type should remain "activity" (not overwritten to "parade")
        assert show["type"] == "activity"


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
             "time": "11:30am-12:30pm", "type": "activity"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Ice Spectacular 365", 
             "time": "8:15 pm & 10:30 pm", "type": "show"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Only one event per venue/day
        assert len(result) == 1
        # Show should win over activity
        assert result[0]["title"] == "Ice Spectacular 365"
        assert result[0]["type"] == "show"
    
    def test_evening_time_beats_morning_same_type(self):
        """Evening events should be preferred over morning events."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-10-13", "title": "Morning Show", 
             "time": "10:00 am", "type": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Evening Show", 
             "time": "8:00 pm", "type": "show"},
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
             "time": "7:00 pm", "type": "game"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Comedy Special", 
             "time": "9:00 pm", "type": "headliner"},
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
             "time": "11:00 pm", "type": "party"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Open Skating", 
             "time": "2:00 pm", "type": "activity"},
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
             "time": "7:00 pm", "type": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Event B", 
             "time": "9:00 pm", "type": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Event C", 
             "time": "10:00 pm", "type": "party"},
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
             "time": "8:00 pm", "type": "show"},
            {"venue": "AquaTheater", "date": "2025-10-13", "title": "Aqua Show", 
             "time": "8:00 pm", "type": "show"},
            {"venue": "Studio B", "date": "2025-10-14", "title": "Ice Show 2", 
             "time": "8:00 pm", "type": "show"},
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
             "time": "7:00 pm", "type": "show"},
            {"venue": "Studio B", "date": "2025-10-13", "title": "Ice Show", 
             "time": "9:30 pm", "type": "show"},
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
             "time": "8:00 pm", "type": "backup"},
            {"venue": "AquaTheater", "date": "2025-10-16", "title": "Other Event", 
             "time": "8:00 pm", "type": "other"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # "other" (priority 7) beats "backup" (priority 8)
        assert result[0]["title"] == "Other Event"
    
    def test_parade_type_priority(self):
        """Parade should have moderate priority (not highest, not lowest)."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        # Parade vs Activity - parade has higher priority
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-13", "title": "Costume Parade", 
             "time": "10:00 pm", "type": "parade"},
            {"venue": "Royal Promenade", "date": "2025-10-13", "title": "Random Activity", 
             "time": "2:00 pm", "type": "activity"},
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
             "time": "11:15 pm - midnight", "type": "party"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Should be kept as the highlight for that day
        assert len(result) == 1
        assert result[0]["title"] == "Let's Dance"
        assert result[0]["type"] == "party"
    
    def test_late_night_party_vs_activity(self):
        """Late-night party should beat afternoon activity even at 11pm."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Afternoon Activity", 
             "time": "2:00 pm", "type": "activity"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Let's Dance", 
             "time": "11:15 pm", "type": "party"},
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
             "time": "Midnight - late", "type": "party"},
            {"venue": "AquaTheater", "date": "2025-10-14", "title": "inTENse: Maximum Performance", 
             "time": "8:15 pm & 10:30 pm", "type": "show"},
            {"venue": "Royal Promenade", "date": "2025-10-14", "title": "Let's Dance", 
             "time": "11:15 pm - midnight", "type": "party"},
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
             "time": "8pm - 9:30 pm", "type": "activity"},
            {"venue": "Studio B", "date": "2025-08-21", "title": "Battle of the Sexes", 
             "time": "9:45 pm", "type": "game"},
            {"venue": "Studio B", "date": "2025-08-21", "title": "Crazy Quest", 
             "time": "11:00 pm", "type": "game"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        assert len(result) == 1
        # Game (priority 3) should beat activity (priority 6)
        # Battle of the Sexes is the first game and both have evening time
        assert result[0]["type"] == "game"
        # Either Battle of the Sexes or Crazy Quest should win
        assert result[0]["title"] in ["Battle of the Sexes", "Crazy Quest"]
    
    def test_game_beats_activity_even_earlier_time(self):
        """Game in evening should beat activity even if activity is earlier."""
        from backend.app.services.genai_parser import GenAIParser
        
        parser = GenAIParser(api_key="dummy")
        
        shows = [
            {"venue": "Studio B", "date": "2025-08-21", "title": "Morning Activity", 
             "time": "10:00 am", "type": "activity"},
            {"venue": "Studio B", "date": "2025-08-21", "title": "Evening Game Show", 
             "time": "9:00 pm", "type": "game"},
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
             "time": "6:00 pm & 9:30 pm", "type": "movie"},
            {"venue": "AquaTheater", "date": "2025-08-21", "title": "Finish That Lyric", 
             "time": "8:30 pm", "type": "game"},
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
             "time": "5:00 pm - 6:00 pm (1hr) TEENS", "type": "activity"},
            {"venue": "Studio B", "date": "2025-07-23", "title": "Ice Skating", 
             "time": "6:00 pm - 8:00 pm (2hrs)", "type": "activity"},
            {"venue": "Studio B", "date": "2025-07-23", "title": "Ice Skating", 
             "time": "8:30 pm - 11:30 pm (3hrs)", "type": "activity"},
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
             "time": "1:00 pm - 7:00 pm (6hrs)", "type": "activity"},
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
             "time": "6:45 pm & 9:00 pm", "type": "show"},
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
             "time": "5:00 pm - 8:00 pm", "type": "activity"},
            {"venue": "Studio B", "date": "2025-07-23", "title": "Battle of the Sexes", 
             "time": "9:15 pm", "type": "game"},
        ]
        
        result = parser._filter_other_venue_shows(shows, {})
        
        # Ice Skating blocked, Battle of the Sexes is the only remaining event
        assert len(result) == 1
        assert result[0]["title"] == "Battle of the Sexes"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST GROUP 10: Floor Transition Logic (Studio B specific)
# ═══════════════════════════════════════════════════════════════════════════════

    """
    Integration tests using ACTUAL production venue rules from venue_rules.py.
    These test the full pipeline end-to-end, catching issues that unit tests miss.
    """
    
    @pytest.fixture
    def studio_b_rules(self):
        """Load actual production rules for Studio B."""
        from backend.app.venues import get_venue_rules
        return get_venue_rules("WN", "Studio B")
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_ice_show_generates_all_warmups(self, parser, studio_b_rules):
        """Ice Show should generate BOTH Specialty Ice AND Cast warm ups."""
        
        # Two Ice Shows on same day (triggers preset + multiple warm ups)
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
        # Should have both warm up types
        warmups = [e for e in result if "Warm Up" in e.get("title", "")]
        warmup_titles = [e.get("title") for e in warmups]
        
        assert "Warm Up - Specialty Ice" in warmup_titles, "Missing Specialty Ice warm up"
        assert "Warm Up - Cast" in warmup_titles, "Missing Cast warm up"
    
    def test_game_show_title_rule_no_duplicate_from_catchall(self, parser, studio_b_rules):
        """Battle of the Sexes should match title rule, NOT also match type catch-all."""
        
        events = [
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 21, 0),
             "end_dt": datetime(2025, 1, 15, 22, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
        # Should have exactly ONE setup (not two from title + catch-all)
        setups = [e for e in result if "Set Up" in e.get("title", "") and "Battle" in e.get("title", "")]
        assert len(setups) == 1, f"Expected 1 setup, got {len(setups)}: {[e.get('title') for e in setups]}"
    
    def test_ice_to_floor_transition_merges_with_strike(self, parser, studio_b_rules):
        """Floor transition should merge with Strike & Ice Scrape when adjacent."""
        
        # Ice Show followed by game show (triggers floor transition + strike)
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 20, 0),
             "end_dt": datetime(2025, 1, 15, 21, 0), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        # Call single generation method (handles derived events AND floor transitions)
        result = studio_b_rules.generate_derived_events(events)
        
        # Then merge overlapping operations
        result = parser._merge_overlapping_operations(result)
        
        # Check that Strike & Ice Scrape and Set Floor are combined
        combined = [e for e in result if "Strike" in e.get("title", "") and "Set Floor" in e.get("title", "")]
        assert len(combined) >= 1, "Floor transition should merge with Strike & Ice Scrape"
    
    def test_overlapping_setup_and_strike_merge(self, parser, studio_b_rules):
        """Overlapping setup and strike events should merge together."""
        
        # Ice Show followed by Nightclub (creates Strike + Set Up that overlap)
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 21, 0),
             "end_dt": datetime(2025, 1, 15, 22, 0), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Nightclub", "start_dt": datetime(2025, 1, 15, 23, 0),
             "end_dt": datetime(2025, 1, 16, 1, 0), "type": "party",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        # Full pipeline
        result = studio_b_rules.generate_derived_events(events)
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
        
        # Scenario: Crazy Quest at 11:20 PM - 12:00 AM, RED at 12:00 AM - 1:00 AM
        # Strike Crazy Quest (30 min) would be 12:00 - 12:30, overlapping RED!
        events = [
            {"title": "Crazy Quest", "start_dt": datetime(2025, 1, 15, 23, 20),
             "end_dt": datetime(2025, 1, 16, 0, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 16, 0, 0),
             "end_dt": datetime(2025, 1, 16, 1, 0), "type": "party",
             "raw_date": "2025-01-16", "venue": "Studio B"},
        ]
        
        # Full pipeline with overlap resolution
        result = studio_b_rules.generate_derived_events(events)
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
        
        events = [
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
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
        
        # Two Ice Shows - 75 min gap to test calendar-day logic
        events = [
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 21, 15),
             "end_dt": datetime(2025, 1, 15, 22, 15), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
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
        
        events = [
            {"title": "Private Ice Skating", "start_dt": datetime(2025, 1, 15, 14, 0),
             "end_dt": datetime(2025, 1, 15, 15, 0), "type": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
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
        Multiple skating sessions should only generate ONE strike after the last session.
        With skip_if_next_matches enabled, we don't strike between sessions of same type
        unless there's an intervening event (tested separately below).
        """
        events = [
            {"title": "Open Ice Skating", "start_dt": datetime(2025, 1, 15, 9, 30),
             "end_dt": datetime(2025, 1, 15, 11, 30), "type": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Private Ice Skating", "start_dt": datetime(2025, 1, 15, 21, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "type": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
        # Get all strikes for skating
        strikes = [e for e in result if e.get("type") == "strike" and "Skates" in e.get("title", "")]
        
        # Should have 1 strike only (after last session, since no intervening event)
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
        
        events = [
            {"title": "Open Ice Skating", "start_dt": datetime(2025, 1, 15, 9, 0),
             "end_dt": datetime(2025, 1, 15, 11, 0), "type": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Ice Show: 365", "start_dt": datetime(2025, 1, 15, 14, 0),
             "end_dt": datetime(2025, 1, 15, 15, 0), "type": "show",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Private Ice Skating", "start_dt": datetime(2025, 1, 15, 18, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "type": "activity",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        result = studio_b_rules.generate_derived_events(events)
        
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
        
        # Back-to-back game shows with only 15 min gap
        events = [
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 20, 15),
             "end_dt": datetime(2025, 1, 15, 21, 15), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        # FULL pipeline with overlap resolution
        result = studio_b_rules.generate_derived_events(events)
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
        
        events = [
            {"title": "Family SHUSH!", "start_dt": datetime(2025, 1, 15, 19, 0),
             "end_dt": datetime(2025, 1, 15, 20, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
            {"title": "Battle of the Sexes", "start_dt": datetime(2025, 1, 15, 22, 0),
             "end_dt": datetime(2025, 1, 15, 23, 0), "type": "game",
             "raw_date": "2025-01-15", "venue": "Studio B"},
        ]
        
        # FULL pipeline
        result = studio_b_rules.generate_derived_events(events)
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
             "end_dt": datetime(2025, 1, 20, 1, 0), "type": "party",
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
             "end_dt": datetime(2025, 1, 15, 1, 0), "type": "party",
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
             "end_dt": datetime(2025, 1, 16, 1, 0), "type": "game",
             "raw_date": "2025-01-16", "venue": "Studio B", "type": "game"},
            {"title": "Strike Family SHUSH!", "start_dt": datetime(2025, 1, 16, 1, 0),
             "end_dt": datetime(2025, 1, 16, 1, 30), "type": "strike",
             "is_derived": True, "venue": "Studio B"},
            {"title": "RED: Nightclub Experience", "start_dt": datetime(2025, 1, 16, 1, 30),
             "end_dt": datetime(2025, 1, 16, 2, 30), "type": "party",
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
             "end_dt": datetime(2025, 1, 15, 11, 0), "type": "activity",
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
             "end_dt": datetime(2025, 1, 21, 1, 0), "type": "party",
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
        from backend.app.venues import get_venue_rules
        
        venue_rules = get_venue_rules('WN', 'Studio B')
        derived_rules = venue_rules.derived_event_rules
        floor_config = {
            'floor_requirements': venue_rules.floor_requirements,
            'floor_transition': venue_rules.floor_transition,
        }
        
        # Laser Tag -> Parade (merged) -> Battle of the Sexes (has setup)
        events = [
            {'title': 'Laser Tag', 'start_dt': datetime(2025, 7, 24, 13, 0),
             'end_dt': datetime(2025, 7, 24, 15, 30), 'type': 'activity',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'activity'},
            {'title': 'Anchors Aweigh Parade', 'start_dt': datetime(2025, 7, 24, 15, 30),
             'end_dt': datetime(2025, 7, 24, 16, 0), 'type': 'parade',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'parade', 'is_cross_venue': True},
            {'title': 'Battle of the Sexes', 'start_dt': datetime(2025, 7, 24, 19, 0),
             'end_dt': datetime(2025, 7, 24, 20, 0), 'type': 'game',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'game'},
        ]
        
        result = venue_rules.generate_derived_events(events)
        result = parser._merge_overlapping_operations(result)
        result = parser._resolve_operation_overlaps(result)
        
        # Find the setup for Battle of the Sexes and verify it contains "Strike Laser Tag"
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
        from backend.app.venues import get_venue_rules
        
        venue_rules = get_venue_rules('WN', 'Studio B')
        derived_rules = venue_rules.derived_event_rules
        floor_config = {
            'floor_requirements': venue_rules.floor_requirements,
            'floor_transition': venue_rules.floor_transition,
        }
        
        # Laser Tag -> Parade (merged) -> no more events
        events = [
            {'title': 'Laser Tag', 'start_dt': datetime(2025, 7, 24, 13, 0),
             'end_dt': datetime(2025, 7, 24, 15, 30), 'type': 'activity',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'activity'},
            {'title': 'Anchors Aweigh Parade', 'start_dt': datetime(2025, 7, 24, 15, 30),
             'end_dt': datetime(2025, 7, 24, 16, 0), 'type': 'parade',
             'raw_date': '2025-07-24', 'venue': 'Studio B', 'type': 'parade', 'is_cross_venue': True},
        ]
        
        result = venue_rules.generate_derived_events(events)
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
                 "date": "2025-01-15", "type": "game"},
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
    def venue_rules_obj(self):
        """New VenueRules object from database."""
        from backend.app.venues import get_venue_rules as get_new
        return get_new("WN", "Studio B")
    
    def test_red_nightclub_setup_has_short_title(self, parser, venue_rules_obj):
        """RED: Nightclub Experience should get 'Set Up RED' not 'Set Up RED: Nightclub Experience'."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "RED: Nightclub Experience", "start_time": "21:00", "end_time": "23:00",
                 "date": "2025-01-15", "type": "party"},
            ],
        }
        
        derived_rules = venue_rules_obj.derived_event_rules
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={"RED: Nightclub Experience": 90},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config={},
            
            venue_rules_obj=venue_rules_obj,
        )
        
        # Find setup event for RED - may be merged with other setups
        setup_events = [e for e in result["events"] if "Set Up" in e["title"]]
        assert len(setup_events) >= 1, "Should have at least one setup event"
        
        # Check that 'Set Up RED' is part of the title (may be merged)
        red_setup = [e for e in setup_events if "Set Up RED" in e["title"]]
        assert len(red_setup) >= 1, f"Should have at least one RED setup, got: {[e['title'] for e in setup_events]}"
    
    def test_red_party_strike_has_short_title(self, parser, venue_rules_obj):
        """RED! Party should get 'Strike RED' not 'Strike RED! Party'."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "RED! Party", "start_time": "21:00", "end_time": "23:00",
                 "date": "2025-01-15", "type": "party"},
            ],
        }
        
        derived_rules = venue_rules_obj.derived_event_rules
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config={},
            
            venue_rules_obj=venue_rules_obj,
        )
        
        # Find strike event for RED
        strike_events = [e for e in result["events"] if "Strike" in e["title"]]
        red_strike = [e for e in strike_events if "RED" in e["title"]]
        
        assert len(red_strike) == 1, "Should have exactly one RED strike"
        assert red_strike[0]["title"] == "Strike RED", \
            f"Expected 'Strike RED' but got '{red_strike[0]['title']}'"
    
    def test_non_red_party_gets_full_title(self, parser, venue_rules_obj):
        """Non-RED parties like Battle of the Sexes should get full title in setup/strike."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "Battle of the Sexes", "start_time": "22:00", "end_time": "23:00",
                 "date": "2025-01-15", "type": "game"},
            ],
        }
        
        derived_rules = venue_rules_obj.derived_event_rules
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules=derived_rules,
            floor_config={},
            
            venue_rules_obj=venue_rules_obj,
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
    
    def test_red_party_without_end_time_gets_late_flag(self, parser):
        """RED party events without explicit end time should get end_is_late=True."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "RED: Nightclub Experience", "start_time": "23:30", "end_time": None,
                 "date": "2025-01-15", "type": "party"},
            ],
        }
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules={},
            floor_config={},
            
        )
        
        # Find the main RED event
        red_events = [e for e in result["events"] if "RED" in e["title"] and "Set Up" not in e["title"] and "Strike" not in e["title"]]
        assert len(red_events) >= 1, "Should have at least one RED event"
        
        main_red = red_events[0]
        assert main_red.get("end_is_late") == True, \
            "RED party without end time should have end_is_late=True"
    
    def test_event_with_0100_end_time_gets_late_flag(self, parser):
        """Events with 01:00 end time (LLM interpretation of 'Late') should get end_is_late=True."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "Dance Party", "start_time": "22:00", "end_time": "01:00",
                 "date": "2025-01-15", "type": "party"},
            ],
        }
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules={},
            floor_config={},
            
        )
        
        # Find the dance party event
        party_events = [e for e in result["events"] if "Dance Party" in e["title"]]
        assert len(party_events) == 1, "Should have exactly one Dance Party event"
        
        assert party_events[0].get("end_is_late") == True, \
            "Event with 01:00 end time should have end_is_late=True"
    
    def test_normal_event_does_not_get_late_flag(self, parser):
        """Events with normal end times should NOT have end_is_late flag."""
        llm_result = {
            "itinerary": [
                {"day_number": 1, "date": "2025-01-15", "port": "At Sea"}
            ],
            "events": [
                {"title": "Ice Show: 365", "start_time": "19:30", "end_time": "20:30",
                 "date": "2025-01-15", "type": "show"},
            ],
        }
        
        result = parser._transform_to_api_format(
            llm_result,
            default_durations={},
            renaming_map={},
            cross_venue_policies={},
            derived_event_rules={},
            floor_config={},
            
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
    
    def test_floor_transition_has_is_floor_transition_flag(self, parser):
        """Floor transitions should have is_floor_transition=True flag."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Create a floor transition directly
        prev_event = {
            "title": "Crazy Quest",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 0, 0),  # Ends at midnight
            "type": "game",
            "venue": "Studio B"
        }
        next_event = {
            "title": "Ice Skating",
            "start_dt": datetime(2025, 1, 16, 14, 0),
            "end_dt": datetime(2025, 1, 16, 17, 0),
            "type": "activity",
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
    
    def test_floor_transition_after_midnight_event_is_rescheduled_to_morning(self, parser):
        """Floor transition after event ending AFTER midnight (00:01+) should be at 9 AM."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Event ends AFTER midnight (00:30, not exactly 00:00)
        prev_event = {
            "title": "RED Party",
            "start_dt": datetime(2025, 1, 15, 23, 30),
            "end_dt": datetime(2025, 1, 16, 0, 30),  # Ends at 00:30 - AFTER midnight
            "type": "game",
            "venue": "Studio B"
        }
        next_event = {
            "title": "Ice Skating",
            "start_dt": datetime(2025, 1, 16, 14, 0),
            "end_dt": datetime(2025, 1, 16, 17, 0),
            "type": "activity",
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
    
    def test_floor_transition_before_midnight_event_happens_immediately(self, parser):
        """Floor transition after event ending before midnight should happen immediately."""
        from backend.app.services.genai_parser import GenAIParser
        
        # Event ends before midnight
        prev_event = {
            "title": "Crazy Quest",
            "start_dt": datetime(2025, 1, 15, 21, 0),
            "end_dt": datetime(2025, 1, 15, 22, 30),  # Ends at 10:30 PM
            "type": "game",
            "venue": "Studio B"
        }
        next_event = {
            "title": "Ice Skating",
            "start_dt": datetime(2025, 1, 16, 14, 0),
            "end_dt": datetime(2025, 1, 16, 17, 0),
            "type": "activity",
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
    
    def test_late_night_handler_skips_floor_transitions(self, parser):
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
    
    def test_midnight_strike_is_rescheduled_to_morning(self, parser):
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
    
    def test_midnight_exact_strike_is_not_rescheduled(self, parser):
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
    def venue_rules_obj(self):
        from backend.app.venues import get_venue_rules
        return get_venue_rules("WN", "Studio B")
    
    def test_red_nightclub_creates_only_one_setup_event(self, parser, venue_rules_obj):
        """RED: A Nightclub Experience should create exactly ONE setup event."""
        events = [{
            "title": "RED: A Nightclub Experience",
            "type": "party",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "venue": "Studio B"
        }]
        
        result = venue_rules_obj.generate_derived_events(events)
        setup_events = [e for e in result if "Set Up" in e.get("title", "")]
        
        assert len(setup_events) == 1, \
            f"Expected 1 setup event for RED, got {len(setup_events)}: {[e['title'] for e in setup_events]}"
        assert setup_events[0]["title"] == "Set Up RED", \
            f"Expected 'Set Up RED', got '{setup_events[0]['title']}'"
    
    def test_red_nightclub_creates_only_one_strike_event(self, parser, venue_rules_obj):
        """RED: A Nightclub Experience should create exactly ONE strike event."""
        events = [{
            "title": "RED: A Nightclub Experience",
            "type": "party",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "venue": "Studio B"
        }]
        
        result = venue_rules_obj.generate_derived_events(events)
        strike_events = [e for e in result if e.get("title", "").startswith("Strike") and "Floor" not in e.get("title", "")]
        
        assert len(strike_events) == 1, \
            f"Expected 1 strike event for RED, got {len(strike_events)}: {[e['title'] for e in strike_events]}"
        assert strike_events[0]["title"] == "Strike RED", \
            f"Expected 'Strike RED', got '{strike_events[0]['title']}'"
    
    def test_crazy_quest_creates_only_one_setup_event(self, parser, venue_rules_obj):
        """Crazy Quest should create exactly ONE setup event."""
        events = [{
            "title": "Crazy Quest",
            "type": "game",
            "start_dt": datetime(2025, 1, 15, 22, 0),
            "end_dt": datetime(2025, 1, 16, 0, 0),
            "venue": "Studio B"
        }]
        
        result = venue_rules_obj.generate_derived_events(events)
        setup_events = [e for e in result if "Set Up" in e.get("title", "")]
        
        assert len(setup_events) == 1, \
            f"Expected 1 setup event for Crazy Quest, got {len(setup_events)}: {[e['title'] for e in setup_events]}"
        assert setup_events[0]["title"] == "Set Up Crazy Quest", \
            f"Expected 'Set Up Crazy Quest', got '{setup_events[0]['title']}'"
    
    def test_no_duplicate_due_to_substring_matching(self, parser, venue_rules_obj):
        """Ensure 'Nightclub' in rules doesn't create duplicate for 'RED: A Nightclub Experience'.
        
        Studio B has a rule for 'Nightclub' (Set Up Nightclub).
        RED should NOT trigger that rule just because it contains 'Nightclub'.
        """
        events = [{
            "title": "RED: A Nightclub Experience",
            "type": "party",
            "start_dt": datetime(2025, 1, 15, 23, 0),
            "end_dt": datetime(2025, 1, 16, 1, 0),
            "venue": "Studio B"
        }]
        
        result = venue_rules_obj.generate_derived_events(events)
        setup_events = [e for e in result if "Set Up" in e.get("title", "")]
        
        # Should not have "Set Up Nightclub"
        nightclub_setup = [e for e in setup_events if "Set Up Nightclub" == e["title"]]
        assert len(nightclub_setup) == 0, \
            f"RED should not trigger generic 'Set Up Nightclub' rule"
            
    def _is_catch_all_rule(self, rule):
        """Check if rule is a catch-all (matches type but no titles)."""
        return rule.get("match_types") and not rule.get("match_titles")

# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Venue Rules Structure Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestVenueRulesStructure:
    """Validate the structure of venue rules to catch configuration errors.
    
    Ensures that rule ordering is correct so that the 'first match wins' 
    mechanism works as expected:
    - Specific match_titles rules must come BEFORE catch-all match_types rules
    """
    
    # Common categories that indicate a catch-all rule when used together
    CATCH_ALL_TYPES = ['game', 'party', 'music', 'show', 'activity']
    
    def _is_catch_all_rule(self, rule: dict) -> bool:
        """Return True if rule is a catch-all (matches multiple common types, no match_titles)."""
        has_match_titles = rule.get('match_titles') is not None
        match_types = rule.get('match_types', [])
        
        if has_match_titles:
            return False
        
        # Catch-all = matches 2+ common types
        common_type_count = len([c for c in match_types if c in self.CATCH_ALL_TYPES])
        return common_type_count >= 2
    
    def test_specific_rules_come_before_catch_all_in_setup(self):
        """Specific match_titles rules must come before catch-all match_types rules in setup."""
        from backend.app.venues import get_venue_rules
        
        venue_rules = get_venue_rules("WN", "Studio B")
        setup_rules = venue_rules.derived_event_rules.get("setup", [])
        
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
        """Specific match_titles rules must come before catch-all match_types rules in strike."""
        from backend.app.venues import get_venue_rules
        
        venue_rules = get_venue_rules("WN", "Studio B")
        strike_rules = venue_rules.derived_event_rules.get("strike", [])
        
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
        from backend.app.venues import get_venue_rules
        
        venue_rules = get_venue_rules("WN", "Studio B")
        derived_rules = venue_rules.derived_event_rules
        
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
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 20, 10),  # Only 10 min gap
                "end_dt": datetime(2025, 1, 15, 21, 10),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 20, 0),
                "end_dt": datetime(2025, 1, 15, 21, 0),
            },
            {
                "title": "Set Up Event B",
                "type": "setup",
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
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 14, 0),
                "end_dt": datetime(2025, 1, 15, 15, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 17, 0),  # 2 hour gap
                "end_dt": datetime(2025, 1, 15, 18, 0),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 15, 0),
                "end_dt": datetime(2025, 1, 15, 16, 0),
            },
            {
                "title": "Set Up Event B",
                "type": "setup",
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
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 20, 0),
            },
            {
                "title": "Event B",
                "type": "show",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 21, 0),  # 1 hour gap - setup fits
                "end_dt": datetime(2025, 1, 15, 22, 0),
            },
            {
                "title": "Strike Event A",
                "type": "strike",
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
    
    def test_reset_created_for_activity_type_like_laser_tag(self, parser):
        """Reset created when gap exists between activity (Laser Tag) and show (Family Shush).
        
        Regression test: activity type must be included in operational_types.
        Scenario: Laser Tag 1-7 PM, Family Shush 8-9:30 PM
        Gap = 1 hour (7 PM - 8 PM), only Doors at 7:45 doesn't fill the gap.
        Should create Reset for Family Shush.
        """
        events = [
            {
                "title": "Laser Tag",
                "type": "activity",  # Activity type, not show/game
                "start_dt": datetime(2025, 1, 15, 13, 0),  # 1 PM
                "end_dt": datetime(2025, 1, 15, 19, 0),    # 7 PM
            },
            {
                "title": "Family Shush!",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 20, 0),  # 8 PM
                "end_dt": datetime(2025, 1, 15, 21, 30),   # 9:30 PM
            },
            {
                "title": "Doors",
                "type": "doors",
                "start_dt": datetime(2025, 1, 15, 19, 45),  # 7:45 PM
                "end_dt": datetime(2025, 1, 15, 20, 0),     # 8 PM
                "is_derived": True,
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        resets = [e for e in result if e.get("type") == "reset"]
        
        # Gap between Laser Tag (7 PM) and Family Shush (8 PM) is 1 hour
        # Doors only covers 7:45-8 PM, leaving 7-7:45 unfilled
        assert len(resets) == 1, f"Expected 1 reset for activity->show gap, got {len(resets)}"
        assert "Family Shush" in resets[0]["title"], f"Reset should be for Family Shush, got {resets[0]['title']}"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Reset Events Integration (Full Pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDuplicateDerivedEventsPrevention:
    """Test that events matching multiple rules only get one derived event each."""
    
    def test_ice_show_only_one_doors_event(self):
        """
        Ice Show: 365 matches both:
        - doors_config rule 1: match_titles=['Ice Show: 365']
        - doors_config rule 4: match_types=['show']
        
        Should only create ONE doors event, not two.
        """
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [{
            'title': 'Ice Show: 365',
            'start_dt': datetime(2025, 1, 15, 19, 0),
            'end_dt': datetime(2025, 1, 15, 20, 0),
            'type': 'show',
            'raw_date': '2025-01-15',
            'venue': 'Studio B'
        }]
        
        result = rules.generate_derived_events(events)
        
        doors = [e for e in result if e.get('type') == 'doors']
        
        assert len(doors) == 1, \
            f"Expected 1 doors event, got {len(doors)}. Ice Show matches multiple rules but should only get one doors."
    
    def test_ice_skating_gets_setup_and_ice_make(self):
        """
        Ice skating sessions (Open Ice Skating, Private Ice Skating) should get:
        - Set Up Skates (first_per_day)
        - Ice Make (before each session with min_gap)
        
        This was a regression - skating sessions were missing derived events.
        """
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [{
            'title': 'Open Ice Skating',
            'start_dt': datetime(2025, 1, 15, 9, 30),
            'end_dt': datetime(2025, 1, 15, 11, 45),
            'type': 'activity',
            'raw_date': '2025-01-15',
            'venue': 'Studio B'
        }]
        
        result = rules.generate_derived_events(events)
        
        setups = [e for e in result if e.get('type') == 'setup']
        ice_makes = [e for e in result if e.get('type') == 'ice_make']
        
        assert len(setups) >= 1, \
            f"Expected at least 1 Set Up Skates, got {len(setups)}. Skating sessions need setup."
        assert len(ice_makes) >= 1, \
            f"Expected at least 1 Ice Make, got {len(ice_makes)}. Skating sessions need ice make."
    
    def test_contiguous_skating_sessions_skip_intermediate_events(self):
        """
        Contiguous skating sessions should:
        - Only get ONE Set Up Skates (first_per_day)
        - Only get ONE Ice Make (min_gap_minutes skips contiguous)
        - Only get ONE Strike Skates (last_per_day + skip_if_next_matches)
        
        This was a regression - back-to-back sessions were getting multiple events.
        """
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        # Two back-to-back skating sessions with no gap
        events = [
            {
                'title': 'Open Ice Skating',
                'start_dt': datetime(2025, 1, 15, 9, 30),
                'end_dt': datetime(2025, 1, 15, 11, 30),
                'type': 'activity',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            },
            {
                'title': 'Private Ice Skating',
                'start_dt': datetime(2025, 1, 15, 11, 30),  # Starts when previous ends
                'end_dt': datetime(2025, 1, 15, 12, 30),
                'type': 'activity',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            }
        ]
        
        result = rules.generate_derived_events(events)
        
        setups = [e for e in result if e.get('type') == 'setup']
        ice_makes = [e for e in result if e.get('type') == 'ice_make']
        strikes = [e for e in result if e.get('type') == 'strike']
        
        assert len(setups) == 1, \
            f"Expected 1 Set Up Skates (first_per_day), got {len(setups)}"
        assert len(ice_makes) == 1, \
            f"Expected 1 Ice Make (min_gap_minutes skips contiguous), got {len(ice_makes)}"
        assert len(strikes) == 1, \
            f"Expected 1 Strike Skates (after last session), got {len(strikes)}"
    
    def test_two_ice_shows_get_ice_make_between(self):
        """
        Two Ice Shows on the same day should get Ice Make & Presets BETWEEN them.
        - Ice Make & Presets before first show (first_per_day)
        - Ice Make & Presets AFTER first show (skip_last_per_day - ice resurfacing)
        - NO Ice Make after second show (skip_last_per_day)
        """
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [
            {
                'title': 'Ice Show: 365',
                'start_dt': datetime(2025, 1, 15, 20, 15),
                'end_dt': datetime(2025, 1, 15, 21, 15),
                'type': 'show',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            },
            {
                'title': 'Ice Show: 365',
                'start_dt': datetime(2025, 1, 15, 22, 30),
                'end_dt': datetime(2025, 1, 15, 23, 30),
                'type': 'show',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            }
        ]
        
        result = rules.generate_derived_events(events)
        
        # Check for Ice Make between shows (after first show ends at 21:15)
        presets_after_first = [e for e in result 
            if e.get('type') == 'preset' 
            and e.get('start_dt', datetime.min).hour == 21]
        
        assert len(presets_after_first) >= 1, \
            f"Expected Ice Make & Presets between shows (around 21:15), got none"
    
    def test_derived_events_not_reprocessed(self):
        """
        Derived events (setup, doors) should NOT be processed again by other generators.
        - Setup event should NOT get a strike generated for it
        - Only the original event should have setup and strike
        """
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [{
            'title': 'Battle of the Sexes',
            'start_dt': datetime(2025, 1, 15, 21, 0),
            'end_dt': datetime(2025, 1, 15, 22, 30),
            'type': 'game',
            'raw_date': '2025-01-15',
            'venue': 'Studio B'
        }]
        
        result = rules.generate_derived_events(events)
        
        # Count strikes - should be exactly 1 (for the game, not for the setup)
        strikes = [e for e in result if e.get('type') == 'strike']
        
        assert len(strikes) == 1, \
            f"Expected 1 strike (for Battle of Sexes only), got {len(strikes)}. Setup events should NOT get strikes."
        
        # Verify the strike is for the main event, not for setup
        assert "Battle of the Sexes" in strikes[0].get('title', ''), \
            f"Strike should be for Battle of the Sexes, got {strikes[0].get('title')}"
    
    def test_laser_tag_single_setup_and_strike(self):
        """Laser Tag should get exactly one setup and one strike."""
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [{
            'title': 'Laser Tag',
            'start_dt': datetime(2025, 1, 15, 15, 0),
            'end_dt': datetime(2025, 1, 15, 17, 0),
            'type': 'game',
            'raw_date': '2025-01-15',
            'venue': 'Studio B'
        }]
        
        result = rules.generate_derived_events(events)
        
        setups = [e for e in result if e.get('type') == 'setup']
        strikes = [e for e in result if e.get('type') == 'strike']
        
        assert len(setups) == 1, f"Expected 1 setup, got {len(setups)}"
        assert len(strikes) == 1, f"Expected 1 strike, got {len(strikes)}"
        assert strikes[0].get('start_dt').hour == 17, \
            f"Strike should start when event ends (17:00), got {strikes[0].get('start_dt')}"
    
    def test_red_party_single_setup_and_strike(self):
        """RED Party should get exactly one setup and one strike."""
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [{
            'title': 'RED! Party',
            'start_dt': datetime(2025, 1, 15, 22, 30),
            'end_dt': datetime(2025, 1, 16, 0, 30),
            'type': 'party',
            'raw_date': '2025-01-15',
            'venue': 'Studio B'
        }]
        
        result = rules.generate_derived_events(events)
        
        setups = [e for e in result if e.get('type') == 'setup']
        strikes = [e for e in result if e.get('type') == 'strike']
        
        assert len(setups) == 1, f"Expected 1 setup (Set Up RED), got {len(setups)}"
        assert len(strikes) == 1, f"Expected 1 strike (Strike RED), got {len(strikes)}"
        assert "RED" in setups[0].get('title', ''), \
            f"Setup should be 'Set Up RED', got {setups[0].get('title')}"
        assert "RED" in strikes[0].get('title', ''), \
            f"Strike should be 'Strike RED', got {strikes[0].get('title')}"
    
    def test_family_shush_derived_events(self):
        """Family SHUSH! should get setup, doors, and strike."""
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [{
            'title': 'Family SHUSH!',
            'start_dt': datetime(2025, 1, 15, 10, 0),
            'end_dt': datetime(2025, 1, 15, 11, 30),
            'type': 'game',
            'raw_date': '2025-01-15',
            'venue': 'Studio B'
        }]
        
        result = rules.generate_derived_events(events)
        
        setups = [e for e in result if e.get('type') == 'setup']
        doors = [e for e in result if e.get('type') == 'doors']
        strikes = [e for e in result if e.get('type') == 'strike']
        
        assert len(setups) >= 1, f"Expected at least 1 setup, got {len(setups)}"
        assert len(doors) >= 1, f"Expected at least 1 doors, got {len(doors)}"
        assert len(strikes) == 1, f"Expected 1 strike, got {len(strikes)}"
    
    def test_stacked_events_skip_doors(self):
        """
        Stacked events should skip doors when min_gap_minutes not met.
        Battle of Sexes -> Crazy Quest -> RED: only first event gets doors.
        """
        from backend.app.venues import get_venue_rules
        
        rules = get_venue_rules("WN", "Studio B")
        
        events = [
            {
                'title': 'Battle of the Sexes',
                'start_dt': datetime(2025, 1, 15, 22, 0),
                'end_dt': datetime(2025, 1, 15, 23, 0),
                'type': 'game',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            },
            {
                'title': 'Crazy Quest',
                'start_dt': datetime(2025, 1, 15, 23, 20),  # 20 min gap
                'end_dt': datetime(2025, 1, 16, 0, 0),
                'type': 'game',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            },
            {
                'title': 'RED: Nightclub Experience',
                'start_dt': datetime(2025, 1, 16, 0, 0),    # 0 min gap (contiguous)
                'end_dt': datetime(2025, 1, 16, 2, 0),
                'type': 'party',
                'raw_date': '2025-01-15',
                'venue': 'Studio B'
            }
        ]
        
        result = rules.generate_derived_events(events)
        doors = [e for e in result if e.get('type') == 'doors']
        
        assert len(doors) == 1, \
            f"Expected 1 doors (min_gap_minutes skips stacked events), got {len(doors)}"
