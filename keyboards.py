from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from typing import List, Dict, Any
from config import (
    ADMIN_IDS, REGIONS, ESSOS_MARKET,
    DONATE_PACKAGES, CASTLE_COST, CASTLE_INCOME
)

def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🌋 Oila tanlash"), KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="🛕 Uylar"), KeyboardButton(text="🗺 Valeriya Xaritasi")],
        [KeyboardButton(text="🏰 Qal'a"), KeyboardButton(text="💍 Ittifoq va Nikoh")],
        [KeyboardButton(text="🌍 Esos Savdosi"), KeyboardButton(text="💳 Green Bank")],
        [KeyboardButton(text="⚔️ Janglar"), KeyboardButton(text="🐉 Hayvonlarim 🕷")],
        [KeyboardButton(text="✨ Soliqlar"), KeyboardButton(text="🥇 Reyting")],
        [KeyboardButton(text="🏞 Valeria Ekspiditsya"), KeyboardButton(text="🏦 Golden")],
        [KeyboardButton(text="🛘 Hududiy topshiriqlar")]
    ]
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="👑 Admin paneli")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def houses_category_kb() -> InlineKeyboardMarkup:
    rows = []
    for reg_key, reg in REGIONS.items():
        lord_tag = "👑 Qirol" if reg.get("is_royal") else "🛡 Lord"
        btn_text = f"{reg['name']} ({reg['range'][0]}-{reg['range'][1]}) | {lord_tag}: {reg['lord_name']}"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"house_region:{reg_key}:0")])

    return InlineKeyboardMarkup(inline_keyboard=rows)

def houses_page_kb(houses: List[Dict[str, Any]], region_key: str, page: int, user_house_id: int = None, page_size: int = 10) -> InlineKeyboardMarkup:
    total = len(houses)
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, total)
    current_houses = houses[start_idx:end_idx]

    rows = []
    row = []
    for h in current_houses:
        h_id = h["id"]
        h_name = h["name"]
        is_lord = h.get("is_regional_lord")
        tier = h.get("tier", "B")

        if h["owner_id"] == user_house_id and user_house_id is not None:
            icon = "👑"
        elif h["owner_id"] is not None:
            icon = "🔒"
        elif is_lord:
            icon = "🌟"
        else:
            icon = "🟢"

        lord_badge = f" [{tier}-toifa]"
        btn = InlineKeyboardButton(
            text=f"{icon} {h_id}. {h_name}{lord_badge}",
            callback_data=f"h_detail:{h_id}"
        )
        row.append(btn)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"house_region:{region_key}:{page - 1}"))
    if end_idx < total:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"house_region:{region_key}:{page + 1}"))

    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="🔙 Hududlar ro'yxatiga qaytish", callback_data="house_cats_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def house_action_kb(house_id: int, is_available: bool, is_owner: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_available:
        rows.append([InlineKeyboardButton(text="👑 Ushbu xonadonni tanlash", callback_data=f"h_claim:{house_id}")])
    elif not is_owner:
        rows.append([InlineKeyboardButton(text="⚔️ Ushbu xonadonga hujum qilish", callback_data=f"attack_confirm:{house_id}")])
        rows.append([InlineKeyboardButton(text="💍 Nikoh / Ittifoq taklif qilish", callback_data=f"alliance_choose_type:{house_id}")])
    rows.append([InlineKeyboardButton(text="🔙 Hududlarga qaytish", callback_data="house_cats_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def call_to_arms_bannermen_kb(call_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Ha, yordamga borish (+30% kuch)", callback_data=f"pledge_cta:{call_id}")],
        [InlineKeyboardButton(text="🙅 Rad etish (Qo'shilmaslik)", callback_data=f"decline_cta:{call_id}")]
    ])

