import pytest
from datetime import datetime, time, timedelta
from backend.app.venues.base import VenueRules

class TestDerivedEventOrdering:
    """
    Regression tests for event ordering issues affecting derived event generation.
    Covers scenarios where processing order caused failures in 'first_per_day' and 'skip_last_per_day' rules.
    """
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
        # Config 1: Skip Last Per Day (e.g. "Show Presets")
        # Matches "Show A", skips the last one.
        rules.preset_config = [{
            "match_titles": ["Show A"],
            "title_template": "Preset {parent_title}",
            "type": "preset",
            "anchor": "end",
            "skip_last_per_day": True,
            "duration_minutes": 30,
            "offset_minutes": 0,
            "exclude_types": ["tech_run"], # EXCLUDES tech_run
        },
        # Config 2: First Per Day (e.g. "Sound Check")
        {
            "match_titles": ["Show A"],
            "title_template": "Start {parent_title}",
            "type": "preset",
            "first_per_day": True,
            "duration_minutes": 15,
            "offset_minutes": -30
        }]
        
        # Tech Run Config
        rules.tech_run_config = [{
            "match_titles": ["Show A"],
            "title_template": "Tech Run {parent_title}",
            "type": "tech_run"
        }]
        return rules

    @pytest.fixture
    def show_a_early(self):
        return {
            "title": "Show A",
            "start_dt": datetime(2024, 1, 1, 19, 0),
            "end_dt": datetime(2024, 1, 1, 20, 0),
            "type": "show",
            "venue": "Royal Theater"
        }

    @pytest.fixture
    def show_a_late(self):
         return {
            "title": "Show A",
            "start_dt": datetime(2024, 1, 1, 21, 0),
            "end_dt": datetime(2024, 1, 1, 22, 0),
            "type": "show",
            "venue": "Royal Theater"
        }

    def test_tech_run_interfering_with_skip_last(self, rules, show_a_early, show_a_late):
        """
        Verify that `skip_last_per_day` correctly identifies the CHRONOLOGICAL last event,
        even when Tech Runs (generated separately) are appended to the list later.
        
        Scenario:
        1. Tech Run (10 AM).
        2. Show Early (7 PM).
        3. Show Late (9 PM). -> Should be SKIPPED.
        
        If unsorted, Tech Run appears last, causing Show Late to generate erroneously.
        """
        events = [show_a_early, show_a_late]
        result = rules.generate_derived_events(events)
        
        presets = [e for e in result if e.get('title') == 'Preset Show A' or e.get('title') == 'Preset Tech Run Show A']
        
        # Expected:
        # 1. Tech Run -> EXCLUDED by match_types (no preset).
        # 2. Show Early -> Preset.
        # 3. Show Late -> SKIPPED (Last).
        
        assert len(presets) == 1, f"Expected 1 preset, got {len(presets)}"
        
        # Verify no preset at 22:00 (Show Late end)
        timestamps_2200 = [p for p in presets if p['start_dt'].hour == 22]
        assert len(timestamps_2200) == 0, "Show Late generated a preset! skip_last failed."

    def test_tech_run_interfering_with_first_per_day(self, rules, show_a_early, show_a_late):
        """
        Verify that `first_per_day` logic consumes the quota for the FIRST event (Tech Run),
        blocking subsequent events (Show Early, Show Late).
        
        Scenario:
        1. Tech Run (10 AM).
        2. Show Early (7 PM).
        
        Expected:
        1. Tech Run -> Generates "Start Tech Run Show A".
        2. Show Early -> Sees quota consumed. Skips.
        """
        events = [show_a_early, show_a_late]
        result = rules.generate_derived_events(events)
        
        # Filter for "Start ..." presets
        presets = [e for e in result if "Start" in e.get('title', '')]
        
        # Expected: 2 Presets (One for Tech Run, One for Show Early).
        # Currently failing (Regression) -> Returns 1.
        assert len(presets) == 2, f"Expected 2 presets (Tech Run + Show), got {len(presets)}"
        
        titles = [p.get('parent_title') for p in presets]
        # Verify it belongs to Tech Run
        assert "Tech Run Show A" in presets[0]['parent_title']

    def test_tech_run_excludes_end_presets(self, rules, show_a_early):
        """
        Verify that Tech Runs do NOT trigger "end-anchored" presets like "Show Presets",
        which are intended only for actual shows.
        But they SHOULD triggers start-anchored presets (like "Start ...").
        """
        # Tech Run Config
        rules.tech_run_config = [{
            "match_titles": ["Show A"],
            "title_template": "Tech Run {parent_title}",
            "type": "tech_run"
        }]
        
        events = [show_a_early]
        result = rules.generate_derived_events(events)
        
        # 1. Tech Run (10 AM - 11 AM explicitly for this test calculation usually)
        # 2. Start Preset (from Tech Run). MATCHES.
        # 3. End Preset (from Tech Run). SHOULD NOT MATCH.
        
        # Check for End Preset ("Preset Tech Run Show A")
        end_presets = [e for e in result if e.get('title') == "Preset Tech Run Show A"]
        
        # This currently FAILS (returns 1) because the rule lacks strict type matching.
        # We expect 0.
        assert len(end_presets) == 0, f"Tech Run triggered unwanted end preset! {end_presets}"
        
        # Check start preset exists (sanity check that we didn't break everything)
        start_presets = [e for e in result if e.get('title') == "Start Tech Run Show A"]
        assert len(start_presets) == 1, "Tech Run missing wanted start preset"
        assert "Tech Run Show A" in start_presets[0]['parent_title']
