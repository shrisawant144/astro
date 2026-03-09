# Vedic Astrology Constants
# All data constants used in Kundali calculations

# Zodiac Signs
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

# Nakshatras
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

# Dasha Lords
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

# Dasha Periods (years)
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

# Nakshatra Lord Index
nakshatra_lord_index = [0, 1, 2, 3, 4, 5, 6, 7, 8] * 3

# Planet Codes to Swiss Ephemeris IDs
import swisseph as swe
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

# Dignity Table
dignity_table = {
    "Su": {"own": "Leo", "exalt": "Aries", "deb": "Libra"},
    "Mo": {"own": "Cancer", "exalt": "Taurus", "deb": "Scorpio"},
    "Ma": {"own": ["Aries", "Scorpio"], "exalt": "Capricorn", "deb": "Cancer"},
    "Me": {"own": ["Gemini", "Virgo"], "exalt": "Virgo", "deb": "Pisces"},
    "Ju": {"own": ["Sagittarius", "Pisces"], "exalt": "Cancer", "deb": "Capricorn"},
    "Ve": {"own": ["Taurus", "Libra"], "exalt": "Pisces", "deb": "Virgo"},
    "Sa": {"own": ["Capricorn", "Aquarius"], "exalt": "Libra", "deb": "Aries"},
    # Rahu/Ketu: No classical consensus on exaltation/debilitation exists.
    "Ra": {},
    "Ke": {},
}

# Gochara Effects (Transits)
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

# Sign Lords
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

# Short to Full Planet Names
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

# Combustion Orbs (degrees from Sun for combustion)
# Source: Brihat Parashara Hora Shastra
COMBUSTION_ORBS = {
    "Mo": (12, 12),
    "Ma": (17, 17),
    "Me": (14, 12),
    "Ju": (11, 9),
    "Ve": (10, 8),
    "Sa": (15, 15),
}

# Neecha Bhanga (Cancelled Debilitation) Data
NEECHA_BHANGA_INFO = {
    "Su": ("Ve", "Sa"),
    "Mo": ("Ma", None),
    "Ma": ("Mo", "Ju"),
    "Me": ("Ju", "Ve"),
    "Ju": ("Sa", "Ma"),
    "Ve": ("Me", "Me"),
    "Sa": ("Ma", "Su"),
}

# Functional Benefics / Malefics by Lagna
FUNCTIONAL_QUALITY = {
    "Aries":       {"ben": ["Su", "Ju"], "mal": ["Me", "Sa"], "maraka": ["Ve"], "mixed": ["Ma"], "yk": None},
    "Taurus":      {"ben": ["Me", "Sa"], "mal": ["Ju"], "maraka": ["Ma"], "mixed": ["Ve", "Mo"], "yk": "Sa"},
    "Gemini":      {"ben": ["Me", "Ve", "Sa"], "mal": ["Ma"], "maraka": ["Ju"], "mixed": ["Su"], "yk": None},
    "Cancer":      {"ben": ["Mo", "Ma", "Ju"], "mal": ["Me", "Ve"], "maraka": ["Sa"], "mixed": [], "yk": "Ma"},
    "Leo":         {"ben": ["Su", "Ma"], "mal": ["Sa"], "maraka": ["Me"], "mixed": ["Ju", "Ve"], "yk": "Ma"},
    "Virgo":       {"ben": ["Ve", "Me"], "mal": ["Ma"], "maraka": ["Ju"], "mixed": ["Sa", "Mo"], "yk": None},
    "Libra":       {"ben": ["Sa", "Me"], "mal": ["Ju", "Su"], "maraka": ["Ma"], "mixed": ["Ve"], "yk": "Sa"},
    "Scorpio":     {"ben": ["Mo", "Su", "Ju"], "mal": ["Me"], "maraka": ["Ve"], "mixed": ["Sa"], "yk": "Mo"},
    "Sagittarius": {"ben": ["Su", "Ju"], "mal": ["Ve"], "maraka": ["Me", "Sa"], "mixed": ["Ma"], "yk": None},
    "Capricorn":   {"ben": ["Ve", "Sa"], "mal": ["Ju"], "maraka": ["Mo"], "mixed": ["Me", "Ma"], "yk": "Ve"},
    "Aquarius":    {"ben": ["Ve"], "mal": ["Mo"], "maraka": ["Ju"], "mixed": ["Sa", "Me", "Ma"], "yk": "Ve"},
    "Pisces":      {"ben": ["Ju", "Mo", "Ma"], "mal": ["Sa", "Ve"], "maraka": ["Me"], "mixed": [], "yk": None},
}

