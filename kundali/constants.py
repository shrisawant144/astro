# Remedies for each 7th Lord (marital harmony)
SEVENTH_LORD_REMEDIES = {
    "Su": "Offer water (Arghya) to rising Sun on Sundays; donate wheat/jaggery.",
    "Mo": "Wear pearl/moonstone; offer milk to Shiva on Mondays; stay near water.",
    "Ma": "Recite Hanuman Chalisa on Tuesdays; donate red items; exercise regularly.",
    "Me": "Chant Vishnu Sahasranama on Wednesdays; donate green items/books.",
    "Ju": "Visit temple on Thursdays; donate yellow cloth/turmeric; respect elders/gurus.",
    "Ve": "Offer white sweets on Fridays; donate perfume/white cloth; appreciate art/beauty.",
    "Sa": "Serve the needy on Saturdays; donate black sesame/oil; patience in relationships.",
}
# Remedies for each Lagna (ascendant)
LAGNA_REMEDIES = {
    "Aries": ("Hanuman/Mars", "Om Ang Angarakaya Namah", "Tuesday"),
    "Taurus": ("Lakshmi/Venus", "Om Shum Shukraya Namah", "Friday"),
    "Gemini": ("Vishnu/Mercury", "Om Bum Buddhaya Namah", "Wednesday"),
    "Cancer": ("Moon/Durga", "Om Som Somaya Namah", "Monday"),
    "Leo": ("Sun/Surya", "Om Suryaya Namah", "Sunday"),
    "Virgo": ("Vishnu/Mercury", "Om Bum Buddhaya Namah", "Wednesday"),
    "Libra": ("Lakshmi/Venus", "Om Shum Shukraya Namah", "Friday"),
    "Scorpio": ("Hanuman/Mars", "Om Ang Angarakaya Namah", "Tuesday"),
    "Sagittarius": ("Brihaspati/Jupiter", "Om Brim Brihaspataye Namah", "Thursday"),
    "Capricorn": ("Shani/Saturn", "Om Sham Shanicharaya Namah", "Saturday"),
    "Aquarius": ("Shani/Saturn", "Om Sham Shanicharaya Namah", "Saturday"),
    "Pisces": ("Brihaspati/Jupiter", "Om Brim Brihaspataye Namah", "Thursday"),
}
# Chart weights for divisional charts
CHART_WEIGHTS = {"D1": 1.0, "D9": 2.0, "D10": 1.0, "D7": 1.0}
# constants.py
"""
Vedic astrology constants: signs, nakshatras, planets, dignities, etc.
"""

import swisseph as swe

# -------------------------------------------------------------------
# Basic astronomical and astrological lists
# -------------------------------------------------------------------
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

# Swiss Ephemeris planet IDs
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

# -------------------------------------------------------------------
# Dignity tables (own, exalt, deb)
# -------------------------------------------------------------------
dignity_SIGNS = {
    "Su": {"exalt": "Aries", "own": ["Leo"], "deb": "Libra"},
    "Mo": {"exalt": "Taurus", "own": ["Cancer"], "deb": "Scorpio"},
    "Ma": {"exalt": "Capricorn", "own": ["Aries", "Scorpio"], "deb": "Cancer"},
    "Me": {"exalt": "Virgo", "own": ["Gemini", "Virgo"], "deb": "Pisces"},
    "Ju": {"exalt": "Cancer", "own": ["Sagittarius", "Pisces"], "deb": "Capricorn"},
    "Ve": {"exalt": "Pisces", "own": ["Taurus", "Libra"], "deb": "Virgo"},
    "Sa": {"exalt": "Libra", "own": ["Capricorn", "Aquarius"], "deb": "Aries"},
}
dignity_table = {
    "Su": {"own": "Leo", "exalt": "Aries", "deb": "Libra"},
    "Mo": {"own": "Cancer", "exalt": "Taurus", "deb": "Scorpio"},
    "Ma": {"own": ["Aries", "Scorpio"], "exalt": "Capricorn", "deb": "Cancer"},
    "Me": {"own": ["Gemini", "Virgo"], "exalt": "Virgo", "deb": "Pisces"},
    "Ju": {"own": ["Sagittarius", "Pisces"], "exalt": "Cancer", "deb": "Capricorn"},
    "Ve": {"own": ["Taurus", "Libra"], "exalt": "Pisces", "deb": "Virgo"},
    "Sa": {"own": ["Capricorn", "Aquarius"], "exalt": "Libra", "deb": "Aries"},
    "Ra": {},
    "Ke": {},
}