def battle_confirm_kb(target_house_id: int, can_call_bannermen: bool = False, call_id: int = None) -> InlineKeyboardMarkup:
    rows = []
    if can_call_bannermen:
        rows.append([InlineKeyboardButton(text="🎺 Bayroqdorlarni yordamga chorlash!", callback_data=f"trigger_cta:{target_house_id}")])

    attack_cb = f"attack_exec:{target_house_id}:{call_id if call_id else 0}"
    rows.append([InlineKeyboardButton(text="🔥 HA, JANGNI BOSHLASH!", callback_data=attack_cb)])
    rows.append([InlineKeyboardButton(text="🔙 Chekinish", callback_data="house_cats_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def essos_market_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, item in ESSOS_MARKET.items():
        text = f"{item['city']}: {item['name']} ({item['cost']} 🪙)"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"essos_view:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def essos_item_detail_kb(item_key: str) -> InlineKeyboardMarkup:
    item = ESSOS_MARKET.get(item_key, {})
    cost = item.get("cost", 0)

    rows = []
    if item_key in ["astapor", "meereen"]:
        # Arzonroq ommaviy birliklar (Benuqson, Chakra)
        rows.append([
            InlineKeyboardButton(text=f"🛒 1 ta ({cost} 🪙)", callback_data=f"essos_buy:{item_key}:1"),
            InlineKeyboardButton(text=f"🛒 10 ta ({cost * 10} 🪙)", callback_data=f"essos_buy:{item_key}:10")
        ])
        rows.append([
            InlineKeyboardButton(text=f"🛒 50 ta ({cost * 50} 🪙)", callback_data=f"essos_buy:{item_key}:50"),
            InlineKeyboardButton(text=f"🛒 100 ta ({cost * 100} 🪙)", callback_data=f"essos_buy:{item_key}:100")
        ])
    else:
        # Qimmat maxsus birliklar (O'rgimchak, Yuzsiz, Soya, Zahar)
        rows.append([
            InlineKeyboardButton(text=f"🛒 1 ta xarid qilish ({cost} 🪙)", callback_data=f"essos_buy:{item_key}:1")
        ])
        rows.append([
            InlineKeyboardButton(text=f"🛒 5 ta xarid qilish ({cost * 5} 🪙)", callback_data=f"essos_buy:{item_key}:5")
        ])

    rows.append([InlineKeyboardButton(text="🔙 Esos Bozoriga qaytish", callback_data="essos_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def beasts_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐲 Ajdar sotib olish (400 🪙)", callback_data="buy_beast:dragon")],
        [InlineKeyboardButton(text="🕷 Oʻrgimchak sotib olish (300 🪙)", callback_data="buy_beast:spider")],
        [InlineKeyboardButton(text="⚡️ Ajdarni kuchaytirish", callback_data="beast_upgrades_list")],
        [InlineKeyboardButton(text="🛡 Armiya / Askar yollash", callback_data="open_barracks")]
    ])

def dragons_upgrade_kb(dragons: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = []
    for d in dragons:
        grade = d["grade"]
        power = d["power"]
        name = d["name"]
        d_id = d["id"]
        if grade != "S":
            btn_text = f"⚡️ {name} [{grade} -> {get_next_grade(grade)}] (150 🪙)"
            rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"upgrade_d:{d_id}")])
        else:
            rows.append([InlineKeyboardButton(text=f"⭐️ {name} [MAX S - {power} ball]", callback_data="noop")])

    rows.append([InlineKeyboardButton(text="🔙 Maxluqlar menyusiga qaytish", callback_data="back_beasts")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_next_grade(grade: str) -> str:
    order = {"C": "B", "B": "A", "A": "S"}
    return order.get(grade, "MAX")

def barracks_recruitment_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗡 Oddiy askar +10 (10 🪙)", callback_data="recruit:soldier:10"),
            InlineKeyboardButton(text="🗡 +50 (50 🪙)", callback_data="recruit:soldier:50"),
        ],
        [
            InlineKeyboardButton(text="✨ Chakra +10 (20 🪙)", callback_data="recruit:chakra:10"),
            InlineKeyboardButton(text="✨ +50 (100 🪙)", callback_data="recruit:chakra:50"),
        ],
        [
            InlineKeyboardButton(text="🛡 Tilla plash +10 (30 🪙)", callback_data="recruit:gold_cloak:10"),
            InlineKeyboardButton(text="🛡 +50 (150 🪙)", callback_data="recruit:gold_cloak:50"),
        ],
        [InlineKeyboardButton(text="🔙 Maxluqlar va harbiy boshqaruv", callback_data="back_beasts")]
    ])

