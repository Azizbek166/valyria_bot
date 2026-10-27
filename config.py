import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8817691077:AAEy2vSoWfJ3PjT7ARNKCoMLqlW4FwVyDjs")

# Admin IDs
ADMIN_IDS = [7009689119]

# Database Path
DB_PATH = os.getenv("DB_PATH", "valyria.db")

# Dastlabki o'yinchi balansi
START_GOLD = 200
START_SOLDIERS = 20

# Chakra kunlik limit
CHAKRA_DAILY_LIMIT = 500

# Green Bank (Donate) Karta ma'lumotlari
DONATE_CARD = "9860 1666 5668 2043"
DONATE_CARD_HOLDER = "RONIN VALYRIA"

# Green Bank Donate Paketlari
DONATE_PACKAGES = {
    1: {
        "id": 1,
        "name": "Kichik Fath Paketi",
        "cost_uzs": 15000,
        "gold": 2000,
        "unsullied": 200,
        "valyrian_steel": 0,
        "faceless": 0,
        "shadow": 0,
        "poison": 5,
        "chakra": 200,
        "desc": "2,000 🪙 Oltin + 200 Benuqson 🛡 + 5 Zahar 🧪 + 200 Chakra ⚙️"
    },
    2: {
        "id": 2,
        "name": "Jangovar Gvardiya Paketi",
        "cost_uzs": 35000,
        "gold": 6000,
        "unsullied": 500,
        "valyrian_steel": 1,
        "faceless": 10,
        "shadow": 5,
        "poison": 15,
        "chakra": 500,
        "desc": "6,000 🪙 Oltin + 500 Benuqson 🛡 + 1 Valeriya Po'lati ⚔️ + 10 Yuzsiz 🥷 + 5 Soya 👣 + 15 Zahar 🧪 + 500 Chakra ⚙️"
    },
    3: {
        "id": 3,
        "name": "Valeriya Qudrati Paketi",
        "cost_uzs": 70000,
        "gold": 15000,
        "unsullied": 1500,
        "valyrian_steel": 3,
        "faceless": 25,
        "shadow": 15,
        "poison": 35,
        "chakra": 1000,
        "desc": "15,000 🪙 Oltin + 1,500 Benuqson 🛡 + 3 Valeriya Po'lati ⚔️ + 25 Yuzsiz 🥷 + 15 Soya 👣 + 35 Zahar 🧪 + 1,000 Chakra ⚙️"
    },
    4: {
        "id": 4,
        "name": "Oliy Hukmdor Xazinasi",
        "cost_uzs": 120000,
        "gold": 35000,
        "unsullied": 4000,
        "valyrian_steel": 6,
        "faceless": 60,
        "shadow": 40,
        "poison": 80,
        "chakra": 2500,
        "desc": "35,000 🪙 Oltin + 4,000 Benuqson 🛡 + 6 Valeriya Po'lati ⚔️ + 60 Yuzsiz 🥷 + 40 Soya 👣 + 80 Zahar 🧪 + 2,500 Chakra ⚙️"
    },
    5: {
        "id": 5,
        "name": "To'rt Jodugar Paketi (Witches Pack)",
        "cost_uzs": 17000,
        "gold": 2000,
        "unsullied": 0,
        "valyrian_steel": 0,
        "faceless": 0,
        "shadow": 0,
        "poison": 0,
        "chakra": 0,
        "witches": {
            "red": 1,
            "blood": 1,
            "water": 1,
            "shadow": 1
        },
        "desc": "Qizil 👩‍🦰 + Qon 🩸 + Suv 🧙 + Soya 🔮 Jodugarlari + 2,000 🪙 Bonus Oltin"
    }
}

# Qal'a (Castle) darajalari, narxi va soatlik daromadi
CASTLE_INCOME = {
    1: 10,  # 1-daraja: 10 oltin/soat
    2: 25,  # 2-daraja: 25 oltin/soat
    3: 50   # 3-daraja: 50 oltin/soat
}