# Lord of each sign (short code)
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

# Mapping short codes to full names
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

# -------------------------------------------------------------------
# Combustion orbs (degrees from Sun)
# -------------------------------------------------------------------
COMBUSTION_ORBS = {
    "Mo": (12, 12),  # (direct, retrograde) – Moon never retrograde
    "Ma": (17, 17),
    "Me": (14, 12),
    "Ju": (11, 9),
    "Ve": (10, 8),
    "Sa": (15, 15),
}

# -------------------------------------------------------------------
# Neecha Bhanga (cancelled debilitation) data
# -------------------------------------------------------------------
NEECHA_BHANGA_INFO = {
    "Su": ("Ve", "Sa"),  # (deb sign lord, planet exalted in deb sign)
    "Mo": ("Ma", None),
    "Ma": ("Mo", "Ju"),
    "Me": ("Ju", "Ve"),
    "Ju": ("Sa", "Ma"),
    "Ve": ("Me", "Me"),
    "Sa": ("Ma", "Su"),
}

# -------------------------------------------------------------------
# Gochara (transit) effects from Moon
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# Functional benefic/malefic classification by Lagna
# -------------------------------------------------------------------
FUNCTIONAL_QUALITY = {
    "Aries": {
        "ben": ["Su", "Ju"],
        "mal": ["Me", "Sa"],
        "maraka": ["Ve"],
        "mixed": ["Ma"],
        "yk": None,
    },
    "Taurus": {
        "ben": ["Me", "Sa"],
        "mal": ["Ju"],
        "maraka": ["Ma"],
        "mixed": ["Ve", "Mo"],
        "yk": "Sa",
    },
    "Gemini": {
        "ben": ["Me", "Ve", "Sa"],
        "mal": ["Ma"],
        "maraka": ["Ju"],
        "mixed": ["Su"],
        "yk": None,
    },
    "Cancer": {
        "ben": ["Mo", "Ma", "Ju"],
        "mal": ["Me", "Ve"],
        "maraka": ["Sa"],
        "mixed": [],
        "yk": "Ma",
    },
    "Leo": {
        "ben": ["Su", "Ma"],
        "mal": ["Sa"],
        "maraka": ["Me"],
        "mixed": ["Ju", "Ve"],
        "yk": "Ma",
    },
    "Virgo": {
        "ben": ["Ve", "Me"],
        "mal": ["Ma"],
        "maraka": ["Ju"],
        "mixed": ["Sa", "Mo"],
        "yk": None,
    },
    "Libra": {
        "ben": ["Sa", "Me"],
        "mal": ["Ju", "Su"],
        "maraka": ["Ma"],
        "mixed": ["Ve"],
        "yk": "Sa",
    },
    "Scorpio": {
        "ben": ["Mo", "Su", "Ju"],
        "mal": ["Me"],
        "maraka": ["Ve"],
        "mixed": ["Sa"],
        "yk": "Mo",
    },
    "Sagittarius": {
        "ben": ["Su", "Ju"],
        "mal": ["Ve"],
        "maraka": ["Me", "Sa"],
        "mixed": ["Ma"],
        "yk": None,
    },
    "Capricorn": {
        "ben": ["Ve", "Sa"],
        "mal": ["Ju"],
        "maraka": ["Mo"],
        "mixed": ["Me", "Ma"],
        "yk": "Ve",
    },
    "Aquarius": {
        "ben": ["Ve"],
        "mal": ["Mo"],
        "maraka": ["Ju"],
        "mixed": ["Sa", "Me", "Ma"],
        "yk": "Ve",
    },
    "Pisces": {
        "ben": ["Ju", "Mo", "Ma"],
        "mal": ["Sa", "Ve"],
        "maraka": ["Me"],
        "mixed": [],
        "yk": None,
    },
}

