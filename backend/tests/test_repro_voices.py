import pytest
from datetime import datetime, time, timedelta
from backend.app.venues.base import VenueRules

class TestReproVoices:
    """
    Reproduce the exact Voices scenario from production.
    Day 1: Tech Run Voices at 10:00 AM. 
    Expected presets:
    - 7:30 AM: Sweep/Mop (offset -150)
    - 8:30 AM: Cast Warm Up (offset -90)
    - 8:45 AM: Soundcheck (offset -75) <- MISSING IN PRODUCTION
    - 9:00 AM: STAT Presets (offset -60)
    """
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
        # EXACT config from wn_royal_theater.py for Voices
        rules.preset_config = [
            {
                "match_titles": ["Voices"],
                "offset_minutes": -150,
                "duration_minutes": 60,
                "title_template": "Sweep/Mop Stage and Props Presets @ Video Wall",
                "type": "preset",
                "first_per_day": True
            },
            {
                "match_titles": ["Voices"],
                "offset_minutes": -90,
                "duration_minutes": 15,
                "title_template": "Cast Warm Up",
                "type": "preset",
                "first_per_day": True
            },
            {
                "match_titles": ["Voices"],
                "offset_minutes": -75,
                "duration_minutes": 15,
                "title_template": "Soundcheck",
                "type": "preset",
                "first_per_day": True
            },
            {
                "match_titles": ["Voices"],
                "offset_minutes": -60,
                "duration_minutes": 15,
                "title_template": "STAT Presets",
                "type": "preset",
                "first_per_day": True
            },
        ]
        
        rules.tech_run_config = [{
            "match_titles": ["Voices"],
            "title_template": "Tech Run {parent_title}",
            "type": "tech_run"
        }]
        return rules

    @pytest.fixture
    def evening_show(self):
        return {
            "title": "Voices",
            "start_dt": datetime(2024, 1, 1, 21, 45),  # 9:45 PM
            "end_dt": datetime(2024, 1, 1, 22, 30),
            "type": "show",
            "venue": "Royal Theater"
        }

    def test_voices_all_presets(self, rules, evening_show):
        """
        Start with evening show. Tech Run should be generated.
        ALL 4 presets should generate for Tech Run.
        """
        events = [evening_show]
        result = rules.generate_derived_events(events)
        
        presets = [e for e in result if e.get('type') == 'preset']
        tech_runs = [e for e in result if e.get('type') == 'tech_run']
        
        print("\nAll Generated Events (sorted by time):")
        all_events = sorted(result, key=lambda x: x.get('start_dt') or datetime.min)
        for e in all_events:
            print(f"- {e['start_dt'].strftime('%H:%M')} {e['title']} ({e['type']})")
        
        # Ensure Tech Run was generated
        assert len(tech_runs) == 1, f"Expected 1 Tech Run, got {len(tech_runs)}"
        
        # Find morning presets (before noon)
        morning_presets = [p for p in presets if p['start_dt'].hour < 12]
        
        print("\nMorning Presets (from Tech Run):")
        for p in morning_presets:
            print(f"- {p['start_dt'].strftime('%H:%M')} {p['title']}")
        
        # Assert ALL 4 presets are present
        titles = [p['title'] for p in morning_presets]
        
        assert "Sweep/Mop Stage and Props Presets @ Video Wall" in titles, f"Missing Sweep/Mop! Got: {titles}"
        assert "Cast Warm Up" in titles, f"Missing Cast Warm Up! Got: {titles}"
        assert "Soundcheck" in titles, f"Missing Soundcheck! Got: {titles}"
        assert "STAT Presets" in titles, f"Missing STAT Presets! Got: {titles}"