def expedition_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ 1 Soatlik Ekspeditsiya (~50 🪙)", callback_data="exp_start:1")],
        [InlineKeyboardButton(text="⏳ 4 Soatlik Ekspeditsiya (~220 🪙)", callback_data="exp_start:4")],
        [InlineKeyboardButton(text="⏳ 8 Soatlik Ekspeditsiya (~500 🪙)", callback_data="exp_start:8")],
        [InlineKeyboardButton(text="🔄 Holatni tekshirish / O'ljani olish", callback_data="exp_check")]
    ])

def bank_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Kunlik oltin bonusni olish", callback_data="bank_claim_daily")],
        [InlineKeyboardButton(text="📈 Xonadon moliyasi", callback_data="bank_info")]
    ])

def taxes_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Vassallardan soliqlarni yig'ish (24 soatda 1 marta)", callback_data="collect_all_taxes")]
    ])

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Barchaga xabar tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 O'yinchiga oltin berish", callback_data="admin_give_gold")],
        [InlineKeyboardButton(text="❄️ Ajdarlarni muzdan chiqarish", callback_data="admin_unfreeze")],
        [InlineKeyboardButton(text="🔄 Xonadonni bo'shatish", callback_data="admin_clear_house")],
        [InlineKeyboardButton(text="📊 To'liq statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⚠️ O'yinni Restart qilish (Reset)", callback_data="admin_restart_prompt")]
    ])

def admin_restart_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 HA, O'YINNI TO'LIQ RESTART QILISH", callback_data="admin_do_restart")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_cancel_restart")]
    ])

# --- Green Bank Keyboards ---

def green_bank_packages_kb() -> InlineKeyboardMarkup:
    rows = []
    for pkg_id, pkg in DONATE_PACKAGES.items():
        btn_text = f"💳 {pkg['name']} — {pkg['cost_uzs']:,} so'm"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"gb_view:{pkg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def green_bank_package_detail_kb(pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧾 Chekni (Skrinshot) yuborish", callback_data=f"gb_send_receipt:{pkg_id}")],
        [InlineKeyboardButton(text="🔙 Paketlar ro'yxatiga qaytish", callback_data="gb_back")]
    ])

def admin_donation_verify_kb(donation_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_don:{donation_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_don:{donation_id}")
        ]
    ])

# --- Qal'alar (Castles) Keyboards ---

def castle_menu_kb(castle: Optional[Dict[str, Any]], can_collect: bool, hours_passed: int = 0, income: int = 0) -> InlineKeyboardMarkup:
    rows = []
    if not castle:
        cost = CASTLE_COST[1]
        rows.append([InlineKeyboardButton(text=f"🏰 1-darajali Qal'a qurish ({cost} 🪙)", callback_data="castle_build_or_upgrade")])
    else:
        lvl = castle["level"]
        if lvl < 3:
            cost = CASTLE_COST[lvl + 1]
            rows.append([InlineKeyboardButton(text=f"⚡️ {lvl+1}-darajaga ko'tarish ({cost} 🪙)", callback_data="castle_build_or_upgrade")])
        else:
            rows.append([InlineKeyboardButton(text="⭐️ Maksimal daraja (3-daraja)", callback_data="noop")])

        if can_collect:
            rows.append([InlineKeyboardButton(text=f"💰 Daromadni yig'ish (+{income} 🪙)", callback_data="castle_collect_gold")])
        else:
            rows.append([InlineKeyboardButton(text="⏳ Daromad to'planmoqda...", callback_data="noop")])

    return InlineKeyboardMarkup(inline_keyboard=rows)

# --- Nikoh va Manfaatli Ittifoq (Alliances) Keyboards ---

