import pytest
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Data Preservation (Strict Invariance)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataPreservation:
    """Tests that ensure _resolve_operation_overlaps NEVER drops events unexpectedly."""
    
    @pytest.fixture
    def parser(self):
        from backend.app.services.genai_parser import GenAIParser
        return GenAIParser(api_key="dummy")
    
    def test_preserves_derived_event_types(self, parser):
        """Verify that doors, warm_up, ice_make, etc. are preserved."""
        events = [
            # Actual events
            {"title": "Show A", "type": "show", "start_dt": datetime(2025, 1, 1, 10, 0), "end_dt": datetime(2025, 1, 1, 11, 0)},
            
            # Derived events that should constitute 'other_derived'
            {"title": "Doors A", "type": "doors", "start_dt": datetime(2025, 1, 1, 9, 30), "end_dt": datetime(2025, 1, 1, 10, 0)},
            {"title": "Warm Up A", "type": "warm_up", "start_dt": datetime(2025, 1, 1, 9, 0), "end_dt": datetime(2025, 1, 1, 9, 30)},
            {"title": "Ice Make A", "type": "ice_make", "start_dt": datetime(2025, 1, 1, 11, 0), "end_dt": datetime(2025, 1, 1, 11, 15)},
            {"title": "Cast Install", "type": "cast_install", "start_dt": datetime(2025, 1, 1, 8, 0), "end_dt": datetime(2025, 1, 1, 9, 0)},
        ]
        
        result = parser._resolve_operation_overlaps(events)
        
        titles_in = {e["title"] for e in events}
        titles_out = {e["title"] for e in result}
        
        assert titles_in == titles_out, \
            f"Events dropped! Missing: {titles_in - titles_out}"
            
    def test_preserves_arbitrary_unknown_types(self, parser):
        """Verify that unknown event types are preserved (treated as actual events)."""
        events = [
            {"title": "Unknown X", "type": "mystery_type", "start_dt": datetime(2025, 1, 1, 10, 0), "end_dt": datetime(2025, 1, 1, 11, 0)},
            {"title": "Custom Y", "type": "custom_op", "start_dt": datetime(2025, 1, 1, 11, 0), "end_dt": datetime(2025, 1, 1, 12, 0)},
        ]
        
        result = parser._resolve_operation_overlaps(events)
        
        types_out = {e["type"] for e in result}
        assert "mystery_type" in types_out
        assert "custom_op" in types_out
        
    def test_preserves_merged_operations_logic(self, parser):
        """Verify that while operations merge, the intended logic remains consistent."""
        events = [
            {"title": "Show A", "type": "show", "start_dt": datetime(2025, 1, 1, 10, 0), "end_dt": datetime(2025, 1, 1, 11, 0)},
            # Setup overlaps show -> bumped
            {"title": "Setup A", "type": "setup", "start_dt": datetime(2025, 1, 1, 10, 30), "end_dt": datetime(2025, 1, 1, 11, 30)},
        ]
        
        result = parser._resolve_operation_overlaps(events)
        
        # Setup should exist but moved
        setups = [e for e in result if e["type"] == "setup"]
        assert len(setups) == 1
        assert setups[0]["start_dt"] < datetime(2025, 1, 1, 10, 0), "Setup should be bumped earlier"
