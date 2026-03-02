import re
import swisseph as swe
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# ────────────────────────────────────────────────
# Swiss Ephemeris Setup
# ────────────────────────────────────────────────
swe.set_ephe_path(".")  # Put seas_18.se1, sepl_18.se1, semo_18.se1 etc. in this folder
swe.set_sid_mode(swe.SIDM_LAHIRI)
zodiac_signs = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]
nakshatras = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]
dasha_lords = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]
dasha_periods = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}
nakshatra_lord_index = [0, 1, 2, 3, 4, 5, 6, 7, 8] * 3
planets = {
    "Su": swe.SUN,
    "Mo": swe.MOON,
    "Ma": swe.MARS,
    "Me": swe.MERCURY,
    "Ju": swe.JUPITER,
    "Ve": swe.VENUS,
    "Sa": swe.SATURN,
    "Ra": swe.MEAN_NODE,
}
dignity_table = {
    "Su": {"own": "Leo", "exalt": "Aries", "deb": "Libra"},
    "Mo": {"own": "Cancer", "exalt": "Taurus", "deb": "Scorpio"},
    "Ma": {"own": ["Aries", "Scorpio"], "exalt": "Capricorn", "deb": "Cancer"},
    "Me": {"own": ["Gemini", "Virgo"], "exalt": "Virgo", "deb": "Pisces"},
    "Ju": {"own": ["Sagittarius", "Pisces"], "exalt": "Cancer", "deb": "Capricorn"},
    "Ve": {"own": ["Taurus", "Libra"], "exalt": "Pisces", "deb": "Virgo"},
    "Sa": {"own": ["Capricorn", "Aquarius"], "exalt": "Libra", "deb": "Aries"},
    # Rahu/Ketu: No classical consensus on exaltation/debilitation exists.
    # Some traditions use Taurus/Scorpio, others Gemini/Sagittarius, others Virgo/Pisces.
    # We omit dignity labels for nodes to avoid implying false certainty.
    "Ra": {},
    "Ke": {},
}
gochara_effects = {
    "Su": {
        1: "Good for health",
        2: "Expenses",
        3: "Short travels",
        4: "Home happiness",
        5: "Children luck",
        6: "Enemies/defeat",
        7: "Marriage/partners",
        8: "Obstacles",
        9: "Luck",
        10: "Career",
        11: "Gains",
        12: "Losses",
    },
    "Mo": {
        1: "Peace",
        2: "Family issues",
        3: "Communication",
        4: "Mother/home",
        5: "Creativity",
        6: "Health issues",
        7: "Relations",
        8: "Secrets",
        9: "Travel",
        10: "Status",
        11: "Friends",
        12: "Isolation",
    },
    "Ma": {
        1: "Energy",
        2: "Arguments",
        3: "Courage",
        4: "Property",
        5: "Speculation",
        6: "Victory",
        7: "Conflicts",
        8: "Accidents",
        9: "Father",
        10: "Authority",
        11: "Ambition",
        12: "Hidden enemies",
    },
    "Me": {
        1: "Intellect",
        2: "Learning",
        3: "Siblings",
        4: "Education",
        5: "Wit",
        6: "Debts",
        7: "Trade",
        8: "Research",
        9: "Philosophy",
        10: "Communication",
        11: "Networks",
        12: "Imagination",
    },
    "Ju": {
        1: "Growth",
        2: "Wealth",
        3: "Knowledge",
        4: "Comfort",
        5: "Wisdom",
        6: "Service",
        7: "Harmony",
        8: "Occult",
        9: "Guru",
        10: "Success",
        11: "Prosperity",
        12: "Charity",
    },
    "Ve": {
        1: "Charm",
        2: "Luxury",
        3: "Arts",
        4: "Vehicles",
        5: "Romance",
        6: "Pleasures",
        7: "Love",
        8: "Intimacy",
        9: "Beauty",
        10: "Fame",
        11: "Income",
        12: "Expenses on fun",
    },
    "Sa": {
        1: "Discipline",
        2: "Stability",
        3: "Hard work",
        4: "Roots",
        5: "Karma",
        6: "Delays",
        7: "Commitments",
        8: "Transformation",
        9: "Dharma",
        10: "Career hurdles",
        11: "Long-term gains",
        12: "Isolation",
    },
    "Ra": {
        1: "Ambition",
        2: "Unusual gains",
        3: "Adventures",
        4: "Foreign home",
        5: "Innovation",
        6: "Obsession",
        7: "Unconventional partners",
        8: "Sudden changes",
        9: "Spiritual quests",
        10: "Power struggles",
        11: "Mass gains",
        12: "Karmic losses",
    },
    "Ke": {
        1: "Detachment",
        2: "Mysticism",
        3: "Intuition",
        4: "Spiritual home",
        5: "Past karma",
        6: "Healing",
        7: "Karmic ties",
        8: "Release",
        9: "Moksha",
        10: "Hidden talents",
        11: "Sudden losses",
        12: "Enlightenment",
    },
}
sign_lords = {
    "Aries": "Ma",
    "Taurus": "Ve",
    "Gemini": "Me",
    "Cancer": "Mo",
    "Leo": "Su",
    "Virgo": "Me",
    "Libra": "Ve",
    "Scorpio": "Ma",
    "Sagittarius": "Ju",
    "Capricorn": "Sa",
    "Aquarius": "Sa",
    "Pisces": "Ju",
}
short_to_full = {
    "Su": "Sun",
    "Mo": "Moon",
    "Ma": "Mars",
    "Me": "Mercury",
    "Ju": "Jupiter",
    "Ve": "Venus",
    "Sa": "Saturn",
    "Ra": "Rahu",
    "Ke": "Ketu",
}

# ────────────────────────────────────────────────
# Combustion Orbs (degrees from Sun for combustion)
# Source: Brihat Parashara Hora Shastra
# ────────────────────────────────────────────────
COMBUSTION_ORBS = {
    "Mo": (12, 12),   # (direct, retrograde) — Moon is never retrograde but uniform
    "Ma": (17, 17),
    "Me": (14, 12),
    "Ju": (11, 11),
    "Ve": (10, 8),
    "Sa": (15, 15),
}  # Ra/Ke/Su not affected

# ────────────────────────────────────────────────
# Neecha Bhanga (Cancelled Debilitation) Data
# Rules (Parashari):
#   A – Lord of debilitation sign in kendra from Lagna or Moon
#   B – Planet exalted in debilitation sign is in kendra from Lagna or Moon
#   C – Debilitated planet itself is in kendra from Lagna or Moon
# ────────────────────────────────────────────────
NEECHA_BHANGA_INFO = {
    # planet: (deb_sign_lord, planet_exalted_in_deb_sign)
    "Su": ("Ve", "Sa"),   # Sun deb Libra; Libra lord=Ve; Saturn exalts in Libra
    "Mo": ("Ma", None),   # Moon deb Scorpio; Scorpio lord=Ma; no classical exalt in Scorpio
    "Ma": ("Mo", "Ju"),   # Mars deb Cancer; Cancer lord=Mo; Jupiter exalts in Cancer
    "Me": ("Ju", "Ve"),   # Mercury deb Pisces; Pisces lord=Ju; Venus exalts in Pisces
    "Ju": ("Sa", "Ma"),   # Jupiter deb Capricorn; Capricorn lord=Sa; Mars exalts in Capricorn
    "Ve": ("Me", "Me"),   # Venus deb Virgo; Virgo lord=Me; Mercury exalts in Virgo
    "Sa": ("Ma", "Su"),   # Saturn deb Aries; Aries lord=Ma; Sun exalts in Aries
}

# ────────────────────────────────────────────────
# Functional Benefics / Malefics by Lagna
# Source: Parashari rules (kendra/trikona lords)
# Categories:
#   ben    = Functional benefics (trikona lords, lagna lord)
#   mal    = Functional malefics (6/8/12 lords, or dusthana-heavy)
#   maraka = Maraka (2nd/7th lords – can cause death/harm in their dashas)
#   mixed  = Mixed nature (owns one good + one bad house)
#   yk     = Yogakaraka (owns both kendra + trikona)
# ────────────────────────────────────────────────
FUNCTIONAL_QUALITY = {
    # Aries: Su(5), Ju(9,12), Ma(1,8) | Me(3,6), Ve(2,7), Sa(10,11)
    "Aries":       {"ben": ["Su", "Ju"], "mal": ["Me", "Sa"], "maraka": ["Ve"], "mixed": ["Ma"], "yk": None},
    # Taurus: Ve(1,6), Me(2,5), Sa(9,10) | Ju(8,11), Mo(3), Ma(7,12)
    "Taurus":      {"ben": ["Me", "Sa"], "mal": ["Ju"], "maraka": ["Ma"], "mixed": ["Ve", "Mo"], "yk": "Sa"},
    # Gemini: Ve(5,12), Me(1,4), Sa(8,9) | Ju(7,10), Su(3), Ma(6,11)
    "Gemini":      {"ben": ["Me"], "mal": ["Ma"], "maraka": ["Ju"], "mixed": ["Ve", "Sa", "Su"], "yk": None},
    # Cancer: Ma(5,10), Ju(6,9), Mo(1) | Me(3,12), Ve(4,11), Sa(7,8)
    "Cancer":      {"ben": ["Mo", "Ma", "Ju"], "mal": ["Me", "Ve"], "maraka": ["Sa"], "mixed": [], "yk": "Ma"},
    # Leo: Su(1), Ma(4,9), Ju(5,8) | Me(2,11), Ve(3,10), Sa(6,7)
    "Leo":         {"ben": ["Su", "Ma"], "mal": ["Sa"], "maraka": ["Me"], "mixed": ["Ju", "Ve"], "yk": "Ma"},
    # Virgo: Ve(2,9), Me(1,10), Sa(5,6) | Ma(3,8), Ju(4,7), Mo(11)
    "Virgo":       {"ben": ["Ve", "Me"], "mal": ["Ma"], "maraka": ["Ju"], "mixed": ["Sa", "Mo"], "yk": None},
    # Libra: Sa(4,5), Ve(1,8), Me(9,12) | Ju(3,6), Su(11), Ma(2,7)
    "Libra":       {"ben": ["Sa", "Me"], "mal": ["Ju", "Su"], "maraka": ["Ma"], "mixed": ["Ve"], "yk": "Sa"},
    # Scorpio: Ju(2,5), Mo(9), Su(10) | Me(8,11), Ve(7,12), Sa(3,4)
    "Scorpio":     {"ben": ["Mo", "Su", "Ju"], "mal": ["Me"], "maraka": ["Ve"], "mixed": ["Sa"], "yk": "Mo"},
    # Sagittarius: Su(9), Ma(5,12), Ju(1,4) | Ve(6,11), Me(7,10), Sa(2,3)
    "Sagittarius": {"ben": ["Su", "Ju"], "mal": ["Ve"], "maraka": ["Me", "Sa"], "mixed": ["Ma"], "yk": None},
    # Capricorn: Ve(5,10), Me(6,9), Sa(1,2) | Ju(3,12), Ma(4,11), Mo(7)
    "Capricorn":   {"ben": ["Ve", "Sa"], "mal": ["Ju"], "maraka": ["Mo"], "mixed": ["Me", "Ma"], "yk": "Ve"},
    # Aquarius: Ve(4,9), Sa(1,12), Me(5,8) | Ju(2,11), Mo(6), Ma(3,10)
    "Aquarius":    {"ben": ["Ve"], "mal": ["Mo"], "maraka": ["Ju"], "mixed": ["Sa", "Me", "Ma"], "yk": "Ve"},
    # Pisces: Ju(1,10), Mo(5), Ma(2,9) | Sa(11,12), Ve(3,8), Me(4,7)
    "Pisces":      {"ben": ["Ju", "Mo", "Ma"], "mal": ["Sa", "Ve"], "maraka": ["Me"], "mixed": [], "yk": None},
}

