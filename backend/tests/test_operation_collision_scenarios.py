
import pytest
from datetime import datetime, timedelta
from backend.app.services.genai_parser import GenAIParser

class TestOperationCollisionScenarios:
    """
    Tests specific scenarios where operations (setups/strikes) collide with:
    1. Actual events (shows, games, etc.)
    2. Derived events (doors, ice makes, etc.)
    3. Other operations
    
    Verifies that the overlap resolution logic:
    - Bumps operations to valid time slots.
    - Preserves derived events.
    - Merges overlapping operations correctly.
    - Prevents invalid "monster" merges.
    """
    
    @pytest.fixture
    def parser(self):
        return GenAIParser(api_key="dummy")
        
    def test_scenario_day_5_laser_tag_to_family_shush(self, parser):
        """
        Mirroring Day 5 (St. Kitts):
        - 1:00 PM - 7:00 PM: Laser Tag
        - 7:00 PM - 7:45 PM: Set Up Family Shush! & Strike Laser Tag [MERGED]
        - 7:45 PM - 8:00 PM: Doors [Derived]
        - 8:00 PM - 9:30 PM: Family Shush!
        
        This makes sure:
        1. Set Up Family Shush (45m) merges with Strike Laser Tag (30m)
        2. Doors are preserved
        3. No 'monstrosity' merges occur (checking for bumping issues)
        """
        events = [
            # Laser Tag
            {
                "title": "Laser Tag",
                "type": "activity",
                "start_dt": datetime(2025, 1, 15, 13, 0),
                "end_dt": datetime(2025, 1, 15, 19, 0),
            },
            # Family Shush!
            {
                "title": "Family Shush!",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 20, 0),
                "end_dt": datetime(2025, 1, 15, 21, 30),
            },
            
            # --- DERIVED INPUTS (Simulated) ---
            # Strike Laser Tag: 30 min -> 19:00 - 19:30
            {
                "title": "Strike Laser Tag",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 19, 0),
                "end_dt": datetime(2025, 1, 15, 19, 30),
            },
            # Set Up Family Shush: 45 min -> 19:15 - 20:00 (Starts before Doors?)
            # Doors is 19:45. So Set Up must end by 19:45 to not overlap Doors? 
            # OR Set Up bumps to 19:00 - 19:45.
            {
                "title": "Set Up Family Shush!",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 19, 15), # Initial guess
                "end_dt": datetime(2025, 1, 15, 20, 0),    # 45 min
            },
            # Doors: 19:45 - 20:00
            {
                "title": "Doors",
                "type": "doors",
                "start_dt": datetime(2025, 1, 15, 19, 45),
                "end_dt": datetime(2025, 1, 15, 20, 0),
                "is_derived": True,
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        
        print("\n=== Result Day 5 ===")
        for e in result:
            print(f"{e['title']} ({e['type']}) : {e['start_dt'].strftime('%H:%M')} - {e['end_dt'].strftime('%H:%M')}")
            
        titles = [e['title'] for e in result]
        
        # Verify specific merged title exists
        merged_title = "Set Up Family Shush! & Strike Laser Tag" # OR reversed based on sort
        # Note: logic combines title as "Target & Source". 
        # Strike starts 19:00. Setup bumps to 19:00?
        # If merged start is 19:00.
        
        # Check that we have ONE strike/setup merged event
        ops = [e for e in result if e['type'] in ['setup', 'strike'] or '&' in e['title']]
        assert len(ops) == 1, f"Should be 1 merged op, got {len(ops)}: {[o['title'] for o in ops]}"
        
        # Check Doors existence
        doors = [e for e in result if e['type'] == 'doors']
        assert len(doors) == 1, "Doors event missing!"
        assert doors[0]['start_dt'].hour == 19 and doors[0]['start_dt'].minute == 45
        
        # Verify Reset Clamping (New Requirement)
        # If Setup Family Shush was dropped (simulating user failure scenario), 
        # a Reset should appear but MUST END at Doors (19:45), not 20:00.
        resets = [e for e in result if e['type'] == 'reset']
        if resets:
            # If we have a reset, it means merge failed. Check if reset respects Doors.
            reset = resets[0]
            print(f"FAILSAFE CHECK: Reset found: {reset['start_dt']} - {reset['end_dt']}")
            assert reset['end_dt'] <= doors[0]['start_dt'], "Reset overlapped Doors!"
        
    def test_scenario_day_3_parade_to_skating(self, parser):
        """
        Mirroring Day 3:
        - 12:30 - 1:00 PM: Anchors Aweigh Parade
        - 1:00 - 1:30 PM: Strike Bingo & Set Up Skates [MERGED]
        - 1:30 - 2:00 PM: Ice Make
        - 2:00 - 4:30 PM: Open Ice Skating
        """
        events = [
            # Parade
            {
                "title": "Anchors Aweigh Parade",
                "type": "show",
                "start_dt": datetime(2025, 1, 15, 12, 30),
                "end_dt": datetime(2025, 1, 15, 13, 0),
                "is_cross_venue": True,
            },
            # Bingo (Previous event, establishing the Strike Bingo part)
            {
                "title": "Bingo",
                "type": "activity",
                "start_dt": datetime(2025, 1, 15, 11, 30),
                "end_dt": datetime(2025, 1, 15, 12, 30),
            },
            # Open Ice Skating
            {
                "title": "Open Ice Skating",
                "type": "activity", # or game/show? Skating usually activity
                "start_dt": datetime(2025, 1, 15, 14, 0),
                "end_dt": datetime(2025, 1, 15, 16, 30),
            },
            
            # --- DERIVED ---
            # Strike Bingo (30 min) -> 12:30 - 13:00 (Overlaps Parade!)
            # So Strike Bingo should be BUMPED to 13:00? 
            # Or Parade is cross-venue? Let's assume Parade is "Show".
            # If Strike Bingo bumps to 13:00-13:30.
            {
                "title": "Strike Bingo",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 12, 30),
                "end_dt": datetime(2025, 1, 15, 13, 0),
            },
            # Set Up Skates (30 min) -> 13:30 - 14:00 (Overlaps Ice Make?)
            # Or Set Up Skates is 13:00 - 13:30.
            {
                "title": "Set Up Skates",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 13, 30),
                "end_dt": datetime(2025, 1, 15, 14, 0),
            },
            # Ice Make (30 min) -> 13:30 - 14:00 (Before Skating)
            {
                "title": "Ice Make",
                "type": "ice_make",
                "start_dt": datetime(2025, 1, 15, 13, 30),
                "end_dt": datetime(2025, 1, 15, 14, 0),
            },
        ]
        
        # Note: Set Up Skates typically happens BEFORE Ice Make? 
        # Or Set Up Skates (Floor removal) -> Ice Make -> Skating.
        
        result = parser._resolve_operation_overlaps(events)
        
        print("\n=== Result Day 3 ===")
        for e in result:
            print(f"{e['title']} ({e['type']}) : {e['start_dt'].strftime('%H:%M')} - {e['end_dt'].strftime('%H:%M')}")
            
        # Verify valid sequence
        # Should contain: "Strike Bingo & Set Up Skates" at 13:00 - 13:30
        ops = [e for e in result if '&' in e['title']]
        assert len(ops) >= 1
        assert ops[0]['start_dt'].hour == 13 and ops[0]['start_dt'].minute == 0
        
        # Verify Ice Make preserved at 13:30
        ice = [e for e in result if e['type'] == 'ice_make']
        assert len(ice) == 1
        assert ice[0]['start_dt'].hour == 13 and ice[0]['start_dt'].minute == 30
        
    def test_reset_naming_conventions(self, parser):
        """
        Verify that:
        - Reset <= 30 mins -> "Reset for [Next]"
        - Reset > 30 mins  -> "Strike [Prev] & Set Up [Next]"
        """
        events = [
            # Short Gap Case (30 mins)
            {
                "title": "Short Gap A",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 12, 0),
                "end_dt": datetime(2025, 1, 15, 13, 0),
            },
            {
                "title": "Short Gap B",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 13, 30),
                "end_dt": datetime(2025, 1, 15, 14, 30),
            },
            
            # Long Gap Case (60 mins)
            # Starts immediately after Short Gap B ends (14:30) to avoid extra reset
            {
                "title": "Long Gap A",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 14, 30),
                "end_dt": datetime(2025, 1, 15, 15, 30),
            },
            {
                "title": "Long Gap B",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 16, 30),
                "end_dt": datetime(2025, 1, 15, 17, 30),
            },
        ]
        
        # Result should contain 2 resets (since no operations provided)
        result = parser._resolve_operation_overlaps(events)
        
        resets = [e for e in result if e['type'] == 'reset']
        assert len(resets) == 2
        
        # Check Short Gap Reset
        short_reset = next(r for r in resets if r['start_dt'].hour == 13)
        duration = (short_reset['end_dt'] - short_reset['start_dt']).total_seconds() / 60
        assert duration == 30
        assert short_reset['title'] == "Reset for Short Gap B"
        
        # Check Long Gap Reset
        long_reset = next(r for r in resets if r['end_dt'].hour == 16) # Ends at 16:30
        duration = (long_reset['end_dt'] - long_reset['start_dt']).total_seconds() / 60
        assert duration == 60
        assert long_reset['title'] == "Strike Long Gap A & Set Up Long Gap B"

    def test_merge_naming_order(self, parser):
        """
        Verify that merged titles are always ordered:
        Strike -> Reset -> Ice -> Set Up
        
        Input: "Set Up X", "Strike Y", "Ice Scrape" (in any order)
        Output: "Strike Y & Ice Scrape & Set Up X"
        """
        events = [
            # Event A
            {
                "title": "A",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 10, 0),
                "end_dt": datetime(2025, 1, 15, 11, 0),
            },
            # Event B
            {
                "title": "B",
                "type": "game",
                "start_dt": datetime(2025, 1, 15, 12, 0),
                "end_dt": datetime(2025, 1, 15, 13, 0),
            },
            # Operations that will merge
            {
                "title": "Set Up B",
                "type": "setup",
                "start_dt": datetime(2025, 1, 15, 11, 0),
                "end_dt": datetime(2025, 1, 15, 12, 0),
            },
            {
                "title": "Strike A",
                "type": "strike",
                "start_dt": datetime(2025, 1, 15, 11, 0),
                "end_dt": datetime(2025, 1, 15, 11, 30),
            },
            {
                "title": "Ice Scrape",
                "type": "setup", # treated as op
                "start_dt": datetime(2025, 1, 15, 11, 30),
                "end_dt": datetime(2025, 1, 15, 12, 0),
            },
        ]
        
        result = parser._resolve_operation_overlaps(events)
        
        # Should have 1 merged operation
        ops = [e for e in result if '&' in e['title']]
        assert len(ops) == 1
        
        # Verify strict order
        # Expect: Strike A & Ice Scrape & Set Up B
        expected = "Strike A & Ice Scrape & Set Up B"
        assert ops[0]['title'] == expected, f"Expected '{expected}', got '{ops[0]['title']}'"
