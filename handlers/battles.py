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
    get_battle_by_id, get_war_status, set_battle_defense_troops
)
from keyboards import (
    battle_confirm_kb, call_to_arms_bannermen_kb,
    battle_army_select_kb, active_battle_status_kb,
    defense_army_select_kb
)
from config import REGIONS, UNITS, BATTLE_DURATION_SECONDS

router = Router()

class BattleState(StatesGroup):
    selecting_army = State()
    waiting_for_custom_input = State()
    defending_castle = State()

def format_army_selection_text(
    target_house: dict,
    user_house: dict,
    army: dict,
    selected: dict,
    active_dragons: list,
    include_dragons: bool,
    active_spiders: list,
    include_spiders: bool,
    valyrian_steel: int,
    include_valyrian: bool,
    strike_poison: bool,
    strike_faceless: bool,
    strike_shadow: bool
) -> tuple[str, int]:
    effective_valyrian = valyrian_steel if include_valyrian else 0
    chakra_mult = 2 if effective_valyrian >= 1 else 1

    power = (
        selected.get("soldiers", 0) * UNITS["soldier"]["atk"] +
        selected.get("archers", 0) * UNITS.get("archer", {}).get("atk", 3) +
        selected.get("cavalry", 0) * UNITS.get("cavalry", {}).get("atk", 6) +
        selected.get("chakra", 0) * UNITS["chakra"]["atk"] * chakra_mult +
        selected.get("gold_cloaks", 0) * UNITS["gold_cloak"]["atk"] +
        selected.get("unsullied", 0) * UNITS["unsullied"]["atk"] +
        (effective_valyrian * 500)
    )

    dragons_power = 0
    if include_dragons and active_dragons:
        dragons_power = sum(d.get("power", 500) for d in active_dragons)
        power += dragons_power

    spiders_power = 0
    if include_spiders and active_spiders:
        spiders_power = sum(s.get("power", 500) for s in active_spiders)
        power += spiders_power

    target_reg = REGIONS.get(target_house.get("region", ""), {})

    text = (
        f"⚔️ **HUJUM TARKIBINI SHAKLLANTIRISH (QO'SHIN TANLASH)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Nishingoh: **{target_house['name']}** (#{target_house['id']})\n"
        f"🌍 Hudud: **{target_reg.get('name', '')}**\n\n"
        f"📋 **Jangga yuborilayotgan kuchlar:**\n"
        f"• 🗡 Oddiy askar: **{selected.get('soldiers', 0)}** ta (mavjud: {army.get('soldiers', 0)})\n"
    )
    if army.get("archers", 0) > 0:
        text += f"• 🏹 Kamonchi: **{selected.get('archers', 0)}** ta (mavjud: {army.get('archers', 0)})\n"
    if army.get("cavalry", 0) > 0:
        text += f"• 🐎 Otliq: **{selected.get('cavalry', 0)}** ta (mavjud: {army.get('cavalry', 0)})\n"
    if army.get("chakra", 0) > 0:
        text += f"• ⚙️ Chakra: **{selected.get('chakra', 0)}** ta (mavjud: {army.get('chakra', 0)})\n"
    if army.get("gold_cloaks", 0) > 0:
        text += f"• 🟡 Tilla plash: **{selected.get('gold_cloaks', 0)}** ta (mavjud: {army.get('gold_cloaks', 0)})\n"
    if army.get("unsullied", 0) > 0:
        text += f"• 🛡 Benuqson: **{selected.get('unsullied', 0)}** ta (mavjud: {army.get('unsullied', 0)})\n"
    if valyrian_steel > 0:
        v_tag = f"✅ Jangga olingan (+{effective_valyrian * 500} ball, Chakra x{chakra_mult})" if include_valyrian else "❌ Qal'ada qoldirilgan"
        text += f"• ⚔️ Valeriya po'lati: {v_tag}\n"
    if active_dragons:
        d_tag = f"✅ **{len(active_dragons)} ta ajdar** (+{dragons_power} ball)" if include_dragons else "❌ Qal'ada qoldirilgan"
        text += f"• 🐲 Ajdarlar: {d_tag}\n"
    if active_spiders:
        s_tag = f"✅ **{len(active_spiders)} ta o'rgamchak** (+{spiders_power} ball)" if include_spiders else "❌ Qal'ada qoldirilgan"
        text += f"• 🕷 O'rgamchaklar: {s_tag}\n"

    strikes = []
    if strike_poison:
        strikes.append("🧪 **Zahar Hujumi:** Dushman mudofaasini 25% pasaytiradi")
    if strike_faceless:
        strikes.append("🥷 **Yuzsiz Qotil:** Dushman mudofaasini 30% buzib o'tadi")
    if strike_shadow:
        strikes.append("👣 **Soya Qotili:** Dushmanning 1 ta ajdarini o'ldiradi!")

    if strikes:
        text += "\n💥 **Pastki Panel Taktik Zarbalari:**\n" + "\n".join([f"• {st}" for st in strikes]) + "\n"

    text += (
        f"\n⚡️ **Umumiy zarba quvvati:** **{power} ball**\n"
        f"⏳ **Jang davomiyligi:** **7 daqiqa** (420 soniya)\n\n"
        f"⚠️ *Eslatma: Faqat jangga yuborilgan qo'shinlar talafot ko'radi. Qal'angizda qolgan kuchlaringiz xavfsiz saqlanadi!*"
    )
    return text, power

