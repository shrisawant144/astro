# Kundali Import Compatibility Fix - TODO Steps

## Current Status
- ✅ Analyzed all 11 Python modules in `/home/shrikrishna/astro/kundali/`
- ✅ Identified root cause: `printing.py` imports missing constants from `constants.py`
- ✅ Confirmed other modules import existing constants successfully
- ✅ Extracted exact definitions for missing constants

## Approved Plan Steps (Breakdown)

**Step 1: [PENDING] Update constants.py**
- Add 4 missing constants at the end of file
- Definitions ready from printing.py analysis

**Step 2: [PENDING] Clean printing.py**
- Remove failed import lines (DIGNITY_SIGNS, CHART_WEIGHTS, LAGNA_REMEDIES, SEVENTH_LORD_REMEDIES)
- Delete hardcoded duplicates (DIGNITY_SIGNS block ~252-261, CHART_WEIGHTS ~263)

**Step 3: [PENDING] Test Compatibility**
```
cd /home/shrikrishna/astro/kundali && python3 main.py
```
- Expect: No ImportError, full report generates
- Check: All modules interoperate cleanly

**Step 4: [PENDING] Verify & Complete**
- Run `python3 -m pylint *.py` (optional)
- Test interactive input flow
- attempt_completion()

## Missing Constants to Add (Verified from printing.py)
```
DIGNITY_SIGNS = { ... }  # Matches dignity_table format
CHART_WEIGHTS = {'D1':1.0, 'D9':2.0, 'D10':1.0, 'D7':1.0}
LAGNA_REMEDIES = { ... }  # Lagna-specific remedies
SEVENTH_LORD_REMEDIES = { ... }  # 7th lord remedies
```

## Completion Criteria
- `python3 main.py` runs without ImportError
- Full kundali report prints/saves
- All modules compatible ✅

**Next Action: Proceed with Step 1 (constants.py edits)**