CASTLE_COST = {
    1: 150, # 1-darajali qal'a qurish narxi
    2: 350, # 2-darajaga ko'tarish narxi
    3: 800  # 3-darajaga ko'tarish narxi
}

# Hudud Lordlari (A Toifa) ro'yxati
TIER_A_HOUSES = [1, 11, 21, 31, 41]

# Harbiy narxlar va ko'rsatkichlar
UNITS = {
    "soldier": {
        "name": "Oddiy askar 🗡",
        "cost": 1,
        "atk": 1,
        "def": 1
    },
    "archer": {
        "name": "Kamonchi 🏹",
        "cost": 3,
        "atk": 3,
        "def": 3
    },
    "cavalry": {
        "name": "Otliq 🐎",
        "cost": 5,
        "atk": 6,
        "def": 6
    },
    "chakra": {
        "name": "Chakra",
        "cost": 2,
        "atk": 2,
        "def": 2
    },
    "gold_cloak": {
        "name": "Tilla plash",
        "cost": 3,
        "atk": 3,
        "def": 3
    },
    "unsullied": {
        "name": "Benuqson 🛡",
        "cost": 5,
        "atk": 5,
        "def": 5
    },
    "faceless": {
        "name": "Yuzsiz qotil 🥷",
        "cost": 150,
        "atk": 300,
        "def": 300
    },
    "shadow": {
        "name": "Soya qotil 👣",
        "cost": 200,
        "atk": 400,
        "def": 400
    },
    "poison": {
        "name": "Zahar 🧪",
        "cost": 150,
        "atk": 300,
        "def": 300
    },
    "spider": {
        "name": "Oʻrgimchak 🕷",
        "cost": 300,
        "atk": 500,
        "def": 500
    },
    "dragon": {
        "name": "Ajdar 🐲",
        "cost": 400,
        "base_grade": "C",
        "base_power": 500
    }
}

# Esos Savdosi shaharlari va tovarlari
ESSOS_MARKET = {
    "asshai": {
        "city": "Asshai",
        "name": "Oʻrgimchak 🕷",
        "unit_key": "spider",
        "cost": 300,
        "power": 500,
        "desc": "Soyalar o'lkasining afsonaviy muz maxluqi"
    },
    "astapor": {
        "city": "Astapor",
        "name": "Benuqson 🛡",
        "unit_key": "unsullied",
        "cost": 5,
        "power": 5,
        "desc": "Qul bo'lmagan, temir intizomli elit jangchi (5/5)"
    },
    "braavos": {
        "city": "Braavos",
        "name": "Yuzsiz qotil 🥷",
        "unit_key": "faceless",
        "cost": 150,
        "power": 300,
        "desc": "Ko'p yuzli xudo xizmatkori, pinhona qotil"
    },
    "lorath": {
        "city": "Lorath",
        "name": "Soya qotil 👣",
        "unit_key": "shadow",
        "cost": 200,
        "power": 400,
        "desc": "Soyalardan paydo bo'luvchi qotil"
    },
    "lys": {
        "city": "Lys",
        "name": "Zahar 🧪",
        "unit_key": "poison",
        "cost": 150,
        "power": 300,
        "desc": "Halokatli Lys zahari"
    },
    "meereen": {
        "city": "Meereen",
        "name": "Chakra ⚙️",
        "unit_key": "chakra",
        "cost": 2,
        "power": 2,
        "desc": "O'tkir charxli Meereen quroli (2/2, kuniga 500 ta limit)"
    }
}