# Panchanga Names
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

# House Significations
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

# Natural Benefics and Malefics
NATURAL_BENEFICS = {"Ju", "Ve", "Mo"}
NATURAL_MALEFICS = {"Sa", "Ma", "Su", "Ra", "Ke"}

# Ashtakavarga Benefic Dots
ASHTAKAVARGA_REKHAS = {
    "Su": {
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

# Lagna-specific Remedies
LAGNA_REMEDIES = {
    "Aries":       ("Hanuman/Mars", "Om Ang Angarakaya Namah", "Tuesday"),
    "Taurus":      ("Lakshmi/Venus", "Om Shum Shukraya Namah", "Friday"),
    "Gemini":      ("Vishnu/Mercury", "Om Bum Buddhaya Namah", "Wednesday"),
    "Cancer":      ("Moon/Durga", "Om Som Somaya Namah", "Monday"),
    "Leo":         ("Sun/Surya", "Om Suryaya Namah", "Sunday"),
    "Virgo":       ("Vishnu/Mercury", "Om Bum Buddhaya Namah", "Wednesday"),
    "Libra":       ("Lakshmi/Venus", "Om Shum Shukraya Namah", "Friday"),
    "Scorpio":     ("Hanuman/Mars", "Om Ang Angarakaya Namah", "Tuesday"),
    "Sagittarius": ("Brihaspati/Jupiter", "Om Brim Brihaspataye Namah", "Thursday"),
    "Capricorn":   ("Shani/Saturn", "Om Sham Shanicharaya Namah", "Saturday"),
    "Aquarius":    ("Shani/Saturn", "Om Sham Shanicharaya Namah", "Saturday"),
    "Pisces":      ("Brihaspati/Jupiter", "Om Brim Brihaspataye Namah", "Thursday"),
}

# 7th Lord Remedies
SEVENTH_LORD_REMEDIES = {
    "Su": "Offer water (Arghya) to rising Sun on Sundays; donate wheat/jaggery.",
    "Mo": "Wear pearl/moonstone; offer milk to Shiva on Mondays; stay near water.",
    "Ma": "Recite Hanuman Chalisa on Tuesdays; donate red items; exercise regularly.",
    "Me": "Chant Vishnu Sahasranama on Wednesdays; donate green items/books.",
    "Ju": "Visit temple on Thursdays; donate yellow cloth/turmeric; respect elders/gurus.",
    "Ve": "Offer white sweets on Fridays; donate perfume/white cloth; appreciate art/beauty.",
    "Sa": "Serve the needy on Saturdays; donate black sesame/oil; patience in relationships.",
}

# Exaltation Signs
EXALT_SIGNS = {
    "Su": "Aries", "Mo": "Taurus", "Ma": "Capricorn", "Me": "Virgo",
    "Ju": "Cancer", "Ve": "Pisces", "Sa": "Libra",
}

# Natural Friends and Enemies
NATURAL_FRIENDS = {
    "Su": {"Mo", "Ma", "Ju"},
    "Mo": {"Su", "Me"},
    "Ma": {"Su", "Mo", "Ju"},
    "Me": {"Su", "Ve"},
    "Ju": {"Su", "Mo", "Ma"},
    "Ve": {"Me", "Sa"},
    "Sa": {"Me", "Ve"},
}

NATURAL_ENEMIES = {
    "Su": {"Ve", "Sa"},
    "Mo": set(),
    "Ma": {"Me"},
    "Me": {"Mo"},
    "Ju": {"Me", "Ve"},
    "Ve": {"Su", "Mo"},
    "Sa": {"Su", "Mo", "Ma"},
}