# ────────────────────────────────────────────────
# Panchanga Names
# ────────────────────────────────────────────────
TITHI_NAMES = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
]
YOGA_NAMES = [
    "Vishkamba", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Mahendra", "Vaidhriti",
]
KARANA_REPEATING = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# House lord → placement meaning (lord of house A placed in house B)
HOUSE_LORD_IN_HOUSE = {
    # ── Lord of H1 (Self / Lagna) ──
    (1,  1): "Strong, self-reliant personality; health and vitality prominent; life is self-driven.",
    (1,  2): "Wealth and family shape identity; skilled in speech; face is a fortunate asset.",
    (1,  3): "Courageous and communicative; siblings and short travel define life greatly.",
    (1,  4): "Deeply rooted in home and mother; domestic comfort is a life priority.",
    (1,  5): "Creative, intelligent, child-oriented life; fame possible through wisdom or arts.",
    (1,  6): "Life centred on service, health, or competition; enemies demand vigilance.",
    (1,  7): "Partnerships are central to identity; marriage-oriented; may settle abroad.",
    (1,  8): "Transformative, occult-drawn life; longevity issues possible; deep hidden strengths.",
    (1,  9): "Highly fortunate; life guided by dharma, luck, and father's blessings.",
    (1, 10): "Career and authority are powerfully expressed; public recognition is strong.",
    (1, 11): "Gains and social networks prosper naturally; desires fulfilled with effort.",
    (1, 12): "Spiritual, isolated, or foreign-oriented life; expenditure-prone; hidden tendencies.",
    # ── Lord of H2 (Wealth / Family / Speech) ──
    (2,  1): "Wealth comes through personality and initiative; strong family presence in self.",
    (2,  2): "Very strong wealth house; speech, food, and family are major life assets.",
    (2,  3): "Wealth through communication, writing, or trade; siblings involved in finances.",
    (2,  4): "Family wealth through property and mother; financial security via real estate.",
    (2,  5): "Wealth through children, creativity, or speculation; rich family legacy.",
    (2,  6): "Debt and health expenses affect wealth; income possible from service or medicine.",
    (2,  7): "Wealth through partnerships and marriage; business-minded spouse; joint finances.",
    (2,  8): "Transformative events affect finances; possible inheritance or sudden gains/losses.",
    (2,  9): "Wealth through luck, dharma, father's legacy, or religious activities.",
    (2, 10): "Wealth through career and public status; financial recognition and high income.",
    (2, 11): "Excellent for wealth — 2nd lord in 11H: strong income, gains, and accumulation.",
    (2, 12): "Expenses drain wealth; foreign expenditure or spiritual spending dominates.",
    # ── Lord of H3 (Courage / Communication / Siblings) ──
    (3,  1): "Brave, communicative personality; siblings influential; self-expression is bold.",
    (3,  2): "Communication skills bring wealth; writing, speaking, or media = income.",
    (3,  3): "Very strong courage and communication; siblings prosper; own writing/media.",
    (3,  4): "Communication rooted in home and education; home-based literary or creative work.",
    (3,  5): "Courage and creativity merge; arts, writing, and romance flourish; creative children.",
    (3,  6): "Courage used against enemies in competition; physical activity guards health.",
    (3,  7): "Spouse is communicative or a sibling-like figure; business partnerships through media.",
    (3,  8): "Communication about secrets or occult; hidden writings; siblings face challenges.",
    (3,  9): "Philosophical and dharmic communication; sibling is spiritual; travel for religion.",
    (3, 10): "Career in communication, media, writing, IT, or travel; prominent public speaker.",
    (3, 11): "Gains through communication, media, or siblings; income from writing or trade.",
    (3, 12): "Communications lead to foreign connections or isolation; siblings may live abroad.",
    # ── Lord of H4 (Home / Mother / Property / Happiness) ──
    (4,  1): "Domestic comfort and mother shape personality; deep attachment to homeland.",
    (4,  2): "Family property is a primary source of wealth; home is investment vehicle.",
    (4,  3): "Communication about property; home-based business; travels for domestic reasons.",
    (4,  4): "Very strong home, mother, and property themes; deeply domestic and content.",
    (4,  5): "Creative, educated home; children bring happiness; home is a place of learning.",
    (4,  6): "Domestic conflicts; mother's health may suffer; property disputes possible.",
    (4,  7): "Happy domestic married life; spouse settles at home; property gained through marriage.",
    (4,  8): "Inheritance of property; home linked to transformations; ancestral real estate.",
    (4,  9): "Highly fortunate home; spiritual, educated household; father's property benefits.",
    (4, 10): "Career in real estate, construction, or governance; mother's name attached to career.",
    (4, 11): "Gains through property; home brings income; mother connected to social success.",
    (4, 12): "Foreign residence; home is abroad or spiritual retreat; hidden domestic challenges.",
    # ── Lord of H5 (Children / Creativity / Intelligence / Speculation) ──
    (5,  1): "Intelligent, creative personality; children are important; natural teacher or adviser.",
    (5,  2): "Children and creativity bring wealth; income through speculation, arts, or education.",
    (5,  3): "Creativity in communication; children are communicative; artistic or literary nature.",
    (5,  4): "Creative, educated home environment; children live at home; happiness through intellect.",
    (5,  5): "Very strong creativity and intelligence; own sign lord — excellent for children and arts.",
    (5,  6): "Challenges with children or creative projects; speculative losses possible; serve creatively.",
    (5,  7): "Marriage brings children and creativity; romantic partnership; creative spouse.",
    (5,  8): "Secret or past-life creative debts; occult intellect; children may face early hardships.",
    (5,  9): "Most auspicious — trikona lord in trikona; excellent luck, children, and wisdom.",
    (5, 10): "Career in education, arts, performance, or child-related fields; fame through creativity.",
    (5, 11): "Gains through creativity, children, or speculation; income from arts or education.",
    (5, 12): "Hidden creativity; spiritual philosophy; children may live abroad; isolated artistry.",
    # ── Lord of H6 (Enemies / Debt / Disease / Service) ──
    (6,  1): "Competitive, service-oriented personality; health demands attention; argumentative.",
    (6,  2): "Debts affect wealth; family enemies possible; income from medical or service field.",
    (6,  3): "Courage against enemies; siblings may create conflict; competitive communication.",
    (6,  4): "Domestic enmity or disputes; mother's health could suffer; unhappy home possible.",
    (6,  5): "Enemies of creative work; health issues in romance; service-oriented creativity.",
    (6,  6): "Very strong in competition — enemies defeated repeatedly; also amplified conflicts.",
    (6,  7): "Conflicts in marriage; spouse may be adversarial; legal disputes in partnership.",
    (6,  8): "Enemies trigger transformation; hidden health crises; intense karmic struggle.",
    (6,  9): "Dharma tested through service and health; father's health may suffer.",
    (6, 10): "Career in litigation, military, medicine, or competitive fields; enemies at workplace.",
    (6, 11): "Gains by defeating enemies; income from service, medicine, or competitive work.",
    (6, 12): "Enemies abroad; hospitalization or secret enmity; health complications in isolation.",
    # ── Lord of H7 (Marriage / Partnership / Business) ──
    (7,  1): "Spouse reflects the native's own identity; self-oriented in marriage; strong partnerships.",
    (7,  2): "Spouse brings wealth and family harmony; marriage is financially rewarding.",
    (7,  3): "Spouse is communicative or from nearby area; business through communication field.",
    (7,  4): "Spouse settles in native's home; happy domestic married life; property through marriage.",
    (7,  5): "Marriage brings children and creativity; deeply romantic union; creative, wise spouse.",
    (7,  6): "Marital conflicts or health issues in marriage; spouse may be competitive or adversarial.",
    (7,  7): "Very powerful marriage and business partnerships; spouse very prominent in life.",
    (7,  8): "Transformative marriage; spouse has occult interests; longevity in marriage is complex.",
    (7,  9): "Very fortunate marriage — 7th lord in 9H is highly auspicious; wise, dharmic spouse.",
    (7, 10): "Spouse connected to career; marriage enhances public status; business with spouse.",
    (7, 11): "Gains through marriage; financially beneficial partnership; spouse fulfils aspirations.",
    (7, 12): "Foreign spouse; expenses through marriage; spiritual or isolated union; spouse abroad.",
    # ── Lord of H8 (Longevity / Transformation / Occult / Inheritance) ──
    (8,  1): "Health and longevity tied to personality; transformative life; occult fascination.",
    (8,  2): "Inheritance through family; family wealth through transformation or hidden means.",
    (8,  3): "Siblings involved in occult or transformations; communication about secrets.",
    (8,  4): "Property from inheritance; home linked to ancestral transformation; mother's health.",
    (8,  5): "Occult creativity; children with karmic past-life debt; risky speculative ventures.",
    (8,  6): "Enemies cause sudden health crises; hidden illness; 6+8 lords combining = serious risk.",
    (8,  7): "Spouse is secretive or occult-oriented; transformative marriage; longevity of spouse.",
    (8,  8): "Extremely strong occult and research interest; deep longevity study; phoenix-like life.",
    (8,  9): "Transformation through dharma; inherited religious philosophy; father's longevity.",
    (8, 10): "Career in research, surgery, occult, inheritance law, or investigative finance.",
    (8, 11): "Sudden gains or inheritance through elder siblings; occult brings income.",
    (8, 12): "Spiritual transformation; moksha path; foreign occult experiences; losses via change.",
    # ── Lord of H9 (Luck / Dharma / Father / Guru) ──
    (9,  1): "Very fortunate personality; dharmic, philosophical; father is highly influential.",
    (9,  2): "Wealth through dharma and father; family prosperity through luck and virtue.",
    (9,  3): "Philosophical writing and communication; siblings are spiritual; fortunate journeys.",
    (9,  4): "Spiritual home; fortunate, pious mother; property through luck; educated household.",
    (9,  5): "Most auspicious — 9th lord in 5H (trikona-trikona): abundant luck, wise children.",
    (9,  6): "Dharma tested through service and health; fortune through service to others.",
    (9,  7): "Fortunate, spiritually wise spouse; dharmic marriage; luck through partnerships.",
    (9,  8): "Dharma through transformation; inherited religious wisdom; occult philosophy.",
    (9,  9): "Extremely strong dharma, luck, and fortune; deeply religious and philosophical life.",
    (9, 10): "Career in law, religion, philosophy, or education; fame through dharmic work.",
    (9, 11): "Outstanding — gains come through luck and dharma; elder siblings are fortunate.",
    (9, 12): "Dharma through foreign lands or spiritual isolation; pilgrimages abroad; moksha path.",
    # ── Lord of H10 (Career / Authority / Fame / Status) ──
    (10,  1): "Career defines identity; authority and public image are central to personality.",
    (10,  2): "Career brings wealth and family status; income from authority or public position.",
    (10,  3): "Career in communication, media, writing, or travel; courage in professional life.",
    (10,  4): "Career linked to home, real estate, or mother; working from home; domestic vocation.",
    (10,  5): "Career in creativity, arts, education, or child-related fields; fame through intellect.",
    (10,  6): "Service-oriented career; medical, military, competitive, or legal profession.",
    (10,  7): "Career through partnerships or business with spouse; public career enhanced by partner.",
    (10,  8): "Transformative career; research, occult, medicine, or investigative profession.",
    (10,  9): "Highly auspicious — career aligned with dharma; fame through wisdom and virtue.",
    (10, 10): "Extremely strong career; high authority; government or top leadership; great fame.",
    (10, 11): "Gains through career; professional aspirations fulfilled; income from authority.",
    (10, 12): "Career abroad or in isolation; foreign employment; spiritual or behind-the-scenes work.",
    # ── Lord of H11 (Gains / Income / Friends / Aspirations) ──
    (11,  1): "Desires and gains are self-driven; socially ambitious personality; friends shape self.",
    (11,  2): "Gains through family and speech; income aligned with family wealth.",
    (11,  3): "Gains through communication, media, siblings, or short journeys.",
    (11,  4): "Gains through property and home; domestic income; mother linked to social success.",
    (11,  5): "Gains through children, creativity, or speculation; income from arts or education.",
    (11,  6): "Gains through service, competition, or health industry; income by defeating obstacles.",
    (11,  7): "Gains through marriage and partnerships; financially beneficial spouse.",
    (11,  8): "Sudden gains or inheritance; occult brings income; elder siblings face transformation.",
    (11,  9): "Gains through father, dharma, or luck; fortune grows through spiritual activities.",
    (11, 10): "Gains through career and authority; professional fame converts to income.",
    (11, 11): "Very strong gains house; powerful income, large social network, fulfilled desires.",
    (11, 12): "Gains lead to expenses; income from foreign sources or isolated work.",
    # ── Lord of H12 (Losses / Isolation / Foreign / Moksha) ──
    (12,  1): "Spiritual or foreign-natured personality; expenditure tied to self; hidden tendencies.",
    (12,  2): "Family wealth spent on foreign or spiritual matters; speech about hidden or divine things.",
    (12,  3): "Communication about foreign or spiritual matters; siblings abroad; long journeys.",
    (12,  4): "Home is abroad or spiritual retreat; mother may live far; property in foreign land.",
    (12,  5): "Creativity in isolation; children may live abroad; spiritual romance; hidden pleasures.",
    (12,  6): "Enemies abroad or in isolation; hospitalisation; secret enmity is the main challenge.",
    (12,  7): "Foreign spouse; marriage involves foreign living; spiritual partnership; partner abroad.",
    (12,  8): "Deep transformation through foreign or isolated experiences; occult linked to abroad.",
    (12,  9): "Dharma in foreign lands; pilgrimages abroad; foreign guru; spiritual fortune.",
    (12, 10): "Career in foreign country; work in isolated or spiritual fields; behind-the-scenes role.",
    (12, 11): "Gains from foreign sources; income from isolated work; friends or network abroad.",
    (12, 12): "Extremely strong 12H themes; deeply spiritual, moksha-oriented, costly but enlightened.",
}


# ────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────
def get_sign(deg):
    return zodiac_signs[int(deg / 30) % 12]


def get_nakshatra(deg):
    nak_index = int(deg / (360 / 27)) % 27
    return nakshatras[nak_index]


def get_nakshatra_progress(deg):
    nak_span = 360 / 27
    nak_start = int(deg / nak_span) * nak_span
    progress = (deg - nak_start) / nak_span
    return progress


def get_dignity(planet, sign):
    if planet not in dignity_table:
        return ""
    d = dignity_table[planet]
    own_signs = d.get("own", [])
    if isinstance(own_signs, str):
        own_signs = [own_signs]
    if sign in own_signs:
        return "Own"
    exalt_str = d.get("exalt", "")
    if exalt_str:
        exalt_signs = [s.strip() for s in exalt_str.split("/") if s.strip()]
        if sign in exalt_signs:
            return "Exalt"
    deb_str = d.get("deb", "")
    if deb_str:
        deb_signs = [s.strip() for s in deb_str.split("/") if s.strip()]
        if sign in deb_signs:
            return "Debilitated"
    return ""


def get_lat_lon(place):
    geo = Nominatim(user_agent="vedic_kundali_cli")
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError(
            f"Location not found: {place}. Try 'Mumbai, Maharashtra, India'"
        )
    return loc.latitude, loc.longitude


def is_retrograde(speed):
    return speed < 0


def get_house_from_sign(asc_sign_idx, planet_sign_idx):
    return ((planet_sign_idx - asc_sign_idx) % 12) + 1


def datetime_to_jd(dt):
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)


def check_combustion(planet_code, planet_full_lon, sun_full_lon, is_retro):
    """Return True if planet is combust (within orb of Sun)."""
    if planet_code not in COMBUSTION_ORBS:
        return False
    orb_direct, orb_retro = COMBUSTION_ORBS[planet_code]
    orb = orb_retro if is_retro else orb_direct
    diff = abs((planet_full_lon - sun_full_lon + 360) % 360)
    if diff > 180:
        diff = 360 - diff
    return diff <= orb


def _houses_are_consecutive(house_set):
    """Return True if the given set of house numbers (1-12) form a
    gapless consecutive sequence, accounting for zodiac wrap-around.
    E.g. {10,11,12,1} is consecutive; {2,3,5} is not.
    """
    houses = sorted(house_set)
    n = len(houses)
    if n < 2:
        return True
    for start_i in range(n):
        ok = True
        for j in range(1, n):
            diff = (houses[(start_i + j) % n] - houses[(start_i + j - 1) % n]) % 12
            if diff != 1:
                ok = False
                break
        if ok:
            return True
    return False


def check_neecha_bhanga(planet_code, planet_data, house_planets, lagna_idx, moon_house):
    """Return True if the debilitated planet's debilitation is cancelled
    (Neecha Bhanga Raja Yoga).
    Three Parashari rules are checked:
      A – The lord of the debilitation sign is in a kendra from Lagna or Moon.
      B – The planet that is exalted in the debilitation sign is in a kendra
          from Lagna or Moon.
      C – The debilitated planet itself is in a kendra from Lagna or Moon.
    Any one rule being satisfied cancels the debilitation.
    """
    if planet_code not in NEECHA_BHANGA_INFO:
        return False
    if planet_code not in planet_data:
        return False
    if planet_data[planet_code]["dignity"] != "Debilitated":
        return False  # not debilitated, no cancellation needed

    kendra_from_lagna = {1, 4, 7, 10}
    # Kendras from Moon (houses 1,4,7,10 counted from Moon's house)
    if moon_house is not None:
        kendra_from_moon = {((moon_house - 1 + offset) % 12) + 1 for offset in (0, 3, 6, 9)}
    else:
        kendra_from_moon = set()

    def planet_in_kendra(pl_code):
        """Return True if pl_code is found in a kendra from Lagna or Moon."""
        for h, plist in house_planets.items():
            if pl_code in plist:
                return h in kendra_from_lagna or h in kendra_from_moon
        return False

    def self_in_kendra(pl_code):
        """Return True if pl_code itself is in a kendra from Lagna or Moon."""
        for h, plist in house_planets.items():
            if pl_code in plist:
                return h in kendra_from_lagna or h in kendra_from_moon
        return False

    deb_lord, exalt_planet = NEECHA_BHANGA_INFO[planet_code]
    # Rule A
    if deb_lord and planet_in_kendra(deb_lord):
        return True
    # Rule B
    if exalt_planet and exalt_planet != deb_lord and planet_in_kendra(exalt_planet):
        return True
    # Rule C
    if self_in_kendra(planet_code):
        return True
    return False


def get_panchanga(birth_jd, sun_lon, moon_lon):
    """Return birth Panchanga: Tithi, Vara, Yoga, Karana."""
    # Tithi
    tithi_num = int((moon_lon - sun_lon) % 360 / 12)  # 0-29
    tithi = TITHI_NAMES[tithi_num]
    # Vara (day of week)
    vara_idx = int(birth_jd + 1.5) % 7  # 0=Sun,1=Mon,...,6=Sat
    vara = VARA_NAMES[vara_idx]
    # Yoga (27 Nithya Yogas)
    yoga_idx = int((sun_lon + moon_lon) % 360 / (360 / 27)) % 27
    yoga = YOGA_NAMES[yoga_idx]
    # Karana (half-tithi)
    half_idx = int((moon_lon - sun_lon) % 360 / 6)  # 0-59
    if half_idx == 0:
        karana = "Kimstughna"
    elif half_idx <= 56:
        karana = KARANA_REPEATING[(half_idx - 1) % 7]
    elif half_idx == 57:
        karana = "Shakuni"
    elif half_idx == 58:
        karana = "Chatushpada"
    else:
        karana = "Naga"
    return {"tithi": tithi, "vara": vara, "yoga": yoga, "karana": karana}


