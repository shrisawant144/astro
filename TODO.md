# TODO - Fix chart.py code issues

## Issues Identified:
1. [ ] get_house function has complex boundary logic that may have edge case bugs
2. [ ] Missing house calculation for planets exactly on house boundaries
3. [ ] Add input validation for date and time formats
4. [ ] Add better error handling for timezone lookup failures

## Plan:
1. Simplify and fix the get_house function with clearer boundary logic
2. Add input validation for date (YYYY-MM-DD) and time (HH:MM) formats
3. Add try-except for timezonefinder to handle edge cases
4. Test the corrected code

