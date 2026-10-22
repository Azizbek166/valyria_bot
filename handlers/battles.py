import random
import time
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    get_user_house, get_houses, get_house_by_id,
    calculate_player_power, execute_battle, get_user,
    create_call_to_arms, get_active_call_to_arms,
    pledge_bannerman_support, get_region_bannermen,
    get_call_pledged_power, get_user_army, get_user_beasts,
    start_house_attack, resolve_battle, get_user_active_battle,
    get_battle_by_id
)
from keyboards import (
    battle_confirm_kb, call_to_arms_bannermen_kb,
    battle_army_select_kb, active_battle_status_kb
)
from config import REGIONS, UNITS, BATTLE_DURATION_SECONDS

router = Router()

class BattleState(StatesGroup):
    selecting_army = State()
    waiting_for_custom_input = State()

def format_army_selection_text(
    target_house: dict,
    user_house: dict,
    army: dict,
    selected: dict,
    active_dragons: list,
    include_dragons: bool,
    has_specials: bool,
    include_specials: bool,
    valyrian_steel: int
) -> tuple[str, int]:
    chakra_mult = 2 if valyrian_steel >= 1 else 1

    power = (
        selected.get("soldiers", 0) * UNITS["soldier"]["atk"] +
        selected.get("archers", 0) * UNITS.get("archer", {}).get("atk", 3) +
        selected.get("cavalry", 0) * UNITS.get("cavalry", {}).get("atk", 6)
    )

    if include_specials:
        power += (
            selected.get("chakra", 0) * UNITS["chakra"]["atk"] * chakra_mult +
            selected.get("gold_cloaks", 0) * UNITS["gold_cloak"]["atk"] +
            selected.get("unsullied", 0) * UNITS["unsullied"]["atk"] +
            selected.get("faceless", 0) * UNITS["faceless"]["atk"] +
            selected.get("shadow", 0) * UNITS["shadow"]["atk"] +
            selected.get("poison", 0) * UNITS["poison"]["atk"] +
            (valyrian_steel * 500)
        )

    dragons_power = 0
    if include_dragons and active_dragons:
        dragons_power = sum(d.get("power", 500) for d in active_dragons)
        power += dragons_power

    target_reg = REGIONS.get(target_house.get("region", ""), {})

    text = (
        f"⚔️ **HUJUM TARKIBINI SHAKLLANTIRISH (QO'SHIN TANLASH)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Nishingoh: **{target_house['name']}** (#{target_house['id']})\n"
        f"🌍 Hudud: **{target_reg.get('name', '')}**\n\n"
        f"📋 **Jangga yuborilayotgan qo'shin:**\n"
        f"• 🗡 Oddiy askar: **{selected.get('soldiers', 0)}** ta (mavjud: {army.get('soldiers', 0)})\n"
        f"• 🏹 Kamonchi: **{selected.get('archers', 0)}** ta (mavjud: {army.get('archers', 0)})\n"
        f"• 🐎 Otliq: **{selected.get('cavalry', 0)}** ta (mavjud: {army.get('cavalry', 0)})\n"
    )
    if active_dragons:
        d_status = f"**{len(active_dragons)} ta ajdar** (+{dragons_power} ball)" if include_dragons else "❌ Olib tashlangan"
        text += f"• 🐲 Ajdarlar: {d_status}\n"
    if has_specials:
        s_status = "✅ Qo'shilgan" if include_specials else "❌ Olib tashlangan"
        text += f"• ⚡️ Maxsus kuchlar: {s_status}\n"

    text += (
        f"\n⚡️ **Umumiy zarba quvvati:** **{power} ball**\n"
        f"⏳ **Jang davomiyligi:** **8 daqiqa** (480 soniya)\n\n"
        f"⚠️ *Eslatma: Faqat jangga yuborilgan qo'shinlar talafot ko'radi. Qal'angizda qolgan kuchlaringiz xavfsiz saqlanadi!*"
    )
    return text, power