# -------------------------------------------------------------------
# Panchanga names
# -------------------------------------------------------------------
TITHI_NAMES = [
    "Shukla Pratipada",
    "Shukla Dwitiya",
    "Shukla Tritiya",
    "Shukla Chaturthi",
    "Shukla Panchami",
    "Shukla Shashthi",
    "Shukla Saptami",
    "Shukla Ashtami",
    "Shukla Navami",
    "Shukla Dashami",
    "Shukla Ekadashi",
    "Shukla Dwadashi",
    "Shukla Trayodashi",
    "Shukla Chaturdashi",
    "Purnima",
    "Krishna Pratipada",
    "Krishna Dwitiya",
    "Krishna Tritiya",
    "Krishna Chaturthi",
    "Krishna Panchami",
    "Krishna Shashthi",
    "Krishna Saptami",
    "Krishna Ashtami",
    "Krishna Navami",
    "Krishna Dashami",
    "Krishna Ekadashi",
    "Krishna Dwadashi",
    "Krishna Trayodashi",
    "Krishna Chaturdashi",
    "Amavasya",
]

YOGA_NAMES = [
    "Vishkamba",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyana",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Mahendra",
    "Vaidhriti",
]

KARANA_REPEATING = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
VARA_NAMES = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]

# -------------------------------------------------------------------
# House significations (general)
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# House lord placement meanings (lord of house A placed in house B)
# -------------------------------------------------------------------
HOUSE_LORD_IN_HOUSE = {
    # ── Lord of H1 (Self / Lagna) ──
    (
        1,
        1,
    ): "Strong, self-reliant personality; health and vitality prominent; life is self-driven.",
    (
        1,
        2,
    ): "Wealth and family shape identity; skilled in speech; face is a fortunate asset.",
    (
        1,
        3,
    ): "Courageous and communicative; siblings and short travel define life greatly.",
    (1, 4): "Deeply rooted in home and mother; domestic comfort is a life priority.",
    (
        1,
        5,
    ): "Creative, intelligent, child-oriented life; fame possible through wisdom or arts.",
    (
        1,
        6,
    ): "Life centred on service, health, or competition; enemies demand vigilance.",
    (
        1,
        7,
    ): "Partnerships are central to identity; marriage-oriented; may settle abroad.",
    (
        1,
        8,
    ): "Transformative, occult-drawn life; longevity issues possible; deep hidden strengths.",
    (1, 9): "Highly fortunate; life guided by dharma, luck, and father's blessings.",
    (
        1,
        10,
    ): "Career and authority are powerfully expressed; public recognition is strong.",
    (
        1,
        11,
    ): "Gains and social networks prosper naturally; desires fulfilled with effort.",
    (
        1,
        12,
    ): "Spiritual, isolated, or foreign-oriented life; expenditure-prone; hidden tendencies.",
    # ── Lord of H2 (Wealth / Family / Speech) ──
    (
        2,
        1,
    ): "Wealth comes through personality and initiative; strong family presence in self.",
    (2, 2): "Very strong wealth house; speech, food, and family are major life assets.",
    (
        2,
        3,
    ): "Wealth through communication, writing, or trade; siblings involved in finances.",
    (
        2,
        4,
    ): "Family wealth through property and mother; financial security via real estate.",
    (2, 5): "Wealth through children, creativity, or speculation; rich family legacy.",
    (
        2,
        6,
    ): "Debt and health expenses affect wealth; income possible from service or medicine.",
    (
        2,
        7,
    ): "Wealth through partnerships and marriage; business-minded spouse; joint finances.",
    (
        2,
        8,
    ): "Transformative events affect finances; possible inheritance or sudden gains/losses.",
    (2, 9): "Wealth through luck, dharma, father's legacy, or religious activities.",
    (
        2,
        10,
    ): "Wealth through career and public status; financial recognition and high income.",
    (
        2,
        11,
    ): "Excellent for wealth — 2nd lord in 11H: strong income, gains, and accumulation.",
    (
        2,
        12,
    ): "Expenses drain wealth; foreign expenditure or spiritual spending dominates.",
    # ── Lord of H3 (Courage / Communication / Siblings) ──
    (
        3,
        1,
    ): "Brave, communicative personality; siblings influential; self-expression is bold.",
    (3, 2): "Communication skills bring wealth; writing, speaking, or media = income.",
    (
        3,
        3,
    ): "Very strong courage and communication; siblings prosper; own writing/media.",
    (
        3,
        4,
    ): "Communication rooted in home and education; home-based literary or creative work.",
    (
        3,
        5,
    ): "Courage and creativity merge; arts, writing, and romance flourish; creative children.",
    (
        3,
        6,
    ): "Courage used against enemies in competition; physical activity guards health.",
    (
        3,
        7,
    ): "Spouse is communicative or a sibling-like figure; business partnerships through media.",
    (
        3,
        8,
    ): "Communication about secrets or occult; hidden writings; siblings face challenges.",
    (
        3,
        9,
    ): "Philosophical and dharmic communication; sibling is spiritual; travel for religion.",
    (
        3,
        10,
    ): "Career in communication, media, writing, IT, or travel; prominent public speaker.",
    (
        3,
        11,
    ): "Gains through communication, media, or siblings; income from writing or trade.",
    (
        3,
        12,
    ): "Communications lead to foreign connections or isolation; siblings may live abroad.",
    # ── Lord of H4 (Home / Mother / Property / Happiness) ──
    (
        4,
        1,
    ): "Domestic comfort and mother shape personality; deep attachment to homeland.",
    (
        4,
        2,
    ): "Family property is a primary source of wealth; home is investment vehicle.",
    (
        4,
        3,
    ): "Communication about property; home-based business; travels for domestic reasons.",
    (
        4,
        4,
    ): "Very strong home, mother, and property themes; deeply domestic and content.",
    (
        4,
        5,
    ): "Creative, educated home; children bring happiness; home is a place of learning.",
    (
        4,
        6,
    ): "Domestic conflicts; mother's health may suffer; property disputes possible.",
    (
        4,
        7,
    ): "Happy domestic married life; spouse settles at home; property gained through marriage.",
    (
        4,
        8,
    ): "Inheritance of property; home linked to transformations; ancestral real estate.",
    (
        4,
        9,
    ): "Highly fortunate home; spiritual, educated household; father's property benefits.",
    (
        4,
        10,
    ): "Career in real estate, construction, or governance; mother's name attached to career.",
    (
        4,
        11,
    ): "Gains through property; home brings income; mother connected to social success.",
    (
        4,
        12,
    ): "Foreign residence; home is abroad or spiritual retreat; hidden domestic challenges.",
    # ── Lord of H5 (Children / Creativity / Intelligence / Speculation) ──
    (
        5,
        1,
    ): "Intelligent, creative personality; children are important; natural teacher or adviser.",
    (
        5,
        2,
    ): "Children and creativity bring wealth; income through speculation, arts, or education.",
    (
        5,
        3,
    ): "Creativity in communication; children are communicative; artistic or literary nature.",
    (
        5,
        4,
    ): "Creative, educated home environment; children live at home; happiness through intellect.",
    (
        5,
        5,
    ): "Very strong creativity and intelligence; own sign lord — excellent for children and arts.",
    (
        5,
        6,
    ): "Challenges with children or creative projects; speculative losses possible; serve creatively.",
    (
        5,
        7,
    ): "Marriage brings children and creativity; romantic partnership; creative spouse.",
    (
        5,
        8,
    ): "Secret or past-life creative debts; occult intellect; children may face early hardships.",
    (
        5,
        9,
    ): "Most auspicious — trikona lord in trikona; excellent luck, children, and wisdom.",
    (
        5,
        10,
    ): "Career in education, arts, performance, or child-related fields; fame through creativity.",
    (
        5,
        11,
    ): "Gains through creativity, children, or speculation; income from arts or education.",
    (
        5,
        12,
    ): "Hidden creativity; spiritual philosophy; children may live abroad; isolated artistry.",
    # ── Lord of H6 (Enemies / Debt / Disease / Service) ──
    (
        6,
        1,
    ): "Competitive, service-oriented personality; health demands attention; argumentative.",
    (
        6,
        2,
    ): "Debts affect wealth; family enemies possible; income from medical or service field.",
    (
        6,
        3,
    ): "Courage against enemies; siblings may create conflict; competitive communication.",
    (
        6,
        4,
    ): "Domestic enmity or disputes; mother's health could suffer; unhappy home possible.",
    (
        6,
        5,
    ): "Enemies of creative work; health issues in romance; service-oriented creativity.",
    (
        6,
        6,
    ): "Very strong in competition — enemies defeated repeatedly; also amplified conflicts.",
    (
        6,
        7,
    ): "Conflicts in marriage; spouse may be adversarial; legal disputes in partnership.",
    (
        6,
        8,
    ): "Enemies trigger transformation; hidden health crises; intense karmic struggle.",
    (6, 9): "Dharma tested through service and health; father's health may suffer.",
    (
        6,
        10,
    ): "Career in litigation, military, medicine, or competitive fields; enemies at workplace.",
    (
        6,
        11,
    ): "Gains by defeating enemies; income from service, medicine, or competitive work.",
    (
        6,
        12,
    ): "Enemies abroad; hospitalization or secret enmity; health complications in isolation.",
    # ── Lord of H7 (Marriage / Partnership / Business) ──
    (
        7,
        1,
    ): "Spouse reflects the native's own identity; self-oriented in marriage; strong partnerships.",
    (
        7,
        2,
    ): "Spouse brings wealth and family harmony; marriage is financially rewarding.",
    (
        7,
        3,
    ): "Spouse is communicative or from nearby area; business through communication field.",
    (
        7,
        4,
    ): "Spouse settles in native's home; happy domestic married life; property through marriage.",
    (
        7,
        5,
    ): "Marriage brings children and creativity; deeply romantic union; creative, wise spouse.",
    (
        7,
        6,
    ): "Marital conflicts or health issues in marriage; spouse may be competitive or adversarial.",
    (
        7,
        7,
    ): "Very powerful marriage and business partnerships; spouse very prominent in life.",
    (
        7,
        8,
    ): "Transformative marriage; spouse has occult interests; longevity in marriage is complex.",
    (
        7,
        9,
    ): "Very fortunate marriage — 7th lord in 9H is highly auspicious; wise, dharmic spouse.",
    (
        7,
        10,
    ): "Spouse connected to career; marriage enhances public status; business with spouse.",
    (
        7,
        11,
    ): "Gains through marriage; financially beneficial partnership; spouse fulfils aspirations.",
    (
        7,
        12,
    ): "Foreign spouse; expenses through marriage; spiritual or isolated union; spouse abroad.",
    # ── Lord of H8 (Longevity / Transformation / Occult / Inheritance) ──
    (
        8,
        1,
    ): "Health and longevity tied to personality; transformative life; occult fascination.",
    (
        8,
        2,
    ): "Inheritance through family; family wealth through transformation or hidden means.",
    (
        8,
        3,
    ): "Siblings involved in occult or transformations; communication about secrets.",
    (
        8,
        4,
    ): "Property from inheritance; home linked to ancestral transformation; mother's health.",
    (
        8,
        5,
    ): "Occult creativity; children with karmic past-life debt; risky speculative ventures.",
    (
        8,
        6,
    ): "Enemies cause sudden health crises; hidden illness; 6+8 lords combining = serious risk.",
    (
        8,
        7,
    ): "Spouse is secretive or occult-oriented; transformative marriage; longevity of spouse.",
    (
        8,
        8,
    ): "Extremely strong occult and research interest; deep longevity study; phoenix-like life.",
    (
        8,
        9,
    ): "Transformation through dharma; inherited religious philosophy; father's longevity.",
    (
        8,
        10,
    ): "Career in research, surgery, occult, inheritance law, or investigative finance.",
    (
        8,
        11,
    ): "Sudden gains or inheritance through elder siblings; occult brings income.",
    (
        8,
        12,
    ): "Spiritual transformation; moksha path; foreign occult experiences; losses via change.",
    # ── Lord of H9 (Luck / Dharma / Father / Guru) ──
    (
        9,
        1,
    ): "Very fortunate personality; dharmic, philosophical; father is highly influential.",
    (
        9,
        2,
    ): "Wealth through dharma and father; family prosperity through luck and virtue.",
    (
        9,
        3,
    ): "Philosophical writing and communication; siblings are spiritual; fortunate journeys.",
    (
        9,
        4,
    ): "Spiritual home; fortunate, pious mother; property through luck; educated household.",
    (
        9,
        5,
    ): "Most auspicious — 9th lord in 5H (trikona-trikona): abundant luck, wise children.",
    (
        9,
        6,
    ): "Dharma tested through service and health; fortune through service to others.",
    (
        9,
        7,
    ): "Fortunate, spiritually wise spouse; dharmic marriage; luck through partnerships.",
    (
        9,
        8,
    ): "Dharma through transformation; inherited religious wisdom; occult philosophy.",
    (
        9,
        9,
    ): "Extremely strong dharma, luck, and fortune; deeply religious and philosophical life.",
    (
        9,
        10,
    ): "Career in law, religion, philosophy, or education; fame through dharmic work.",
    (
        9,
        11,
    ): "Outstanding — gains come through luck and dharma; elder siblings are fortunate.",
    (
        9,
        12,
    ): "Dharma through foreign lands or spiritual isolation; pilgrimages abroad; moksha path.",
    # ── Lord of H10 (Career / Authority / Fame / Status) ──
    (
        10,
        1,
    ): "Career defines identity; authority and public image are central to personality.",
    (
        10,
        2,
    ): "Career brings wealth and family status; income from authority or public position.",
    (
        10,
        3,
    ): "Career in communication, media, writing, or travel; courage in professional life.",
    (
        10,
        4,
    ): "Career linked to home, real estate, or mother; working from home; domestic vocation.",
    (
        10,
        5,
    ): "Career in creativity, arts, education, or child-related fields; fame through intellect.",
    (
        10,
        6,
    ): "Service-oriented career; medical, military, competitive, or legal profession.",
    (
        10,
        7,
    ): "Career through partnerships or business with spouse; public career enhanced by partner.",
    (
        10,
        8,
    ): "Transformative career; research, occult, medicine, or investigative profession.",
    (
        10,
        9,
    ): "Highly auspicious — career aligned with dharma; fame through wisdom and virtue.",
    (
        10,
        10,
    ): "Extremely strong career; high authority; government or top leadership; great fame.",
    (
        10,
        11,
    ): "Gains through career; professional aspirations fulfilled; income from authority.",
    (
        10,
        12,
    ): "Career abroad or in isolation; foreign employment; spiritual or behind-the-scenes work.",
    # ── Lord of H11 (Gains / Income / Friends / Aspirations) ──
    (
        11,
        1,
    ): "Desires and gains are self-driven; socially ambitious personality; friends shape self.",
    (11, 2): "Gains through family and speech; income aligned with family wealth.",
    (11, 3): "Gains through communication, media, siblings, or short journeys.",
    (
        11,
        4,
    ): "Gains through property and home; domestic income; mother linked to social success.",
    (
        11,
        5,
    ): "Gains through children, creativity, or speculation; income from arts or education.",
    (
        11,
        6,
    ): "Gains through service, competition, or health industry; income by defeating obstacles.",
    (11, 7): "Gains through marriage and partnerships; financially beneficial spouse.",
    (
        11,
        8,
    ): "Sudden gains or inheritance; occult brings income; elder siblings face transformation.",
    (
        11,
        9,
    ): "Gains through father, dharma, or luck; fortune grows through spiritual activities.",
    (
        11,
        10,
    ): "Gains through career and authority; professional fame converts to income.",
    (
        11,
        11,
    ): "Very strong gains house; powerful income, large social network, fulfilled desires.",
    (11, 12): "Gains lead to expenses; income from foreign sources or isolated work.",
    # ── Lord of H12 (Losses / Isolation / Foreign / Moksha) ──
    (
        12,
        1,
    ): "Spiritual or foreign-natured personality; expenditure tied to self; hidden tendencies.",
    (
        12,
        2,
    ): "Family wealth spent on foreign or spiritual matters; speech about hidden or divine things.",
    (
        12,
        3,
    ): "Communication about foreign or spiritual matters; siblings abroad; long journeys.",
    (
        12,
        4,
    ): "Home is abroad or spiritual retreat; mother may live far; property in foreign land.",
    (
        12,
        5,
    ): "Creativity in isolation; children may live abroad; spiritual romance; hidden pleasures.",
    (
        12,
        6,
    ): "Enemies abroad or in isolation; hospitalisation; secret enmity is the main challenge.",
    (
        12,
        7,
    ): "Foreign spouse; marriage involves foreign living; spiritual partnership; partner abroad.",
    (
        12,
        8,
    ): "Deep transformation through foreign or isolated experiences; occult linked to abroad.",
    (
        12,
        9,
    ): "Dharma in foreign lands; pilgrimages abroad; foreign guru; spiritual fortune.",
    (
        12,
        10,
    ): "Career in foreign country; work in isolated or spiritual fields; behind-the-scenes role.",
    (
        12,
        11,
    ): "Gains from foreign sources; income from isolated work; friends or network abroad.",
    (
        12,
        12,
    ): "Extremely strong 12H themes; deeply spiritual, moksha-oriented, costly but enlightened.",
}