def get_sade_sati_status(natal_moon_sign, current_sa_sign):
    """Return Sade Sati / Dhaiya status from natal Moon and transiting Saturn sign."""
    moon_idx = zodiac_signs.index(natal_moon_sign)
    sa_idx = zodiac_signs.index(current_sa_sign)
    diff = (sa_idx - moon_idx + 12) % 12
    if diff == 11:
        return "Sade Sati – Rising Phase (Saturn in 12th from Moon): increased expenses, inner unrest, foreign journeys"
    elif diff == 0:
        return "Sade Sati – Peak Phase (Saturn on Moon sign): maximum pressure on mind, health, and finances"
    elif diff == 1:
        return "Sade Sati – Setting Phase (Saturn in 2nd from Moon): family friction, financial stress, speech issues"
    elif diff == 3:
        return "Kantaka Shani / Dhaiya (Saturn in 4th from Moon): troubles at home, property, vehicles, mother's health"
    elif diff == 7:
        return "Ashtama Shani / Dhaiya (Saturn in 8th from Moon): health challenges, obstacles, financial losses; intense karmic period"
    else:
        return None  # No special Saturn transit now


# ────────────────────────────────────────────────
# Divisional Charts (Traditional Parashari)
# ────────────────────────────────────────────────
def get_navamsa_sign_and_deg(full_lon):
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    nav_size = 30.0 / 9
    navamsa_in_rasi = int(deg_in_rasi / nav_size)
    start_nav_idx = [0, 9, 6, 3][rasi_idx % 4]  # Fire/Earth/Air/Water
    nav_sign_idx = (start_nav_idx + navamsa_in_rasi) % 12
    remainder = deg_in_rasi % nav_size
    deg_in_nav = remainder * 9
    return zodiac_signs[nav_sign_idx], round(deg_in_nav, 2)


def get_d7_sign_and_deg(full_lon):
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    sapt_size = 30.0 / 7
    sapt_idx = int(deg_in_rasi / sapt_size)
    if rasi_idx % 2 == 0:  # Odd signs (Aries, Gemini...)
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 6) % 12
    new_idx = (start_idx + sapt_idx) % 12
    frac = (deg_in_rasi % sapt_size) / sapt_size
    deg_in_d7 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d7, 2)


