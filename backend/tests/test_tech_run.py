import pytest
from datetime import datetime, time, timedelta, date
from backend.app.venues.base import VenueRules

class TestTechRunDerivedEvent:
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
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
            "venue": "Royal Theater",
            "color": "#FF0000"
        }

    @pytest.fixture
    def show_a_day_2(self):
         return {
            "title": "Show A",
            "start_dt": datetime(2024, 1, 2, 20, 0),
            "end_dt": datetime(2024, 1, 2, 21, 30),
            "type": "show",
            "venue": "Royal Theater",
            "color": "#FF0000"
        }

    @pytest.fixture
    def show_b_day_3(self):
         return {
            "title": "Show B",
            "start_dt": datetime(2024, 1, 3, 20, 0),
            "end_dt": datetime(2024, 1, 3, 21, 30),
            "type": "show",
            "venue": "Royal Theater",
             "color": "#00FF00"
        }

    def test_tech_run_generated_on_turnover(self, rules, show_a_day_1):
        """Tech run should be generated for the first show."""
        result = rules.generate_derived_events([show_a_day_1])
        
        # Expect Original + Tech Run = 2
        assert len(result) == 2
        
        tech_run = [e for e in result if e.get('type') == 'tech_run'][0]
        assert tech_run['title'] == 'Tech Run Show A'
        # Check time: Morning (10:00 AM) of same day
        expected_start = datetime(2024, 1, 1, 10, 0)
        assert tech_run['start_dt'] == expected_start
        assert tech_run['parent_title'] == 'Show A'
        assert tech_run['color'] == '#FF0000'

    def test_tech_run_skipped_sequence(self, rules, show_a_day_1, show_a_day_2):
        """Tech run should only be generated for the first show in a sequence."""
        result = rules.generate_derived_events([show_a_day_1, show_a_day_2])
        
        # Expect 2 Show A + 1 Tech Run (Day 1) = 3
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        assert len(tech_runs) == 1
        assert tech_runs[0]['start_dt'].date() == show_a_day_1['start_dt'].date()
        assert tech_runs[0]['start_dt'].time() == time(10, 0)

    def test_tech_run_generated_multiple_blocks(self, rules, show_a_day_1, show_b_day_3):
        """Tech run generated for Show A, then Show B (assuming Show B in config)."""
        rules.tech_run_config.append({
            "match_titles": ["Show B"],
            "title_template": "Tech Run {parent_title}",
            "type": "tech_run"
        })
        
        result = rules.generate_derived_events([show_a_day_1, show_b_day_3])
        
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        assert len(tech_runs) == 2
        # Sort by start_dt
        tech_runs.sort(key=lambda x: x['start_dt'])
        assert tech_runs[0]['title'] == 'Tech Run Show A'
        assert tech_runs[1]['title'] == 'Tech Run Show B'

    def test_tech_run_ignored_interruption(self, rules, show_a_day_1, show_a_day_2):
        """Interruption by minor event (activity) should NOT trigger new tech run."""
        interruption = {
             "title": "Corporate Meeting",
             "start_dt": datetime(2024, 1, 2, 12, 0),
             "type": "activity"
        }
        
        # Sequence: Show A -> Activity -> Show A
        # Activity should be ignored for turnover.
        # So it looks like Show A -> Show A.
        # Expectation: 1 Tech Run (Day 1).
        
        result = rules.generate_derived_events([show_a_day_1, interruption, show_a_day_2])
        
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        assert len(tech_runs) == 1

    def test_tech_run_major_interruption(self, rules, show_a_day_1, show_a_day_2):
        """Interruption by MAJOR event (headliner) SHOULD trigger new tech run."""
        interruption = {
             "title": "Headliner Bob",
             "start_dt": datetime(2024, 1, 2, 12, 0),
             "type": "headliner"
        }
        
        # Sequence: Show A -> Headliner -> Show A
        # Headliner changes state.
        # Expectation: 2 Tech Runs (Day 1 for Show A, Day 2 for Show A).
        
        result = rules.generate_derived_events([show_a_day_1, interruption, show_a_day_2])
        
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        # Note: Headliner itself might trigger a Tech Run if configured, but here we only have config for Show A.
        # So we expect Tech Run (Day 1) + Tech Run (Day 2).
        assert len(tech_runs) == 2

    def test_tech_run_presets(self, rules, show_a_day_1):
        """Tech Runs should trigger presets if configured."""
        rules.preset_config = [{
            "match_titles": ["Show A"],
            "offset_minutes": -30,
            "duration_minutes": 15,
            "title_template": "Preset for {parent_title}",
            "type": "preset"
        }]
        
        result = rules.generate_derived_events([show_a_day_1])
        
        # Should have 2 presets: 1 for Show A, 1 for Tech Run
        presets = [e for e in result if e.get('type') == 'preset']
        assert len(presets) == 2
        
        # Analyze parents
        parents = [e.get('parent_title') for e in presets]
        # One parent is "Show A"
        # One parent is "Tech Run Show A"
        assert "Show A" in parents
        assert "Tech Run Show A" in parents