def format_defense_selection_text(
    battle: dict,
    defender_house: dict,
    army: dict,
    selected: dict,
    active_dragons: list,
    include_dragons: bool,
    active_spiders: list,
    include_spiders: bool,
    valyrian_steel: int,
    include_valyrian: bool
) -> tuple[str, int]:
    effective_valyrian = valyrian_steel if include_valyrian else 0
    chakra_mult = 2 if effective_valyrian >= 1 else 1

    power = (
        selected.get("soldiers", 0) * UNITS["soldier"]["def"] +
        selected.get("archers", 0) * UNITS.get("archer", {}).get("def", 5) +
        selected.get("cavalry", 0) * UNITS.get("cavalry", {}).get("def", 4) +
        selected.get("chakra", 0) * UNITS["chakra"]["def"] * chakra_mult +
        selected.get("gold_cloaks", 0) * UNITS["gold_cloak"]["def"] +
        selected.get("unsullied", 0) * UNITS["unsullied"]["def"] +
        (effective_valyrian * 500)
    )

    dragons_power = 0
    if include_dragons and active_dragons:
        dragons_power = sum(d.get("power", 500) for d in active_dragons)
        power += dragons_power

    spiders_power = 0
    if include_spiders and active_spiders:
        spiders_power = sum(s.get("power", 500) for s in active_spiders)
        power += spiders_power

    rem_min = battle.get("left_seconds", 0) // 60
    rem_sec = battle.get("left_seconds", 0) % 60

    text = (
        f"🛡 **QAL'ANI HIMOYALASH — MUDOFAA SAFLARI** 🏰\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ Hujum qiluvchi dushman: **{battle.get('attacker_house_name', 'Dushman')}**\n"
        f"🏰 Qal'angiz: **{defender_house.get('name', '')}** (#{defender_house.get('id', 0)})\n"
        f"⏳ Dushman yetib kelishiga: **{rem_min} daqiqa {rem_sec} soniya** qoldi!\n\n"
        f"📋 **Mudofaa devoriga safarbar etilayotgan kuchlar:**\n"
        f"• 🗡 Askar: **{selected.get('soldiers', 0)}** ta (mavjud: {army.get('soldiers', 0)})\n"
    )
    if army.get("archers", 0) > 0:
        text += f"• 🏹 Kamonchi: **{selected.get('archers', 0)}** ta (mavjud: {army.get('archers', 0)})\n"
    if army.get("cavalry", 0) > 0:
        text += f"• 🐎 Otliq: **{selected.get('cavalry', 0)}** ta (mavjud: {army.get('cavalry', 0)})\n"
    if army.get("chakra", 0) > 0:
        text += f"• ⚙️ Chakra: **{selected.get('chakra', 0)}** ta (mavjud: {army.get('chakra', 0)})\n"
    if army.get("gold_cloaks", 0) > 0:
        text += f"• 🟡 Tilla plash: **{selected.get('gold_cloaks', 0)}** ta (mavjud: {army.get('gold_cloaks', 0)})\n"
    if army.get("unsullied", 0) > 0:
        text += f"• 🛡 Benuqson: **{selected.get('unsullied', 0)}** ta (mavjud: {army.get('unsullied', 0)})\n"
    if valyrian_steel > 0:
        v_tag = f"✅ Safarbar etilgan (+{effective_valyrian * 500} ball, Chakra x{chakra_mult})" if include_valyrian else "❌ Qal'ada qoldirilgan"
        text += f"• ⚔️ Valeriya po'lati: {v_tag}\n"
    if active_dragons:
        d_tag = f"✅ **{len(active_dragons)} ta ajdar** (+{dragons_power} ball)" if include_dragons else "❌ Qal'ada qoldirilgan"
        text += f"• 🐲 Ajdarlar: {d_tag}\n"
    if active_spiders:
        s_tag = f"✅ **{len(active_spiders)} ta o'rgamchak** (+{spiders_power} ball)" if include_spiders else "❌ Qal'ada qoldirilgan"
        text += f"• 🕷 O'rgamchaklar: {s_tag}\n"

    text += (
        f"\n⚡️ **Mudofaa zarba quvvati:** **{power} ball**\n\n"
        f"⚠️ *Eslatma: Faqat mudofaaga safarbar etilgan kuchlar jangda qatnashadi va talafot ko'radi. Qolgan zaxirangiz xavfsiz qoladi!*"
    )
    return text, power