# Sword Bank Qarz Paketlari (15% ustama foiz bilan)
LOAN_PACKAGES = {
    1: {
        "id": 1,
        "name": "Kichik qarz",
        "amount": 200,
        "due_amount": 230,
        "desc": "200 🪙 qarz olinadi — 230 🪙 qaytariladi (+15% foiz)"
    },
    2: {
        "id": 2,
        "name": "O'rta qarz",
        "amount": 500,
        "due_amount": 575,
        "desc": "500 🪙 qarz olinadi — 575 🪙 qaytariladi (+15% foiz)"
    },
    3: {
        "id": 3,
        "name": "Katta harbiy kredit",
        "amount": 1000,
        "due_amount": 1150,
        "desc": "1,000 🪙 qarz olinadi — 1,150 🪙 qaytariladi (+15% foiz)"
    },
    4: {
        "id": 4,
        "name": "Oliy Lord qarzi",
        "amount": 2500,
        "due_amount": 2875,
        "desc": "2,500 🪙 qarz olinadi — 2,875 🪙 qaytariladi (+15% foiz)"
    }
}

# Ajdarlar darajalari va kuchaytirish narxi
DRAGON_GRADES = {
    "C": {"power": 500, "next": "B", "upgrade_cost": 150},
    "B": {"power": 1000, "next": "A", "upgrade_cost": 150},
    "A": {"power": 1500, "next": "S", "upgrade_cost": 150},
    "S": {"power": 2000, "next": None, "upgrade_cost": 0}
}

# Ajdar muzlash vaqti (3 kun = 72 soat = 259,200 soniya)
DRAGON_FREEZE_SECONDS = 3 * 24 * 3600

# O'rgamchak muzlash vaqti (28 soat = 100,800 soniya)
SPIDER_FREEZE_SECONDS = 28 * 3600

# Westeros talon-taroj qilish umumiy limiti (6 soat = 21,600 soniya)
WESTEROS_GLOBAL_COOLDOWN = 6 * 3600

# Josuslik narxi va vaqti
SPY_COST = 300
SPY_DURATION_SECONDS = 30 * 60

# Jang davomiyligi (7 daqiqa = 420 soniya)
BATTLE_DURATION_SECONDS = 7 * 60

# 5 ta Asosiy Hududlar
REGIONS = {
    "crownlands": {
        "id": "crownlands",
        "name": "Qirollik yerlari 👑",
        "lord_house_id": 1,
        "lord_name": "Targaryen",
        "title": "Oliy Qirol 👑",
        "range": (1, 10),
        "desc": "Valeriyaning poytaxt va markaziy taxt yerlari. Hukmdor: Oliy Qirol Targaryen"
    },
    "volcanoes": {
        "id": "volcanoes",
        "name": "Valeriya Vulqonlar lordligi 🌋",
        "lord_house_id": 11,
        "lord_name": "Zaldrizar",
        "title": "Vulqonlar Lordi 🌋",
        "range": (11, 20),
        "desc": "Olovli tog'lar, ajdarlar maskani va vulqonlar. Hukmdor: Lord Zaldrizar"
    },
    "forest": {
        "id": "forest",
        "name": "Oʻrmon yerlari 🌲",
        "lord_house_id": 21,
        "lord_name": "Varezys",
        "title": "O'rmon Lordi 🌲",
        "range": (21, 30),
        "desc": "Qadimiy sirli o'rmonlar va qudratli qal'alar. Hukmdor: Lord Varezys"
    },
    "sorcerers": {
        "id": "sorcerers",
        "name": "Jodugarlar yerlari 🔮",
        "lord_house_id": 31,
        "lord_name": "Maeraxes",
        "title": "Jodugarlar Lordi 🔮",
        "range": (31, 40),
        "desc": "Qadimgi sehrgarlar va qon jodulari makoni. Hukmdor: Lord Maeraxes"
    },
    "sea_guardians": {
        "id": "sea_guardians",
        "name": "Dengiz Qoʻriqchilari 🌊",
        "lord_house_id": 41,
        "lord_name": "Nyzarys",
        "title": "Dengiz Lordi 🌊",
        "range": (41, 52),
        "desc": "Dengizlar, kemalar va orollar hukmdorligi. Hukmdor: Lord Nyzarys"
    }
}