def get_d10_sign_and_deg(full_lon):
    full_lon = full_lon % 360
    rasi_idx = int(full_lon // 30)
    deg_in_rasi = full_lon % 30
    dasa_size = 3.0
    dasa_idx = int(deg_in_rasi / dasa_size)
    if rasi_idx % 2 == 0:  # Odd signs
        start_idx = rasi_idx
    else:
        start_idx = (rasi_idx + 8) % 12
    new_idx = (start_idx + dasa_idx) % 12
    frac = (deg_in_rasi % dasa_size) / dasa_size
    deg_in_d10 = frac * 30
    return zodiac_signs[new_idx], round(deg_in_d10, 2)


# ────────────────────────────────────────────────
# Yoga Strength Calculation (1-10)
# ────────────────────────────────────────────────
def get_yoga_strength(pl_list, result):
    """Calculate yoga strength from 1-10 based on dignity, house, retro,
    combustion, and Neecha Bhanga status."""
    score = 5  # baseline
    for pl in pl_list:
        if pl not in result["planets"]:
            continue
        d = result["planets"][pl]
        # Dignity bonus/penalty (Neecha Bhanga softens debilitation from -3 to -1)
        if d["dignity"] == "Exalt":
            score += 3
        elif d["dignity"] == "Own":
            score += 2
        elif d["dignity"] == "Debilitated":
            if d.get("neecha_bhanga", False):
                score -= 1  # debilitation cancelled; minor residual only
            else:
                score -= 3
        # Combust penalty (combustion severely weakens a planet)
        if d.get("combust", False):
            score -= 2
        # Direct motion bonus
        if not d["retro"]:
            score += 1
        # House placement bonus
        planet_house = None
        for h, pls in result["houses"].items():
            if pl in pls:
                planet_house = h
                break
        if planet_house:
            if planet_house in [1, 4, 7, 10]:  # Kendras
                score += 2
            elif planet_house in [5, 9]:  # Trikonas
                score += 1
    return max(1, min(10, score))


# ────────────────────────────────────────────────
# Detect Problems/Doshas
# ────────────────────────────────────────────────
def detect_problems(result):
    """Detect major problems/doshas in the Kundali"""
    problems = []
    p = result["planets"]
    h = result["houses"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    # Create planet to house mapping (excluding Asc)
    planet_house = {}
    for house, pls in h.items():
        for pl in pls:
            if pl != "Asc":
                planet_house[pl] = house
    
    # 1. Mangal Dosha (Mars in 1,2,4,7,8,12 from Lagna) with CANCELLATION CHECKS
    if "Ma" in planet_house and planet_house["Ma"] in [1, 2, 4, 7, 8, 12]:
        house_num = planet_house["Ma"]
        mars_sign = p.get("Ma", {}).get("sign", "")
        mars_dignity = p.get("Ma", {}).get("dignity", "")
        moon_dignity = p.get("Mo", {}).get("dignity", "")
        
        # Calculate cancellation factors
        cancellation_factors = []
        severity_reduction = 0
        
        # Factor 1: Jupiter aspects 7th house (check Jupiter's 5th aspect)
        ju_house = planet_house.get("Ju", 0)
        if ju_house:
            ju_5th_aspect = ((ju_house - 1 + 4) % 12) + 1  # 5th aspect
            ju_7th_aspect = ((ju_house - 1 + 6) % 12) + 1  # 7th aspect
            ju_9th_aspect = ((ju_house - 1 + 8) % 12) + 1  # 9th aspect
            if 7 in [ju_5th_aspect, ju_7th_aspect, ju_9th_aspect]:
                cancellation_factors.append("Jupiter aspects 7th house")
                severity_reduction += 3
        
        # Factor 2: Jupiter aspects Mars directly
        if ju_house and "Ma" in planet_house:
            mars_h = planet_house["Ma"]
            if mars_h in [ju_5th_aspect, ju_7th_aspect, ju_9th_aspect]:
                cancellation_factors.append("Jupiter aspects Mars")
                severity_reduction += 2
        
        # Factor 3: Mars in own sign (Aries/Scorpio) or exalted (Capricorn)
        if mars_dignity in ["Own", "Exalted"]:
            cancellation_factors.append(f"Mars {mars_dignity.lower()} in {mars_sign}")
            severity_reduction += 2
        
        # Factor 4: Mars in Leo or Aquarius (cancellation in some traditions)
        if mars_sign in ["Leo", "Aquarius"]:
            cancellation_factors.append(f"Mars in {mars_sign} (mitigating sign)")
            severity_reduction += 1
        
        # Factor 5: Strong Moon (exalted/own sign) provides emotional stability
        if moon_dignity in ["Exalted", "Own"]:
            cancellation_factors.append(f"Moon {moon_dignity.lower()} (emotional stability)")
            severity_reduction += 2
        
        # Factor 6: Check D9 Venus dignity from result (if available)
        d9_data = result.get("d9", {})
        d9_venus_info = d9_data.get("Ve", {})
        d9_venus_dignity = d9_venus_info.get("dignity", "")
        if d9_venus_dignity in ["Exalted", "Own"]:
            cancellation_factors.append(f"D9 Venus {d9_venus_dignity.lower()}")
            severity_reduction += 2
        
        # Factor 7: Check D9 Mars dignity
        d9_mars_info = d9_data.get("Ma", {})
        d9_mars_dignity = d9_mars_info.get("dignity", "")
        if d9_mars_dignity in ["Exalted", "Own"]:
            cancellation_factors.append(f"D9 Mars {d9_mars_dignity.lower()}")
            severity_reduction += 1
        
        # Calculate severity: base 10, reduce by factors
        base_severity = 10
        # House-specific severity: 7th and 8th are traditionally more impactful
        if house_num in [7, 8]:
            base_severity = 8
        elif house_num in [1, 4]:
            base_severity = 6
        else:  # 2, 12
            base_severity = 5
        
        final_severity = max(1, base_severity - severity_reduction)
        
        # Determine severity label
        if final_severity <= 3:
            severity_label = "Mild"
            outcome = "Minor adjustments in marriage; generally manageable with awareness"
        elif final_severity <= 5:
            severity_label = "Moderate"
            outcome = "Some delays or disagreements possible; remedies helpful but not urgent"
        elif final_severity <= 7:
            severity_label = "Significant"
            outcome = "Potential delays/discord in marriage; remedies recommended"
        else:
            severity_label = "Severe"
            outcome = "Possible marital discord, delays in marriage, or heated arguments; remedies like Kumbh Vivah advised"
        
        # Build summary and detail
        cancel_text = ""
        if cancellation_factors:
            cancel_text = f" MITIGATING FACTORS: {', '.join(cancellation_factors)}."
        
        summary = f"Mangal Dosha – {severity_label} (Mars in {house_num}H, score {final_severity}/10): {outcome}"
        
        detail = (
            f"- Reason: Mangal Dosha occurs when Mars is in houses 1,2,4,7,8,12 from Lagna. "
            f"Mars in {house_num}H in {mars_sign} creates assertive energy in marriage house themes.\n"
            f"- Severity Assessment: Base severity {base_severity}/10 "
            f"(house {house_num}), reduced by {severity_reduction} points due to mitigating factors.\n"
            f"- Direct Outcome: {outcome}.{cancel_text}"
        )
        
        # Only add to problems if severity is above mild threshold, or add with reduced emphasis
        if final_severity > 3:
            problems.append({"summary": summary, "detail": detail})
        else:
            # Still note it, but with "largely cancelled" language
            summary = f"Mangal Dosha – Largely Cancelled (Mars in {house_num}H): {', '.join(cancellation_factors)}"
            detail = (
                f"- Reason: Mars in {house_num}H technically creates Mangal Dosha, but multiple mitigating factors "
                f"({', '.join(cancellation_factors)}) effectively neutralise it.\n"
                f"- Direct Outcome: Marriage is protected; no significant delays or discord expected from this placement."
            )
            problems.append({"summary": summary, "detail": detail})
    # 2. Kemdrum Yoga (Moon with no planets in 2nd/12th from it, and alone in its house)
    if "Mo" in planet_house:
        moon_house = planet_house["Mo"]
        moon_house_planets = [pl for pl in h[moon_house] if pl != "Mo"]
        prev_house = ((moon_house - 2) % 12) + 1
        next_house = ((moon_house) % 12) + 1
        if (
            len(moon_house_planets) == 0
            and len(h[prev_house]) == 0
            and len(h[next_house]) == 0
        ):
            summary = "Kemdrum Yoga: Moon isolated – Emotional instability, financial fluctuations"
            detail = f"- Reason: Kemdrum Yoga forms when the Moon is alone without planetary support in adjacent houses, leading to emotional void.\n- Direct Outcome: Loneliness, mood swings, or financial instability; strengthened by Moon's aspects or remedies like Chandra mantra."
            problems.append({"summary": summary, "detail": detail})
    # 3. Kaal Sarp Yoga (Basic: All planets between Rahu and Ketu in one arc)
    if "Ra" in planet_house and "Ke" in planet_house:
        ra_house = planet_house["Ra"]
        ke_house = planet_house["Ke"]
        # Normalize houses: assume houses are 1-12
        # Check if all other planets are between ra_house and ke_house (clockwise or anticlockwise)
        all_planets_between = True
        direction1 = (ke_house - ra_house + 12) % 12  # From Ra to Ke clockwise
        direction2 = (ra_house - ke_house + 12) % 12  # From Ke to Ra clockwise
        if (
            direction1 <= 6 or direction2 <= 6
        ):  # Only if span is half or less (simplified)
            for pl_house in planet_house.values():
                if pl_house not in [ra_house, ke_house]:
                    pos_from_ra = (pl_house - ra_house + 12) % 12
                    if not (0 < pos_from_ra < direction1):
                        all_planets_between = False
                        break
            if all_planets_between:
                summary = "Kaal Sarp Yoga: All planets hemmed between Rahu-Ketu – Life obstacles, but potential for sudden rise"
                detail = f"- Reason: Kaal Sarp forms when all planets are trapped between Rahu and Ketu's axis, creating karmic restrictions.\n- Direct Outcome: Life struggles, delays in success, but potential breakthroughs after mid-life; remedies include Naga puja."
                problems.append({"summary": summary, "detail": detail})
    # 4. Debilitated Planets
    deb_planets = [pl for pl, data in p.items() if data["dignity"] == "Debilitated"]
    if deb_planets:
        full_names = [short_to_full.get(pl, pl) for pl in deb_planets]
        deb_details = []
        for pl in deb_planets:
            sign = p[pl]["sign"]
            if pl == "Me":
                deb_details.append(
                    f"Mercury in {sign}: Scattered thinking, communication delays."
                )
            elif pl == "Sa":
                deb_details.append(
                    f"Saturn in {sign}: Lack of stability, chronic delays."
                )
        summary = f"Debilitated Planets ({', '.join(full_names)}): Weakened vitality/effects in respective areas"
        detail = f"- Reason: A planet is debilitated when in a sign opposing its nature, e.g., Mercury in Pisces clashes with its analytical energy, Saturn in Aries conflicts with its patience.\n- Direct Outcome: {'; '.join(deb_details)} Possible health or career issues; remedies like gemstones (emerald for Mercury, blue sapphire for Saturn)."
        problems.append({"summary": summary, "detail": detail})
    # 5. Pitru Dosha (Sun afflicted by Saturn/Rahu, or Sun in 12th)
    # Affliction = same house (conjunction) OR 7 houses away (mutual opposition/aspect)
    sun_house = planet_house.get("Su", None)
    afflictions = []
    if "Sa" in planet_house and sun_house is not None:
        h_diff = (planet_house["Sa"] - sun_house + 12) % 12
        if h_diff in (0, 6):  # conjunction or direct opposition
            afflictions.append("Saturn")
    if "Ra" in planet_house and sun_house is not None:
        h_diff = (planet_house["Ra"] - sun_house + 12) % 12
        if h_diff in (0, 6):
            afflictions.append("Rahu")
    if sun_house == 12:
        afflictions.append("in 12H")
    if afflictions:
        summary = f"Pitru Dosha (Sun afflicted by {', '.join(afflictions)}): Ancestral issues, father-related challenges"
        detail = f"- Reason: Pitru Dosha arises from Sun's affliction by malefics, indicating unresolved ancestral karma.\n- Direct Outcome: Paternal health problems, family disputes, or luck obstacles; remedies include Shradh rituals."
        problems.append({"summary": summary, "detail": detail})
    # 6. Graha Malika Yoga – All 7 classical planets confined to consecutive houses with
    #    no gap.  Using only classical planets (Su Mo Ma Me Ju Ve Sa) avoids false positives
    #    caused by Rahu/Ketu or the Ascendant marker occupying a house.
    _classical = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]
    _c_house_set = set()
    for _pl in _classical:
        for _hnum, _plist in h.items():
            if _pl in _plist:
                _c_house_set.add(_hnum)
                break
    _n_classical_houses = len(_c_house_set)
    if _n_classical_houses >= 6 and _houses_are_consecutive(_c_house_set):
        summary = (f"Graha Malika ({_n_classical_houses} classical planets in consecutive houses): "
                   f"Intense, focused life phases, potential imbalances")
        detail = ("- Reason: Classical planets in sequential houses concentrate all life energy "
                  "into a tight arc – intense achievement in those house themes.\n"
                  "- Direct Outcome: Extreme highs/lows in the activated house arc; "
                  "strong focus but risk of neglecting opposite-house themes; "
                  "balances with simultaneous yogas.")
        problems.append({"summary": summary, "detail": detail})
    if not problems:
        problems.append(
            {
                "summary": "No major doshas/problems detected – Generally favorable chart",
                "detail": "",
                "remedies": [],
            }
        )
        return problems
    # ── Attach targeted remedies to each problem ──
    REMEDIES = {
        "Mangal_Severe": [
            "Recite Hanuman Chalisa daily, especially on Tuesdays.",
            "Donate red lentils (masoor dal) and red cloth on Tuesdays.",
            "Wear red coral (Moonga) in gold/copper ring on right ring finger (after jyotishi consultation).",
            "For marriage: Kumbh Vivah ritual (marrying a Peepal tree) before wedding.",
        ],
        "Mangal_Moderate": [
            "Recite Hanuman Chalisa on Tuesdays (optional).",
            "Donate red lentils (masoor dal) on Tuesdays.",
            "No Kumbh Vivah required – mitigating factors protect marriage.",
        ],
        "Mangal_Mild": [
            "General Mars balance: Light physical exercise and avoid aggression.",
            "Optional: Recite Hanuman Chalisa on Tuesdays if desired.",
            "No specific remedies required – dosha is largely cancelled.",
        ],
        "Kemdrum": [
            "Chant 'Om Som Somaya Namah' or 'Om Chandraya Namah' 108× on Mondays.",
            "Offer white flowers and milk to Shiva on Mondays.",
            "Wear moonstone or pearl in silver ring on right little finger.",
            "Avoid major decisions during waning Moon (Krishna Paksha).",
        ],
        "Kaal Sarp": [
            "Perform Kaal Sarp Dosh puja at Trimbakeshwar (Nasik) or Ujjain.",
            "Recite Maha Mrityunjaya Mantra 108× daily.",
            "Donate silver snake idol at Naga temple on Naga Panchami.",
            "Wear Navagraha or Kaal Sarp yantra after proper energisation.",
        ],
        "Debilitated_Me": [
            "Donate green cloth, green moong dal, or books on Wednesdays.",
            "Chant 'Om Bum Buddhaya Namah' 108× on Wednesdays.",
            "Wear emerald (Panna) in gold ring on right little finger – "
            "ONLY if Mercury is your functional benefic and not combust (consult jyotishi).",
            "Feed green grass to cows and read/give away books.",
        ],
        "Debilitated_Sa": [
            "Recite Shani Stotra and 'Om Sham Shanicharaya Namah' on Saturdays.",
            "Donate black sesame seeds, mustard oil, and black cloth on Saturdays.",
            "Light sesame oil lamp under Peepal tree on Saturdays.",
            # Gemstone only recommended if Saturn is functional benefic AND not combust
            "Wear blue sapphire only after thorough jyotishi trial (powerful and risky) – "
            "ONLY if Saturn is your functional benefic and not combust.",
        ],
        "Debilitated_Su": [
            "Offer water (Arghya) to the rising Sun daily with mantra.",
            "Donate wheat, jaggery, or copper items on Sundays.",
            "Chant 'Om Suryaya Namah' 108× mornings.",
        ],
        "Debilitated_Mo": [
            "Fast on Mondays or eat only once.",
            "Offer raw milk/white rice in flowing water on Mondays.",
            "Wear pearl or moonstone in silver on right little finger.",
        ],
        "Debilitated_Ma": [
            "Donate red lentils and copper items on Tuesdays.",
            "Chant 'Om Ang Angarakaya Namah' 108× on Tuesdays.",
            "Physical exercise and discipline reduce Mars's turbulent energy.",
        ],
        "Debilitated_Ju": [
            "Donate yellow cloth, chickpeas, turmeric on Thursdays.",
            "Chant 'Om Brim Brihaspataye Namah' 108× on Thursdays.",
            "Seek blessings of guru/elders; avoid disrespecting knowledge or teachers.",
        ],
        "Debilitated_Ve": [
            "Donate white sweets, white cloth, perfume on Fridays.",
            "Chant 'Om Shum Shukraya Namah' 108× on Fridays.",
            "Wear diamond or white sapphire (after consultation) on right index finger.",
        ],
        "Pitru": [
            "Perform Pitru Tarpan (water libation to ancestors) on every Amavasya.",
            "Observe Shradh rituals for 16 days (Pitru Paksha) annually.",
            "Donate cooked food (kheer/rice) to Brahmins or the needy.",
            "Plant a Peepal tree; feed crows on Saturdays.",
        ],
        "Graha Malika": [
            "Worship all nine Navagraha together on Saturdays.",
            "Recite Navagraha Stotra regularly.",
            "Balance planetary energies through colour therapy and gemstone consultation.",
        ],
    }
    for prob in problems:
        summary = prob["summary"]
        rems = []
        if "Mangal" in summary:
            # Check severity level in summary to assign appropriate remedies
            if "Severe" in summary or "Significant" in summary:
                rems = REMEDIES["Mangal_Severe"]
            elif "Moderate" in summary:
                rems = REMEDIES["Mangal_Moderate"]
            else:  # Mild or Largely Cancelled
                rems = REMEDIES["Mangal_Mild"]
        elif "Kemdrum" in summary:
            rems = REMEDIES["Kemdrum"]
        elif "Kaal Sarp" in summary:
            rems = REMEDIES["Kaal Sarp"]
        elif "Graha Malika" in summary:
            rems = REMEDIES["Graha Malika"]
        elif "Pitru" in summary:
            rems = REMEDIES["Pitru"]
        elif "Debilitated" in summary:
            # Find which planets are debilitated and add their specific remedies
            for pl_short, key in [("Mercury","Me"),("Saturn","Sa"),("Sun","Su"),
                                   ("Moon","Mo"),("Mars","Ma"),("Jupiter","Ju"),("Venus","Ve")]:
                if pl_short in summary:
                    rems += REMEDIES.get(f"Debilitated_{key}", [])
        # ── Gemstone filter: warn/skip if planet is a functional malefic or combust ──
        # Applied AFTER rems is filled so the full list is available for filtering.
        if "Debilitated" in summary and rems:
            lagna_sign_r = result.get("lagna_sign", "")
            fq_r = FUNCTIONAL_QUALITY.get(lagna_sign_r, {})
            func_malefics = fq_r.get("mal", [])
            # Map each remedy line to the planet it belongs to by tracking which
            # planet's remedy block we are in (remedies appear in the same order
            # as the debilitated planets listed in the summary).
            _deb_order = []
            for ps, pk in [("Mercury","Me"),("Saturn","Sa"),("Sun","Su"),
                            ("Moon","Mo"),("Mars","Ma"),("Jupiter","Ju"),("Venus","Ve")]:
                if ps in summary:
                    _deb_order.append(pk)
            # Each planet's REMEDIES block has the same length → partition rems
            _block_size = {}
            for pk in _deb_order:
                _block_size[pk] = len(REMEDIES.get(f"Debilitated_{pk}", []))
            filtered = []
            _rem_idx = 0
            for pk in _deb_order:
                _planet_rems = rems[_rem_idx: _rem_idx + _block_size[pk]]
                _rem_idx += _block_size[pk]
                is_malefic = pk in func_malefics
                is_combust = result.get("planets", {}).get(pk, {}).get("combust", False)
                for rem_line in _planet_rems:
                    is_gem_line = any(g in rem_line for g in ["sapphire", "emerald",
                                                               "pearl", "coral", "ruby",
                                                               "diamond", "moonstone",
                                                               "gemstone"])
                    if is_gem_line and is_malefic:
                        filtered.append(
                            f"{rem_line} [⚠ SKIP – {pk} is a functional malefic for "
                            f"{lagna_sign_r} lagna; wearing this gem will amplify harm]")
                    elif is_gem_line and is_combust:
                        filtered.append(
                            f"{rem_line} [⚠ CAUTION – {pk} is currently combust; "
                            f"wait for combustion to clear before using this gemstone]")
                    else:
                        filtered.append(rem_line)
            rems = filtered
        prob["remedies"] = rems
    return problems


# ────────────────────────────────────────────────
# Generate Final Analysis
# ────────────────────────────────────────────────
def generate_final_analysis(result):
    yogas = result["yogas"]
    problems = result["problems"]
    timings = result["timings"]
    lagna = result["lagna_sign"]
    moon_sign = result["moon_sign"]
    moon_nak = result["moon_nakshatra"]
    vim = result["vimshottari"]
    current_md = vim["current_md"]
    current_ad = vim["current_ad"]
    birth_year = result["birth_year"]
    birth_jd = result["birth_jd"]

    # --- Dynamic: find when current Mahadasha ends ---
    md_end_year = None
    for md in vim["mahadasas"]:
        if md["lord"] == current_md:
            md_end_year = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
            break

    # --- Dynamic: first yoga name ---
    if yogas and yogas != ["No major classical yogas formed"]:
        first_yoga_name = yogas[0].split(" (")[0]
        yoga_summary = (
            f"Strong benefics create yogas like {first_yoga_name}, indicating potential "
            f"for success in wisdom- and Jupiter/Venus-driven fields."
        )
    else:
        yoga_summary = "Limited classical yogas; growth through steady effort."

    # --- Dynamic: primary doshas ---
    active_doshas = [p["summary"].split(":")[0] for p in problems if p["detail"]]

    # --- Dynamic: first timing period ---
    first_event = list(timings.keys())[0]
    first_range = "upcoming years"
    for _event, _periods in timings.items():
        if _periods:
            first_event = _event
            _m = re.search(r'\((\d{4}-\d{4})\)', _periods[0])
            first_range = _m.group(1) if _m else "upcoming years"
            break

    # --- Dynamic: current dasha description ---
    current_md_full = short_to_full.get(current_md, current_md) if current_md else "Unknown"
    current_ad_full = short_to_full.get(current_ad, current_ad) if current_ad else "Unknown"
    dasha_desc = f"{current_md_full}/{current_ad_full} Antardasha"

    # --- Dynamic: planet qualities for current MD ---
    md_qualities = {
        "Mercury": "analytical thinking and communication are heightened",
        "Jupiter": "wisdom, expansion, and spiritual growth dominate",
        "Venus": "relationships, beauty, and material comforts take center stage",
        "Saturn": "discipline, hard work, and karmic dues come to the fore",
        "Mars": "energy, ambition, and assertiveness are activated",
        "Sun": "leadership, fame, and self-expression are in focus",
        "Moon": "emotions, family, and mental sensitivity are heightened",
        "Rahu": "ambition, foreign exposure, and unconventional paths open",
        "Ketu": "detachment, spirituality, and past-karma resolution dominate",
    }
    md_quality = md_qualities.get(current_md_full, "the dasha lord's significations are active")

    # --- Build analysis ---
    analysis = "### Final Analysis: Overall Chart Balance, Active Doshas, and Direct Life Outcomes\n"
    analysis += f"Your Kundali ({lagna} Lagna, {moon_sign} Moon in {moon_nak}) shows a distinctive planetary configuration: "
    analysis += yoga_summary + "\n"
    analysis += (
        f"Doshas indicate areas of concentrated planetary energy that require attention, "
        f"not fixed negative fate. They reflect learning opportunities and growth areas.\n"
    )
    analysis += "- Why Present? Natal positions place malefics in sensitive houses/signs, creating lessons in "
    if active_doshas:
        analysis += f"areas ruled by {', '.join(d.split('(')[0].strip() for d in active_doshas)}.\n"
    else:
        analysis += "patience, clarity, and harmony.\n"
    analysis += "- Direct Outcomes: "
    if not active_doshas:
        analysis += "Balanced chart with minimal challenges; leverage positive transits actively. "
    else:
        analysis += (
            "Potential delays in stability and clarity in decisions; intense life phases may bring "
            "career shifts and emotional highs/lows as karmic debts resolve. "
        )
    analysis += (
        f"Positive: High-strength yogas promise material gains and wisdom; "
        f"key fructification window for {first_event} is around {first_range}.\n"
    )
    if md_end_year:
        analysis += (
            f"- Overall Trajectory: In the current {dasha_desc}, {md_quality}. "
            f"This Mahadasha runs until ~{md_end_year}, after which the next dasha brings a shift in life theme. "
            f"Focus remedies now to mitigate active doshas and capitalise on strong yoga periods."
        )
    else:
        analysis += (
            f"- Overall Trajectory: In the current {dasha_desc}, {md_quality}. "
            f"Focus remedies to mitigate active doshas and capitalise on strong yoga periods."
        )
    return analysis


# ────────────────────────────────────────────────
# Marriage Probability Scoring
# ────────────────────────────────────────────────
def calculate_marriage_score(result, md_lord, ad_lord=None):
    """Calculate marriage probability score (0-10) for a dasha period.
    
    Comprehensive scoring for ALL lagnas:
    
    PRIMARY FACTORS (high weight):
    1. 7th lord involvement (+3) - Direct marriage significator
    2. Venus involvement (+2 base) - Natural marriage karaka
       - Yogakaraka bonus (+2)
       - D1 dignity bonus (+1)
    3. 2nd lord involvement (+2) - Family/kutumb
    
    SECONDARY FACTORS (medium weight):
    4. 5th lord involvement (+1.5) - Romance, love
    5. 11th lord involvement (+1) - Fulfillment of desires
    6. 4th lord involvement (+1) - Domestic happiness
    7. Jupiter involvement (+1) - Natural benefic, dharma
    8. 12th lord involvement (+0.5) - Bed pleasures (minor)
    
    D9 FACTORS (marriage-specific):
    9. D9 Venus exalt (+2) / own (+1)
    10. D9 7th lord strong (+1)
    11. D9 dasha lord strong (+1)
    12. D9 lagna lord strong (+0.5)
    
    PLACEMENT & DIGNITY FACTORS:
    13. Dasha lord in house 1/2/5/7/11 (+1)
    14. Dasha lord aspects 7th house (+1)
    15. Dasha lord D1 dignity own/exalt (+1)
    
    LAGNA-SPECIFIC FACTORS:
    16. Yogakaraka dasha lord (+2)
    17. Functional benefic (+1)
    
    SYNERGY BONUS:
    18. Both MD and AD marriage-related (+1)
    
    RAHU/KETU HANDLING:
    19. Rahu in 7th or with 7th lord (+1) - unconventional marriage
    20. Ketu special - can delay but also give spiritual spouse
    """
    score = 0.0
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    
    def lord_of(house_no):
        sign_idx = (lagna_idx + house_no - 1) % 12
        return sign_lords[zodiac_signs[sign_idx]]
    
    def house_of(planet):
        """Get house number where planet is placed"""
        for h, plist in result.get("houses", {}).items():
            if planet in plist:
                return h
        return 0
    
    def planet_aspects_house(planet, target_house):
        """Check if planet aspects a specific house"""
        pl_house = house_of(planet)
        if pl_house == 0:
            return False
        # 7th aspect (all planets)
        if ((pl_house - 1 + 6) % 12) + 1 == target_house:
            return True
        # Special aspects
        if planet == "Ma":  # Mars: 4th and 8th
            if ((pl_house - 1 + 3) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 7) % 12) + 1 == target_house:
                return True
        elif planet == "Ju":  # Jupiter: 5th and 9th
            if ((pl_house - 1 + 4) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 8) % 12) + 1 == target_house:
                return True
        elif planet == "Sa":  # Saturn: 3rd and 10th
            if ((pl_house - 1 + 2) % 12) + 1 == target_house:
                return True
            if ((pl_house - 1 + 9) % 12) + 1 == target_house:
                return True
        return False
    
    # Get house lords
    seventh_lord = result.get("seventh_lord", lord_of(7))
    second_lord = lord_of(2)
    fifth_lord = lord_of(5)
    fourth_lord = lord_of(4)
    eleventh_lord = lord_of(11)
    twelfth_lord = lord_of(12)
    first_lord = lord_of(1)  # Lagna lord
    
    # Get functional quality for this lagna
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    func_benefics = fq.get("ben", [])
    func_malefics = fq.get("mal", [])
    yogakaraka = fq.get("yoga", None)
    
    # Convert to short form for comparison
    md_short = next((k for k, v in short_to_full.items() if v == md_lord), md_lord)
    ad_short = next((k for k, v in short_to_full.items() if v == ad_lord), ad_lord) if ad_lord else None
    
    planets_involved = [md_short]
    if ad_short:
        planets_involved.append(ad_short)
    
    # Track what marriage factors are activated for synergy bonus
    marriage_factors_hit = 0
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY FACTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 1. 7th lord involvement (+3)
    if seventh_lord in planets_involved:
        score += 3
        marriage_factors_hit += 1
    
    # 2. Venus involvement (+2 base)
    if "Ve" in planets_involved:
        score += 2
        marriage_factors_hit += 1
        # Yogakaraka bonus (+2)
        if yogakaraka == "Ve":
            score += 2
        # D1 dignity bonus (+1)
        ve_d1_dig = result.get("planets", {}).get("Ve", {}).get("dignity", "")
        if ve_d1_dig in ("Own", "Exalted"):
            score += 1
    
    # 3. 2nd lord involvement (+2)
    if second_lord in planets_involved:
        score += 2
        marriage_factors_hit += 1
    
    # ═══════════════════════════════════════════════════════════════
    # SECONDARY FACTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 4. 5th lord involvement (+1.5) - romance
    if fifth_lord in planets_involved:
        score += 1.5
        marriage_factors_hit += 1
    
    # 5. 11th lord involvement (+1) - fulfillment of desires
    if eleventh_lord in planets_involved:
        score += 1
    
    # 6. 4th lord involvement (+1) - domestic happiness
    if fourth_lord in planets_involved:
        score += 1
    
    # 7. Jupiter involvement (+1) - natural benefic
    if "Ju" in planets_involved:
        score += 1
        # Extra if Jupiter is Yogakaraka
        if yogakaraka == "Ju":
            score += 1
    
    # 8. 12th lord involvement (+0.5) - bed pleasures
    if twelfth_lord in planets_involved:
        score += 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # D9 (NAVAMSA) FACTORS - Critical for marriage
    # ═══════════════════════════════════════════════════════════════
    navamsa = result.get("navamsa", {})
    
    # 9. D9 Venus strength
    if "Ve" in navamsa:
        ve_d9_sign = navamsa["Ve"].get("sign", "")
        ve_d9_dig = get_dignity("Ve", ve_d9_sign)
        if ve_d9_dig == "Exalt":
            score += 2
        elif ve_d9_dig == "Own":
            score += 1
    
    # 10. D9 7th lord strength
    if seventh_lord in navamsa:
        sl_d9_sign = navamsa[seventh_lord].get("sign", "")
        sl_d9_dig = get_dignity(seventh_lord, sl_d9_sign)
        if sl_d9_dig in ("Exalt", "Own"):
            score += 1
    
    # 11. D9 dasha lord strength
    for pl in planets_involved:
        if pl in navamsa and pl not in ["Ra", "Ke"]:
            pl_d9_sign = navamsa[pl].get("sign", "")
            pl_d9_dig = get_dignity(pl, pl_d9_sign)
            if pl_d9_dig in ("Exalt", "Own"):
                score += 1
                break  # Count once
    
    # 12. D9 lagna lord strength (+0.5)
    if first_lord in navamsa:
        fl_d9_sign = navamsa[first_lord].get("sign", "")
        fl_d9_dig = get_dignity(first_lord, fl_d9_sign)
        if fl_d9_dig in ("Exalt", "Own"):
            score += 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # PLACEMENT & DIGNITY FACTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 13. Dasha lord in marriage-relevant houses (1, 2, 5, 7, 11)
    for pl in planets_involved:
        pl_house = house_of(pl)
        if pl_house in [1, 2, 5, 7, 11]:
            score += 1
            break
    
    # 14. Dasha lord aspects 7th house (+1)
    for pl in planets_involved:
        if planet_aspects_house(pl, 7):
            score += 1
            break
    
    # 15. Dasha lord D1 dignity bonus (+1)
    for pl in planets_involved:
        if pl in result.get("planets", {}):
            pl_dig = result["planets"][pl].get("dignity", "")
            if pl_dig in ("Own", "Exalted"):
                score += 1
                break
    
    # ═══════════════════════════════════════════════════════════════
    # LAGNA-SPECIFIC FACTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 16. Yogakaraka dasha lord (+2) - already handled above for Ve/Ju
    for pl in planets_involved:
        if pl == yogakaraka and pl not in ["Ve", "Ju"]:  # Avoid double counting
            score += 2
            break
    
    # 17. Functional benefic (+1)
    for pl in planets_involved:
        if pl in func_benefics:
            score += 1
            break
    
    # Penalty for functional malefic mahadasha lord (-0.5)
    if md_short in func_malefics:
        score -= 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # SYNERGY BONUS
    # ═══════════════════════════════════════════════════════════════
    
    # 18. Both MD and AD are marriage-related (+1)
    if marriage_factors_hit >= 2 and ad_short:
        score += 1
    
    # ═══════════════════════════════════════════════════════════════
    # RAHU/KETU SPECIAL HANDLING
    # ═══════════════════════════════════════════════════════════════
    
    # 19. Rahu in 7th or aspecting 7th - unconventional but can give marriage
    if "Ra" in planets_involved:
        ra_house = house_of("Ra")
        if ra_house == 7:
            score += 1.5  # Strong indicator of marriage (unconventional)
        elif ra_house == 5:  # Rahu in 5th aspects 11th (desires)
            score += 0.5
        # Rahu with 7th lord
        seventh_lord_house = house_of(seventh_lord)
        if ra_house == seventh_lord_house:
            score += 1
    
    # 20. Ketu special handling
    if "Ke" in planets_involved:
        ke_house = house_of("Ke")
        if ke_house == 7:
            score += 0.5  # Can give marriage but spiritual/karmic spouse
        # Ketu in 12th - moksha but also bed pleasures
        if ke_house == 12:
            score += 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # MOON FACTOR (for males especially, Moon = wife's mind)
    # ═══════════════════════════════════════════════════════════════
    if "Mo" in planets_involved:
        score += 0.5
        # Moon as 7th lord already counted above
        # Moon in good dignity
        mo_dig = result.get("planets", {}).get("Mo", {}).get("dignity", "")
        if mo_dig in ("Exalted", "Own"):
            score += 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # FINAL ADJUSTMENTS
    # ═══════════════════════════════════════════════════════════════
    
    # Ensure score stays in 0-10 range
    return min(10, max(0, int(round(score))))