@router.message(F.text == "⚔️ Janglar")
async def show_battles_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_house = await get_user_house(user_id)

    if not user_house:
        await message.answer(
            "⚠️ **Siz hali birorta xonadonni boshqarmayapsiz!**\n"
            "Jangga kirishdan oldin **🌋 Oila tanlash** bo'limidan o'z xonadoningizni tanlang.",
            parse_mode="Markdown"
        )
        return

    # Faol jang bormi tekshirish (8 daqiqalik davom etayotgan jang)
    active_battle = await get_user_active_battle(user_id)
    if active_battle:
        rem_min = active_battle["left_seconds"] // 60
        rem_sec = active_battle["left_seconds"] % 60
        is_ready = active_battle["ready"]
        
        status_note = "🎉 **Qo'shinlar manzilga yetib bordi! Jang natijasini qabul qilib oling!**" if is_ready else f"⏳ Dushman qal'asigacha: **{rem_min} daqiqa {rem_sec} soniya** qoldi."
        text = (
            f"⚔️ **QADIMGI VALERIYA JANG MAYDONI (FAOL JANG)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{active_battle['attacker_house_name']}**\n"
            f"🛡 Himoyachi qal'a: **{active_battle['defender_house_name']}**\n\n"
            f"Holat: {status_note}\n\n"
            f"Jang yakunlanishi bilan natijani ko'rishingiz mumkin."
        )
        await message.answer(text, reply_markup=active_battle_status_kb(active_battle["id"], is_ready=is_ready), parse_mode="Markdown")
        return

    power_info = await calculate_player_power(user_id)
    houses = await get_houses()

    occupied_houses = [
        h for h in houses
        if h["owner_id"] is not None and h["owner_id"] != user_id
    ]

    reg_info = REGIONS.get(user_house.get("region", ""), {})
    role_tag = "👑 Oliy Qirol" if user_house["id"] == 1 else ("🛡 Hudud Lordi" if user_house.get("is_regional_lord") else "🗡 Bayroqdor")

    text = (
        f"⚔️ **QADIMGI VALERIYA URUSHLARI VA JANG MAYDONI**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Sizning xonadoningiz: **{user_house['name']}** ({reg_info.get('name', '')})\n"
        f"🎖 Maqomingiz: **{role_tag}**\n"
        f"⚡️ Faol jangovar kuchingiz: **{power_info['total_active_power']} ball**\n"
        f"🐲 Faol ajdarlaringiz: {len(power_info['active_dragons'])} ta\n"
        f"❄️ Muzlagan ajdarlaringiz: {len(power_info['frozen_dragons'])} ta\n\n"
        f"🔥 **Jang va Hududiy Qoidalar:**\n"
        f"1. ⏳ **Hujum vaqti:** Har bir jang **8 daqiqa** davom etadi. Shu vaqt mobaynida qo'shinlar yurish qiladi.\n"
        f"2. 🛡 **Qo'shin tanlash:** Jangga qaysi askar va qancha miqdorda yuborilishini o'zingiz belgilaysiz!\n"
        f"3. G'alaba qozonsangiz, mag'lub xonadon sizning **vassalingizga** aylanadi va 20% oltini o'lja qilinadi.\n"
        f"4. Faqat jangga yuborilgan ajdarlaringiz **3 kunga muzlaydi**!\n\n"
        f"Hujum qilish uchun raqib xonadonni tanlang:"
    )

    if not occupied_houses:
        text += "\n\n😴 *Hozircha boshqa o'yinchilar xonadon tanlamagan. Boshqa o'yinchilar botga kirib xonadon tanlashi kutilmoqda.*"
        await message.answer(text, parse_mode="Markdown")
        return

    rows = []
    for h in occupied_houses[:12]:
        h_owner = await get_user(h["owner_id"])
        owner_name = h_owner.get("custom_name") or h_owner["full_name"] if h_owner else f"Lord #{h['owner_id']}"
        username_str = f" (@{h_owner['username']})" if (h_owner and h_owner.get("username")) else ""
        vassal_tag = " (Vassal)" if h["overlord_id"] else ""
        tier_tag = f" [{h.get('tier', 'B')}-toifa]"
        btn_text = f"⚔️ {h['name']}{tier_tag}{vassal_tag} — {owner_name}{username_str}"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"attack_confirm:{h['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("attack_confirm:"))