# -------------------------------------------------------------------
# Natural benefic/malefic classification (for default scoring)
# -------------------------------------------------------------------
NATURAL_BENEFICS = {"Ju", "Ve", "Mo"}
NATURAL_MALEFICS = {"Sa", "Ma", "Su", "Ra", "Ke"}

# -------------------------------------------------------------------
# Ashtakavarga reference tables (benefic houses for each planet)
# -------------------------------------------------------------------
ASHTAKAVARGA_REKHAS = {
    "Su": {  # Sun's Ashtakavarga
        "Su": [0, 1, 2, 3, 4, 6, 9, 10, 11],
        "Mo": [2, 5, 6, 8, 10, 11],
        "Ma": [0, 2, 3, 4, 6, 9, 10],
        "Me": [2, 4, 5, 6, 8, 10, 11],
        "Ju": [4, 5, 6, 8],
        "Ve": [5, 6, 8, 10, 11],
        "Sa": [0, 1, 3, 4, 6, 9, 10],
        "As": [2, 3, 4, 6, 9, 10, 11],
    },
    "Mo": {
        "Su": [2, 5, 6, 8, 10, 11],
        "Mo": [0, 2, 5, 6, 8, 9, 10],
        "Ma": [1, 2, 3, 6, 9, 10],
        "Me": [0, 2, 3, 4, 5, 6, 8, 10],
        "Ju": [0, 3, 5, 6, 8, 10],
        "Ve": [2, 3, 5, 6, 8, 9, 10],
        "Sa": [2, 5, 6, 10, 11],
        "As": [2, 5, 6, 8, 10, 11],
    },
    "Ma": {
        "Su": [2, 4, 5, 6, 9, 10],
        "Mo": [2, 5, 6, 8, 10, 11],
        "Ma": [0, 1, 3, 5, 9, 10],
        "Me": [2, 4, 6, 9, 10, 11],
        "Ju": [5, 6, 9, 10],
        "Ve": [5, 7, 8, 10, 11],
        "Sa": [2, 4, 5, 6, 8, 10, 11],
        "As": [0, 2, 3, 5, 9, 10],
    },
    "Me": {
        "Su": [4, 5, 6, 8, 10, 11],
        "Mo": [1, 2, 3, 4, 5, 7, 8],
        "Ma": [0, 1, 2, 3, 4, 6, 7, 9, 10],
        "Me": [0, 1, 2, 3, 4, 5, 6, 7, 9, 10],
        "Ju": [5, 6, 8, 11],
        "Ve": [0, 1, 2, 3, 4, 5, 7, 8],
        "Sa": [0, 1, 3, 4, 5, 6, 7, 9, 10],
        "As": [0, 1, 3, 4, 5, 6, 7, 9, 10],
    },
    "Ju": {
        "Su": [0, 1, 3, 4, 5, 6, 8, 10],
        "Mo": [1, 2, 3, 5, 6, 8, 10],
        "Ma": [0, 1, 3, 5, 8, 10],
        "Me": [0, 1, 2, 4, 5, 6, 8, 10],
        "Ju": [0, 1, 2, 4, 6, 7, 8, 10],
        "Ve": [1, 2, 4, 5, 6, 8, 10, 11],
        "Sa": [2, 4, 5, 6, 9, 10, 11],
        "As": [0, 1, 3, 4, 5, 6, 8, 10],
    },
    "Ve": {
        "Su": [7, 8, 10, 11],
        "Mo": [0, 1, 2, 3, 4, 5, 7, 8, 11],
        "Ma": [2, 3, 4, 5, 7, 8, 10, 11],
        "Me": [2, 4, 5, 7, 8, 10, 11],
        "Ju": [4, 5, 7, 8, 10],
        "Ve": [0, 1, 2, 3, 4, 5, 7, 8],
        "Sa": [2, 3, 4, 5, 7, 8, 10, 11],
        "As": [0, 1, 2, 3, 4, 5, 7, 8, 10, 11],
    },
    "Sa": {
        "Su": [0, 1, 3, 4, 5, 6, 10, 11],
        "Mo": [2, 5, 6, 11],
        "Ma": [2, 4, 6, 9, 10, 11],
        "Me": [5, 6, 10, 11],
        "Ju": [5, 6, 11],
        "Ve": [5, 6, 11],
        "Sa": [2, 5, 6, 10, 11],
        "As": [0, 2, 3, 6, 10, 11],
    },
}

# -------------------------------------------------------------------
# Aspect interpretation themes (for print)
# -------------------------------------------------------------------
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
