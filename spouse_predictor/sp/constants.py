# constants.py

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    "Aries": "Ma", "Taurus": "Ve", "Gemini": "Me", "Cancer": "Mo",
    "Leo": "Su", "Virgo": "Me", "Libra": "Ve", "Scorpio": "Ma",
    "Sagittarius": "Ju", "Capricorn": "Sa", "Aquarius": "Sa", "Pisces": "Ju"
}

SHORT_TO_FULL = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu"
}

FULL_TO_SHORT = {v: k for k, v in SHORT_TO_FULL.items()}

DIGNITY_TABLE = {
    "Su": {"exalt": "Aries", "own": ["Leo"], "deb": "Libra", "friends": ["Mo", "Ma", "Ju"], "enemies": ["Ve", "Sa"]},
    "Mo": {"exalt": "Taurus", "own": ["Cancer"], "deb": "Scorpio", "friends": ["Su", "Me"], "enemies": []},
    "Ma": {"exalt": "Capricorn", "own": ["Aries", "Scorpio"], "deb": "Cancer", "friends": ["Su", "Mo", "Ju"], "enemies": ["Me"]},
    "Me": {"exalt": "Virgo", "own": ["Gemini", "Virgo"], "deb": "Pisces", "friends": ["Su", "Ve"], "enemies": ["Mo"]},
    "Ju": {"exalt": "Cancer", "own": ["Sagittarius", "Pisces"], "deb": "Capricorn", "friends": ["Su", "Mo", "Ma"], "enemies": ["Me", "Ve"]},
    "Ve": {"exalt": "Pisces", "own": ["Taurus", "Libra"], "deb": "Virgo", "friends": ["Me", "Sa"], "enemies": ["Su", "Mo"]},
    "Sa": {"exalt": "Libra", "own": ["Capricorn", "Aquarius"], "deb": "Aries", "friends": ["Me", "Ve"], "enemies": ["Su", "Mo", "Ma"]},
    "Ra": {"exalt": None, "own": [], "deb": None, "friends": [], "enemies": []},
    "Ke": {"exalt": None, "own": [], "deb": None, "friends": [], "enemies": []}
}

SIGN_APPEARANCE = {
    "Aries": {"build": "Athletic, medium height", "face": "Sharp features, prominent forehead", "complexion": "Fair to reddish", "personality": "Independent, pioneering, energetic"},
    "Taurus": {"build": "Sturdy, well-built", "face": "Beautiful, full lips, attractive eyes", "complexion": "Fair", "personality": "Sensual, stable, loves luxury"},
    "Gemini": {"build": "Tall, slender, youthful", "face": "Expressive, intelligent eyes", "complexion": "Fair", "personality": "Communicative, versatile, intellectual"},
    "Cancer": {"build": "Medium, round face, soft", "face": "Round, nurturing, prominent eyes", "complexion": "Fair to pale", "personality": "Nurturing, emotional, protective"},
    "Leo": {"build": "Tall, commanding, broad shoulders", "face": "Lion-like, impressive, mane-like hair", "complexion": "Fair to golden", "personality": "Dignified, generous, proud"},
    "Virgo": {"build": "Medium, neat, well-proportioned", "face": "Refined, intelligent expression", "complexion": "Fair", "personality": "Analytical, practical, health-conscious"},
    "Libra": {"build": "Well-proportioned, attractive, graceful", "face": "Very attractive, symmetrical", "complexion": "Fair", "personality": "Charming, balanced, harmonious"},
    "Scorpio": {"build": "Medium to tall, intense presence", "face": "Penetrating eyes, sharp features", "complexion": "Medium to dark", "personality": "Intense, secretive, passionate"},
    "Sagittarius": {"build": "Tall, athletic, good posture", "face": "Cheerful, open expression", "complexion": "Fair to medium", "personality": "Philosophical, adventurous, optimistic"},
    "Capricorn": {"build": "Tall, thin, bony, serious", "face": "Mature, serious, prominent bones", "complexion": "Dark or tanned", "personality": "Ambitious, disciplined, traditional"},
    "Aquarius": {"build": "Tall, unusual features", "face": "Distinctive, friendly, quirky", "complexion": "Fair", "personality": "Unconventional, humanitarian, detached"},
    "Pisces": {"build": "Medium, soft, dreamy", "face": "Soft features, dreamy eyes", "complexion": "Fair to pale", "personality": "Spiritual, compassionate, artistic"}
}

