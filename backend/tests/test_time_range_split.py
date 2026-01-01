"""
Tests for CD Grid Time Range Auto-Split feature.

This feature detects CD Grid typos where "7pm - 9pm" for a 60-minute show
should actually be two separate shows at 7pm and 9pm.
"""
import pytest
from datetime import datetime, timedelta
from backend.app.services.genai_parser import GenAIParser


class TestAutoSplitTimeRanges:
    """Tests for _auto_split_time_ranges method."""
    
    @pytest.fixture
    def parser(self):
        return GenAIParser(api_key="mock-api-key")
    
    @pytest.fixture
    def default_durations(self):
        return {
            "Voices": 45,
            "Effectors": 60,
            "Headliner": 60,
        }

    def test_double_show_split(self, parser, default_durations):
        """
        7pm - 9pm with 60min configured duration -> 2 shows at 7pm AND 9pm
        (start/end times represent show times, not a continuous span)
        """
        events = [{
            "title": "The Effectors II",
            "start_dt": datetime(2024, 1, 1, 19, 0),  # 7pm
            "end_dt": datetime(2024, 1, 1, 21, 0),    # 9pm (120 min)
            "type": "show",
        }]
        
        result = parser._auto_split_time_ranges(events, default_durations)
        
        assert len(result) == 2, f"Expected 2 events, got {len(result)}"
        assert result[0]['start_dt'] == datetime(2024, 1, 1, 19, 0)  # 7pm
        assert result[1]['start_dt'] == datetime(2024, 1, 1, 21, 0)  # 9pm (original end time)
        assert result[0]['end_dt'] is None  # Cleared for duration resolution
        assert result[1]['end_dt'] is None

    def test_triple_time_range_becomes_two_shows(self, parser, default_durations):
        """
        7pm - 10pm with 60min configured duration -> still 2 shows at 7pm AND 10pm
        (regardless of gap, we only use start/end times)
        """
        events = [{
            "title": "Headliner Comedy Show",
            "start_dt": datetime(2024, 1, 1, 19, 0),  # 7pm
            "end_dt": datetime(2024, 1, 1, 22, 0),    # 10pm (180 min)
            "type": "headliner",
        }]
        
        result = parser._auto_split_time_ranges(events, default_durations)
        
        # Still only 2 shows - at start and end times
        assert len(result) == 2, f"Expected 2 events, got {len(result)}"
        assert result[0]['start_dt'] == datetime(2024, 1, 1, 19, 0)  # 7pm
        assert result[1]['start_dt'] == datetime(2024, 1, 1, 22, 0)  # 10pm

    def test_no_split_without_configured_duration(self, parser, default_durations):
        """
        Events without configured duration are left as-is.
        """
        events = [{
            "title": "Unknown Show",  # Not in default_durations
            "start_dt": datetime(2024, 1, 1, 19, 0),
            "end_dt": datetime(2024, 1, 1, 21, 0),
            "type": "show",
        }]
        
        result = parser._auto_split_time_ranges(events, default_durations)
        
        assert len(result) == 1, "Event without configured duration should not split"
        assert result[0]['end_dt'] == datetime(2024, 1, 1, 21, 0)  # Original end preserved

    def test_no_split_when_duration_matches(self, parser, default_durations):
        """
        Event with duration matching configured value should not split.
        """
        events = [{
            "title": "Voices",
            "start_dt": datetime(2024, 1, 1, 19, 0),
            "end_dt": datetime(2024, 1, 1, 19, 45),  # 45 min = configured
            "type": "show",
        }]
        
        result = parser._auto_split_time_ranges(events, default_durations)
        
        assert len(result) == 1, "Event matching configured duration should not split"

    def test_no_split_when_duration_below_threshold(self, parser, default_durations):
        """
        Event with duration < 2x configured should not split.
        """
        events = [{
            "title": "Voices",
            "start_dt": datetime(2024, 1, 1, 19, 0),
            "end_dt": datetime(2024, 1, 1, 20, 20),  # 80 min (< 90 = 2*45)
            "type": "show",
        }]
        
        result = parser._auto_split_time_ranges(events, default_durations)
        
        assert len(result) == 1, "Event below 2x threshold should not split"

    def test_no_split_when_no_end_time(self, parser, default_durations):
        """
        Events with only start time (no end time) are left as-is.
        """
        events = [{
            "title": "Voices",
            "start_dt": datetime(2024, 1, 1, 19, 0),
            "end_dt": None,
            "type": "show",
        }]
        
        result = parser._auto_split_time_ranges(events, default_durations)
        
        assert len(result) == 1, "Event without end time should not split"
