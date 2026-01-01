import pytest
from datetime import datetime, time, timedelta
from backend.app.venues.base import VenueRules

class TestTechRunRefinements:
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
        # Presets: First per day
        rules.preset_config = [{
            "match_titles": ["Show A"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Preset {parent_title}",
            "type": "preset",
            "first_per_day": True
        }]
        # Tech Run: For Show A
        rules.tech_run_config = [{
            "match_titles": ["Show A"],
            "title_template": "Tech Run {parent_title}",
            "type": "tech_run"
        }]
        return rules

    @pytest.fixture
    def show_a_day_1(self):
        return {
            "title": "Show A",
            "start_dt": datetime(2024, 1, 1, 20, 0),
            "end_dt": datetime(2024, 1, 1, 21, 30),
            "type": "show",
            "venue": "Royal Theater"
        }

    @pytest.fixture
    def show_a_day_2(self):
         return {
            "title": "Show A",
            "start_dt": datetime(2024, 1, 2, 20, 0),
            "end_dt": datetime(2024, 1, 2, 21, 30),
            "type": "show",
            "venue": "Royal Theater"
        }

    @pytest.fixture
    def bingo_day_2_am(self):
         return {
            "title": "Bingo",
            "start_dt": datetime(2024, 1, 2, 10, 0),
            "end_dt": datetime(2024, 1, 2, 11, 0),
            "type": "activity", # Not a show/headliner
            "venue": "Royal Theater"
        }
        
    @pytest.fixture
    def headliner_day_2(self):
         return {
            "title": "Headliner: Bob",
            "start_dt": datetime(2024, 1, 2, 22, 0),
            "end_dt": datetime(2024, 1, 2, 23, 0),
            "type": "headliner",
            "venue": "Royal Theater"
        }

    def test_reproduction_tech_run_continuous_days(self, rules, show_a_day_1, show_a_day_2):
        """
        ISSUE 1: Consecutive days of same show triggers Tech Run every day.
        Expected: Only Day 1 has Tech Run. Day 2 skipped.
        """
        result = rules.generate_derived_events([show_a_day_1, show_a_day_2])
        
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        # Currently this passes (1 tech run), but we need to ensure "Bingo" doesn't break it.
        # If the code works as expected for purely consecutive days, good.
        assert len(tech_runs) == 1
        assert tech_runs[0]['start_dt'].date() == show_a_day_1['start_dt'].date()

    def test_reproduction_tech_run_interrupted_by_minor_event(self, rules, show_a_day_1, bingo_day_2_am, show_a_day_2):
        """
        ISSUE 1b: Minor event (Bingo) should NOT trigger new Tech Run for subsequent Show A.
        Show A (Day 1) -> Bingo (Day 2) -> Show A (Day 2).
        Expected: 1 Tech Run (Day 1). Bingo is ignored for turnover.
        """
        events = [show_a_day_1, bingo_day_2_am, show_a_day_2]
        result = rules.generate_derived_events(events)
        
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        
        # If Bingo is treated as turnover, we'd get 2. We want 1.
        assert len(tech_runs) == 1, f"Expected 1 tech run, got {len(tech_runs)}"

    def test_reproduction_tech_run_interrupted_by_major_event(self, rules, show_a_day_1, headliner_day_2, show_a_day_2):
        """
        ISSUE 1c: Major event (Headliner) SHOULD trigger new Tech Run if we go back to Show A.
        Wait, usually sequence is Show A -> Headliner.
        If we do Show A (Day 1) -> Headliner (Day 2) -> Show A (Day 3).
        Then Day 3 needs Tech Run.
        
        Here we test: Show A (Day 1) -> Headliner (Day 2).
        Does Headliner trigger a Tech Run?
        The Headliner *itself* doesn't strictly need a Tech Run unless configured.
        But if we had Show A after Headliner, Show A needs Tech Run.
        """
        show_a_day_3 = show_a_day_2.copy()
        show_a_day_3['start_dt'] = datetime(2024, 1, 3, 20, 0)
        show_a_day_3['end_dt'] = datetime(2024, 1, 3, 21, 30)
        
        events = [show_a_day_1, headliner_day_2, show_a_day_3]
        result = rules.generate_derived_events(events)
        
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        # Show A (Day 1) -> Tech Run.
        # Headliner (Day 2) -> Changes "Last Title".
        # Show A (Day 3) -> "Last Title" was Headliner != Show A. -> Tech Run.
        assert len(tech_runs) == 2

    def test_reproduction_preset_blocking(self, rules, show_a_day_1):
        """
        ISSUE 2: Tech Run consumes 'first_per_day' preset, leaving evening show without preset.
        Expected: Tech Run gets preset AND Evening Show gets preset.
        """
        # Tech Run will be generated at 10 AM.
        # Show is at 8 PM.
        # Rule matches "Show A". Tech Run title is "Tech Run Show A" (matches).
        
        result = rules.generate_derived_events([show_a_day_1])
        
        presets = [e for e in result if e.get('type') == 'preset']
        
        # Identify parents
        parents = [e.get('parent_title') for e in presets]
        
        # We expect TWO presets:
        # 1. For "Tech Run Show A"
        # 2. For "Show A"
        assert len(presets) == 2, f"Expected 2 presets, got {len(presets)}: {parents}"
        assert "Show A" in parents, "Evening show missing preset"
        assert "Tech Run Show A" in parents, "Tech run missing preset"