PLANET_SPOUSE_TRAITS = {
    "Su": {"personality": "Authoritative, dignified, proud, leadership qualities", "profession": "Government, administration, politics, medicine", "appearance": "Dignified bearing, commanding presence"},
    "Mo": {"personality": "Nurturing, emotional, caring, family-oriented", "profession": "Nursing, hospitality, food industry, psychology", "appearance": "Attractive, fair, round features, expressive eyes"},
    "Ma": {"personality": "Energetic, passionate, athletic, courageous", "profession": "Military, sports, engineering, surgery, police", "appearance": "Athletic, reddish complexion, sharp features"},
    "Me": {"personality": "Intelligent, communicative, youthful, business-minded", "profession": "Business, accounting, writing, teaching, IT", "appearance": "Youthful, slender, expressive face"},
    "Ju": {"personality": "Wise, philosophical, generous, ethical", "profession": "Teaching, law, finance, religion, consulting", "appearance": "Well-built, pleasant, dignified"},
    "Ve": {"personality": "Attractive, artistic, romantic, refined", "profession": "Arts, entertainment, fashion, beauty, luxury", "appearance": "Very attractive, beautiful, charming"},
    "Sa": {"personality": "Mature, disciplined, hardworking, serious", "profession": "Agriculture, mining, labor, law, construction", "appearance": "Thin, tall, mature-looking, dark complexion"},
    "Ra": {"personality": "Unconventional, foreign influence, ambitious", "profession": "Foreign companies, research, technology", "appearance": "Unusual or exotic features, magnetic"},
    "Ke": {"personality": "Spiritual, detached, intuitive", "profession": "Spiritual fields, research, occult, healing", "appearance": "Simple, spiritual aura, thin"}
}

MEETING_CIRCUMSTANCES = {
    1: "Through self-effort, personal approach, events focused on you",
    2: "Through family introduction, family business, financial settings",
    3: "Through siblings, neighbors, social media, short trips",
    4: "At home, through mother, real estate, domestic settings",
    5: "Through romance, entertainment, education, creative pursuits",
    6: "At workplace (service), health settings, daily routine",
    7: "Through business partnership, public dealings, social gatherings",
    8: "Through sudden events, research, inheritance matters",
    9: "Through travel, higher education, religious settings, foreign lands",
    10: "At workplace (career), professional settings, through authority",
    11: "Through friends, social networks, elder siblings, groups",
    12: "In foreign lands, spiritual retreats, hospitals, secluded places"
}

PROFESSION_BY_HOUSE = {
    1: "Independent business, self-employment, personal brand",
    2: "Finance, banking, food industry, family business",
    3: "Media, communication, writing, marketing, sales",
    4: "Real estate, agriculture, vehicles, interior design",
    5: "Education, entertainment, speculation, creativity",
    6: "Healthcare, service industry, law, dispute resolution",
    7: "Partnership business, consulting, public relations",
    8: "Research, insurance, occult, inheritance management",
    9: "Teaching, law, religion, publishing, international trade",
    10: "Corporate career, government, management, leadership",
    11: "Technology, networking, large organizations, social causes",
    12: "Foreign jobs, healthcare, spirituality, hospitality"
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]

NAKSHATRA_DEITIES = {
    "Ashwini": "Ashwini Kumaras (divine physicians)", "Bharani": "Yama (god of death)", "Krittika": "Agni (fire god)",
    "Rohini": "Brahma (creator) or Prajapati", "Mrigashira": "Soma (moon god)", "Ardra": "Rudra (storm god)",
    "Punarvasu": "Aditi (mother of gods)", "Pushya": "Brihaspati (guru of gods)", "Ashlesha": "Nagas (serpents)",
    "Magha": "Pitris (ancestors)", "Purva Phalguni": "Bhaga (god of enjoyment)", "Uttara Phalguni": "Aryaman (god of contracts)",
    "Hasta": "Savitr (sun god)", "Chitra": "Vishvakarma (divine architect)", "Swati": "Vayu (wind god)",
    "Vishakha": "Indra-Agni (dual deities)", "Anuradha": "Mitra (god of friendship)", "Jyeshtha": "Indra (king of gods)",
    "Mula": "Nirriti (goddess of dissolution)", "Purva Ashadha": "Apas (water goddesses)", "Uttara Ashadha": "Vishvadevas (universal gods)",
    "Shravana": "Vishnu (preserver)", "Dhanishta": "Vasus (eight deities)", "Shatabhisha": "Varuna (god of cosmic waters)",
    "Purva Bhadrapada": "Aja Ekapada (one-footed serpent)", "Uttara Bhadrapada": "Ahir Budhnya (serpent of the deep)", "Revati": "Pushan (nourisher)"
}

