import pytest
from datetime import datetime, time, timedelta
from backend.app.venues.base import VenueRules

class TestDerivedEventOrdering:
    """
    Regression tests for event ordering issues affecting derived event generation.
    Tests the clean separation of Show rules and Tech Run rules.
    
    Architecture:
    - Rules WITHOUT match_types: auto-exclude tech_run events (apply to shows only)
    - Rules WITH match_types: ["tech_run"]: apply only to tech_run events
    """
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
        rules.preset_config = [
            # Show rule: skip_last_per_day (auto-excludes tech_run)
            {
                "match_titles": ["Show A"],
                "title_template": "Preset {parent_title}",
                "type": "preset",
                "anchor": "end",
                "skip_last_per_day": True,
                "duration_minutes": 30,
                "offset_minutes": 0,
            },
            # Show rule: first_per_day (auto-excludes tech_run)
            {
                "match_titles": ["Show A"],
                "title_template": "Start {parent_title}",
                "type": "preset",
                "first_per_day": True,
                "duration_minutes": 15,
                "offset_minutes": -30
            },
            # Tech Run rule: first_per_day (explicit match_types)
            {
                "match_titles": ["Show A"],
                "match_types": ["tech_run"],
                "title_template": "Start {parent_title}",
                "type": "preset",
                "first_per_day": True,
                "duration_minutes": 15,
                "offset_minutes": -15  # Adjusted offset for Tech Run (no doors gap)
            }
        ]
        
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

    def test_skip_last_per_day_works_for_shows(self, rules, show_a_early, show_a_late):
        """
        Verify that skip_last_per_day correctly identifies the last SHOW of the day.
        Tech Runs are excluded from this rule (by auto-exclusion).
        """
        events = [show_a_early, show_a_late]
        result = rules.generate_derived_events(events)
        
        # Filter for end-anchored presets ("Preset Show A")
        presets = [e for e in result if e.get('title') == 'Preset Show A']
        
        # Expected:
        # - Show Early (7 PM) -> Preset at 8:00 PM
        # - Show Late (9 PM) -> SKIPPED (last)
        assert len(presets) == 1, f"Expected 1 preset (Show Early only), got {len(presets)}"
        assert presets[0]['start_dt'].hour == 20, "Preset should be from Show Early (8 PM)"

    def test_separate_quotas_for_tech_run_and_shows(self, rules, show_a_early, show_a_late):
        """
        Verify that Tech Runs and Shows have SEPARATE first_per_day quotas.
        Tech Run gets its own preset, Shows get their own preset.
        """
        events = [show_a_early, show_a_late]
        result = rules.generate_derived_events(events)
        
        # Filter for start presets
        start_presets = [e for e in result if "Start" in e.get('title', '')]
        
        # Expected: 2 presets
        # 1. Tech Run Start (9:45 AM) - from Tech Run rule
        # 2. Show Early Start (6:30 PM) - from Show rule
        assert len(start_presets) == 2, f"Expected 2 presets (Tech Run + Show), got {len(start_presets)}"
        
        # Verify one is morning (tech run), one is evening (show)
        morning_presets = [p for p in start_presets if p['start_dt'].hour < 12]
        evening_presets = [p for p in start_presets if p['start_dt'].hour >= 12]
        assert len(morning_presets) == 1, "Should have 1 morning preset (Tech Run)"
        assert len(evening_presets) == 1, "Should have 1 evening preset (Show)"

    def test_tech_run_auto_excluded_from_show_rules(self, rules, show_a_early):
        """
        Verify that Tech Runs are automatically excluded from rules
        that don't have explicit match_types.
        """
        # Remove Tech Run-specific rule to test auto-exclusion
        rules.preset_config = [
            {
                "match_titles": ["Show A"],
                "title_template": "Preset {parent_title}",
                "type": "preset",
                "anchor": "end",
                "duration_minutes": 30,
                "offset_minutes": 0,
            },
        ]
        
        events = [show_a_early]
        result = rules.generate_derived_events(events)
        
        # Find presets from Tech Run
        tech_run_presets = [e for e in result if 'Tech Run' in e.get('parent_title', '')]
        
        # Tech Run should NOT get this preset (auto-excluded)
        assert len(tech_run_presets) == 0, f"Tech Run should be auto-excluded! Got: {tech_run_presets}"
        
        # Show should still get the preset
        show_presets = [e for e in result if e.get('parent_title') == 'Show A' and e.get('type') == 'preset']
        assert len(show_presets) == 1, "Show should get the preset"