# 52 ta Valeriya Xonadoni ro'yxati (A va B toifalari bilan)
HOUSES_DATA = [
    # 1 - 10: Qirollik yerlari (Crownlands)
    {"id": 1, "name": "Targaryen", "type": "land", "region": "crownlands", "is_regional_lord": True, "tier": "A"},
    {"id": 2, "name": "Velaryon", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 3, "name": "Celtigar", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 4, "name": "Qoherys", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 5, "name": "Peanmion", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 6, "name": "Aeloris", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 7, "name": "Vaeloryn", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 8, "name": "Maegorys", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 9, "name": "Drakorys", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},
    {"id": 10, "name": "Aetherys", "type": "land", "region": "crownlands", "is_regional_lord": False, "tier": "B"},

    # 11 - 20: Valeriya Vulqonlar lordligi
    {"id": 11, "name": "Zaldrizar", "type": "land", "region": "volcanoes", "is_regional_lord": True, "tier": "A"},
    {"id": 12, "name": "Vhaelyx", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 13, "name": "Rhaekar", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 14, "name": "Daemoryn", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 15, "name": "Aenarion", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 16, "name": "Vaegoryn", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 17, "name": "Belmorys", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 18, "name": "Aelyndar", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 19, "name": "Thorynax", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},
    {"id": 20, "name": "Qhaedarys", "type": "land", "region": "volcanoes", "is_regional_lord": False, "tier": "B"},

    # 21 - 30: O'rmon yerlari
    {"id": 21, "name": "Varezys", "type": "land", "region": "forest", "is_regional_lord": True, "tier": "A"},
    {"id": 22, "name": "Aethonar", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 23, "name": "Qelbar", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 24, "name": "Morgharys", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 25, "name": "Zobridar", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 26, "name": "Vaelqar", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 27, "name": "Rhaenorys", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 28, "name": "Draevor", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 29, "name": "Aelyxar", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},
    {"id": 30, "name": "Qhaelor", "type": "land", "region": "forest", "is_regional_lord": False, "tier": "B"},

    # 31 - 40: Jodugarlar yerlari
    {"id": 31, "name": "Maeraxes", "type": "land", "region": "sorcerers", "is_regional_lord": True, "tier": "A"},
    {"id": 32, "name": "Velqorys", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 33, "name": "Oryndor", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 34, "name": "Vaezhar", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 35, "name": "Thalorys", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 36, "name": "Aenovar", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 37, "name": "Zhaedrion", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 38, "name": "Rhaevos", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 39, "name": "Daelorax", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},
    {"id": 40, "name": "Qorvarys", "type": "land", "region": "sorcerers", "is_regional_lord": False, "tier": "B"},

    # 41 - 52: Dengiz Qo'riqchilari
    {"id": 41, "name": "Nyzarys", "type": "sea", "region": "sea_guardians", "is_regional_lord": True, "tier": "A"},
    {"id": 42, "name": "Volnorys", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 43, "name": "Aethyron", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 44, "name": "Qelarys", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 45, "name": "Zalvorys", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 46, "name": "Rhaqelor", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 47, "name": "Vhaenorys", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 48, "name": "Orvaedys", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 49, "name": "Maelqor", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 50, "name": "Draezhar", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 51, "name": "Belvaeron", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"},
    {"id": 52, "name": "Aenqarys", "type": "sea", "region": "sea_guardians", "is_regional_lord": False, "tier": "B"}
]

def escape_md(text: Any) -> str:
    """Telegram Markdown (v1) maxsus belgilarini (_ * ` [) xavfsiz qilish"""
    if not text:
        return ""
    res = str(text)
    for ch in ("_", "*", "`", "["):
        res = res.replace(ch, "\\" + ch)
    return res

# --- Westerosni Talon-Taroj Qilish (Westeros Raids) Nishonlari ---
WESTEROS_TARGETS = {
    "coastal_villages": {
        "id": "coastal_villages",
        "name": "🌊 Qirg'oq Qishloqlari va Savdo Kemalar",
        "region_name": "Tor Dengiz Sohillari",
        "difficulty": "🟢 Oson (Boshlang'ich)",
        "min_power": 50,
        "requires_dragon": False,
        "cooldown_seconds": 1800,  # 30 daqiqa
        "gold_min": 150,
        "gold_max": 350,
        "chakra_min": 20,
        "chakra_max": 50,
        "unsullied_loot": 0,
        "valyrian_steel_chance": 0.0,
        "loss_min": 1,
        "loss_max": 3,
        "desc": "Westerosning himoyasiz baliqchilar qishloqlari va dengizdagi boy savdo kemalari. Kam kuch bilan tezkor o'lja olish uchun eng qulay joy."
    },
    "casterly_rock": {
        "id": "casterly_rock",
        "name": "🦁 Casterly Rock (Lannisterlar Oltin Konlari)",
        "region_name": "G'arbiy Qoyatosh",
        "difficulty": "🟡 O'rta",
        "min_power": 250,
        "requires_dragon": False,
        "cooldown_seconds": 7200,  # 2 soat
        "gold_min": 600,
        "gold_max": 1200,
        "chakra_min": 80,
        "chakra_max": 160,
        "unsullied_loot": 0,
        "valyrian_steel_chance": 0.0,
        "loss_min": 3,
        "loss_max": 8,
        "desc": "Lannisterlar sulolasining afsonaviy oltin konlari. Bu yerdagi konlar asrlar davomida Westerosning eng katta boylik manbai bo'lib kelgan."
    },
    "highgarden": {
        "id": "highgarden",
        "name": "🌹 Highgarden va Reach Dalalari (Tyrellar)",
        "region_name": "Reach Unumdor Yerlari",
        "difficulty": "🟠 Qiyin",
        "min_power": 600,
        "requires_dragon": False,
        "cooldown_seconds": 14400,  # 4 soat
        "gold_min": 1500,
        "gold_max": 2800,
        "chakra_min": 180,
        "chakra_max": 300,
        "unsullied_loot": 15,
        "valyrian_steel_chance": 0.05,
        "loss_min": 8,
        "loss_max": 15,
        "desc": "Westerosning eng serhosil va boy viloyati. Qasr omborlarida mislsiz xazina va unumdor boyliklar saqlanadi. Asirlardan jangchilar o'lja qilinadi."
    },
    "kings_landing": {
        "id": "kings_landing",
        "name": "👑 Qirollik Qo'nimgohi (King's Landing — Qizil Qasr)",
        "region_name": "Westeros Poytaxti",
        "difficulty": "🔴 Og'ir (Katta reyd)",
        "min_power": 1500,
        "requires_dragon": True,
        "cooldown_seconds": 28800,  # 8 soat
        "gold_min": 3500,
        "gold_max": 6500,
        "chakra_min": 400,
        "chakra_max": 700,
        "unsullied_loot": 30,
        "valyrian_steel_chance": 0.15,
        "loss_min": 15,
        "loss_max": 30,
        "desc": "Temir Taxt joylashgan poytaxt shahar. Qizil Qasr xazinasi yetti qirollikning soliqlariga to'la. Hujum uchun qudratli armiya va kamida 1 ta Ajdar talab etiladi."
    },
    "winterfell": {
        "id": "winterfell",
        "name": "🐺 Winterfell (Shimolning Qadimiy Qal'asi)",
        "region_name": "Shimol Qirolligi",
        "difficulty": "🟣 Afsonaviy (Elita)",
        "min_power": 3000,
        "requires_dragon": True,
        "cooldown_seconds": 43200,  # 12 soat
        "gold_min": 7000,
        "gold_max": 12000,
        "chakra_min": 800,
        "chakra_max": 1200,
        "unsullied_loot": 50,
        "valyrian_steel_chance": 0.35,
        "loss_min": 25,
        "loss_max": 50,
        "desc": "Ming yillik muz va po'lat qal'asi. Faqat eng qudratli Valeriya Lordlari Shimolning qattiq sovuqlari va Starklar qarshiligini yengib, ulkan boylik olib qayta oladi."
    }
}