NAKSHATRA_QUALITIES = {
    "Ashwini": {"animal": "Horse (male)", "guna": "Sattvic", "temperament": "Swift, healing, initiating"},
    "Bharani": {"animal": "Elephant (male)", "guna": "Rajasic", "temperament": "Intense, transformative, creative"},
    "Krittika": {"animal": "Sheep (female)", "guna": "Rajasic", "temperament": "Sharp, fiery, purifying"},
    "Rohini": {"animal": "Serpent (male)", "guna": "Rajasic", "temperament": "Creative, nurturing, fertile"},
    "Mrigashira": {"animal": "Serpent (female)", "guna": "Sattvic", "temperament": "Searching, gentle, curious"},
    "Ardra": {"animal": "Dog (female)", "guna": "Tamasic", "temperament": "Stormy, passionate, transformative"},
    "Punarvasu": {"animal": "Cat (female)", "guna": "Sattvic", "temperament": "Renewal, optimistic, returning"},
    "Pushya": {"animal": "Goat (male)", "guna": "Sattvic", "temperament": "Nourishing, protective, generous"},
    "Ashlesha": {"animal": "Cat (male)", "guna": "Tamasic", "temperament": "Cunning, wise, serpentine"},
    "Magha": {"animal": "Rat (male)", "guna": "Tamasic", "temperament": "Regal, ancestral, proud"},
    "Purva Phalguni": {"animal": "Rat (female)", "guna": "Rajasic", "temperament": "Romantic, creative, pleasure-seeking"},
    "Uttara Phalguni": {"animal": "Cow (male)", "guna": "Rajasic", "temperament": "Stable, contractual, reliable"},
    "Hasta": {"animal": "Buffalo (female)", "guna": "Sattvic", "temperament": "Skillful, dexterous, crafty"},
    "Chitra": {"animal": "Tiger (female)", "guna": "Rajasic", "temperament": "Artistic, brilliant, charismatic"},
    "Swati": {"animal": "Buffalo (male)", "guna": "Sattvic", "temperament": "Independent, flexible, scattered"},
    "Vishakha": {"animal": "Tiger (male)", "guna": "Rajasic", "temperament": "Determined, competitive, goal-driven"},
    "Anuradha": {"animal": "Deer (female)", "guna": "Sattvic", "temperament": "Devoted, friendly, successful"},
    "Jyeshtha": {"animal": "Deer (male)", "guna": "Tamasic", "temperament": "Senior, authoritative, protective"},
    "Mula": {"animal": "Dog (male)", "guna": "Tamasic", "temperament": "Investigative, destructive, rooted"},
    "Purva Ashadha": {"animal": "Monkey (male)", "guna": "Rajasic", "temperament": "Victorious, influential, invigorating"},
    "Uttara Ashadha": {"animal": "Mongoose (male)", "guna": "Sattvic", "temperament": "Enduring, universal, righteous"},
    "Shravana": {"animal": "Monkey (female)", "guna": "Sattvic", "temperament": "Learned, listening, connected"},
    "Dhanishta": {"animal": "Lion (female)", "guna": "Rajasic", "temperament": "Musical, wealthy, ambitious"},
    "Shatabhisha": {"animal": "Horse (female)", "guna": "Tamasic", "temperament": "Healing, secretive, philosophical"},
    "Purva Bhadrapada": {"animal": "Lion (male)", "guna": "Rajasic", "temperament": "Spiritual, eccentric, fiery"},
    "Uttara Bhadrapada": {"animal": "Cow (female)", "guna": "Sattvic", "temperament": "Grounded, deep, watery"},
    "Revati": {"animal": "Elephant (female)", "guna": "Sattvic", "temperament": "Nurturing, compassionate, journeying"}
}



