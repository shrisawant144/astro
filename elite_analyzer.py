#!/usr/bin/env python3
import re
import json
from collections import defaultdict
from datetime import datetime

class KundaliParser:
    def __init__(self, txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            self.content = f.read()
    
    def parse_all(self):
        return {
            'basic': self._parse_basic(),
            'planets_d1': self._parse_planets_section('Planets in Rasi'),
            'd9': self._parse_div_chart('Navamsa'),
            'd7': self._parse_div_chart('Saptamsa'),
            'd10': self._parse_div_chart('Dasamsa'),
            'houses': self._parse_houses(),
            'aspects': self._parse_aspects_detailed(),
            'yogas': self._parse_yogas_with_strength(),
            'doshas': self._parse_doshas_detailed(),
            'timings': self._parse_timings_detailed(),
            'dasha': self._parse_dasha_full(),
            'transits': self._parse_transits(),
            'remedies': self._parse_remedies()
        }
    
    def _parse_basic(self):
        data = {}
        patterns = [
            (r'Gender\s+:\s+(\w+)', 'gender'),
            (r'Lagna\s+:\s+(\w+)\s+([\d.]+)', 'lagna'),
            (r'Moon.*?:\s+(\w+)\s+–\s+(\w+)', 'moon'),
            (r'7th Lord\s+:\s+(\w+)', 'seventh_lord'),
            (r'Tithi\s+:\s+(.+)', 'tithi'),
            (r'Vara\s+:\s+(\w+)', 'vara')
        ]
        for pattern, key in patterns:
            if m := re.search(pattern, self.content):
                data[key] = m.groups() if len(m.groups()) > 1 else m.group(1)
        # Default gender if not found
        if 'gender' not in data:
            data['gender'] = 'Male'
        return data
    
    def _parse_planets_section(self, section_name):
        planets = {}
        if section := re.search(rf'{section_name}.*?\n-+\n(.*?)(?=\n\n)', self.content, re.DOTALL):
            for line in section.group(1).split('\n'):
                if m := re.match(r'\s*(\w+):\s+([\d.]+)°\s+(\w+)\s+(\w+)(?:\s+\(([^)]+)\))?(.*)', line):
                    planets[m.group(1)] = {
                        'deg': float(m.group(2)), 'sign': m.group(3),
                        'nak': m.group(4), 'dignity': m.group(5) or '',
                        'flags': m.group(6).strip()
                    }
        return planets
    
    def _parse_div_chart(self, name):
        div = {}
        if section := re.search(rf'{name}.*?\n-+\n(.*?)(?=\n\nDetailed)', self.content, re.DOTALL):
            for line in section.group(1).split('\n'):
                if m := re.match(r'\s*(\w+):\s+([\d.]+)°\s+(\w+)', line):
                    div[m.group(1)] = {'sign': m.group(3), 'deg': float(m.group(2))}
        return div
    
    def _parse_houses(self):
        houses = {}
        if section := re.search(r'Houses.*?\n-+\n(.*?)(?=\n\nAspects)', self.content, re.DOTALL):
            for line in section.group(1).split('\n'):
                if m := re.match(r'House\s+(\d+)\s+\((\w+)\):\s+(.+)', line):
                    houses[int(m.group(1))] = {
                        'sign': m.group(2),
                        'planets': m.group(3).split() if m.group(3) != '—' else []
                    }
        return houses
    
    def _parse_aspects_detailed(self):
        aspects = {}
        if section := re.search(r'Aspects.*?Full Analysis:(.*?)(?=\n\nFunctional)', self.content, re.DOTALL):
            current_house = None
            for line in section.group(1).split('\n'):
                if m := re.match(r'House\s+(\d+)', line):
                    current_house = int(m.group(1))
                    aspects[current_house] = {'planets': [], 'net': ''}
                elif current_house and '•' in line:
                    aspects[current_house]['planets'].append(line.strip())
                elif current_house and 'Net:' in line:
                    aspects[current_house]['net'] = line.strip()
        return aspects
    
    def _parse_yogas_with_strength(self):
        yogas = []
        if section := re.search(r'YOGAS.*?\n-+\n(.*?)(?=\n\n📅)', self.content, re.DOTALL):
            for line in section.group(1).split('\n'):
                if line.strip().startswith('•'):
                    yogas.append(line.strip()[2:])
        return yogas
    
    def _parse_doshas_detailed(self):
        doshas = []
        if section := re.search(r'PROBLEMS/DOSHAS.*?\n-+\n(.*?)(?=\n\nDetailed)', self.content, re.DOTALL):
            for line in section.group(1).split('\n'):
                if line.strip().startswith('•'):
                    doshas.append(line.strip()[2:])
        return doshas
    
    def _parse_timings_detailed(self):
        timings = {}
        if section := re.search(r'FRUCTIFICATION PERIODS.*?\n-+\n(.*?)(?=\n\n⚠)', self.content, re.DOTALL):
            current = None
            for line in section.group(1).split('\n'):
                if line and not line.startswith(' ') and ':' in line:
                    current = line.strip().rstrip(':')
                    timings[current] = []
                elif current and (line.strip().startswith('•') or line.strip().startswith('└')):
                    timings[current].append(line.strip())
        return timings
    
    def _parse_dasha_full(self):
        dasha = {}
        if m := re.search(r'Current.*?:\s*(\w+)\s*/\s*(\w+)(?:\s*/\s*(\w+))?', self.content):
            dasha = {'md': m.group(1), 'ad': m.group(2), 'pd': m.group(3)}
        return dasha
    
    def _parse_transits(self):
        transits = {}
        if section := re.search(r'Current Gochara.*?\n-+\n(.*?)(?=\n\n)', self.content, re.DOTALL):
            for line in section.group(1).split('\n'):
                if m := re.match(r'\s*(\w+):\s+(\w+)\s+\(house\s+(\d+)\)\s+–\s+(.+)', line):
                    transits[m.group(1)] = {
                        'sign': m.group(2), 'house': int(m.group(3)), 'effect': m.group(4)
                    }
        return transits
    
    def _parse_remedies(self):
        remedies = {}
        if section := re.search(r'TARGETED REMEDIES.*?\n-+\n(.*?)(?=\n\n)', self.content, re.DOTALL):
            current = None
            for line in section.group(1).split('\n'):
                if line and not line.startswith(' ') and ':' in line:
                    current = line.strip().rstrip(':')
                    remedies[current] = []
                elif current and line.strip().startswith('•'):
                    remedies[current].append(line.strip()[2:])
        return remedies


# Elite Planetary Engine Constants
PLANET_DIGNITY = {
    'Exalted': 30, 'Own': 20, 'Friendly': 10, 'Neutral': 0, 'Enemy': -10, 'Debilitated': -25
}

HOUSE_WEIGHTS = {
    1: 15, 2: 5, 3: 8, 4: 15, 5: 20, 6: -10, 7: 15, 8: -15, 9: 20, 10: 25, 11: 12, 12: -12
}

# Planetary Influence Matrix (interaction scores)
PLANET_MATRIX = {
    'Su': {'Mo': -5, 'Ma': 10, 'Me': -3, 'Ju': 8, 'Ve': -2, 'Sa': -12, 'Ra': -8, 'Ke': -6},
    'Mo': {'Su': -5, 'Ma': -4, 'Me': 7, 'Ju': 9, 'Ve': 8, 'Sa': -10, 'Ra': -15, 'Ke': -12},
    'Ma': {'Su': 10, 'Mo': -4, 'Me': -2, 'Ju': 6, 'Ve': -3, 'Sa': -8, 'Ra': 5, 'Ke': 4},
    'Me': {'Su': -3, 'Mo': 7, 'Ma': -2, 'Ju': 8, 'Ve': 9, 'Sa': -5, 'Ra': -4, 'Ke': -3},
    'Ju': {'Su': 8, 'Mo': 9, 'Ma': 6, 'Me': 8, 'Ve': 7, 'Sa': -6, 'Ra': -7, 'Ke': -5},
    'Ve': {'Su': -2, 'Mo': 8, 'Ma': -3, 'Me': 9, 'Ju': 7, 'Sa': -4, 'Ra': -6, 'Ke': -5},
    'Sa': {'Su': -12, 'Mo': -10, 'Ma': -8, 'Me': -5, 'Ju': -6, 'Ve': -4, 'Ra': 8, 'Ke': 7},
    'Ra': {'Su': -8, 'Mo': -15, 'Ma': 5, 'Me': -4, 'Ju': -7, 'Ve': -6, 'Sa': 8, 'Ke': -10},
    'Ke': {'Su': -6, 'Mo': -12, 'Ma': 4, 'Me': -3, 'Ju': -5, 'Ve': -5, 'Sa': 7, 'Ra': -10}
}

class EliteAnalyzer:
    def __init__(self, data):
        self.data = data
        self.insights = {}
        self.planet_powers = {}
        self.gender = data.get('basic', {}).get('gender', 'Male')
        self.spouse_term = "husband" if self.gender == "Female" else "wife"
        self.spouse_karaka = "Ju" if self.gender == "Female" else "Ve"
        self.spouse_karaka_full = "Jupiter" if self.gender == "Female" else "Venus"
    
    def analyze(self):
        self.insights['planetary_power'] = self._calculate_planetary_powers()
        self.insights['planetary_integrity'] = self._calculate_planetary_integrity()
        self.insights['influence_matrix'] = self._calculate_interplanetary_influence()
        self.insights['dimensional_strength'] = self._dimensional_analysis()
        self.insights['marriage_complexity'] = self._marriage_complexity_analysis()
        self.insights['karmic_patterns'] = self._karmic_pattern_detection()
        self.insights['life_trajectory'] = self._life_trajectory_model()
        self.insights['synergy_matrix'] = self._calculate_synergy()
        self.insights['predictive_timeline'] = self._predictive_modeling()
        self.insights['risk_opportunities'] = self._risk_opportunity_analysis()
        self.insights['optimal_strategies'] = self._strategy_optimization()
        self.insights['consciousness_level'] = self._consciousness_analysis()
        self.insights['resonance_index'] = self._calculate_resonance_index()
        self.insights['saturn_phases'] = self._saturn_maturity_analysis()
        return self.insights
    
    def _calculate_planetary_powers(self):
        """Weighted planetary strength calculation"""
        d1 = self.data['planets_d1']
        houses = self.data['houses']
        powers = {}
        
        for planet, info in d1.items():
            score = 50
            
            # Dignity scoring
            dignity = info.get('dignity', '')
            if 'Exalted' in dignity:
                score += PLANET_DIGNITY['Exalted']
            elif 'Own' in dignity:
                score += PLANET_DIGNITY['Own']
            elif 'Debilitated' in dignity:
                score += PLANET_DIGNITY['Debilitated']
            
            # House placement impact
            for house_no, house_data in houses.items():
                if planet in house_data['planets']:
                    score += HOUSE_WEIGHTS.get(house_no, 0)
                    break
            
            # Retrograde modifier (depth/intensity)
            if 'R' in info.get('flags', ''):
                score += 5
            
            # Combustion penalty
            if 'Combust' in info.get('flags', ''):
                score -= 15
            
            powers[planet] = {
                'raw_score': max(0, min(100, score)),
                'grade': self._grade_power(score),
                'dignity': dignity or 'Neutral',
                'modifiers': info.get('flags', '')
            }
            self.planet_powers[planet] = score
        
        return powers
    
    def _grade_power(self, score):
        if score >= 80: return 'A+ Exceptional'
        if score >= 70: return 'A Strong'
        if score >= 60: return 'B+ Good'
        if score >= 50: return 'B Average'
        if score >= 40: return 'C Weak'
        return 'D Critical'
    
    def _calculate_planetary_integrity(self):
        """Cross-chart integrity index for each planet (D1-D9-D10-D7 alignment)"""
        d1 = self.data['planets_d1']
        d9 = self.data['d9']
        d10 = self.data['d10']
        d7 = self.data['d7']
        
        # Dignity signs for each planet
        DIGNITY_SIGNS = {
            'Su': {'exalt': 'Aries', 'own': ['Leo'], 'deb': 'Libra'},
            'Mo': {'exalt': 'Taurus', 'own': ['Cancer'], 'deb': 'Scorpio'},
            'Ma': {'exalt': 'Capricorn', 'own': ['Aries', 'Scorpio'], 'deb': 'Cancer'},
            'Me': {'exalt': 'Virgo', 'own': ['Gemini', 'Virgo'], 'deb': 'Pisces'},
            'Ju': {'exalt': 'Cancer', 'own': ['Sagittarius', 'Pisces'], 'deb': 'Capricorn'},
            'Ve': {'exalt': 'Pisces', 'own': ['Taurus', 'Libra'], 'deb': 'Virgo'},
            'Sa': {'exalt': 'Libra', 'own': ['Capricorn', 'Aquarius'], 'deb': 'Aries'},
            'Ra': {'exalt': 'Gemini', 'own': [], 'deb': 'Sagittarius'},
            'Ke': {'exalt': 'Sagittarius', 'own': [], 'deb': 'Gemini'}
        }
        
        integrity = {}
        
        for planet in d1:
            score = 50  # Base score
            chart_positions = {'D1': d1[planet]['sign']}
            
            if planet in d9:
                chart_positions['D9'] = d9[planet]['sign']
            if planet in d10:
                chart_positions['D10'] = d10[planet]['sign']
            if planet in d7:
                chart_positions['D7'] = d7[planet]['sign']
            
            dig_info = DIGNITY_SIGNS.get(planet, {})
            strong_count = 0
            weak_count = 0
            
            for chart, sign in chart_positions.items():
                if sign == dig_info.get('exalt'):
                    score += 15 if chart == 'D1' else 10
                    strong_count += 1
                elif sign in dig_info.get('own', []):
                    score += 12 if chart == 'D1' else 8
                    strong_count += 1
                elif sign == dig_info.get('deb'):
                    score -= 15 if chart == 'D1' else 8
                    weak_count += 1
            
            # Vargottama bonus (same sign in D1 and D9)
            if planet in d9 and d1[planet]['sign'] == d9[planet]['sign']:
                score += 15
            
            # Triple alignment bonus (D1-D9-D10)
            if planet in d9 and planet in d10:
                if d1[planet]['sign'] == d9[planet]['sign'] == d10[planet]['sign']:
                    score += 20
            
            integrity[planet] = {
                'score': max(0, min(100, score)),
                'positions': chart_positions,
                'strong_charts': strong_count,
                'weak_charts': weak_count,
                'reliability': self._classify_reliability(score, strong_count, weak_count)
            }
        
        return integrity
    
    def _classify_reliability(self, score, strong, weak):
        if score >= 80 and weak == 0:
            return 'Highly Reliable (Triple Confirmation)'
        if score >= 65 and strong >= 2:
            return 'Reliable (Multi-Chart Support)'
        if score >= 50:
            return 'Moderate (Needs Activation)'
        if weak >= 2:
            return 'Challenged (Karmic Work Required)'
        return 'Variable (Context-Dependent)'
    
    def _marriage_complexity_analysis(self):
        """Analyze marriage afflictions, complexity, and realistic timing factors"""
        houses = self.data['houses']
        d1 = self.data['planets_d1']
        d9 = self.data['d9']
        
        analysis = {
            'complexity_score': 0,
            'afflictions': [],
            'positive_factors': [],
            'timing_modifiers': [],
            'realistic_assessment': ''
        }
        
        # Check 7th house afflictions
        seventh_planets = houses.get(7, {}).get('planets', [])
        
        # Rahu in 7th - unconventional partner
        if 'Ra' in seventh_planets:
            analysis['afflictions'].append({
                'factor': 'Rahu in 7th House',
                'impact': 'Unconventional partner, possible foreign/different background',
                'severity': 6
            })
            analysis['complexity_score'] += 15
        
        # Ketu in 7th - detachment issues
        if 'Ke' in seventh_planets:
            analysis['afflictions'].append({
                'factor': 'Ketu in 7th House',
                'impact': 'Spiritual detachment, past-life karmic bond',
                'severity': 5
            })
            analysis['complexity_score'] += 12
        
        # Saturn in 7th - delays
        if 'Sa' in seventh_planets:
            analysis['afflictions'].append({
                'factor': 'Saturn in 7th House',
                'impact': 'Delayed marriage, older/mature partner, long-term commitment',
                'severity': 4
            })
            analysis['complexity_score'] += 10
        
        # Mars in 7th - Manglik
        if 'Ma' in seventh_planets:
            analysis['afflictions'].append({
                'factor': 'Mars in 7th House (Manglik)',
                'impact': 'Passionate but potential conflicts, needs Manglik matching',
                'severity': 5
            })
            analysis['complexity_score'] += 12
        
        # 7th lord debilitated
        # Check if 7th lord is in debilitation
        seventh_lord_info = self.data['basic'].get('seventh_lord')
        if seventh_lord_info:
            seventh_lord = seventh_lord_info[0] if isinstance(seventh_lord_info, tuple) else seventh_lord_info
            if seventh_lord in d1:
                if 'Debilitated' in d1[seventh_lord].get('dignity', ''):
                    analysis['afflictions'].append({
                        'factor': '7th Lord Debilitated',
                        'impact': 'Marriage promise weakened, requires dasha activation',
                        'severity': 6
                    })
                    analysis['complexity_score'] += 15
        
        # Spouse karaka analysis (gender-specific)
        karaka = self.spouse_karaka
        if karaka in d1:
            karaka_dignity = d1[karaka].get('dignity', '')
            if 'Exalted' in karaka_dignity or 'Own' in karaka_dignity:
                analysis['positive_factors'].append({
                    'factor': f'{self.spouse_karaka_full} in Strong Dignity',
                    'impact': f'Strong {self.spouse_term} qualities indicated',
                    'strength': 8
                })
                analysis['complexity_score'] -= 10
            elif 'Debilitated' in karaka_dignity:
                analysis['afflictions'].append({
                    'factor': f'{self.spouse_karaka_full} Debilitated',
                    'impact': f'{self.spouse_term.capitalize()} karma requires conscious development',
                    'severity': 5
                })
                analysis['complexity_score'] += 12
        
        # D9 karaka check
        if karaka in d9:
            d9_sign = d9[karaka]['sign']
            if self.gender == "Female" and d9_sign in ['Cancer', 'Sagittarius', 'Pisces']:
                analysis['positive_factors'].append({
                    'factor': 'Jupiter strong in D9',
                    'impact': 'Husband qualities well-supported',
                    'strength': 7
                })
            elif self.gender == "Male" and d9_sign in ['Pisces', 'Taurus', 'Libra']:
                analysis['positive_factors'].append({
                    'factor': 'Venus strong in D9',
                    'impact': 'Wife qualities well-supported',
                    'strength': 7
                })
        
        # Calculate realistic assessment
        total_afflictions = sum(a['severity'] for a in analysis['afflictions'])
        total_positives = sum(p['strength'] for p in analysis['positive_factors'])
        net_score = total_positives - total_afflictions
        
        if net_score >= 10:
            analysis['realistic_assessment'] = 'Favorable marriage with minimal obstacles'
        elif net_score >= 0:
            analysis['realistic_assessment'] = 'Marriage will happen but with some karmic patterns to work through'
        elif net_score >= -10:
            analysis['realistic_assessment'] = 'Marriage possible with delays or unconventional circumstances'
        else:
            analysis['realistic_assessment'] = 'Significant karmic work required; timing needs careful analysis'
        
        analysis['net_marriage_score'] = 50 + net_score
        
        return analysis
    
    def _saturn_maturity_analysis(self):
        """Saturn maturity phases and their impact on life trajectory"""
        d1 = self.data['planets_d1']
        
        phases = []
        
        # Saturn return cycles
        phases.append({
            'age_range': '28-30',
            'phase': 'First Saturn Return',
            'significance': 'Major life restructuring, career crystallization, relationship maturity',
            'intensity': 'High'
        })
        phases.append({
            'age_range': '36',
            'phase': 'Saturn Maturity',
            'significance': 'Full Saturn significations manifest; career peak begins',
            'intensity': 'Peak'
        })
        phases.append({
            'age_range': '57-60',
            'phase': 'Second Saturn Return',
            'significance': 'Legacy building, wisdom transmission, life review',
            'intensity': 'High'
        })
        
        # Sade Sati impact assessment
        sade_sati_impact = {
            'current_phase': None,
            'intensity': 'None',
            'effects': []
        }
        
        # Check transits for Sade Sati (simplified)
        transits = self.data.get('transits', {})
        moon_sign = self.data['basic'].get('moon', ('', ''))[0] if self.data['basic'].get('moon') else ''
        
        if 'Sa' in transits:
            sat_transit = transits['Sa']
            sat_house = sat_transit.get('house', 0)
            
            if sat_house in [12, 1, 2]:
                phase_names = {12: 'Rising Phase', 1: 'Peak Phase', 2: 'Setting Phase'}
                sade_sati_impact['current_phase'] = phase_names.get(sat_house, 'Active')
                sade_sati_impact['intensity'] = 'High' if sat_house == 1 else 'Moderate'
                
                if sat_house == 1:
                    sade_sati_impact['effects'] = [
                        'Maximum karmic pressure on mind and emotions',
                        'Health vigilance required',
                        'Avoid major financial risks',
                        'Relationship patience critical'
                    ]
                elif sat_house == 2:
                    sade_sati_impact['effects'] = [
                        'Financial pressure or family restructuring',
                        'Speech karma active - choose words carefully',
                        'Family responsibilities increase',
                        'Marriage timing affected - delays possible'
                    ]
                elif sat_house == 12:
                    sade_sati_impact['effects'] = [
                        'Expenditure increases',
                        'Sleep/health surveillance needed',
                        'Foreign opportunities may arise',
                        'Spiritual awakening begins'
                    ]
        
        return {
            'maturity_phases': phases,
            'sade_sati': sade_sati_impact,
            'saturn_d1_status': d1.get('Sa', {}).get('dignity', 'Unknown')
        }

    def _calculate_interplanetary_influence(self):
        """Calculate planetary interaction matrix"""
        d1 = self.data['planets_d1']
        total_influence = 0
        interactions = []
        
        for p1 in d1:
            if p1 not in PLANET_MATRIX:
                continue
            for p2 in d1:
                if p1 != p2 and p2 in PLANET_MATRIX[p1]:
                    score = PLANET_MATRIX[p1][p2]
                    total_influence += score
                    if abs(score) >= 8:
                        interactions.append({
                            'pair': f'{p1}-{p2}',
                            'score': score,
                            'type': 'Synergy' if score > 0 else 'Conflict'
                        })
        
        return {
            'net_influence': total_influence,
            'harmony_level': self._classify_harmony(total_influence),
            'key_interactions': sorted(interactions, key=lambda x: abs(x['score']), reverse=True)[:5]
        }
    
    def _classify_harmony(self, score):
        if score > 50: return 'Highly Harmonious'
        if score > 20: return 'Balanced Positive'
        if score > -20: return 'Neutral'
        if score > -50: return 'Conflicted'
        return 'Highly Turbulent'
    
    def _calculate_resonance_index(self):
        """Multi-chart alignment score (D1-D9-D10)"""
        d1 = self.data['planets_d1']
        d9 = self.data['d9']
        d10 = self.data['d10']
        
        alignment = 0
        details = []
        
        for planet in d1:
            d1_sign = d1[planet]['sign']
            d9_match = planet in d9 and d9[planet]['sign'] == d1_sign
            d10_match = planet in d10 and d10[planet]['sign'] == d1_sign
            
            if d9_match:
                alignment += 10
                details.append(f'{planet}: D1-D9 aligned in {d1_sign}')
            if d10_match:
                alignment += 8
                details.append(f'{planet}: D1-D10 aligned in {d1_sign}')
        
        return {
            'score': alignment,
            'integrity': self._classify_integrity(alignment),
            'aligned_planets': details
        }
    
    def _classify_integrity(self, score):
        if score >= 50: return 'Destiny-Aligned (Exceptional)'
        if score >= 20: return 'Dual Path (Moderate)'
        return 'Fragmented (Needs Focus)'
    
    def _dimensional_analysis(self):
        scores = {}
        d1 = self.data['planets_d1']
        d9 = self.data['d9']
        d10 = self.data['d10']
        
        for area in ['Career', 'Marriage', 'Wealth', 'Spirituality', 'Health', 'Fame']:
            d1_score = self._score_d1_for_area(area, d1)
            d9_score = self._score_d9_for_area(area, d9)
            d10_score = self._score_d10_for_area(area, d10)
            
            consistency = abs(d1_score - d9_score) < 20
            scores[area] = {
                'd1': d1_score, 'd9': d9_score, 'd10': d10_score,
                'composite': int((d1_score * 0.5 + d9_score * 0.3 + d10_score * 0.2)),
                'consistency': 'High' if consistency else 'Variable',
                'reliability': 'Excellent' if consistency and d1_score > 70 else 'Moderate'
            }
        return scores
    
    def _score_d1_for_area(self, area, d1):
        """Dynamic area scoring using planetary powers"""
        score = 50
        
        # Gender-specific karakas for marriage
        marriage_planets = ['Ju', 'Mo', 'Ve'] if self.gender == "Female" else ['Ve', 'Mo', 'Ju']
        
        area_planets = {
            'Career': ['Su', 'Ma', 'Sa', 'Me'],
            'Marriage': marriage_planets,
            'Wealth': ['Ju', 'Ve', 'Me'],
            'Spirituality': ['Ju', 'Ke', 'Mo'],
            'Health': ['Su', 'Mo', 'Ma'],
            'Fame': ['Su', 'Ju', 'Ra']
        }
        
        for planet in area_planets.get(area, []):
            if planet in self.planet_powers:
                score += (self.planet_powers[planet] - 50) * 0.3
        
        return int(min(100, max(0, score)))
    
    def _score_d9_for_area(self, area, d9):
        score = 50
        if area == 'Marriage':
            # Gender-specific spouse karaka
            karaka = self.spouse_karaka
            if karaka in d9:
                if self.gender == "Female":
                    # Jupiter in own/exaltation signs for females
                    if d9[karaka]['sign'] in ['Cancer', 'Sagittarius', 'Pisces']:
                        score += 30
                else:
                    # Venus in own/exaltation signs for males
                    if d9[karaka]['sign'] in ['Pisces', 'Taurus', 'Libra']:
                        score += 30
        return min(100, score)
    
    def _score_d10_for_area(self, area, d10):
        score = 50
        if area == 'Career':
            if 'Ve' in d10 and d10['Ve']['sign'] == 'Pisces':
                score += 40
            if 'Su' in d10 and d10['Su']['sign'] == 'Leo':
                score += 35
        return min(100, score)
    
    def _karmic_pattern_detection(self):
        patterns = []
        houses = self.data['houses']
        
        if 8 in houses and houses[8]['planets']:
            patterns.append({
                'type': 'Transformation Karma',
                'intensity': 'High',
                'theme': 'Past-life debts in occult/hidden matters',
                'resolution': 'Through research, healing, or spiritual practices'
            })
        
        if 12 in houses and houses[12]['planets']:
            patterns.append({
                'type': 'Moksha Karma',
                'intensity': 'Medium',
                'theme': 'Liberation-oriented soul',
                'resolution': 'Foreign lands, isolation, or spiritual retreat'
            })
        
        return patterns
    
    def _life_trajectory_model(self):
        trajectory = {'phases': []}
        current_year = 2026
        
        phases_data = [
            (0, 28, 'Foundation'),
            (28, 42, 'Growth'),
            (42, 56, 'Peak'),
            (56, 70, 'Wisdom')
        ]
        
        for start_age, end_age, phase in phases_data:
            trajectory['phases'].append({
                'age': f'{start_age}-{end_age}',
                'phase': phase,
                'focus': self._get_phase_focus(phase),
                'challenges': self._get_phase_challenges(phase),
                'opportunities': self._get_phase_opportunities(phase)
            })
        
        return trajectory
    
    def _get_phase_focus(self, phase):
        focuses = {
            'Foundation': 'Education, skill building, early career',
            'Growth': 'Career advancement, marriage, wealth accumulation',
            'Peak': 'Authority, leadership, legacy building',
            'Wisdom': 'Mentorship, spirituality, giving back'
        }
        return focuses.get(phase, '')
    
    def _get_phase_challenges(self, phase):
        return ['Saturn delays', 'Dosha effects'] if phase == 'Foundation' else ['Competition']
    
    def _get_phase_opportunities(self, phase):
        return ['Yoga activation', 'Dasha alignment'] if phase == 'Growth' else ['Recognition']
    
    def _calculate_synergy(self):
        matrix = {}
        yogas = self.data['yogas']
        doshas = self.data['doshas']
        
        yoga_power = len([y for y in yogas if 'Strength' in y and int(re.search(r'(\d+)/10', y).group(1)) >= 7])
        dosha_burden = len([d for d in doshas if 'Severe' in d or 'Significant' in d])
        
        matrix['net_karmic_balance'] = yoga_power - dosha_burden
        matrix['synergy_score'] = min(100, max(0, 50 + (yoga_power * 10) - (dosha_burden * 15)))
        matrix['dominant_force'] = 'Yogas' if yoga_power > dosha_burden else 'Doshas' if dosha_burden > yoga_power else 'Balanced'
        
        return matrix
    
    def _predictive_modeling(self):
        """Probabilistic prediction engine with Bayesian-style weighting"""
        timeline = []
        timings = self.data['timings']
        yogas = self.data['yogas']
        doshas = self.data['doshas']
        
        # Calculate base factors
        yoga_strength = len([y for y in yogas if re.search(r'(\d+)/10', y) and int(re.search(r'(\d+)/10', y).group(1)) >= 7]) / max(len(yogas), 1)
        dosha_severity = len([d for d in doshas if 'Severe' in d or 'Significant' in d]) / max(len(doshas), 1)
        
        for event, periods in timings.items():
            for period in periods[:3]:
                if years := re.findall(r'(\d{4})-(\d{4})', period):
                    # Base probability from stars
                    base_prob = 0.75 if '★★★' in period else 0.55 if '★★' in period else 0.35
                    
                    # Dasha alignment bonus
                    dasha_match = re.search(r'(\w+)/(\w+)', period)
                    dasha_alignment = 0.15 if dasha_match else 0
                    
                    # Calculate event probability
                    probability = self._calculate_event_probability(
                        base_prob, yoga_strength, dosha_severity, dasha_alignment
                    )
                    
                    timeline.append({
                        'event': event,
                        'window': f"{years[0][0]}-{years[0][1]}",
                        'probability': probability,
                        'confidence': self._classify_probability(probability),
                        'dasha': dasha_match.groups() if dasha_match else None
                    })
        
        return sorted(timeline, key=lambda x: x['window'])
    
    def _calculate_event_probability(self, base, yoga_strength, dosha_severity, dasha_alignment):
        """Bayesian-style probability calculation"""
        prob = base
        prob += yoga_strength * 0.15
        prob -= dosha_severity * 0.20
        prob += dasha_alignment
        return round(min(max(prob, 0.05), 0.95), 2)
    
    def _classify_probability(self, prob):
        if prob >= 0.75: return 'Very High'
        if prob >= 0.60: return 'High'
        if prob >= 0.45: return 'Moderate'
        if prob >= 0.30: return 'Low'
        return 'Very Low'
    
    def _risk_opportunity_analysis(self):
        analysis = {'risks': [], 'opportunities': []}
        
        doshas = self.data['doshas']
        for dosha in doshas:
            if 'Severe' in dosha or 'Significant' in dosha:
                analysis['risks'].append({
                    'type': dosha.split(':')[0] if ':' in dosha else dosha,
                    'severity': 'High',
                    'mitigation': 'Remedies required'
                })
        
        yogas = self.data['yogas']
        for yoga in yogas:
            if strength_match := re.search(r'Strength (\d+)/10', yoga):
                if int(strength_match.group(1)) >= 7:
                    analysis['opportunities'].append({
                        'type': yoga.split('(')[0].strip(),
                        'strength': int(strength_match.group(1)),
                        'activation': 'High priority'
                    })
        
        return analysis
    
    def _strategy_optimization(self):
        strategies = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        dim_strength = self.insights.get('dimensional_strength', {})
        
        for area, scores in dim_strength.items():
            if scores['composite'] >= 80:
                strategies['immediate'].append(f"Capitalize on {area} strength now")
            elif scores['composite'] >= 60:
                strategies['short_term'].append(f"Develop {area} over 2-3 years")
            else:
                strategies['long_term'].append(f"Build {area} foundation gradually")
        
        return strategies
    
    def _consciousness_analysis(self):
        houses = self.data['houses']
        
        spiritual_score = 0
        if 9 in houses and houses[9]['planets']:
            spiritual_score += 20
        if 12 in houses and houses[12]['planets']:
            spiritual_score += 25
        
        yogas = self.data['yogas']
        if any('Jupiter' in y for y in yogas):
            spiritual_score += 15
        
        levels = {
            (0, 30): 'Material Focus',
            (30, 60): 'Balanced Path',
            (60, 100): 'Spiritual Orientation'
        }
        
        level = next(v for (low, high), v in levels.items() if low <= spiritual_score < high)
        
        return {
            'score': spiritual_score,
            'level': level,
            'path': 'Dharmic evolution through worldly success' if spiritual_score < 60 else 'Direct spiritual path'
        }


def generate_elite_report(insights, data):
    # Get gender information
    gender = data.get('basic', {}).get('gender', 'Male')
    spouse_term = "husband" if gender == "Female" else "wife"
    spouse_karaka = "Jupiter" if gender == "Female" else "Venus"
    
    lines = []
    lines.append("=" * 90)
    lines.append("🔮 ELITE KUNDALI INTELLIGENCE SYSTEM 3.0")
    lines.append("Weighted Planetary Engine • Integrity Index • Marriage Complexity • Saturn Phases")
    lines.append("=" * 90)
    lines.append(f"Gender: {gender} | {spouse_term.capitalize()} Karaka: {spouse_karaka}")
    lines.append("")
    lines.append("📊 SYSTEM CAPABILITIES:")
    lines.append("  ✓ Planetary Dignity Scoring (Exalted/Own/Debilitated)")
    lines.append("  ✓ Cross-Chart Planetary Integrity Index (D1-D9-D10-D7)")
    lines.append("  ✓ House Strength Weighting (Kendra/Trikona/Dusthana)")
    lines.append("  ✓ Interplanetary Influence Matrix (Synergy/Conflict Detection)")
    lines.append("  ✓ Multi-Chart Resonance Index (Vargottama + Triple Alignment)")
    lines.append("  ✓ Marriage Complexity Analysis (Afflictions + Realistic Assessment)")
    lines.append("  ✓ Saturn Maturity Phase Mapping (28-36-60 Cycles)")
    lines.append("  ✓ Sade Sati Impact Assessment")
    lines.append("  ✓ Bayesian Probability Modeling (Event Prediction)")
    lines.append("  ✓ Gender-Specific Karaka Analysis")
    lines.append("")
    lines.append("=" * 90)
    lines.append("")
    
    lines.append("🔬 DIMENSIONAL STRENGTH ANALYSIS")
    lines.append("-" * 90)
    for area, scores in insights['dimensional_strength'].items():
        area_display = area
        # Use gender-specific terminology for Marriage
        if area == 'Marriage':
            area_display = f"Marriage ({spouse_term.capitalize()})"
        bar = "█" * (scores['composite'] // 5) + "░" * (20 - scores['composite'] // 5)
        lines.append(f"{area_display:25} [{bar}] {scores['composite']}/100")
        lines.append(f"                          D1:{scores['d1']} D9:{scores['d9']} D10:{scores['d10']} | "
                    f"Consistency:{scores['consistency']} | Reliability:{scores['reliability']}")
    lines.append("")
    
    lines.append("🧬 KARMIC PATTERN DETECTION")
    lines.append("-" * 90)
    for pattern in insights['karmic_patterns']:
        lines.append(f"• {pattern['type']} (Intensity: {pattern['intensity']})")
        lines.append(f"  Theme: {pattern['theme']}")
        lines.append(f"  Resolution: {pattern['resolution']}")
    lines.append("")
    
    lines.append("📈 LIFE TRAJECTORY MODEL")
    lines.append("-" * 90)
    for phase in insights['life_trajectory']['phases']:
        lines.append(f"Ages {phase['age']} - {phase['phase']} Phase")
        lines.append(f"  Focus: {phase['focus']}")
        lines.append(f"  Challenges: {', '.join(phase['challenges'])}")
        lines.append(f"  Opportunities: {', '.join(phase['opportunities'])}")
    lines.append("")
    
    lines.append("⚡ SYNERGY MATRIX")
    lines.append("-" * 90)
    matrix = insights['synergy_matrix']
    lines.append(f"Net Karmic Balance: {matrix['net_karmic_balance']:+d}")
    lines.append(f"Synergy Score: {matrix['synergy_score']}/100")
    lines.append(f"Dominant Force: {matrix['dominant_force']}")
    lines.append("")
    
    lines.append("⚡ PLANETARY POWER INDEX")
    lines.append("-" * 90)
    for planet, power in insights['planetary_power'].items():
        score = power['raw_score']
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        lines.append(f"{planet:8} [{bar}] {score}/100 | {power['grade']}")
        if power['dignity'] != 'Neutral':
            lines.append(f"         Dignity: {power['dignity']} | Modifiers: {power['modifiers'] or 'None'}")
    lines.append("")
    
    lines.append("🌐 INTERPLANETARY INFLUENCE MATRIX")
    lines.append("-" * 90)
    influence = insights['influence_matrix']
    lines.append(f"Net Influence Score: {influence['net_influence']:+d}")
    lines.append(f"Harmony Level: {influence['harmony_level']}")
    lines.append("\nKey Interactions:")
    for interaction in influence['key_interactions']:
        symbol = "⚡" if interaction['type'] == 'Synergy' else "⚠️"
        lines.append(f"  {symbol} {interaction['pair']}: {interaction['score']:+d} ({interaction['type']})")
    lines.append("")
    
    lines.append("🔗 DIVISIONAL RESONANCE INDEX")
    lines.append("-" * 90)
    resonance = insights['resonance_index']
    lines.append(f"Alignment Score: {resonance['score']}/100")
    lines.append(f"Destiny Integrity: {resonance['integrity']}")
    if resonance['aligned_planets']:
        lines.append("\nAligned Planets:")
        for detail in resonance['aligned_planets'][:5]:
            lines.append(f"  • {detail}")
    lines.append("")
    
    # NEW: Planetary Integrity Index
    lines.append("🔬 PLANETARY INTEGRITY INDEX (Cross-Chart Resonance)")
    lines.append("-" * 90)
    lines.append("(Measures each planet's consistency across D1-D9-D10-D7 charts)")
    lines.append("")
    for planet, integrity in insights['planetary_integrity'].items():
        score = integrity['score']
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        positions = integrity['positions']
        pos_str = " | ".join([f"{k}:{v}" for k, v in positions.items()])
        lines.append(f"{planet:4} [{bar}] {score:3}/100 | {integrity['reliability']}")
        lines.append(f"     Positions: {pos_str}")
    lines.append("")
    
    # NEW: Marriage Complexity Analysis
    lines.append(f"💍 MARRIAGE COMPLEXITY ANALYSIS ({spouse_term.upper()} KARMA)")
    lines.append("-" * 90)
    marriage = insights['marriage_complexity']
    lines.append(f"Net Marriage Score: {marriage['net_marriage_score']}/100")
    lines.append(f"Realistic Assessment: {marriage['realistic_assessment']}")
    lines.append("")
    if marriage['afflictions']:
        lines.append("AFFLICTIONS (Complexity Factors):")
        for aff in marriage['afflictions']:
            lines.append(f"  ⚠️ {aff['factor']} (Severity: {aff['severity']}/10)")
            lines.append(f"     → {aff['impact']}")
    if marriage['positive_factors']:
        lines.append("\nPOSITIVE FACTORS:")
        for pos in marriage['positive_factors']:
            lines.append(f"  ✓ {pos['factor']} (Strength: {pos['strength']}/10)")
            lines.append(f"     → {pos['impact']}")
    lines.append("")
    
    # NEW: Saturn Maturity & Sade Sati Analysis
    lines.append("🪐 SATURN MATURITY & SADE SATI ANALYSIS")
    lines.append("-" * 90)
    saturn = insights['saturn_phases']
    lines.append(f"Saturn D1 Status: {saturn['saturn_d1_status']}")
    lines.append("")
    lines.append("MATURITY PHASES:")
    for phase in saturn['maturity_phases']:
        lines.append(f"  Age {phase['age_range']}: {phase['phase']} ({phase['intensity']} Intensity)")
        lines.append(f"    → {phase['significance']}")
    
    sade = saturn['sade_sati']
    if sade['current_phase']:
        lines.append("")
        lines.append(f"⚠️ SADE SATI ACTIVE: {sade['current_phase']} (Intensity: {sade['intensity']})")
        lines.append("   Effects:")
        for effect in sade['effects']:
            lines.append(f"   • {effect}")
    else:
        lines.append("")
        lines.append("✓ No active Sade Sati - Saturn transit not in critical position")
    lines.append("")
    
    lines.append("🎯 PREDICTIVE TIMELINE (Probabilistic Model)")
    lines.append("-" * 90)
    for event in insights['predictive_timeline'][:10]:
        prob_pct = int(event['probability'] * 100)
        conf_bar = "●" * (prob_pct // 10) + "○" * (10 - prob_pct // 10)
        lines.append(f"{event['window']}: {event['event']}")
        lines.append(f"           [{conf_bar}] {prob_pct}% | Confidence: {event['confidence']}")
        if event['dasha']:
            lines.append(f"           Dasha: {event['dasha'][0]}/{event['dasha'][1]}")
    lines.append("")
    
    lines.append("⚠️  RISK & OPPORTUNITY ANALYSIS")
    lines.append("-" * 90)
    lines.append("RISKS:")
    for risk in insights['risk_opportunities']['risks'][:5]:
        lines.append(f"  • {risk['type']} (Severity: {risk['severity']}) → {risk['mitigation']}")
    lines.append("\nOPPORTUNITIES:")
    for opp in insights['risk_opportunities']['opportunities'][:5]:
        lines.append(f"  • {opp['type']} (Strength: {opp['strength']}/10) → {opp['activation']}")
    lines.append("")
    
    lines.append("🎲 OPTIMAL STRATEGIES")
    lines.append("-" * 90)
    strat = insights['optimal_strategies']
    lines.append("IMMEDIATE (0-6 months):")
    for s in strat['immediate']:
        lines.append(f"  • {s}")
    lines.append("\nSHORT-TERM (6 months - 3 years):")
    for s in strat['short_term']:
        lines.append(f"  • {s}")
    lines.append("\nLONG-TERM (3+ years):")
    for s in strat['long_term']:
        lines.append(f"  • {s}")
    lines.append("")
    
    lines.append("🧘 CONSCIOUSNESS LEVEL ANALYSIS")
    lines.append("-" * 90)
    cons = insights['consciousness_level']
    lines.append(f"Spiritual Score: {cons['score']}/100")
    lines.append(f"Consciousness Level: {cons['level']}")
    lines.append(f"Evolutionary Path: {cons['path']}")
    lines.append("")
    
    lines.append("=" * 90)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 90)
    
    return "\n".join(lines)


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python elite_analyzer.py <kundali_report.txt>")
        sys.exit(1)
    
    txt_file = sys.argv[1]
    
    print("🔮 Parsing kundali...")
    parser = KundaliParser(txt_file)
    data = parser.parse_all()
    
    print("🧠 Elite analysis in progress...")
    analyzer = EliteAnalyzer(data)
    insights = analyzer.analyze()
    
    print("📊 Generating outputs...")
    
    json_file = txt_file.replace('.txt', '_elite.json')
    with open(json_file, 'w') as f:
        json.dump({'data': data, 'insights': insights}, f, indent=2)
    print(f"✓ JSON: {json_file}")
    
    report = generate_elite_report(insights, data)
    report_file = txt_file.replace('.txt', '_elite_report.txt')
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"✓ Report: {report_file}")
    
    print("\n" + report)


if __name__ == '__main__':
    main()
