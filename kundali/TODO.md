# Multi-Ayanamsa + D60 Implementation TODO

## Status: In Progress

### [ ] 1. Update constants.py
- Add AYANAMSA_OPTIONS dict
- Add DEFAULT_AYANAMSA = "Lahiri"

### [x] 2. Update utils.py
- Add get_d60_sign_and_deg(full_lon) function (complete implementation)

### [x] 3. Update main.py
- Import AYANAMSA_OPTIONS/DEFAULT_AYANAMSA ✓
- Add ayanamsa_name param to calculate_kundali() ✓
- CLI input for ayanamsa_choice + validation ✓
- swe.set_sid_mode(ayanamsa_code) in calculate_kundali ✓
- result["ayanamsa"] = ayanamsa_name ✓
- Import get_d60_sign_and_deg ✓
- Compute D60 for all planets (after D9/D7/D10 loop) ✓
- Add result["d60"] dict ✓

### [x] 4. Update interpretations.py
- Add complete interpret_d60(result) function (full task code) ✓

### [x] 5. Update printing.py
- Header: add Ayanamsa line ✓
- div loop: add ("d60", "Shashtiamsa (D60 – Past Life Karma)", interpret_d60) ✓
- Imports: add interpret_d60 to interpretations import ✓

### [ ] 6. Test
- cd /home/miko/astro/kundali && python3 main.py
- Verify: Ayanamsa prompt/options, Lahiri default works, D60 table/interpretations print, no errors

### [ ] 7. Complete
- attempt_completion