def alliance_main_kb(alliances: Dict[str, Any], pending_count: int) -> InlineKeyboardMarkup:
    has_marriage = alliances.get("marriage") is not None
    has_strategic = alliances.get("strategic") is not None
    rows = []

    # 1. Sulolaviy Nikoh
    if has_marriage:
        rows.append([InlineKeyboardButton(text="💔 Sulolaviy Nikohni bekor qilish", callback_data="alliance_break:marriage")])
    else:
        rows.append([InlineKeyboardButton(text="💍 Sulolaviy Nikoh taklif qilish", callback_data="alliance_list:marriage")])

    # 2. Manfaatli Ittifoq
    if has_strategic:
        rows.append([InlineKeyboardButton(text="⚔️ Manfaatli Ittifoqni bekor qilish", callback_data="alliance_break:strategic")])
    else:
        rows.append([InlineKeyboardButton(text="🤝 Manfaatli Ittifoq taklif qilish", callback_data="alliance_list:strategic")])

    if pending_count > 0:
        rows.append([InlineKeyboardButton(text=f"📬 Kelgan takliflar ({pending_count} ta)", callback_data="alliance_pending_list")])

    return InlineKeyboardMarkup(inline_keyboard=rows)

def alliance_type_select_kb(target_house_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💍 Sulolaviy Nikoh taklif qilish", callback_data=f"propose_all:marriage:{target_house_id}")],
        [InlineKeyboardButton(text="🤝 Manfaatli Ittifoq taklif qilish", callback_data=f"propose_all:strategic:{target_house_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"h_detail:{target_house_id}")]
    ])

def alliance_decision_kb(proposal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_all:{proposal_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_all:{proposal_id}")
        ],
        [InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="alliance_back")]
    ])

# --- Kunlik Hududiy Topshiriqlar Keyboards ---

def daily_tasks_kb(tasks: Dict[str, Any]) -> InlineKeyboardMarkup:
    t1_done = tasks.get("task1_done", 0) == 1
    t2_done = tasks.get("task2_done", 0) == 1
    t3_done = tasks.get("task3_done", 0) == 1
    super_claimed = tasks.get("super_claimed", 0) == 1
    all_done = t1_done and t2_done and t3_done

    rows = []

    # 1. Chegara patruli
    if t1_done:
        rows.append([InlineKeyboardButton(text="✅ 1. Chegara patruli (Bajarildi)", callback_data="noop")])
    else:
        rows.append([InlineKeyboardButton(text="🛡 1. Chegarani patrul qilish (5 ⚙️)", callback_data="daily_task_1")])

    # 2. Garnizon mudofaasi
    if t2_done:
        rows.append([InlineKeyboardButton(text="✅ 2. Garnizon mudofaasi (Bajarildi)", callback_data="noop")])
    else:
        rows.append([InlineKeyboardButton(text="🏰 2. Garnizonni kuchaytirish (Qal'a/25 askar)", callback_data="daily_task_2")])

    # 3. Harbiy yurish
    if t3_done:
        rows.append([InlineKeyboardButton(text="✅ 3. Harbiy yurish (Bajarildi)", callback_data="noop")])
    else:
        rows.append([InlineKeyboardButton(text="⚔️ 3. Harbiy yurishga chiqish (10 ⚙️)", callback_data="daily_task_3")])

    # 4. Kunlik Super-Bonus
    if super_claimed:
        rows.append([InlineKeyboardButton(text="🌟 Bugungi Super-Bonus olindi!", callback_data="noop")])
    elif all_done:
        rows.append([InlineKeyboardButton(text="🎁 KUNLIK SUPER-BONUSNI OLISH (+350 🪙)", callback_data="daily_super_bonus")])
    else:
        done_count = sum([1 for x in [t1_done, t2_done, t3_done] if x])
        rows.append([InlineKeyboardButton(text=f"⏳ Super-Bonus ({done_count}/3 bajarildi)", callback_data="noop")])

    rows.append([InlineKeyboardButton(text="🔄 Yangilash", callback_data="daily_tasks_refresh")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