async def refresh_army_selection_ui(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0

    selected = data.get("selected_troops", {})
    include_dragons = data.get("include_dragons", True)
    include_spiders = data.get("include_spiders", True)
    include_valyrian = data.get("include_valyrian", True)
    strike_poison = data.get("strike_poison", False)
    strike_faceless = data.get("strike_faceless", False)
    strike_shadow = data.get("strike_shadow", False)
    can_call_bannermen = data.get("can_call_bannermen", False)
    call_id = data.get("call_id", 0)

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian,
        strike_poison=strike_poison,
        strike_faceless=strike_faceless,
        strike_shadow=strike_shadow
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian,
        strike_poison=strike_poison,
        strike_faceless=strike_faceless,
        strike_shadow=strike_shadow,
        can_call_bannermen=can_call_bannermen,
        call_id=call_id
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass

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

    # Urush holati (Sulh davri) tekshiruvi
    if not await get_war_status():
        text = (
            "🕊 **HOZIRDA VALERIYADA SULH DAVRI E'LON QILINGAN!**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Admin tomonidan barcha janglar va urushlar vaqtinchalik to'xtatilgan.\n"
            "Hozirda barcha Valeriya xonadonlari o'rtasida tinchlik bitimi amalda.\n\n"
            "🏰 Qal'angizni rivojlantiring, armiyangizni to'ldiring va Sword Bankdan yangi askarlar yollab turing!\n"
            "Admin urushni qayta ochgach, jang maydoni yana faollashadi."
        )
        await message.answer(text, parse_mode="Markdown")
        return

    # Faol jang bormi tekshirish (7 daqiqalik davom etayotgan jang)
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
        f"1. ⏳ **Hujum vaqti:** Har bir jang **7 daqiqa** davom etadi. Shu vaqt mobaynida qo'shinlar yurish qiladi.\n"
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
    if not await get_war_status():
        await callback.answer("🕊 Valeriyada sulh davri e'lon qilingan! Urush vaqtincha to'xtatilgan.", show_alert=True)
        return

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
        await callback.answer("Sizda jangga kiradigan askar yoki maxluq yo'q!", show_alert=True)
        return

    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0

    selected_troops = {
        "soldiers": army.get("soldiers", 0),
        "archers": army.get("archers", 0),
        "cavalry": army.get("cavalry", 0),
        "chakra": army.get("chakra", 0),
        "gold_cloaks": army.get("gold_cloaks", 0),
        "unsullied": army.get("unsullied", 0),
        "faceless": 0,
        "shadow": 0,
        "poison": 0,
        "dragon_ids": [d["id"] for d in active_dragons],
        "spider_ids": [s["id"] for s in active_spiders]
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
        include_spiders=True,
        include_valyrian=True,
        strike_poison=False,
        strike_faceless=False,
        strike_shadow=False,
        can_call_bannermen=can_call_bannermen
    )

    text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected_troops,
        active_dragons=active_dragons,
        include_dragons=True,
        active_spiders=active_spiders,
        include_spiders=True,
        valyrian_steel=valyrian_steel,
        include_valyrian=True,
        strike_poison=False,
        strike_faceless=False,
        strike_shadow=False
    )

    kb = battle_army_select_kb(
        target_house_id=house_id,
        army=army,
        selected=selected_troops,
        active_dragons=active_dragons,
        include_dragons=True,
        active_spiders=active_spiders,
        include_spiders=True,
        valyrian_steel=valyrian_steel,
        include_valyrian=True,
        strike_poison=False,
        strike_faceless=False,
        strike_shadow=False,
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
    await refresh_army_selection_ui(callback, state)
    await callback.answer(f"{unit_type.capitalize()}: {current} ta")

@router.callback_query(F.data.startswith("bt_toggle:"), BattleState.selecting_army)
async def callback_battle_toggle(callback: types.CallbackQuery, state: FSMContext):
    toggle_key = callback.data.split(":")[1]
    data = await state.get_data()

    if toggle_key == "dragons":
        val = not data.get("include_dragons", True)
        await state.update_data(include_dragons=val)
        ans = "Ajdarlar holati o'zgartirildi!"
    elif toggle_key == "spiders":
        val = not data.get("include_spiders", True)
        await state.update_data(include_spiders=val)
        ans = "O'rgamchaklar holati o'zgartirildi!"
    elif toggle_key == "valyrian":
        val = not data.get("include_valyrian", True)
        await state.update_data(include_valyrian=val)
        ans = "Valeriya po'lati holati o'zgartirildi!"
    elif toggle_key == "strike_poison":
        val = not data.get("strike_poison", False)
        await state.update_data(strike_poison=val)
        ans = "Zahar hujumi yoqildi! (-25% mudofaa)" if val else "Zahar hujumi o'chirildi!"
    elif toggle_key == "strike_faceless":
        val = not data.get("strike_faceless", False)
        await state.update_data(strike_faceless=val)
        ans = "Yuzsiz qotil hujumi yoqildi! (-30% mudofaa)" if val else "Yuzsiz qotil hujumi o'chirildi!"
    elif toggle_key == "strike_shadow":
        val = not data.get("strike_shadow", False)
        await state.update_data(strike_shadow=val)
        ans = "Soya qotili hujumi (1 Ajdarni o'ldirish) yoqildi!" if val else "Soya qotili hujumi o'chirildi!"
    else:
        ans = "Yangilandi"

    await refresh_army_selection_ui(callback, state)
    await callback.answer(ans)

@router.callback_query(F.data == "bt_preset:all", BattleState.selecting_army)
async def callback_battle_preset_all(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]

    selected = {
        "soldiers": army.get("soldiers", 0),
        "archers": army.get("archers", 0),
        "cavalry": army.get("cavalry", 0),
        "chakra": army.get("chakra", 0),
        "gold_cloaks": army.get("gold_cloaks", 0),
        "unsullied": army.get("unsullied", 0),
        "faceless": 0,
        "shadow": 0,
        "poison": 0,
        "dragon_ids": [d["id"] for d in active_dragons],
        "spider_ids": [s["id"] for s in active_spiders]
    }
    await state.update_data(
        selected_troops=selected,
        include_dragons=True,
        include_spiders=True,
        include_valyrian=True,
        strike_poison=(army.get("poison", 0) > 0),
        strike_faceless=(army.get("faceless", 0) > 0),
        strike_shadow=(army.get("shadow", 0) > 0)
    )
    await refresh_army_selection_ui(callback, state)
    await callback.answer("Barcha mavjud kuchlar tanlandi!")

@router.callback_query(F.data == "bt_preset:zero", BattleState.selecting_army)
async def callback_battle_preset_zero(callback: types.CallbackQuery, state: FSMContext):
    selected = {
        "soldiers": 0, "archers": 0, "cavalry": 0,
        "chakra": 0, "gold_cloaks": 0, "unsullied": 0,
        "faceless": 0, "shadow": 0, "poison": 0,
        "dragon_ids": [],
        "spider_ids": []
    }
    await state.update_data(
        selected_troops=selected,
        include_dragons=False,
        include_spiders=False,
        include_valyrian=False,
        strike_poison=False,
        strike_faceless=False,
        strike_shadow=False
    )
    await refresh_army_selection_ui(callback, state)
    await callback.answer("Tanlov tozalandi!")

@router.callback_query(F.data == "bt_custom_input", BattleState.selecting_army)
async def callback_battle_custom_input(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BattleState.waiting_for_custom_input)
    prompt = (
        "📝 **QO'SHIN MIQDORINI QO'LDA KIRITISH**\n\n"
        "Jangga yubormoqchi bo'lgan askarlarni ketma-ket bo'sh joy bilan yozing:\n"
        "`Oddiy_Askar Kamonchi Otliq Chakra Tilla_Plash Benuqson`\n\n"
        "Masalan: `50 15 5 20 10 30`\n"
        "*(50 ta askar, 15 ta kamonchi, 5 ta otliq, 20 chakra, 10 tilla plash, 30 benuqson)*"
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
        chk_cnt = int(parts[3]) if len(parts) > 3 else 0
        gc_cnt = int(parts[4]) if len(parts) > 4 else 0
        uns_cnt = int(parts[5]) if len(parts) > 5 else 0
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat sonlar yozing, masalan: `30 10 5 0 0 0`")
        return

    data = await state.get_data()
    selected = data.get("selected_troops", {})

    selected["soldiers"] = max(0, min(army.get("soldiers", 0), s_cnt))
    selected["archers"] = max(0, min(army.get("archers", 0), a_cnt))
    selected["cavalry"] = max(0, min(army.get("cavalry", 0), c_cnt))
    selected["chakra"] = max(0, min(army.get("chakra", 0), chk_cnt))
    selected["gold_cloaks"] = max(0, min(army.get("gold_cloaks", 0), gc_cnt))
    selected["unsullied"] = max(0, min(army.get("unsullied", 0), uns_cnt))

    await state.set_state(BattleState.selecting_army)
    await state.update_data(selected_troops=selected)

    target_house = await get_house_by_id(data["target_house_id"])
    user_house = await get_user_house(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0

    res_text, power = format_army_selection_text(
        target_house=target_house,
        user_house=user_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=data.get("include_dragons", True),
        active_spiders=active_spiders,
        include_spiders=data.get("include_spiders", True),
        valyrian_steel=valyrian_steel,
        include_valyrian=data.get("include_valyrian", True),
        strike_poison=data.get("strike_poison", False),
        strike_faceless=data.get("strike_faceless", False),
        strike_shadow=data.get("strike_shadow", False)
    )

    kb = battle_army_select_kb(
        target_house_id=data["target_house_id"],
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=data.get("include_dragons", True),
        active_spiders=active_spiders,
        include_spiders=data.get("include_spiders", True),
        valyrian_steel=valyrian_steel,
        include_valyrian=data.get("include_valyrian", True),
        strike_poison=data.get("strike_poison", False),
        strike_faceless=data.get("strike_faceless", False),
        strike_shadow=data.get("strike_shadow", False),
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

    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [b["id"] for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [b["id"] for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]

    if not data.get("include_dragons", True):
        selected_troops["dragon_ids"] = []
    else:
        selected_troops["dragon_ids"] = active_dragons

    if not data.get("include_spiders", True):
        selected_troops["spider_ids"] = []
    else:
        selected_troops["spider_ids"] = active_spiders

    selected_troops["include_valyrian"] = data.get("include_valyrian", True)
    selected_troops["poison_strike"] = data.get("strike_poison", False)
    selected_troops["faceless_strike"] = data.get("strike_faceless", False)
    selected_troops["shadow_strike"] = data.get("strike_shadow", False)

    success, msg, battle_id = await start_house_attack(user_id, target_house_id, selected_troops, call_id)
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    await state.clear()

    target_house = await get_house_by_id(target_house_id)
    user_house = await get_user_house(user_id)

    report_start = (
        f"🚀 **QO'SHIN JANGGA OT LANDI! (7 DAQIQA)** ⚔️\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Nishon: **{target_house['name']}**\n"
        f"⏳ **Yurish vaqti:** 7 daqiqa (420 soniya)\n\n"
        f"📋 **Safdagi kuchlar:**\n"
        f"• 🗡 Askar: **{selected_troops.get('soldiers', 0)}** ta\n"
        f"• 🏹 Kamonchi: **{selected_troops.get('archers', 0)}** ta\n"
        f"• 🐎 Otliq: **{selected_troops.get('cavalry', 0)}** ta\n"
        f"• ⚙️ Chakra: **{selected_troops.get('chakra', 0)}** ta\n"
        f"• 🟡 Tilla plash: **{selected_troops.get('gold_cloaks', 0)}** ta\n"
        f"• 🛡 Benuqson: **{selected_troops.get('unsullied', 0)}** ta\n"
        f"• 🐲 Ajdarlar: **{len(selected_troops.get('dragon_ids', []))}** ta\n"
        f"• 🕷 O'rgamchaklar: **{len(selected_troops.get('spider_ids', []))}** ta\n"
    )
    if selected_troops.get("include_valyrian"):
        report_start += "• ⚔️ Valeriya po'lati: Qo'shilgan (+500 ball, Chakra x2)\n"
    if selected_troops.get("poison_strike"):
        report_start += "• 🧪 Taktik zarba: Zahar Hujumi (-25% mudofaa)\n"
    if selected_troops.get("faceless_strike"):
        report_start += "• 🥷 Taktik zarba: Yuzsiz Qotil (-30% mudofaa)\n"
    if selected_troops.get("shadow_strike"):
        report_start += "• 👣 Taktik zarba: Soya Qotili (1 Ajdarni o'ldirish)\n"

    report_start += "\n🛡 *Qo'shinlaringiz dushman qal'asi tomon yo'l oldi. 7 daqiqa o'tgach natijani qabul qilib olishingiz mumkin!*"

    await callback.message.edit_text(
        report_start,
        reply_markup=active_battle_status_kb(battle_id, is_ready=False),
        parse_mode="Markdown"
    )
    await callback.answer("Qo'shin jangga otlandi! ⚔️", show_alert=True)

    # Himoyachiga faol mudofaa tugmasi bilan ogohlantirish yuborish
    if target_house and target_house.get("owner_id"):
        try:
            defender_msg = (
                f"🚨 **SHOSHILINCH OGOHLANTIRISH! QAL'ANGIZGA HUJUM!** ⚔️\n\n"
                f"Lord! Dushman **{user_house['name']}** xonadoni qo'shini sizning qal'angizga bostirib kelmoqda!\n"
                f"⏳ **Yetib kelish va javob berish vaqti: 7 DAQIQA!**\n\n"
                f"Qal'angizni mudofaa qilish uchun qaysi kuchlaringizni safarbar etasiz? "
                f"Quyidagi tugmani bosing va mudofaa rejangizni tuzing!\n"
                f"*(Agar mudofaa rejasini tuzmasangiz, 7 daqiqadan so'ng mavjud qal'a garnizoni avtomatik mudofaaga kirishadi)*"
            )
            def_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛡 Qal'ani Himoyalash (Mudofaa Rejasi)", callback_data=f"defend_battle:{battle_id}")]
            ])
            await callback.bot.send_message(target_house["owner_id"], defender_msg, reply_markup=def_kb, parse_mode="Markdown")
        except Exception:
            pass

    # 1. Lordlar o'z vassallarini himoya qilishi: Overlordga zudlik bilan xabar yuborish!
    if target_house and target_house.get("overlord_id") and target_house["overlord_id"] != user_id:
        try:
            overlord_msg = (
                f"🚨 **VASSALINGIZGA HUJUM BOSHLANDI!** ⚔️\n\n"
                f"Lord! Sizning vassalingiz bo'lgan **{target_house['name']}** qal'asiga dushman **{user_house['name']}** xonadoni hujum qildi!\n"
                f"🛡 Lord sifatida sizning armiyangizning **50% kuchi** avtomatik ravishda vassalingiz mudofaasiga safarbar etiladi!"
            )
            await callback.bot.send_message(target_house["overlord_id"], overlord_msg, parse_mode="Markdown")
        except Exception:
            pass

# --- Himoyachining Mudofaa Rejasi (Defense Formation Handlers) ---

@router.callback_query(F.data.startswith("defend_battle:"))
async def callback_defend_battle(callback: types.CallbackQuery, state: FSMContext):
    battle_id = int(callback.data.split(":")[1])
    battle = await get_battle_by_id(battle_id)
    if not battle or battle["status"] != "marching":
        await callback.answer("Jang yakunlangan yoki bekor qilingan!", show_alert=True)
        return

    now = int(time.time())
    if now >= battle["end_time"]:
        await callback.answer("Jang vaqti tugagan!", show_alert=True)
        return

    user_id = callback.from_user.id
    if battle.get("defender_id") != user_id:
        await callback.answer("Siz bu jangda himoyachi emassiz!", show_alert=True)
        return

    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0

    existing_def = battle.get("defender_troops")
    if not existing_def:
        selected = {
            "soldiers": army.get("soldiers", 0),
            "archers": army.get("archers", 0),
            "cavalry": army.get("cavalry", 0),
            "chakra": army.get("chakra", 0),
            "gold_cloaks": army.get("gold_cloaks", 0),
            "unsullied": army.get("unsullied", 0),
            "dragon_ids": [d["id"] for d in active_dragons],
            "spider_ids": [s["id"] for s in active_spiders]
        }
        include_dragons = True
        include_spiders = True
        include_valyrian = True
    else:
        selected = existing_def
        include_dragons = len(selected.get("dragon_ids", [])) > 0
        include_spiders = len(selected.get("spider_ids", [])) > 0
        include_valyrian = selected.get("include_valyrian", True)

    await state.set_state(BattleState.defending_castle)
    await state.update_data(
        def_battle_id=battle_id,
        selected_troops=selected,
        include_dragons=include_dragons,
        include_spiders=include_spiders,
        include_valyrian=include_valyrian
    )

    defender_house = await get_house_by_id(battle["defender_house_id"])
    text, power = format_defense_selection_text(
        battle=battle,
        defender_house=defender_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian
    )

    kb = defense_army_select_kb(
        battle_id=battle_id,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian
    )

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("def_adj:"), BattleState.defending_castle)
async def callback_defense_adjust(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    battle_id = int(parts[1])
    unit_type = parts[2]
    action = parts[3]

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

    battle = await get_battle_by_id(battle_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    defender_house = await get_house_by_id(battle["defender_house_id"])

    include_dragons = data.get("include_dragons", True)
    include_spiders = data.get("include_spiders", True)
    include_valyrian = data.get("include_valyrian", True)

    text, power = format_defense_selection_text(
        battle=battle,
        defender_house=defender_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian
    )

    kb = defense_army_select_kb(
        battle_id=battle_id,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer(f"{unit_type.capitalize()}: {current} ta")

@router.callback_query(F.data.startswith("def_toggle:"), BattleState.defending_castle)
async def callback_defense_toggle(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    battle_id = int(parts[1])
    toggle_key = parts[2]
    data = await state.get_data()

    if toggle_key == "dragons":
        val = not data.get("include_dragons", True)
        await state.update_data(include_dragons=val)
        ans = "Ajdarlar mudofaa holati o'zgartirildi!"
    elif toggle_key == "spiders":
        val = not data.get("include_spiders", True)
        await state.update_data(include_spiders=val)
        ans = "O'rgamchaklar mudofaa holati o'zgartirildi!"
    elif toggle_key == "valyrian":
        val = not data.get("include_valyrian", True)
        await state.update_data(include_valyrian=val)
        ans = "Valeriya po'lati holati o'zgartirildi!"
    else:
        ans = "Yangilandi"

    user_id = callback.from_user.id
    battle = await get_battle_by_id(battle_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    defender_house = await get_house_by_id(battle["defender_house_id"])

    updated_data = await state.get_data()
    selected = updated_data.get("selected_troops", {})
    include_dragons = updated_data.get("include_dragons", True)
    include_spiders = updated_data.get("include_spiders", True)
    include_valyrian = updated_data.get("include_valyrian", True)

    text, power = format_defense_selection_text(
        battle=battle,
        defender_house=defender_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian
    )

    kb = defense_army_select_kb(
        battle_id=battle_id,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=include_dragons,
        active_spiders=active_spiders,
        include_spiders=include_spiders,
        valyrian_steel=valyrian_steel,
        include_valyrian=include_valyrian
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer(ans)

@router.callback_query(F.data.startswith("def_preset:"), BattleState.defending_castle)
async def callback_defense_preset(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    battle_id = int(parts[1])
    preset = parts[2]
    user_id = callback.from_user.id
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [dict(b) for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [dict(b) for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]

    if preset == "all":
        selected = {
            "soldiers": army.get("soldiers", 0),
            "archers": army.get("archers", 0),
            "cavalry": army.get("cavalry", 0),
            "chakra": army.get("chakra", 0),
            "gold_cloaks": army.get("gold_cloaks", 0),
            "unsullied": army.get("unsullied", 0),
            "dragon_ids": [d["id"] for d in active_dragons],
            "spider_ids": [s["id"] for s in active_spiders]
        }
        await state.update_data(
            selected_troops=selected,
            include_dragons=True,
            include_spiders=True,
            include_valyrian=True
        )
        ans = "Barcha kuchlar mudofaaga safarbar etildi!"
    else:
        selected = {
            "soldiers": 0,
            "archers": 0,
            "cavalry": 0,
            "chakra": 0,
            "gold_cloaks": 0,
            "unsullied": 0,
            "dragon_ids": [],
            "spider_ids": []
        }
        await state.update_data(
            selected_troops=selected,
            include_dragons=False,
            include_spiders=False,
            include_valyrian=False
        )
        ans = "Mudofaa saflari tozalandi!"

    battle = await get_battle_by_id(battle_id)
    user_row = await get_user(user_id)
    valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
    defender_house = await get_house_by_id(battle["defender_house_id"])
    updated_data = await state.get_data()

    text, power = format_defense_selection_text(
        battle=battle,
        defender_house=defender_house,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=updated_data.get("include_dragons", True),
        active_spiders=active_spiders,
        include_spiders=updated_data.get("include_spiders", True),
        valyrian_steel=valyrian_steel,
        include_valyrian=updated_data.get("include_valyrian", True)
    )

    kb = defense_army_select_kb(
        battle_id=battle_id,
        army=army,
        selected=selected,
        active_dragons=active_dragons,
        include_dragons=updated_data.get("include_dragons", True),
        active_spiders=active_spiders,
        include_spiders=updated_data.get("include_spiders", True),
        valyrian_steel=valyrian_steel,
        include_valyrian=updated_data.get("include_valyrian", True)
    )

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer(ans)

@router.callback_query(F.data.startswith("def_confirm:"), BattleState.defending_castle)
async def callback_defense_confirm(callback: types.CallbackQuery, state: FSMContext):
    battle_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected_troops = data.get("selected_troops", {})
    user_id = callback.from_user.id

    beasts = await get_user_beasts(user_id)
    now = int(time.time())
    active_dragons = [b["id"] for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    active_spiders = [b["id"] for b in beasts if b["beast_type"] == "spider" and b["frozen_until"] <= now]

    if not data.get("include_dragons", True):
        selected_troops["dragon_ids"] = []
    else:
        selected_troops["dragon_ids"] = active_dragons

    if not data.get("include_spiders", True):
        selected_troops["spider_ids"] = []
    else:
        selected_troops["spider_ids"] = active_spiders

    selected_troops["include_valyrian"] = data.get("include_valyrian", True)

    success, msg = await set_battle_defense_troops(battle_id, user_id, selected_troops)
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    await state.clear()
    battle = await get_battle_by_id(battle_id)
    rem_min = battle["left_seconds"] // 60 if battle else 0
    rem_sec = battle["left_seconds"] % 60 if battle else 0

    conf_text = (
        "🛡 **MUDOFAA REJANGIZ TASDIQLANDI!** ⚔️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Siz tanlagan barcha kuchlar qal'a devorlari va minoralariga safarbar etildi.\n\n"
        f"• 🗡 Askar: **{selected_troops.get('soldiers', 0)}** ta\n"
        f"• 🏹 Kamonchi: **{selected_troops.get('archers', 0)}** ta\n"
        f"• 🐎 Otliq: **{selected_troops.get('cavalry', 0)}** ta\n"
        f"• ⚙️ Chakra: **{selected_troops.get('chakra', 0)}** ta\n"
        f"• 🟡 Tilla plash: **{selected_troops.get('gold_cloaks', 0)}** ta\n"
        f"• 🛡 Benuqson: **{selected_troops.get('unsullied', 0)}** ta\n"
        f"• 🐲 Ajdarlar: **{len(selected_troops.get('dragon_ids', []))}** ta\n"
        f"• 🕷 O'rgamchaklar: **{len(selected_troops.get('spider_ids', []))}** ta\n\n"
        f"⏳ Dushman bilan to'qnashuvgacha: **{rem_min} daqiqa {rem_sec} soniya** qoldi.\n"
        "Lordimizga zafarlar tilaymiz!"
    )

    await callback.message.edit_text(conf_text, parse_mode="Markdown")
    await callback.answer("Mudofaa rejasi saqlandi! 🛡", show_alert=True)

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

    overlord_info = ""
    if res.get("overlord_support_power", 0) > 0:
        overlord_info = f"\n🛡 **Overlord Himoyasi:** Himoyachining Lordi ({res.get('overlord_name', 'Lord')}) 50% qo'shini bilan yordam berdi (+{res['overlord_support_power']} mudofaa kuchi)!"

    special_events = []
    if res.get("shadow_killed_dragon"):
        special_events.append(f"👣 **Soya Qotili Hujumi:** Dushmanning 1 ta ajdari ({res['shadow_killed_dragon']}) pistirmada o'ldirildi!")
    if res.get("witch_kill_dragons"):
        killed_d_str = ", ".join(res["witch_kill_dragons"])
        special_events.append(f"🧙 **Suv Jodugari Mudofaasi:** Dushmanning {len(res['witch_kill_dragons'])} ta ajdari ({killed_d_str}) butunlay halok qilindi!")
    if res.get("witch_kill_spiders"):
        killed_s_str = ", ".join(res["witch_kill_spiders"])
        special_events.append(f"🔮 **Soya Jodugari Mudofaasi:** Dushmanning {len(res['witch_kill_spiders'])} ta o'rgamchagi ({killed_s_str}) butunlay halok qilindi!")

    special_events_str = ("\n" + "\n".join(special_events)) if special_events else ""

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
        if surv.get("chakra", 0) > 0:
            surv_parts.append(f"{surv['chakra']} chakra")
        if surv.get("gold_cloaks", 0) > 0:
            surv_parts.append(f"{surv['gold_cloaks']} tilla plash")
        if surv.get("unsullied", 0) > 0:
            surv_parts.append(f"{surv['unsullied']} benuqson")
        if surv_parts:
            survivors_note = f"\n🛡 **Qal'aga omon qaytgan qo'shinlar:** {', '.join(surv_parts)}"

    # Resurslar va qo'shinlar taqsimoti (Hujum va Himoya)
    att_sent = res.get("attacker_troops_sent", {})
    att_loss = res.get("attacker_losses_detail", {})
    att_troops_str = []
    if att_sent.get("soldiers", 0) > 0:
        att_troops_str.append(f"🗡 Askar: {att_sent['soldiers']} ta (-{att_loss.get('soldiers', 0)})")
    if att_sent.get("archers", 0) > 0:
        att_troops_str.append(f"🏹 Kamonchi: {att_sent['archers']} ta (-{att_loss.get('archers', 0)})")
    if att_sent.get("cavalry", 0) > 0:
        att_troops_str.append(f"🐎 Otliq: {att_sent['cavalry']} ta (-{att_loss.get('cavalry', 0)})")
    if att_sent.get("chakra", 0) > 0:
        att_troops_str.append(f"⚙️ Chakra: {att_sent['chakra']} ta (-{att_loss.get('chakra', 0)})")
    if att_sent.get("gold_cloaks", 0) > 0:
        att_troops_str.append(f"🟡 Tilla plash: {att_sent['gold_cloaks']} ta (-{att_loss.get('gold_cloaks', 0)})")
    if att_sent.get("unsullied", 0) > 0:
        att_troops_str.append(f"🛡 Benuqson: {att_sent['unsullied']} ta (-{att_loss.get('unsullied', 0)})")
    if att_sent.get("dragon_ids"):
        att_troops_str.append(f"🐲 Ajdarlar: {len(att_sent['dragon_ids'])} ta (❄️ 72 soat muzladi)")
    if att_sent.get("spider_ids"):
        att_troops_str.append(f"🕷 O'rgamchaklar: {len(att_sent['spider_ids'])} ta (❄️ 28 soat muzladi)")
    if att_sent.get("include_valyrian"):
        att_troops_str.append("⚔️ Valeriya po'lati (+500)")

    def_sent = res.get("defender_troops_sent")
    def_loss = res.get("defender_losses_detail", {})
    def_troops_str = []
    if def_sent:
        if def_sent.get("soldiers", 0) > 0:
            def_troops_str.append(f"🗡 Askar: {def_sent['soldiers']} ta (-{def_loss.get('soldiers', 0)})")
        if def_sent.get("archers", 0) > 0:
            def_troops_str.append(f"🏹 Kamonchi: {def_sent['archers']} ta (-{def_loss.get('archers', 0)})")
        if def_sent.get("cavalry", 0) > 0:
            def_troops_str.append(f"🐎 Otliq: {def_sent['cavalry']} ta (-{def_loss.get('cavalry', 0)})")
        if def_sent.get("chakra", 0) > 0:
            def_troops_str.append(f"⚙️ Chakra: {def_sent['chakra']} ta (-{def_loss.get('chakra', 0)})")
        if def_sent.get("gold_cloaks", 0) > 0:
            def_troops_str.append(f"🟡 Tilla plash: {def_sent['gold_cloaks']} ta (-{def_loss.get('gold_cloaks', 0)})")
        if def_sent.get("unsullied", 0) > 0:
            def_troops_str.append(f"🛡 Benuqson: {def_sent['unsullied']} ta (-{def_loss.get('unsullied', 0)})")
        if def_sent.get("dragon_ids"):
            def_troops_str.append(f"🐲 Ajdarlar: {len(def_sent['dragon_ids'])} ta (❄️ 72 soat muzladi)")
        if def_sent.get("spider_ids"):
            def_troops_str.append(f"🕷 O'rgamchaklar: {len(def_sent['spider_ids'])} ta (❄️ 28 soat muzladi)")
        if def_sent.get("include_valyrian"):
            def_troops_str.append("⚔️ Valeriya po'lati (+500)")
    else:
        def_troops_str.append(f"🏰 Qal'a garnizoni — jami -{res['defender_loss']} ta yo'qotish")

    att_breakdown_block = "\n".join([f"  • {x}" for x in att_troops_str]) if att_troops_str else "  • Noma'lum"
    def_breakdown_block = "\n".join([f"  • {x}" for x in def_troops_str]) if def_troops_str else "  • Garnizon"

    breakdown_text = (
        f"\n📋 **JANG MAYDONIDAGI RESURSLAR VA SAFARBARLIK:**\n"
        f"⚔️ **Hujumchi ({res['attacker_house']}):**\n{att_breakdown_block}\n\n"
        f"🛡 **Himoyachi ({res['defender_house']}):**\n{def_breakdown_block}\n"
    )

    if res["attacker_won"]:
        if res.get("is_king_ascension"):
            political_result = (
                f"👑 **BUYUK TARIXIY VOQEA: OLIY QIROL TAXTI AG'DARILDI!** 🌋\n"
                f"Siz **Westerosning yangi OLIY QIROLISIZ** (#{1} Targaryen taxti sizga o'tdi)!\n"
                f"Sobiq Qirol esa taxtdan tushirilib, sizning avvalgi xonadoningizga ko'chirildi va sizga **VASSAL** bo'ldi!"
            )
        else:
            political_result = (
                f"👑 **SIYOSIY NATIJA:**\n"
                f"**{res['defender_house']}** xonadoni tizzaga cho'kdi va sizning **VASSALINGIZGA** aylandi! "
                f"Endi siz ulardan muntazam soliq yig'ib olasiz."
            )

        report = (
            f"🎉 **BUYUK G'ALABA! VALERIYA QON BILAN SUG'ORILDI!** 🩸\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{res['attacker_house']}**\n"
            f"🛡 Himoyachi: **{res['defender_house']}**\n\n"
            f"⚡️ Jangdagi zarba kuchi: **{res['attacker_power']}** vs **{res['defender_power']}**"
            f"{bannermen_info}{ally_info}{overlord_info}{special_events_str}\n"
            f"{breakdown_text}\n"
            f"🗡 Jami yo'qotilgan askarlaringiz: **-{res['attacker_loss']} ta**\n"
            f"💀 Dushmanning talafoti: **-{res['defender_loss']} ta** askar{survivors_note}\n"
            f"💰 Qo'lga kiritilgan o'lja: **+{res['loot_gold']} 🪙**\n\n"
            f"{political_result}\n\n"
            f"❄️ *Muzlash holati:* Jangda qatnashgan ajdarlaringiz **3 kunga (72 soat)**, o'rgamchaklaringiz esa **28 soatga** muzladi."
        )
    else:
        reward_bannermen_note = "\n💰 *Yordamga kelgan barcha bayroqdorlarga +30 🪙 mukofot berildi!*" if res.get("bannermen_count", 0) > 0 else ""
        report = (
            f"💀 **MAG'LUBIYAT! HUJUM QAYTARILDI!** 🛡\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{res['attacker_house']}**\n"
            f"🛡 Himoyachi: **{res['defender_house']}**\n\n"
            f"⚡️ Jangdagi zarba kuchi: **{res['attacker_power']}** vs **{res['defender_power']}**"
            f"{bannermen_info}{overlord_info}{special_events_str}\n"
            f"{breakdown_text}\n"
            f"🗡 Halok bo'lgan askarlaringiz: **-{res['attacker_loss']} ta**\n"
            f"🛡 Qal'a va uning himoyachilari hujumni muvaffaqiyatli qaytardi!{reward_bannermen_note}{survivors_note}\n\n"
            f"❄️ *Muzlash holati:* Jangda qatnashgan ajdarlaringiz **3 kunga (72 soat)**, o'rgamchaklaringiz esa **28 soatga** muzladi."
        )

    await callback.message.edit_text(report, parse_mode="Markdown")
    await callback.answer("Jang yakunlandi!")

    # Himoyachiga ham jang hisobotini yuborish
    if res.get("defender_id"):
        try:
            res_status_str = "💀 Mag'lubiyatga uchradingiz" if res['attacker_won'] else "🛡 Hujumni muvaffaqiyatli qaytardingiz!"
            loot_str = f"Boy berilgan oltin: -{res['loot_gold']} 🪙\n" if res['attacker_won'] else ""
            king_lost_str = "\n👑 **QIROLLIK TAXTI BOY BERILDI!** Dushman sizni taxtdan ag'dardi va siz endi yangi Qirolning vassalisiz!" if res.get("is_king_ascension") else ""
            def_alert = (
                f"⚔️ **QAL'ANGIZGA QILINGAN HUJUM YAKUNLANDI!**\n\n"
                f"Hujumchi: **{res['attacker_house']}**\n"
                f"Natija: {res_status_str}\n"
                f"{breakdown_text}\n"
                f"Umumiy talafot: -{res['defender_loss']} askar\n"
                f"{loot_str}{king_lost_str}"
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
