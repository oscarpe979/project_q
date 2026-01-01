"""
Integration test to trace where presets are lost in the post-processing pipeline.
Tests: generate_derived_events -> _merge_overlapping_operations -> _resolve_operation_overlaps
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from backend.app.venues.base import VenueRules
from backend.app.services.genai_parser import GenAIParser

class TestPresetPipelineIntegration:
    
    @pytest.fixture
    def parser(self):
        # Create parser with mock API key (we won't use LLM, just post-processing methods)
        return GenAIParser(api_key="mock-api-key")
    
    @pytest.fixture
    def rules(self):
        rules = VenueRules()
        # Voices config
        rules.preset_config = [
            {
                "match_titles": ["Voices"],
                "offset_minutes": -150,
                "duration_minutes": 60,
                "title_template": "Sweep/Mop",
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
            "start_dt": datetime(2024, 1, 1, 21, 45),
            "end_dt": datetime(2024, 1, 1, 22, 30),
            "type": "show",
            "venue": "Royal Theater"
        }

    def test_full_pipeline(self, parser, rules, evening_show):
        """
        Step 1: generate_derived_events
        Step 2: _merge_overlapping_operations
        Step 3: _resolve_operation_overlaps
        
        Track presets at each step.
        """
        events = [evening_show]
        
        # Step 1: Generate derived events
        print("\n=== STEP 1: generate_derived_events ===")
        step1_events = rules.generate_derived_events(events)
        step1_presets = [e for e in step1_events if e.get('type') == 'preset']
        print(f"Presets after Step 1: {len(step1_presets)}")
        for p in sorted(step1_presets, key=lambda x: x['start_dt']):
            print(f"  - {p['start_dt'].strftime('%H:%M')} {p['title']}")
        
        # Verify Step 1 has Soundcheck
        step1_titles = [p['title'] for p in step1_presets]
        assert "Soundcheck" in step1_titles, f"Step 1 Missing Soundcheck! Got: {step1_titles}"
        
        # Step 2: _merge_overlapping_operations
        print("\n=== STEP 2: _merge_overlapping_operations ===")
        step2_events = parser._merge_overlapping_operations(step1_events)
        step2_presets = [e for e in step2_events if e.get('type') == 'preset']
        print(f"Presets after Step 2: {len(step2_presets)}")
        for p in sorted(step2_presets, key=lambda x: x['start_dt']):
            print(f"  - {p['start_dt'].strftime('%H:%M')} {p['title']}")
        
        # Verify Step 2 still has Soundcheck
        step2_titles = [p['title'] for p in step2_presets]
        assert "Soundcheck" in step2_titles, f"Step 2 LOST Soundcheck! Got: {step2_titles}"
        
        # Step 3: _resolve_operation_overlaps
        print("\n=== STEP 3: _resolve_operation_overlaps ===")
        step3_events = parser._resolve_operation_overlaps(step2_events)
        step3_presets = [e for e in step3_events if e.get('type') == 'preset']
        print(f"Presets after Step 3: {len(step3_presets)}")
        for p in sorted(step3_presets, key=lambda x: x['start_dt']):
            print(f"  - {p['start_dt'].strftime('%H:%M')} {p['title']}")
        
        # Verify Step 3 still has Soundcheck
        step3_titles = [p['title'] for p in step3_presets]
        assert "Soundcheck" in step3_titles, f"Step 3 LOST Soundcheck! Got: {step3_titles}"