async def callback_attack_confirm(callback: types.CallbackQuery, state: FSMContext):
    house_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Faol jang bormi tekshirish
    active_battle = await get_user_active_battle(user_id)
    if active_battle:
        rem_min = active_battle["left_seconds"] // 60
        rem_sec = active_battle["left_seconds"] % 60
        await callback.answer(f"⚠️ Sizda faol jang ketmoqda! Qolgan vaqt: {rem_min} daq {rem_sec} son.", show_alert=True)
        return

    target_house = await get_house_by_id(house_id)
    if not target_house:
        await callback.answer("Xonadon topilmadi!", show_alert=True)
        return

    user_house = await get_user_house(user_id)
    if not user_house:
        await callback.answer("Sizda xonadon yo'q!", show_alert=True)
        return

    power_info = await calculate_player_power(user_id)
    if power_info["total_active_power"] <= 0:
        await callback.answer("Sizda jangga kiradigan askar yoki ajdar yo'q!", show_alert=True)
        return

    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]

    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    # Standart holatda barcha mavjud qo'shinlarni tanlaymiz (foydalanuvchi xohlasa o'zgartiradi)
    selected_troops = {
        "soldiers": army.get("soldiers", 0),
        "archers": army.get("archers", 0),
        "cavalry": army.get("cavalry", 0),
        "chakra": army.get("chakra", 0),
        "gold_cloaks": army.get("gold_cloaks", 0),
        "unsullied": army.get("unsullied", 0),
        "faceless": army.get("faceless", 0),
        "shadow": army.get("shadow", 0),
        "poison": army.get("poison", 0),
        "dragon_ids": [d["id"] for d in active_dragons]
    }

    active_cta = await get_active_call_to_arms(house_id)
    call_id = active_cta["id"] if active_cta else 0

    is_target_lord = target_house.get("is_regional_lord") or target_house["id"] == 1
    can_call_bannermen = False
    if is_target_lord and not active_cta:
        bannermen = await get_region_bannermen(target_house["region"])
        can_call_bannermen = len(bannermen) > 0

    await state.set_state(BattleState.selecting_army)
    await state.update_data(
        target_house_id=house_id,
        call_id=call_id,
        selected_troops=selected_troops,
        include_dragons=True,
        include_specials=True,
        can_call_bannermen=can_call_bannermen
    )

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected_troops,
        active_dragons=active_dragons,
        include_dragons=True,
        has_specials=has_specials,
        include_specials=True,
        valyrian_steel=power_info.get("valyrian_steel", 0)
    )

    kb = battle_army_select_kb(
        target_house_id=house_id,
        army=army,
        selected=selected_troops,
        has_dragons=len(active_dragons) > 0,
        include_dragons=True,
        has_specials=has_specials,
        include_specials=True,
        can_call_bannermen=can_call_bannermen,
        call_id=call_id
    )

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("bt_adj:"), BattleState.selecting_army)
async def callback_battle_adjust_troops(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    unit_type = parts[1]
    action = parts[2]

    data = await state.get_data()
    selected = data.get("selected_troops", {})
    user_id = callback.from_user.id
    army = await get_user_army(user_id)
    max_avail = army.get(unit_type, 0)
    current = selected.get(unit_type, 0)

    if action == "all":
        current = max_avail
    elif action == "zero":
        current = 0
    else:
        diff = int(action)
        current = max(0, min(max_avail, current + diff))

    selected[unit_type] = current
    await state.update_data(selected_troops=selected)

    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=data.get("include_dragons", True),
        has_specials=has_specials,
        include_specials=data.get("include_specials", True),
        valyrian_steel=valyrian_steel
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=selected,
        has_dragons=len(active_dragons) > 0,
        include_dragons=data.get("include_dragons", True),
        has_specials=has_specials,
        include_specials=data.get("include_specials", True),
        can_call_bannermen=data.get("can_call_bannermen", False),
        call_id=data.get("call_id", 0)
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer(f"{unit_type.capitalize()}: {current} ta")

@router.callback_query(F.data == "bt_toggle:dragons", BattleState.selecting_army)
async def callback_battle_toggle_dragons(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    inc_dragons = not data.get("include_dragons", True)
    await state.update_data(include_dragons=inc_dragons)

    user_id = callback.from_user.id
    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=data.get("selected_troops", {}),
        active_dragons=active_dragons,
        include_dragons=inc_dragons,
        has_specials=has_specials,
        include_specials=data.get("include_specials", True),
        valyrian_steel=valyrian_steel
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=data.get("selected_troops", {}),
        has_dragons=len(active_dragons) > 0,
        include_dragons=inc_dragons,
        has_specials=has_specials,
        include_specials=data.get("include_specials", True),
        can_call_bannermen=data.get("can_call_bannermen", False),
        call_id=data.get("call_id", 0)
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Ajdarlar holati yangilandi!")

@router.callback_query(F.data == "bt_toggle:specials", BattleState.selecting_army)
async def callback_battle_toggle_specials(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    inc_specials = not data.get("include_specials", True)
    await state.update_data(include_specials=inc_specials)

    user_id = callback.from_user.id
    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=data.get("selected_troops", {}),
        active_dragons=active_dragons,
        include_dragons=data.get("include_dragons", True),
        has_specials=has_specials,
        include_specials=inc_specials,
        valyrian_steel=valyrian_steel
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=data.get("selected_troops", {}),
        has_dragons=len(active_dragons) > 0,
        include_dragons=data.get("include_dragons", True),
        has_specials=has_specials,
        include_specials=inc_specials,
        can_call_bannermen=data.get("can_call_bannermen", False),
        call_id=data.get("call_id", 0)
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Maxsus qo'shinlar holati yangilandi!")

@router.callback_query(F.data == "bt_preset:all", BattleState.selecting_army)
async def callback_battle_preset_all(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]

    selected = {
        "soldiers": army.get("soldiers", 0),
        "archers": army.get("archers", 0),
        "cavalry": army.get("cavalry", 0),
        "chakra": army.get("chakra", 0),
        "gold_cloaks": army.get("gold_cloaks", 0),
        "unsullied": army.get("unsullied", 0),
        "faceless": army.get("faceless", 0),
        "shadow": army.get("shadow", 0),
        "poison": army.get("poison", 0),
        "dragon_ids": [d["id"] for d in active_dragons]
    }
    await state.update_data(selected_troops=selected, include_dragons=True, include_specials=True)

    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=True,
        has_specials=has_specials,
        include_specials=True,
        valyrian_steel=valyrian_steel
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=selected,
        has_dragons=len(active_dragons) > 0,
        include_dragons=True,
        has_specials=has_specials,
        include_specials=True,
        can_call_bannermen=data.get("can_call_bannermen", False),
        call_id=data.get("call_id", 0)
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Barcha mavjud kuchlar tanlandi!")

@router.callback_query(F.data == "bt_preset:zero", BattleState.selecting_army)
async def callback_battle_preset_zero(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]

    selected = {
        "soldiers": 0, "archers": 0, "cavalry": 0,
        "chakra": 0, "gold_cloaks": 0, "unsullied": 0,
        "faceless": 0, "shadow": 0, "poison": 0,
        "dragon_ids": []
    }
    await state.update_data(selected_troops=selected, include_dragons=False, include_specials=False)

    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=False,
        has_specials=has_specials,
        include_specials=False,
        valyrian_steel=valyrian_steel
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=selected,
        has_dragons=len(active_dragons) > 0,
        include_dragons=False,
        has_specials=has_specials,
        include_specials=False,
        can_call_bannermen=data.get("can_call_bannermen", False),
        call_id=data.get("call_id", 0)
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Tanlov tozalandi!")

@router.callback_query(F.data == "bt_custom_input", BattleState.selecting_army)
async def callback_battle_custom_input(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BattleState.waiting_for_custom_input)
    prompt = (
        "📝 **QO'SHIN MIQDORINI QO'LDA KIRITISH**\n\n"
        "Jangga yubormoqchi bo'lgan **Oddiy askar**, **Kamonchi** va **Otliqlar** sonini bitta qatorda bo'sh joy bilan yozing:\n\n"
        "Masalan: `50 15 5`\n"
        "*(50 ta askar, 15 ta kamonchi, 5 ta otliq)*"
    )
    await callback.message.answer(prompt, parse_mode="Markdown")
    await callback.answer()

@router.message(BattleState.waiting_for_custom_input)
async def handle_custom_troop_input(message: types.Message, state: FSMContext):
    text = message.text.strip()
    parts = text.split()
    user_id = message.from_user.id
    army = await get_user_army(user_id)

    try:
        s_cnt = int(parts[0]) if len(parts) > 0 else 0
        a_cnt = int(parts[1]) if len(parts) > 1 else 0
        c_cnt = int(parts[2]) if len(parts) > 2 else 0
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat sonlar yozing, masalan: `30 10 5`")
        return

    data = await state.get_data()
    selected = data.get("selected_troops", {})

    selected["soldiers"] = max(0, min(army.get("soldiers", 0), s_cnt))
    selected["archers"] = max(0, min(army.get("archers", 0), a_cnt))
    selected["cavalry"] = max(0, min(army.get("cavalry", 0), c_cnt))

    await state.set_state(BattleState.selecting_army)
    await state.update_data(selected_troops=selected)

    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    has_specials = any(army.get(k, 0) > 0 for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"])

    res_text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=data.get("include_dragons", True),
        has_specials=has_specials,
        include_specials=data.get("include_specials", True),
        valyrian_steel=valyrian_steel
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=selected,
        has_dragons=len(active_dragons) > 0,
        include_dragons=data.get("include_dragons", True),
        has_specials=has_specials,
        include_specials=data.get("include_specials", True),
        can_call_bannermen=data.get("can_call_bannermen", False),
        call_id=data.get("call_id", 0)
    )

    await message.answer(f"✅ Qo'shin miqdori belgilandi!\n\n{res_text}", reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("bt_confirm_march:"))
async def callback_battle_confirm_march(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    target_house_id = int(parts[1])
    call_id = int(parts[2]) if len(parts) > 2 else 0

    user_id = callback.from_user.id
    data = await state.get_data()
    selected_troops = data.get("selected_troops", {})

    # Ajdarlar va maxsus kuchlar filtri
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [b["id"] for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]

    if not data.get("include_dragons", True):
        selected_troops["dragon_ids"] = []
    else:
        selected_troops["dragon_ids"] = active_dragons

    if not data.get("include_specials", True):
        for k in ["chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"]:
            selected_troops[k] = 0

    success, msg, battle_id = await start_house_attack(user_id, target_house_id, selected_troops, call_id)
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    await state.clear()

    target_house = await get_house_by_id(target_house_id)
    user_house = await get_user_house(user_id)

    report_start = (
        f"🚀 **QO'SHIN JANGGA OT LANDI! (8 DAQIQA)** ⚔️\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Nishon: **{target_house['name']}**\n"
        f"⏳ **Yurish vaqti:** 8 daqiqa (480 soniya)\n\n"
        f"🗡 Yuborilgan askarlar: **{selected_troops.get('soldiers', 0)}** ta\n"
        f"🏹 Kamonchilar: **{selected_troops.get('archers', 0)}** ta\n"
        f"🐎 Otliqlar: **{selected_troops.get('cavalry', 0)}** ta\n"
        f"🐲 Ajdarlar: **{len(selected_troops.get('dragon_ids', []))}** ta\n\n"
        f"🛡 *Qo'shinlaringiz dushman qal'asi tomon yurish boshladi. 8 daqiqa o'tgach natijani qabul qilib olishingiz mumkin!*"
    )

    await callback.message.edit_text(
        report_start,
        reply_markup=active_battle_status_kb(battle_id, is_ready=False),
        parse_mode="Markdown"
    )
    await callback.answer("Qo'shin jangga otlandi! ⚔️", show_alert=True)

    # Himoyachiga ogohlantirish yuborish
    if target_house and target_house.get("owner_id"):
        try:
            defender_msg = (
                f"🚨 **SHOSHILINCH OGOHLANTIRISH! QAL'ANGIZGA HUJUM!** ⚔️\n\n"
                f"Lord! Dushman **{user_house['name']}** xonadoni qo'shini sizning qal'angizga bostirib kelmoqda!\n"
                f"⏳ **Yetib kelish vaqti: 8 daqiqa!**\n\n"
                f"Mudofaani mustahkamlang yoki ittifoqchilaringizni yordamga chorlang!"
            )
            await callback.bot.send_message(target_house["owner_id"], defender_msg, parse_mode="Markdown")
        except Exception:
            pass

@router.callback_query(F.data.startswith("battle_refresh:"))
async def callback_battle_refresh(callback: types.CallbackQuery):
    battle_id = int(callback.data.split(":")[1])
    battle = await get_battle_by_id(battle_id)

    if not battle or battle["status"] != "marching":
        await callback.answer("Jang yakunlangan yoki topilmadi!", show_alert=True)
        return

    rem_min = battle["left_seconds"] // 60
    rem_sec = battle["left_seconds"] % 60
    is_ready = battle["ready"]

    if is_ready:
        status_note = "🎉 **Qo'shinlar dushman qal'asiga yetib bordi! Jang natijasini qabul qilib oling!**"
    else:
        status_note = f"⏳ Qolgan vaqt: **{rem_min} daqiqa {rem_sec} soniya**."

    text = (
        f"⚔️ **QADIMGI VALERIYA JANG MAYDONI (FAOL JANG)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Hujum qiluvchi: **{battle['attacker_house_name']}**\n"
        f"🛡 Himoyachi qal'a: **{battle['defender_house_name']}**\n\n"
        f"Holat: {status_note}\n\n"
        f"Quyidagi tugma orqali vaqtni tekshiring yoki natijani oling."
    )

    try:
        await callback.message.edit_text(text, reply_markup=active_battle_status_kb(battle_id, is_ready=is_ready), parse_mode="Markdown")
    except Exception:
        pass

    if is_ready:
        await callback.answer("Jang tayyor! Natijani oling! 🎉", show_alert=True)
    else:
        await callback.answer(f"⏳ Qoldi: {rem_min} daq {rem_sec} son.")

@router.callback_query(F.data.startswith("battle_resolve:"))
async def callback_battle_resolve(callback: types.CallbackQuery):
    battle_id = int(callback.data.split(":")[1])
    res = await resolve_battle(battle_id)

    if not res.get("success"):
        await callback.answer(res.get("error", "Xatolik yuz berdi!"), show_alert=True)
        return

    bannermen_info = ""
    if res.get("bannermen_power", 0) > 0:
        bannermen_info = f"\n🎺 **Bayroqdorlar yordami:** +{res['bannermen_power']} ball ({res['bannermen_count']} ta xonadon)!"

    ally_info = ""
    if res.get("ally_support_power", 0) > 0:
        ally_info = f"\n💍 **Ittifoqdosh himoyasi:** {res['ally_house_name']} xonadoni +{res['ally_support_power']} mudofaa kuchi berdi!"

    survivors_note = ""
    if res.get("attacker_survivors"):
        surv = res["attacker_survivors"]
        surv_parts = []
        if surv.get("soldiers", 0) > 0:
            surv_parts.append(f"{surv['soldiers']} askar")
        if surv.get("archers", 0) > 0:
            surv_parts.append(f"{surv['archers']} kamonchi")
        if surv.get("cavalry", 0) > 0:
            surv_parts.append(f"{surv['cavalry']} otliq")
        if surv_parts:
            survivors_note = f"\n🛡 **Qal'aga omon qaytgan qo'shinlar:** {', '.join(surv_parts)}"

    if res["attacker_won"]:
        report = (
            f"🎉 **BUYUK G'ALABA! VALERIYA QON BILAN SUG'ORILDI!** 🩸\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{res['attacker_house']}**\n"
            f"🛡 Himoyachi: **{res['defender_house']}**\n\n"
            f"⚡️ Jangdagi zarba kuchi: **{res['attacker_power']}** vs **{res['defender_power']}**{bannermen_info}{ally_info}\n"
            f"🗡 Qurbon bo'lgan askarlaringiz: **{res['attacker_loss']} ta**\n"
            f"💀 Dushmanning yo'qotishlari: **{res['defender_loss']} ta** askar{survivors_note}\n"
            f"💰 Qo'lga kiritilgan o'lja: **+{res['loot_gold']} 🪙**\n\n"
            f"👑 **SIYOSIY NATIJA:**\n"
            f"**{res['defender_house']}** xonadoni tizzaga cho'kdi va sizning **VASSALINGIZGA** aylandi! "
            f"Endi siz ulardan muntazam soliq yig'ib olasiz.\n\n"
            f"❄️ *Muzlash holati:* Jangda qatnashgan ajdarlaringiz **3 kunga muzladi**."
        )
    else:
        reward_bannermen_note = "\n💰 *Yordamga kelgan barcha bayroqdorlarga +30 🪙 mukofot berildi!*" if res.get("bannermen_count", 0) > 0 else ""
        report = (
            f"💀 **MAG'LUBIYAT! HUJUM QAYTARILDI!** 🛡\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{res['attacker_house']}**\n"
            f"🛡 Himoyachi: **{res['defender_house']}**\n\n"
            f"⚡️ Jangdagi zarba kuchi: **{res['attacker_power']}** vs **{res['defender_power']}**{bannermen_info}\n"
            f"🗡 Halok bo'lgan askarlaringiz: **{res['attacker_loss']} ta**\n"
            f"🛡 Qal'a va uning bayroqdorlari hujumni muvaffaqiyatli qaytardi!{reward_bannermen_note}{survivors_note}\n\n"
            f"❄️ *Muzlash holati:* Jangda qatnashgan ajdarlaringiz **3 kunga muzladi**."
        )

    await callback.message.edit_text(report, parse_mode="Markdown")
    await callback.answer("Jang yakunlandi!")

    # Himoyachiga ham jang hisobotini yuborish
    if res.get("defender_id"):
        try:
            res_status_str = "💀 Mag'lubiyatga uchradingiz" if res['attacker_won'] else "🛡 Hujumni muvaffaqiyatli qaytardingiz!"
            loot_str = f"Boy berilgan oltin: -{res['loot_gold']} 🪙\n" if res['attacker_won'] else ""
            def_alert = (
                f"⚔️ **QAL'ANGIZGA QILINGAN HUJUM YAKUNLANDI!**\n\n"
                f"Hujumchi: **{res['attacker_house']}**\n"
                f"Natija: {res_status_str}\n"
                f"Talafot: -{res['defender_loss']} askar\n"
                f"{loot_str}"
            )
            await callback.bot.send_message(res["defender_id"], def_alert, parse_mode="Markdown")
        except Exception:
            pass

@router.callback_query(F.data.in_(["bt_cancel", "bt_back_menu"]))
async def callback_battle_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Bekor qilindi.")

# Call to Arms (Regional Lord uchun)
@router.callback_query(F.data.startswith("trigger_cta:"))
async def callback_trigger_cta(callback: types.CallbackQuery):
    target_house_id = int(callback.data.split(":")[1])
    target_house = await get_house_by_id(target_house_id)
    user_house = await get_user_house(callback.from_user.id)

    if not target_house:
        await callback.answer("Xonadon topilmadi!", show_alert=True)
        return

    region = target_house["region"]
    call_id = await create_call_to_arms(target_house_id, callback.from_user.id, user_house["id"], region)

    bannermen = await get_region_bannermen(region)
    reg_info = REGIONS.get(region, {})
    sent_count = 0

    for bm in bannermen:
        if bm["owner_id"] and bm["owner_id"] != callback.from_user.id:
            try:
                alert_text = (
                    f"🎺 **SHOSHILINCH CHORLOV (CALL TO ARMS)!**\n\n"
                    f"Hurmatli Lord! Bizning **{reg_info.get('name', '')}** Hudud Lordimiz "
                    f"**{target_house['name']}** xonadoniga dushman (**{user_house['name']}**) hujum qilmoqda!\n\n"
                    f"Lordimizni himoya qilish uchun qo'shin jo'natasizmi?\n"
                    f"*(Armiyangizning 30% kuchi himoyaga qo'shiladi va g'alabadan so'ng sizga +30 🪙 mukofot beriladi)*"
                )
                await callback.bot.send_message(
                    bm["owner_id"],
                    alert_text,
                    reply_markup=call_to_arms_bannermen_kb(call_id),
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception:
                pass

    await callback.answer(f"🎺 {sent_count} ta bayroqdor xonadonga yordam so'rovi yuborildi!", show_alert=True)

@router.callback_query(F.data.startswith("pledge_cta:"))
async def callback_pledge_cta(callback: types.CallbackQuery):
    call_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success, msg, power = await pledge_bannerman_support(call_id, user_id)
    if success:
        await callback.message.edit_text(
            f"🛡 **SADOQAT VA YORDAM!**\n\n{msg}\n\nLordimiz uchun mardonavor kurashing!",
            parse_mode="Markdown"
        )
        await callback.answer("Qo'shin jo'natildi! 🛡", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("decline_cta:"))
async def callback_decline_cta(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🙅 **Siz chorlovni rad etdingiz.** Qo'shinlaringiz o'z qal'angizda qoldi.",
        parse_mode="Markdown"
    )
    await callback.answer()
