# TODO: Fix Conceptual Mistakes in spouse_predictor.py and chart4.py

## Phase 1: spouse_predictor.py Fixes

### 1.1 Remove Non-Standard Dignities for Nodes (Rahu/Ketu)
- Location: DIGNITY_TABLE (~lines 100-150)
- Fix: Remove or mark Ra/Ke dignities as "non-classical" (empty dict)

### 1.2 Populate Nakshatra Qualities Dict
- Location: NAKSHATRA_QUALITIES (~lines 250-260)
- Fix: Populate with standard qualities (e.g., Ashwini: "Deer-like, fiery guna")

### 1.3 Fix Nadi Relations (Simplified)
- Location: signs_have_nadi_relation (~lines 800-810)
- Fix: Clarify as "Nadi-inspired" in comments; add degree-based check

### 1.4 Fix Jupiter Progression
- Location: get_progressed_jupiter_sign (~lines 820-830)
- Fix: Use degree progression (natal deg + age * 30°) % 360

### 1.5 Implement Full Neecha Bhanga Rules
- Location: _parse_neecha_bhanga (~lines 600-610)
- Fix: Implement full 7 BPHS rules (add rules D-G)

### 1.6 Fix Integrity Index Weighting
- Location: _parse_integrity_index (~lines 700-750)
- Fix: Weight D9 x2 for marriage (D1 > D9 for marriage per Jaimini)

### 1.7 Add Venus-Jupiter Aspect Check
- Location: Various analysis methods
- Fix: Add aspect check: if diff <10°, add "harmonious union" trait

### 1.8 Fix Moon Transit Day Filtering
- Location: get_moon_transit_days (~lines 900-950)
- Fix: Filter by auspicious tithis (2/3/5/7/10/11)

### 1.9 Fix Parser for Flexible Report Format
- Location: AdvancedChartParser (~lines 300-400)
- Fix: Use fuzzy regex with fallbacks

### 1.10 Remove Unsubstantiated Accuracy Claim
- Location: Header comment
- Fix: Remove or qualify as "hypothetical based on classical correlations"

## Phase 2: chart4.py Fixes

### 2.1 Fix Combustion Orbs for Retrograde
- Location: COMBUSTION_ORBS (~lines 50-60)
- Fix: Use BPHS exact: Me retro=12°, Ju retro=9°, etc.

### 2.2 Implement Full Neecha Bhanga Rules
- Location: NEECHA_BHANGA_INFO (~lines 70-80)
- Fix: Add all 7 BPHS rules; compute bhanga score (0-100%)

### 2.3 Fix Functional Classification for Mixed Lords
- Location: FUNCTIONAL_QUALITY (~lines 90-120)
- Fix: Reclassify trikona lords as "ben" unless dusthana co-owned

### 2.4 Expand get_dignity for Enemies/Friends
- Location: get_dignity function
- Fix: Include friend/enemy signs (+5 friendly, -5 enemy)

### 2.5 Add House Lords to D7/D10 Interpretation
- Location: interpret_d7, interpret_d10 (~lines 500-600)
- Fix: Add "D10 10th lord in [sign] indicates career via [house themes]"

### 2.6 Fix Vimshottari Dasha with SAV Integration
- Location: generate_timings, print_kundali (~lines 1000+)
- Fix: Weight by SAV points in 7th (e.g., +SAV/10)

### 2.7 Fix Gochara Transit Logic
- Location: gochara_effects, calculate_transits (~lines 1200+)
- Fix: Use ingress JD; add "approaching [house] in X days"

### 2.8 Personalize Remedies
- Location: detect_problems, print_kundali (~lines 1300+)
- Fix: Tailor: "For [dosha] in [Lagna], chant [mantra] on [tithi]"

### 2.9 Fix Ashtakavarga Thresholds
- Location: calculate_ashtakavarga, print_kundali (~lines 1100-1150)
- Fix: Align to standard (28/32 max); add "Sun bindus=3 → spouse authority"

### 2.10 Fix Gender Detection
- Location: calculate_kundali, print_kundali (main)
- Fix: Pass gender to all marriage sections; error if absent

### 2.11 Add Swiss Ephemeris Path Check
- Location: swe.set_ephe_path (~line 10)
- Fix: Add check: if not swe.get_ephe_path(), raise ValueError

## Phase 3: Testing & Validation
- Run with sample data (e.g., birth: 1990-01-01 12:00 Mumbai)
- Verify all fixes work correctly
- Ensure no syntax errors