# ────────────────────────────────────────────────
# Accurate Fructification Timings (2026-2046)
# ────────────────────────────────────────────────
def generate_timings(result, birth_year, birth_jd):
    """Generate accurate timing predictions for next 20 years with probability scores"""
    dashas = result["vimshottari"]["mahadasas"]
    current_year = 2026

    def lord_of(house_no):
        lagna_idx = zodiac_signs.index(result["lagna_sign"])
        sign = zodiac_signs[(lagna_idx + house_no - 1) % 12]
        return sign_lords[sign]

    # Event → favorable lords (expanded list)
    seventh_lord = result["seventh_lord"]
    second_lord = lord_of(2)
    events = {
        "Marriage": [
            short_to_full["Ve"],
            short_to_full[seventh_lord],
            short_to_full["Ju"],
            short_to_full["Mo"],
            short_to_full[second_lord],  # 2nd lord for family/marriage
        ],
        "Career Rise / Fame": [
            short_to_full["Sa"],
            short_to_full[lord_of(10)],
            short_to_full["Ju"],
            short_to_full["Su"],
            short_to_full["Ma"],
        ],
        "Children / Progeny": [
            short_to_full["Ju"],
            short_to_full[lord_of(5)],
            short_to_full["Mo"],
            short_to_full["Ve"],
        ],
        "Major Wealth / Property": [
            short_to_full["Ju"],
            short_to_full["Ve"],
            short_to_full[lord_of(2)],
            short_to_full[lord_of(11)],
            short_to_full["Me"],
        ],
    }
    output = {}
    for event, fav_lords in events.items():
        periods = []
        for md in dashas:
            md_lord = md["lord"]
            md_start_age = (md["start_jd"] - birth_jd) / 365.25
            md_start_y = int(birth_year + md_start_age)
            md_end_y = int(birth_year + (md["end_jd"] - birth_jd) / 365.25)
            # Skip if MD is completely outside our window
            if md_end_y < current_year or md_start_y > current_year + 20:
                continue
            # Include if MD lord is favorable
            if md_lord in fav_lords:
                periods.append(f"• {md_lord} Mahadasha ({md_start_y}-{md_end_y})")
            # Check antardashas within the 2026-2046 window
            for ad in md.get("antardashas", []):
                if ad["lord"] in fav_lords:
                    ad_start_age = (ad["start_jd"] - birth_jd) / 365.25
                    ad_end_age = (ad["end_jd"] - birth_jd) / 365.25
                    ad_start_y = int(birth_year + ad_start_age)
                    ad_end_y = int(birth_year + ad_end_age)
                    # Include if AD starts or overlaps within 2026-2046
                    if ad_start_y <= current_year + 20 and ad_end_y >= current_year:
                        # For marriage, add probability score
                        if event == "Marriage":
                            score = calculate_marriage_score(result, md_lord, ad["lord"])
                            prob_label = "★★★" if score >= 7 else "★★" if score >= 4 else "★"
                            periods.append(
                                f" └─ {md_lord}/{ad['lord']} ({ad_start_y}-{ad_end_y}) {prob_label} [{score}/10]"
                            )
                        else:
                            periods.append(
                                f" └─ {md_lord}/{ad['lord']} Antardasha ({ad_start_y}-{ad_end_y})"
                            )
        output[event] = periods[:10] if periods else []
    return output


# ────────────────────────────────────────────────
# Detect Yogas with Strength
# ────────────────────────────────────────────────
def detect_yogas(result):
    """Detect major yogas and calculate their strength (1-10)"""
    yogas = []
    p = result["planets"]
    h = result["houses"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    # Create planet to house mapping
    planet_house = {}
    for house, pls in h.items():
        for pl in pls:
            if pl != "Asc":
                planet_house[pl] = house

    def lord_of(house_no):
        sign_idx = (lagna_idx + house_no - 1) % 12
        return sign_lords[zodiac_signs[sign_idx]]

    # 1. Gajakesari Yoga (Jupiter-Moon)
    # Traditional rule: Jupiter must occupy a kendra (1st/4th/7th/10th) from the Moon
    if "Ju" in planet_house and "Mo" in planet_house:
        mo_h = planet_house["Mo"]
        ju_h = planet_house["Ju"]
        houses_from_moon = (ju_h - mo_h) % 12  # 0=1st, 3=4th, 6=7th, 9=10th
        if houses_from_moon in (0, 3, 6, 9):   # Jupiter in kendra from Moon
            stren = get_yoga_strength(["Ju", "Mo"], result)
            yogas.append(f"Gajakesari Yoga (Strength {stren}/10) → Fame, wisdom, wealth")
    # 2. Raja Yogas (Kendra-Trikona lords)
    # A Yogakaraka is a single planet that lords both a kendra and a trikona.
    # Two different planets form a Raja Yoga by conjunction (same house) or
    # mutual 7th-house aspect (house difference = 6).
    seen_raja = set()
    yogakarakas_seen = set()
    for k in [1, 4, 7, 10]:
        for t in [1, 5, 9]:
            if k == t:
                continue  # same house — don't check against itself
            kl = lord_of(k)
            tl = lord_of(t)
            if kl not in planet_house or tl not in planet_house:
                continue
            if kl == tl:
                # Same planet lords both a kendra and a trikona → Yogakaraka
                if kl not in yogakarakas_seen:
                    yogakarakas_seen.add(kl)
                    s = get_yoga_strength([kl], result)
                    yogas.append(
                        f"Yogakaraka {short_to_full.get(kl, kl)} (Strength {s}/10) → "
                        f"Most powerful planet for this Lagna; grants both power & grace"
                    )
            else:
                pair = tuple(sorted([kl, tl]))
                if pair in seen_raja:
                    continue
                house_diff = (planet_house[kl] - planet_house[tl] + 12) % 12
                if house_diff in (0, 6):  # conjunction or mutual 7th aspect
                    seen_raja.add(pair)
                    s = get_yoga_strength([kl, tl], result)
                    yogas.append(
                        f"Raja Yoga ({kl}-{tl}) (Strength {s}/10) → Power & status"
                    )
    # 3. Strong Venus Yoga
    if "Ve" in planet_house:
        ve_h = planet_house["Ve"]
        if ve_h in [1, 4, 7, 10] or p["Ve"]["dignity"] in ["Own", "Exalt"]:
            s = get_yoga_strength(["Ve"], result)
            yogas.append(
                f"Strong Venus Yoga (Strength {s}/10) → Beautiful spouse, luxury"
            )
    # 4. Strong 7th Lord
    seventh_lord = result["seventh_lord"]
    if seventh_lord in planet_house and planet_house[seventh_lord] in [
        1,
        4,
        7,
        10,
        5,
        9,
    ]:
        s = get_yoga_strength([seventh_lord], result)
        yogas.append(
            f"Strong 7th Lord ({seventh_lord}) (Strength {s}/10) → Stable marriage"
        )
    # 5. Jupiter in 5th house
    if "Ju" in planet_house and planet_house["Ju"] == 5:
        s = get_yoga_strength(["Ju"], result)
        yogas.append(
            f"Jupiter in 5th (Strength {s}/10) → Excellent progeny, intelligent children"
        )
    # 6. Strong 10th Lord
    tenth_lord = lord_of(10)
    if tenth_lord in planet_house and planet_house[tenth_lord] in [1, 4, 7, 10]:
        s = get_yoga_strength([tenth_lord], result)
        yogas.append(
            f"Strong 10th Lord ({tenth_lord}) (Strength {s}/10) → High career success"
        )
    # 7. Dhana Yoga (2nd + 11th lords)
    d2 = lord_of(2)
    d11 = lord_of(11)
    if d2 in planet_house and d11 in planet_house:
        s = get_yoga_strength([d2, d11], result)
        yogas.append(f"Dhana Yoga (2nd+11th) (Strength {s}/10) → Wealth through effort")
    # 8. Pancha Mahapurusha Yogas
    pmp = {
        "Ruchaka (Mars)": ("Ma", ["Aries", "Scorpio", "Capricorn"]),
        "Bhadra (Mercury)": ("Me", ["Gemini", "Virgo"]),
        "Hamsa (Jupiter)": ("Ju", ["Cancer", "Sagittarius", "Pisces"]),
        "Malavya (Venus)": ("Ve", ["Taurus", "Libra", "Pisces"]),
        "Sasa (Saturn)": ("Sa", ["Libra", "Capricorn", "Aquarius"]),
    }
    for name, (pl, signs) in pmp.items():
        if pl in p and p[pl]["sign"] in signs and planet_house.get(pl) in [1, 4, 7, 10]:
            s = get_yoga_strength([pl], result)
            yogas.append(f"{name} Yoga (Strength {s}/10) → Great personality & success")
    return yogas if yogas else ["No major classical yogas formed"]


# ────────────────────────────────────────────────
# Vimshottari Dasha
# ────────────────────────────────────────────────
def calculate_vimshottari_dasha(moon_deg, birth_jd):
    nak_span = 360 / 27
    nak_index = int(moon_deg / nak_span) % 27
    lord_idx = nakshatra_lord_index[nak_index]
    start_lord = dasha_lords[lord_idx]
    progress = get_nakshatra_progress(moon_deg)
    full_period = dasha_periods[start_lord]
    balance_years = (1 - progress) * full_period
    dashas = []
    current_jd = birth_jd
    current_lord_idx = lord_idx
    # Balance
    balance_days = balance_years * 365.25
    end_jd = current_jd + balance_days
    dashas.append(
        {
            "lord": start_lord,
            "start_jd": current_jd,
            "end_jd": end_jd,
            "years": round(balance_years, 3),
            "antardashas": [],
        }
    )
    current_jd = end_jd
    total_years = balance_years
    while total_years < 130:
        current_lord_idx = (current_lord_idx + 1) % 9
        next_lord = dasha_lords[current_lord_idx]
        period = dasha_periods[next_lord]
        days = period * 365.25
        end_jd = current_jd + days
        dashas.append(
            {
                "lord": next_lord,
                "start_jd": current_jd,
                "end_jd": end_jd,
                "years": period,
                "antardashas": [],
            }
        )
        current_jd = end_jd
        total_years += period
    return start_lord, balance_years, dashas


def calculate_antardashas(mdadasha):
    md_lord = mdadasha["lord"]
    md_days = mdadasha["end_jd"] - mdadasha["start_jd"]
    md_years = md_days / 365.25
    antardashas = []
    current_ad_jd = mdadasha["start_jd"]
    md_idx = dasha_lords.index(md_lord)
    for i in range(9):
        ad_idx = (md_idx + i) % 9
        ad_lord = dasha_lords[ad_idx]
        ad_full_years = dasha_periods[ad_lord]
        ad_proportion = ad_full_years / 120.0
        ad_years_in_md = md_years * ad_proportion
        ad_days = ad_years_in_md * 365.25
        ad_end_jd = current_ad_jd + ad_days
        antardashas.append(
            {
                "lord": ad_lord,
                "start_jd": current_ad_jd,
                "end_jd": ad_end_jd,
                "years": round(ad_years_in_md, 3),
            }
        )
        current_ad_jd = ad_end_jd
    mdadasha["antardashas"] = antardashas
    return mdadasha


def find_current_dasha(birth_jd, current_jd, dashas):
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        md_start_y = (md["start_jd"] - birth_jd) / 365.25
        md_end_y = (md["end_jd"] - birth_jd) / 365.25
        if md_start_y <= years_since < md_end_y:
            for ad in md["antardashas"]:
                ad_start_y = (ad["start_jd"] - birth_jd) / 365.25
                ad_end_y = (ad["end_jd"] - birth_jd) / 365.25
                if ad_start_y <= years_since < ad_end_y:
                    return md["lord"], ad["lord"]
    return None, None


def get_current_pratyantar(birth_jd, current_jd, current_md, current_ad, dashas):
    """Compute and return the current Pratyantar Dasha (3rd level) lord."""
    years_since = (current_jd - birth_jd) / 365.25
    for md in dashas:
        if md["lord"] != current_md:
            continue
        for ad in md["antardashas"]:
            if ad["lord"] != current_ad:
                continue
            # Compute pratyantars for this AD on the fly
            ad_days = ad["end_jd"] - ad["start_jd"]
            ad_years = ad_days / 365.25
            current_pd_jd = ad["start_jd"]
            ad_idx = dasha_lords.index(current_ad)
            for i in range(9):
                pd_idx = (ad_idx + i) % 9
                pd_lord = dasha_lords[pd_idx]
                pd_years = ad_years * (dasha_periods[pd_lord] / 120.0)
                pd_end_jd = current_pd_jd + pd_years * 365.25
                pd_start_y = (current_pd_jd - birth_jd) / 365.25
                pd_end_y = (pd_end_jd - birth_jd) / 365.25
                if pd_start_y <= years_since < pd_end_y:
                    pd_start_date = datetime.datetime(1, 1, 1) + datetime.timedelta(
                        days=int(current_pd_jd - swe.julday(1, 1, 1, 12.0))
                    ) if False else None  # date formatting done elsewhere
                    return pd_lord, current_pd_jd, pd_end_jd
                current_pd_jd = pd_end_jd
    return None, None, None


# ────────────────────────────────────────────────
# Aspects & Transits
# ────────────────────────────────────────────────
def calculate_aspects(houses):
    aspects = {h: [] for h in range(1, 13)}
    planet_houses = {p: h for h, plist in houses.items() for p in plist if p != "Asc"}
    for planet, ph in planet_houses.items():
        aspect_h = ((ph - 1 + 6) % 12) + 1
        aspects[aspect_h].append(f"{planet}-7th")
    special = {"Ma": [3, 7], "Ju": [4, 8], "Sa": [2, 9]}
    for planet, offsets in special.items():
        if planet in planet_houses:
            ph = planet_houses[planet]
            for offset in offsets:
                ah = ((ph - 1 + offset) % 12) + 1
                aspects[ah].append(f"{planet}-{offset + 1}")
    for node in ["Ra", "Ke"]:
        if node in planet_houses:
            nh = planet_houses[node]
            for offset in [4, 8]:
                ah = ((nh - 1 + offset) % 12) + 1
                aspects[ah].append(f"{node}-5/9")
    return aspects


def calculate_transits(natal_moon_sign, current_jd):
    transits = {}
    moon_idx = zodiac_signs.index(natal_moon_sign)
    for pcode, pid in planets.items():
        lon = swe.calc_ut(current_jd, pid, swe.FLG_SIDEREAL)[0][0]
        sign = get_sign(lon)
        sign_idx = zodiac_signs.index(sign)
        rel_house = ((sign_idx - moon_idx + 12) % 12) + 1
        effect = gochara_effects.get(pcode, {}).get(rel_house, "Neutral")
        transits[pcode] = {"sign": sign, "house_from_moon": rel_house, "effect": effect}
    ra_lon = swe.calc_ut(current_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    ra_sign = get_sign(ra_lon)
    ra_idx = zodiac_signs.index(ra_sign)
    ra_house = ((ra_idx - moon_idx + 12) % 12) + 1
    transits["Ra"] = {
        "sign": ra_sign,
        "house_from_moon": ra_house,
        "effect": gochara_effects.get("Ra", {}).get(ra_house, "Neutral"),
    }
    ke_lon = (ra_lon + 180) % 360
    ke_sign = get_sign(ke_lon)
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = ((ke_idx - moon_idx + 12) % 12) + 1
    transits["Ke"] = {
        "sign": ke_sign,
        "house_from_moon": ke_house,
        "effect": gochara_effects.get("Ke", {}).get(ke_house, "Neutral"),
    }
    return transits


# ────────────────────────────────────────────────
# Main Kundali Calculation
# ────────────────────────────────────────────────
def calculate_kundali(birth_date_str, birth_time_str, place):
    y, m, d = map(int, birth_date_str.split("-"))
    hh, mm = map(int, birth_time_str.split(":"))
    lat, lon = get_lat_lon(place)
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if not tz_name:
        raise ValueError("Timezone could not be determined")
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime.datetime(y, m, d, hh, mm))
    utc_dt = local_dt.astimezone(pytz.utc)
    birth_jd = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0
    )
    # Houses & Lagna
    house_data = swe.houses_ex(birth_jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    cusps, ascmc = house_data
    lagna_deg = ascmc[0]
    lagna_sign = get_sign(lagna_deg)
    lagna_idx = zodiac_signs.index(lagna_sign)
    house_planets = {i + 1: [] for i in range(12)}
    planet_data = {}
    moon_sign = None
    moon_nakshatra = None
    sun_full_lon = None
    for code, pid in planets.items():
        pos_speed = swe.calc_ut(birth_jd, pid, swe.FLG_SIDEREAL)[0]
        lon = pos_speed[0]
        speed = pos_speed[3]
        sign = get_sign(lon)
        deg_in_sign = round(lon % 30, 2)
        nak = get_nakshatra(lon)
        dignity = get_dignity(code, sign)
        retro = is_retrograde(speed)
        if code == "Su":
            sun_full_lon = lon
        planet_data[code] = {
            "deg": deg_in_sign,
            "full_lon": round(lon, 4),
            "sign": sign,
            "nakshatra": nak,
            "dignity": dignity,
            "retro": retro,
            "combust": False,  # filled after Sun lon is known
            "neecha_bhanga": False,  # filled after all planets are placed
            "navamsa_sign": None,
            "navamsa_deg": None,
            "d7_sign": None,
            "d7_deg": None,
            "d10_sign": None,
            "d10_deg": None,
        }
        if code == "Mo":
            moon_sign = sign
            moon_nakshatra = nak
        p_idx = zodiac_signs.index(sign)
        house = get_house_from_sign(lagna_idx, p_idx)
        house_planets[house].append(code)
    # Combustion check (requires Sun longitude computed first)
    if sun_full_lon is not None:
        for code in planet_data:
            if code == "Su":
                continue
            planet_data[code]["combust"] = check_combustion(
                code,
                planet_data[code]["full_lon"],
                sun_full_lon,
                planet_data[code]["retro"],
            )
    # Neecha Bhanga (after combustion is set, before Ke is added)
    moon_house_nb = None
    for _h, _plist in house_planets.items():
        if "Mo" in _plist:
            moon_house_nb = _h
            break
    for code in list(planet_data.keys()):
        if code in ("Su", "Ra", "Ke"):
            continue  # Sun never debilitated; Ra/Ke handled separately
        planet_data[code]["neecha_bhanga"] = check_neecha_bhanga(
            code, planet_data, house_planets, lagna_idx, moon_house_nb
        )
    # Ketu + Ra lon for later
    ra_lon = swe.calc_ut(birth_jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0]
    ke_lon = (ra_lon + 180) % 360
    ke_sign = get_sign(ke_lon)
    ke_deg = round(ke_lon % 30, 2)
    ke_nak = get_nakshatra(ke_lon)
    ke_dignity = get_dignity("Ke", ke_sign)
    planet_data["Ke"] = {
        "deg": ke_deg,
        "sign": ke_sign,
        "nakshatra": ke_nak,
        "dignity": ke_dignity,
        "retro": True,
        "combust": False,
        "neecha_bhanga": False,  # nodes not subject to neecha bhanga
        "navamsa_sign": None,
        "navamsa_deg": None,
        "d7_sign": None,
        "d7_deg": None,
        "d10_sign": None,
        "d10_deg": None,
    }
    ke_idx = zodiac_signs.index(ke_sign)
    ke_house = get_house_from_sign(lagna_idx, ke_idx)
    house_planets[ke_house].append("Ke")
    house_planets[1].append("Asc")  # Ascendant in 1st house
    # Add Ketu full_lon and combust
    planet_data["Ke"]["full_lon"] = round(ke_lon, 4)
    planet_data["Ke"]["combust"] = False  # Ke not affected by combustion
    # 7th Lord
    seventh_idx = (lagna_idx + 6) % 12
    seventh_sign = zodiac_signs[seventh_idx]
    seventh_lord = sign_lords[seventh_sign]
    # House Lord Placements
    house_lord_map = {}  # house_num → (lord_code, lord_in_house)
    for h_num in range(1, 13):
        h_sign = zodiac_signs[(lagna_idx + h_num - 1) % 12]
        h_lord = sign_lords[h_sign]
        # Find which house the lord is placed in
        lord_in_house = None
        for ph, plist in house_planets.items():
            if h_lord in plist:
                lord_in_house = ph
                break
        house_lord_map[h_num] = {"lord": h_lord, "placed_in": lord_in_house}
    # Birth Panchanga
    sun_lon_birth = planet_data["Su"]["full_lon"]
    moon_lon_birth = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    panchanga = get_panchanga(birth_jd, sun_lon_birth, moon_lon_birth)
    # Divisional Charts
    for code in planet_data:
        if code == "Ra":
            p_lon = ra_lon
        elif code == "Ke":
            p_lon = ke_lon
        else:
            p_lon = (zodiac_signs.index(planet_data[code]["sign"]) * 30) + planet_data[
                code
            ]["deg"]
        ns, nd = get_navamsa_sign_and_deg(p_lon)
        d7s, d7d = get_d7_sign_and_deg(p_lon)
        d10s, d10d = get_d10_sign_and_deg(p_lon)
        planet_data[code]["navamsa_sign"] = ns
        planet_data[code]["navamsa_deg"] = nd
        planet_data[code]["d7_sign"] = d7s
        planet_data[code]["d7_deg"] = d7d
        planet_data[code]["d10_sign"] = d10s
        planet_data[code]["d10_deg"] = d10d
    # Vimshottari
    moon_lon = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    start_lord, balance_y, dashas_raw = calculate_vimshottari_dasha(moon_lon, birth_jd)
    dashas = [calculate_antardashas(md) for md in dashas_raw]
    # Current time (UTC)
    now_utc = datetime.datetime.now(pytz.utc)
    current_jd = datetime_to_jd(now_utc)
    current_md, current_ad = find_current_dasha(birth_jd, current_jd, dashas)
    current_pd, pd_start_jd, pd_end_jd = get_current_pratyantar(
        birth_jd, current_jd, current_md, current_ad, dashas
    )
    aspects = calculate_aspects(house_planets)
    transits = calculate_transits(moon_sign, current_jd)
    # Sade Sati / Dhaiya
    sa_transit_sign = transits.get("Sa", {}).get("sign", None)
    sade_sati_status = get_sade_sati_status(moon_sign, sa_transit_sign) if sa_transit_sign else None
    result = {
        "lagna_deg": round(lagna_deg, 2),
        "lagna_sign": lagna_sign,
        "seventh_lord": seventh_lord,
        "planets": planet_data,
        "houses": house_planets,
        "moon_sign": moon_sign,
        "moon_nakshatra": moon_nakshatra,
        "vimshottari": {
            "starting_lord": start_lord,
            "balance_at_birth_years": round(balance_y, 2),
            "mahadasas": dashas,
            "current_md": current_md,
            "current_ad": current_ad,
        },
        "aspects": aspects,
        "navamsa": {
            p: {"sign": d["navamsa_sign"], "deg": d["navamsa_deg"]}
            for p, d in planet_data.items()
        },
        "d7": {
            p: {"sign": d["d7_sign"], "deg": d["d7_deg"]}
            for p, d in planet_data.items()
        },
        "d10": {
            p: {"sign": d["d10_sign"], "deg": d["d10_deg"]}
            for p, d in planet_data.items()
        },
        "transits": transits,
        "birth_year": y,
        "birth_jd": birth_jd,
        "panchanga": panchanga,
        "house_lords": house_lord_map,
        "sade_sati": sade_sati_status,
        "vimshottari_pd": {
            "current_pd": current_pd,
            "pd_start_jd": pd_start_jd,
            "pd_end_jd": pd_end_jd,
        },
    }
    # Add yogas, timings, and problems
    result["yogas"] = detect_yogas(result)
    result["timings"] = generate_timings(result, y, birth_jd)
    result["problems"] = detect_problems(result)
    result["final_analysis"] = generate_final_analysis(result)
    return result


# ────────────────────────────────────────────────
# Interpretation Functions
# ────────────────────────────────────────────────

HOUSE_SIGNIFICATIONS = {
    1: "Self, personality, health, constitution, appearance, early life",
    2: "Wealth, family, speech, food, accumulated assets, face",
    3: "Courage, siblings, communication, short travels, initiative, hands",
    4: "Home, mother, property, emotional happiness, vehicles, education",
    5: "Children, creativity, intelligence, romance, past karma, speculation",
    6: "Enemies, debts, disease, service, daily routines, maternal relatives",
    7: "Marriage, partnerships, business partners, open enemies, desires",
    8: "Longevity, transformation, occult, inheritance, sudden events, research",
    9: "Luck, dharma, father, guru, long travels, higher philosophy, fortune",
    10: "Career, fame, authority, status, public image, father, government",
    11: "Gains, income, friends, elder siblings, aspirations, social network",
    12: "Losses, isolation, foreign lands, moksha, hidden enemies, expenses",
}

NATURAL_BENEFICS = {"Ju", "Ve", "Mo"}
NATURAL_MALEFICS = {"Sa", "Ma", "Su", "Ra", "Ke"}


def get_aspect_quality_score(planet, lagna_sign, dignity, is_combust=False, is_retro=False):
    """Calculate aspect quality score for a planet.
    Returns: (score, nature_label)
      score > 0 = beneficial influence
      score < 0 = challenging influence
      score = 0 = neutral
    nature_label describes the functional classification.
    """
    fq = FUNCTIONAL_QUALITY.get(lagna_sign, {})
    
    # Base score from functional nature
    if planet in fq.get("ben", []):
        base = 2
        nature_label = "func. benefic"
    elif planet == fq.get("yk"):
        base = 3
        nature_label = "Yogakaraka"
    elif planet in fq.get("mal", []):
        base = -2
        nature_label = "func. malefic"
    elif planet in fq.get("maraka", []):
        base = -1
        nature_label = "Maraka"
    elif planet in fq.get("mixed", []):
        base = 0
        nature_label = "mixed"
    else:
        # Default to natural classification
        if planet in NATURAL_BENEFICS:
            base = 1
            nature_label = "nat. benefic"
        else:
            base = -1
            nature_label = "nat. malefic"
    
    # Dignity modifier (strength override)
    if dignity == "Exalt":
        base += 2  # Exaltation significantly improves results
    elif dignity == "Own":
        base += 1  # Own sign is stable and positive
    elif dignity == "Debilitated":
        base -= 1  # Debilitation weakens (but doesn't fully negate functional nature)
    
    # Combustion weakens significantly
    if is_combust:
        base -= 1
    
    return base, nature_label

PLANET_ASPECT_THEMES = {
    "Su": {
        "7th": "Sun casts its authority and ego here – leadership potential; father-figures and government influence; pride may cause friction.",
    },
    "Mo": {
        "7th": "Moon's reflective, nurturing energy touches this house – strong emotional sensitivity; fluctuating results; public and maternal influence.",
    },
    "Ma": {
        "7th": "Mars fires this house with energy, ambition, and aggression – disputes possible but also bold initiative and protection.",
        "4": "Mars' 4th aspect energises home/property themes – real estate gains possible; family arguments; drive in educational pursuits.",
        "8": "Mars' full 8th aspect (75%) activates transformation and risk – sudden events, occult interest, accidents; surgery or research fields.",
    },
    "Me": {
        "7th": "Mercury brings intellect and communication to this house – business acumen, analytical energy, youthful and witty expression.",
    },
    "Ju": {
        "7th": "Jupiter's powerful full aspect (100%) blesses and expands this house – wisdom, prosperity, dharmic protection, and divine grace.",
        "5": "Jupiter's 5th aspect (75%) is deeply auspicious – wisdom, children, creativity, intelligence, and past-karma resolution richly blessed.",
        "9": "Jupiter's 9th aspect (75%) bestows dharma, luck, and spiritual blessings – father, guru, and long-distance good fortune.",
    },
    "Ve": {
        "7th": "Venus pours beauty, harmony, love, and material comforts into this house – artistic gifts, refined partnerships.",
    },
    "Sa": {
        "7th": "Saturn's disciplining aspect (100%) creates karmic tests and delays here – slow but lasting results; serious, dutiful outcomes.",
        "3": "Saturn's 3rd aspect (25%) adds persistent caution to communication and courage – methodical, hard-working energy; slow siblings/journeys.",
        "10": "Saturn's powerful 10th aspect (75%) enforces discipline in career and authority – delays early but eventual recognition and structured success.",
    },
    "Ra": {
        "7th": "Rahu amplifies desires and brings unconventional, foreign influences to this house – obsession, illusion, sudden twists.",
        "5/9": "Rahu's 5th/9th axis activates karmic obsessions – unusual circumstances in children, creativity, luck, and dharma themes.",
    },
    "Ke": {
        "7th": "Ketu brings detachment, past-karma, and spiritual insights to this house – dissolution of illusions; mystical or karmic events.",
        "5/9": "Ketu's 5th/9th axis awakens past-life karma – spiritual lessons in children, creativity, luck, dharma, and higher learning.",
    },
}


def interpret_aspects(result):
    """Full Drishti analysis per house with strength, nature, and life outcomes.
    Uses functional nature + dignity for balanced assessment instead of just natural benefic/malefic."""
    aspects = result["aspects"]
    lagna_sign = result["lagna_sign"]
    lagna_idx = zodiac_signs.index(lagna_sign)
    planets_data = result["planets"]
    out = []

    strength_labels = {
        "7th": "100%",
        "4": "50%",
        "8": "75%",
        "5": "75%",
        "9": "75%",
        "3": "25%",
        "10": "75%",
        "5/9": "75%",
    }

    for h in range(1, 13):
        if not aspects[h]:
            continue
        house_sign = zodiac_signs[(lagna_idx + h - 1) % 12]
        signif = HOUSE_SIGNIFICATIONS[h]
        out.append(f"\nHouse {h:2d} ({house_sign}) – {signif.split(',')[0]}:")
        out.append(f"  Significations: {signif}")

        total_score = 0
        aspect_details = []

        for asp in aspects[h]:
            parts = asp.split("-")
            pl = parts[0]
            asp_type = parts[1] if len(parts) > 1 else "7th"

            pl_data = planets_data.get(pl, {})
            dig = pl_data.get("dignity", "") if pl_data else ""
            retro = pl_data.get("retro", False) if pl_data else False
            combust = pl_data.get("combust", False) if pl_data else False
            
            # Strength description
            if dig == "Exalt":
                strength_note = "Exalted – very strong"
            elif dig == "Own":
                strength_note = "Own sign – strong"
            elif dig == "Debilitated":
                strength_note = "Debilitated – weakened"
            elif combust:
                strength_note = "Combust – weakened by Sun"
            elif retro:
                strength_note = "Retrograde – intensified"
            else:
                strength_note = "Normal strength"

            # Get functional nature score
            score, nature_label = get_aspect_quality_score(pl, lagna_sign, dig, combust, retro)
            total_score += score
            
            asp_pct = strength_labels.get(asp_type, "100%")
            pl_full = short_to_full.get(pl, pl)

            theme = PLANET_ASPECT_THEMES.get(pl, {}).get(
                asp_type,
                f"{pl_full} brings its significations into this house.",
            )

            out.append(
                f"  • {pl_full:8} ({asp_type} aspect, {asp_pct}, {nature_label}, {strength_note})"
            )
            out.append(f"    → {theme}")

        # Net summary based on total score
        h_area = signif.split(",")[0]
        if total_score >= 3:
            out.append(
                f"  ✓ Net: Strongly positive influences – {h_area} is well-supported; results come naturally."
            )
        elif total_score >= 1:
            out.append(
                f"  ✓ Net: Positive overall – {h_area} benefits from supportive planetary energy."
            )
        elif total_score >= -1:
            out.append(
                f"  ~ Net: Mixed influences – {h_area} has balanced energies; results depend on dasha periods."
            )
        elif total_score >= -3:
            out.append(
                f"  ~ Net: Challenging influences – {h_area} requires conscious effort; dasha of benefics helps."
            )
        else:
            out.append(
                f"  ⚠ Net: Significant challenges in {h_area}; focused remedies and benefic dashas recommended."
            )

    return out


def interpret_navamsa(result):
    """Full D9 Navamsa analysis – marriage, spouse, dharma, inner soul"""
    navamsa = result["navamsa"]
    planets_data = result["planets"]
    out = []
    out.append("(D9 reveals spouse character, marriage quality, dharmic path, and "
               "the soul's evolutionary direction. D1 shows the promise; D9 confirms or modifies it. "
               "Strong D1 + strong D9 = highly reliable results; strong D1 + weak D9 = fluctuating results; "
               "weak D1 + strong D9 = gradual improvement over time.)")

    planet_d9_meanings = {
        "Su": "Soul authority: spouse may have Sun-like qualities (leadership, pride). Dharma path involves service, governance, or father-like responsibility.",
        "Mo": "Emotional soul: deep emotional bond with spouse; marriage is nurturing. Inner self driven by security, mother, and public approval.",
        "Ma": "Passionate soul: spouse is energetic, ambitious, possibly athletic or bold. Marriage has intense passion; conflicts must be managed consciously.",
        "Me": "Intellectual soul: spouse is communicative, witty, analytical. Marriage thrives on mental connection; dharma through teaching or trade.",
        "Ju": "Wisdom soul: spouse is wise, spiritual, generous. Jupiter's D9 dignity determines dharmic blessings; strong = growth, weak = obstacles.",
        "Ve": "Artistic soul: spouse is beautiful, artistic, loving, comfort-seeking. Venus's D9 dignity is crucial for marital harmony and satisfaction.",
        "Sa": "Karmic soul: spouse may be older, serious, disciplined, or from a different background. Marriage has karmic weight; deep loyalty over time.",
        "Ra": "Unconventional soul: spouse may be foreign, unconventional, or connected by past-life karma. Marriage outside norms; obsessive at times.",
        "Ke": "Spiritual soul: previous-life karmic bond with spouse; partner may be deeply spiritual, detached, or intuitive. Marriage is meaningful but impersonal.",
    }

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for pl in order:
        if pl not in navamsa:
            continue
        d = navamsa[pl]
        nav_sign = d["sign"]
        nav_dig = get_dignity(pl, nav_sign)
        dig_note = f" [{nav_dig}]" if nav_dig else ""
        pl_full = short_to_full.get(pl, pl)
        out.append(f"  {pl_full:9} in {nav_sign:12} {d['deg']:5.2f}°{dig_note}")
        out.append(f"    → {planet_d9_meanings[pl]}")
        if nav_dig == "Debilitated":
            out.append(f"    ⚠ Debilitated in D9: {pl_full}'s marriage/dharma significations are weakened; "
                       f"planet must be strengthened in D1 or by remedies to give good results.")
        elif nav_dig in ("Exalt", "Own"):
            out.append(f"    ✓ {nav_dig} in D9: {pl_full}'s significations are powerfully reliable "
                       f"in marriage and dharmic areas.")

    # Vargottama check
    vargottama = [
        short_to_full.get(pl, pl)
        for pl in order
        if pl in planets_data
        and pl in navamsa
        and planets_data[pl]["sign"] == navamsa[pl]["sign"]
    ]
    out.append("\n  Vargottama (same sign in D1 and D9 – doubled strength):")
    if vargottama:
        out.append(f"  → {', '.join(vargottama)}: These planets are extremely stable and reliable "
                   f"in their results; their placement in D1 is fully confirmed by D9.")
    else:
        out.append("  → No Vargottama planets.")

    # Best and worst D9 placements
    exalt_d9 = [short_to_full.get(pl, pl) for pl in order
                if pl in navamsa and get_dignity(pl, navamsa[pl]["sign"]) == "Exalt"]
    deb_d9 = [short_to_full.get(pl, pl) for pl in order
              if pl in navamsa and get_dignity(pl, navamsa[pl]["sign"]) == "Debilitated"]
    if exalt_d9:
        out.append(f"  ✓ Exalted in D9: {', '.join(exalt_d9)} – Marriage/dharma blessings are magnified.")
    if deb_d9:
        out.append(f"  ⚠ Debilitated in D9: {', '.join(deb_d9)} – D1 promise may fluctuate; conscious effort helps stabilise results.")
    # Venus in D9 is the single most important marriage indicator
    if "Ve" in navamsa:
        ve_d9_sign = navamsa["Ve"]["sign"]
        ve_d9_dig = get_dignity("Ve", ve_d9_sign)
        if ve_d9_dig in ("Exalt", "Own"):
            ve_note = "Excellent – beauty, love, and harmony are core features of marriage."
        elif ve_d9_dig == "Debilitated":
            ve_note = "Debilitated – marital satisfaction may require extra effort; Venus remedies can help."
        else:
            ve_note = "Moderate – marriage has affection but may need conscious nurturing."
        dig_tag = f", {ve_d9_dig}" if ve_d9_dig else ""
        out.append(f"\n  Venus in D9 ({ve_d9_sign}{dig_tag}): {ve_note}")
    return out


def interpret_d7(result):
    """Full D7 Saptamsa analysis – children, progeny, generative energy"""
    d7 = result["d7"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    fifth_sign = zodiac_signs[(lagna_idx + 4) % 12]
    fifth_lord = sign_lords[fifth_sign]
    out = []
    out.append("(D7 reveals potential for children, timing of progeny, their "
               "nature and quality. Jupiter and 5th lord are the primary karakas.)")

    planet_d7_meanings = {
        "Su": "Progeny will have leadership, pride, and authority – strongly willed, possibly in government or power roles. Father's legacy passed to children.",
        "Mo": "Nurturing, sensitive children with strong emotional intelligence. Close mother-child bond. Children may work in public, nurturing, or creative fields.",
        "Ma": "Energetic, bold, athletic children – courageous and competitive. Possibly more sons. Active and passionate generative force.",
        "Me": "Intelligent, communicative, analytical children. Academic excellence likely. Children suited to communication, IT, trade, or education careers.",
        "Ju": "Wise, fortunate, well-educated children – the most auspicious D7 planet. Abundant blessings for progeny; children bring joy and prosperity.",
        "Ve": "Artistic, beautiful, socially gifted children. Strong aesthetic sensibility. Children may excel in arts, design, fashion, or diplomacy.",
        "Sa": "Fewer children or delays; disciplined and serious progeny. Children may face early hardships but build strong characters. Karmic parent-child bond.",
        "Ra": "Unconventional, innovative children – possibly gifted in technology, foreign fields. Unusual conception circumstances or unexpected arrival.",
        "Ke": "Spiritually oriented or intuitive children; past-life karmic connection. Children may show detachment from worldly life or mystical inclinations.",
    }

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for pl in order:
        if pl not in d7:
            continue
        d = d7[pl]
        d7_sign = d["sign"]
        d7_dig = get_dignity(pl, d7_sign)
        dig_note = f" [{d7_dig}]" if d7_dig else ""
        pl_full = short_to_full.get(pl, pl)
        out.append(f"  {pl_full:9} in {d7_sign:12} {d['deg']:5.2f}°{dig_note}")
        out.append(f"    → {planet_d7_meanings[pl]}")
        if d7_dig == "Debilitated":
            out.append(f"    ⚠ Debilitated in D7: challenges to above; remedies (Jupiter mantra, charity) advised.")
        elif d7_dig in ("Exalt", "Own"):
            out.append(f"    ✓ {d7_dig} in D7: above significations fully activated and reliable.")

    # Jupiter in D7 summary
    out.append(f"\n  Key Karakas: Jupiter (natural) + 5th lord {short_to_full.get(fifth_lord, fifth_lord)} (functional)")
    if "Ju" in d7:
        ju_sign = d7["Ju"]["sign"]
        ju_dig = get_dignity("Ju", ju_sign)
        if ju_dig == "Exalt":
            out.append(f"  ✓ Jupiter Exalted in D7 ({ju_sign}) – Excellent, abundant, and wise progeny strongly indicated.")
        elif ju_dig == "Own":
            out.append(f"  ✓ Jupiter in Own sign in D7 ({ju_sign}) – Good number of children; wise and fortunate progeny.")
        elif ju_dig == "Debilitated":
            out.append(f"  ⚠ Jupiter Debilitated in D7 ({ju_sign}) – Progeny challenges; possible delays or health issues for children; remedies essential.")
        else:
            out.append(f"  Jupiter in {ju_sign} in D7 – Moderate progeny; timing through Jupiter/5th lord Dasha is key.")
    return out


def interpret_d10(result):
    """Full D10 Dasamsa analysis – career, profession, public life"""
    d10 = result["d10"]
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    tenth_sign = zodiac_signs[(lagna_idx + 9) % 12]
    tenth_lord = sign_lords[tenth_sign]
    out = []
    out.append("(D10 reveals true professional destiny, career field, authority level, "
               "and the quality of public life. Sun, Saturn, and 10th lord are primary karakas.)")

    planet_d10_meanings = {
        "Su": "Government, administration, politics, leadership roles, father's career influence. Sun strong in D10 = fame, authority, and recognition.",
        "Mo": "Public-facing work, healthcare, hospitality, food, real estate, business involving masses. Fluctuating but popular career.",
        "Ma": "Engineering, military, surgery, real estate, sports, competitive and technical fields. Mars strong = decisive, results-driven professional.",
        "Me": "Communication, writing, IT, education, trade, accounts, media, analysis. Mercury strong = skilled, versatile professional.",
        "Ju": "Teaching, law, counseling, finance, philosophy, management, spiritual guidance. Jupiter strong in D10 = respected, morally driven career.",
        "Ve": "Arts, entertainment, fashion, luxury goods, beauty industry, hospitality, diplomacy. Venus strong = glamorous or aesthetics-driven profession.",
        "Sa": "Service sector, labor, judiciary, mining, research, long-term technical work, social welfare. Saturn strong = career builder who earns through sustained effort.",
        "Ra": "Foreign companies, cutting-edge technology, unconventional professions, film, mass politics, import/export. Rahu = career outside traditional norms.",
        "Ke": "Research, spirituality, healing arts, behind-the-scenes work, mathematics, programming. Ketu = expertise in niche or hidden fields.",
    }

    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    for pl in order:
        if pl not in d10:
            continue
        d = d10[pl]
        d10_sign = d["sign"]
        d10_dig = get_dignity(pl, d10_sign)
        dig_note = f" [{d10_dig}]" if d10_dig else ""
        pl_full = short_to_full.get(pl, pl)
        out.append(f"  {pl_full:9} in {d10_sign:12} {d['deg']:5.2f}°{dig_note}")
        out.append(f"    → {planet_d10_meanings[pl]}")
        if d10_dig == "Debilitated":
            out.append(f"    ⚠ Debilitated in D10: professional obstacles in this area; choose field aligned with planet's strength elsewhere.")
        elif d10_dig in ("Exalt", "Own"):
            out.append(f"    ✓ {d10_dig} in D10: career success in this domain is strongly supported.")

    # 10th lord summary
    out.append(f"\n  Primary Karaka: Sun (fame/authority) | Functional 10th Lord: {short_to_full.get(tenth_lord, tenth_lord)}")
    if tenth_lord in d10:
        tl_sign = d10[tenth_lord]["sign"]
        tl_dig = get_dignity(tenth_lord, tl_sign)
        if tl_dig in ("Exalt", "Own"):
            out.append(f"  ✓ 10th lord ({short_to_full.get(tenth_lord, tenth_lord)}) {tl_dig} in D10 ({tl_sign}) – Peak career success; prominence and rise to authority highly indicated.")
        elif tl_dig == "Debilitated":
            out.append(f"  ⚠ 10th lord Debilitated in D10 ({tl_sign}) – Career hurdles; switching to the planet's natural field (see above) and remedies help significantly.")
        else:
            out.append(f"  10th lord in {tl_sign} in D10 – Career grows steadily through hard work; major rise during 10th lord's Mahadasha.")
    # Sun in D10
    if "Su" in d10:
        su_dig = get_dignity("Su", d10["Su"]["sign"])
        if su_dig in ("Exalt", "Own"):
            out.append(f"  ✓ Sun ({su_dig}) in D10 – Strong public image, authority, and social recognition.")
        elif su_dig == "Debilitated":
            out.append(f"  ⚠ Sun Debilitated in D10 – Ego conflicts with authority; avoid confrontations with superiors; build reputation quietly.")
    # Exalted/debilitated summary
    exalt_d10 = [short_to_full.get(pl, pl) for pl in order
                 if pl in d10 and get_dignity(pl, d10[pl]["sign"]) == "Exalt"]
    deb_d10 = [short_to_full.get(pl, pl) for pl in order
               if pl in d10 and get_dignity(pl, d10[pl]["sign"]) == "Debilitated"]
    if exalt_d10:
        out.append(f"  ✓ Exalted in D10: {', '.join(exalt_d10)} – Career domains of these planets thrive.")
    if deb_d10:
        out.append(f"  ⚠ Debilitated in D10: {', '.join(deb_d10)} – Avoid career fields solely dependent on these planets.")
    return out


# ────────────────────────────────────────────────
# Print Function
# ────────────────────────────────────────────────
def print_kundali(result, file=None):
    lines = []

    def write(s):
        lines.append(s)

    write("\n" + "═" * 95)
    write(" VEDIC KUNDALI – Whole Sign – Lahiri – D7 + D10 + Marriage Timing")
    write("═" * 95)
    write(f"Lagna        : {result['lagna_sign']} {result['lagna_deg']}°")
    write(f"Moon (Rasi)  : {result['moon_sign']} – {result['moon_nakshatra']}")
    write(f"7th Lord     : {result['seventh_lord']}")
    # Panchanga
    pan = result.get("panchanga", {})
    if pan:
        write(f"Tithi        : {pan.get('tithi','?')}")
        write(f"Vara         : {pan.get('vara','?')}")
        write(f"Yoga         : {pan.get('yoga','?')}")
        write(f"Karana       : {pan.get('karana','?')}")
    write("")
    order = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
    write("Planets in Rasi (D1):")
    write("-" * 85)
    for pl in order:
        if pl in result["planets"]:
            d = result["planets"][pl]
            flags = ""
            if d.get("retro"):
                flags += " R"
            if d.get("combust"):
                flags += " C"
            # Dignity label — append NB when neecha bhanga cancels debilitation
            dig_label = d["dignity"]
            if dig_label == "Debilitated" and d.get("neecha_bhanga", False):
                dig_label = "Debilitated (NB)"
            dig = f" ({dig_label})" if dig_label else ""
            write(
                f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11} {d['nakshatra']:18}{dig}{flags}"
            )
    write("  (R = Retrograde, C = Combust/Astangata – weakened by closeness to Sun, NB = Neecha Bhanga – debilitation cancelled)")
    for div, title, interp_fn in [
        ("navamsa", "Navamsa (D9 – Marriage/Spouse/Dharma)", interpret_navamsa),
        ("d7", "Saptamsa (D7 – Children/Progeny)", interpret_d7),
        ("d10", "Dasamsa (D10 – Career/Profession)", interpret_d10),
    ]:
        write(f"\n{title}:")
        write("-" * 85)
        for pl in order:
            if pl in result[div]:
                d = result[div][pl]
                write(f"{pl:>3}: {d['deg']:5.2f}° {d['sign']:11}")
        write(f"\nDetailed {title.split('(')[1].rstrip(')')} Analysis:")
        write("-" * 85)
        for line in interp_fn(result):
            write(line)
    write("\nHouses (Whole Sign):")
    write("-" * 85)
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    for h in range(1, 13):
        sidx = (lagna_idx + h - 1) % 12
        sign = zodiac_signs[sidx]
        pls = sorted(result["houses"][h])
        content = " ".join(pls) if pls else "—"
        write(f"House {h:2d} ({sign:11}): {content}")
    write("\nAspects (Drishti) – Summary:")
    write("-" * 85)
    for h in range(1, 13):
        if result["aspects"][h]:
            write(f"House {h:2d}: {', '.join(result['aspects'][h])}")
    write("\nAspects (Drishti) – Full Analysis:")
    write("-" * 85)
    write("Aspect strengths: 7th=100% | Jupiter 5th/9th=75% | Mars 8th=75% | Saturn 10th=75% | Mars 4th=50% | Saturn 3rd=25%")
    for line in interpret_aspects(result):
        write(line)
    # Functional Benefics/Malefics
    write("\nFunctional Benefics / Malefics (by Lagna):")
    write("-" * 85)
    fq = FUNCTIONAL_QUALITY.get(result["lagna_sign"], {})
    if fq:
        ben_names = [short_to_full.get(p, p) for p in fq.get("ben", [])]
        mal_names = [short_to_full.get(p, p) for p in fq.get("mal", [])]
        maraka_names = [short_to_full.get(p, p) for p in fq.get("maraka", [])]
        mixed_names = [short_to_full.get(p, p) for p in fq.get("mixed", [])]
        yk = fq.get("yk")
        write(f"  Functional Benefics  : {', '.join(ben_names) if ben_names else '—'}")
        write(f"  Functional Malefics  : {', '.join(mal_names) if mal_names else '—'}")
        write(f"  Marakas (2nd/7th)    : {', '.join(maraka_names) if maraka_names else '—'}")
        write(f"  Mixed Nature         : {', '.join(mixed_names) if mixed_names else '—'}")
        if yk:
            write(f"  Yogakaraka           : {short_to_full.get(yk, yk)} "
                  f"(owns both kendra + trikona for this lagna – most powerful single planet)")
        write("  Note: Strengthen benefics and Yogakaraka; be cautious during Maraka dashas.")

    # House Lord Placements
    write("\nHouse Lord Placements:")
    write("-" * 85)
    hl_map = result.get("house_lords", {})
    lagna_idx_p = zodiac_signs.index(result["lagna_sign"])
    for h_num in range(1, 13):
        h_sign = zodiac_signs[(lagna_idx_p + h_num - 1) % 12]
        info = hl_map.get(h_num, {})
        lord = info.get("lord", "?")
        placed = info.get("placed_in")
        lord_full = short_to_full.get(lord, lord)
        placed_sign = zodiac_signs[(lagna_idx_p + placed - 1) % 12] if placed else "?"
        key = (h_num, placed)
        if key in HOUSE_LORD_IN_HOUSE:
            meaning = HOUSE_LORD_IN_HOUSE[key]
        else:
            meaning = (f"Lord of House {h_num} ({h_sign}) placed in House {placed} ({placed_sign}): "
                       f"House {h_num} themes expressed through the environment of House {placed}.")
        write(f"  H{h_num:02d} ({h_sign:11}) lord {lord_full:9} → H{placed:02d} ({placed_sign:11}): "
              f"{meaning.split(':')[-1].strip()}")

    write("\nVimshottari Dasha:")
    write("-" * 85)
    vim = result["vimshottari"]
    write(
        f"Starting MD : {vim['starting_lord']} (balance {vim['balance_at_birth_years']} yrs)"
    )
    if vim["current_md"]:
        pd_info = result.get("vimshottari_pd", {})
        current_pd = pd_info.get("current_pd")
        pd_end_jd = pd_info.get("pd_end_jd")
        if current_pd and pd_end_jd:
            pd_end_yr = int(result["birth_year"] + (pd_end_jd - result["birth_jd"]) / 365.25)
            write(f"Current (MD/AD/PD) : {vim['current_md']} / {vim['current_ad']} / {current_pd} (PD until ~{pd_end_yr})")
        else:
            write(f"Current (MD/AD) : {vim['current_md']} / {vim['current_ad']}")
    write("\nMarriage Timing Insights (Enhanced Parashari):")
    write("-" * 85)
    # Calculate key factors
    lagna_idx = zodiac_signs.index(result["lagna_sign"])
    def lord_of_h(h):
        return sign_lords[zodiac_signs[(lagna_idx + h - 1) % 12]]
    seventh_lord = result["seventh_lord"]
    second_lord = lord_of_h(2)
    
    write(f"  7th Lord (spouse)    : {short_to_full.get(seventh_lord, seventh_lord)}")
    write(f"  2nd Lord (family)    : {short_to_full.get(second_lord, second_lord)}")
    write(f"  Venus (natural karak): {result['planets'].get('Ve', {}).get('sign', '?')}")
    
    # D9 Venus status
    ve_d9 = result.get("navamsa", {}).get("Ve", {})
    if ve_d9:
        ve_d9_dig = get_dignity("Ve", ve_d9.get("sign", ""))
        d9_status = f"{ve_d9.get('sign', '?')}"
        if ve_d9_dig:
            d9_status += f" ({ve_d9_dig})"
        write(f"  D9 Venus             : {d9_status}")
    
    write("\n  Probability factors scored: 7th lord (+3), Venus (+3), 2nd lord (+2),")
    write("  Jupiter (+1), D9 Venus dignity (+1), D9 7th lord (+1), house placement (+1)")
    write("  Score legend: ★★★ (7-10) High | ★★ (4-6) Moderate | ★ (1-3) Lower")
    vm = vim["current_md"]
    va = vim["current_ad"]
    if (
        vm in ["Venus", "Ve"]
        or va in ["Venus", "Ve"]
        or vm == result["seventh_lord"]
        or va == result["seventh_lord"]
    ):
        write("*** CURRENT DASHA IS HIGHLY FAVOURABLE FOR MARRIAGE ***")
    else:
        write(
            "Next favourable periods: Venus or 7th-lord Mahadasha/Antardasha (check full list)"
        )
    write("\nCurrent Gochara (from Moon):")
    write("-" * 85)
    for pl, t in sorted(result["transits"].items()):
        write(
            f"{pl:>3}: {t['sign']:11} (house {t['house_from_moon']:2d}) – {t['effect']}"
        )
    sade = result.get("sade_sati")
    if sade:
        write(f"\n  ⚠ SATURN SPECIAL TRANSIT: {sade}")
    else:
        write("  ✓ No active Sade Sati or Dhaiya (Saturn not in critical position from Moon)")
    write("\n🔥 YOGAS WITH STRENGTH (1-10) & ACCURATE TIMINGS (2026–2046)")
    write("-" * 95)
    for yoga in result.get("yogas", []):
        write(f"• {yoga}")
    write("\n📅 POSSIBLE FRUCTIFICATION PERIODS (Next 20 years)")
    write("-" * 95)
    for event, periods in result.get("timings", {}).items():
        write(f"\n{event}:")
        if periods:
            for p in periods:
                write(p)
        else:
            write(" No major period in next 20 years")
    write("\n⚠️ PROBLEMS/DOSHAS IN KUNDALI")
    write("-" * 95)
    for prob in result.get("problems", []):
        write(f"• {prob['summary']}")
    write("\nDetailed Explanation of Doshas:")
    write("-" * 95)
    for prob in result.get("problems", []):
        if prob["detail"]:
            write(f"{prob['summary'].split(':')[0]}:")
            write(prob["detail"])
            write("")
    write("\n🔧 TARGETED REMEDIES (per detected Dosha)")
    write("-" * 95)
    has_remedy = False
    for prob in result.get("problems", []):
        rems = prob.get("remedies", [])
        if rems:
            has_remedy = True
            write(f"\n{prob['summary'].split(':')[0]}:")
            for r in rems:
                write(f"  • {r}")
    if not has_remedy:
        write("  No specific remedies needed – maintain positive practices.")
    write("\n" + result.get("final_analysis", ""))
    write("\nNote: Highest probability when dasha + transit + gochara align.")
    birth_year = result.get("birth_year", "N/A")
    current_year = datetime.datetime.now().year
    write(
        f"Timings calculated from birth year {birth_year}; current year {current_year}."
    )
    write("Doshas indicate challenges; remedies like mantras/gemstones can mitigate.")
    write("\n" + "═" * 95)
    output = "\n".join(lines) + "\n"
    print(output, end="")
    if file:
        file.write(output)


# ────────────────────────────────────────────────
# Entry Point
# ────────────────────────────────────────────────
def main():
    print("Vedic Kundali Generator – Full Version with D7, D10 & Marriage Timing")
    print("─────────────────────────────────────────────────────────────────────\n")
    while True:
        name = input("Enter Name : ").strip()
        date_str = input("Birth Date (YYYY-MM-DD) : ").strip()
        time_str = input("Birth Time (HH:MM 24h) : ").strip()
        place = input("Birth Place (City, Country) : ").strip()
        try:
            result = calculate_kundali(date_str, time_str, place)
            filename = f"{name}_kundali_report.txt"
            with open(filename, "w", encoding="utf-8") as f:
                print_kundali(result, file=f)
            print(f"\nReport saved as '{filename}'")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Tips: Use place='Mumbai, Maharashtra, India'")
            print(" Make sure Swiss Ephemeris .se1 files are in the same folder")
            print("Please re-enter the details.\n")


if __name__ == "__main__":
    main()
