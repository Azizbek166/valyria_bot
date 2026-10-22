import time
import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (
    get_or_create_user, get_user_house, get_user_army,
    get_user_beasts, calculate_player_power, get_vassals, get_house_by_id,
    get_region_bannermen, get_house_castle, get_house_alliance,
    get_house_all_alliances, set_user_custom_name, get_user
)
from keyboards import profile_custom_name_kb
from config import REGIONS, escape_md

logger = logging.getLogger(__name__)

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_name = State()

async def build_profile_text(user_id: int, telegram_user: types.User) -> str:
    user = await get_or_create_user(user_id, telegram_user.username, telegram_user.full_name)
    house = await get_user_house(user_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)
    power_info = await calculate_player_power(user_id)
    vassals = await get_vassals(user_id)

    castle = await get_house_castle(house["id"]) if house else None
    alliances = await get_house_all_alliances(house["id"]) if house else {"marriage": None, "strategic": None}

    # Xonadon va Hudud ma'lumotlari
    if house:
        reg_info = REGIONS.get(house.get("region", ""), {})
        reg_name = escape_md(reg_info.get("name", "Noma'lum"))
        tier = house.get("tier", "B")

        if house["id"] == 1:
            feudal_title = f"👑 **Oliy Qirol (The High King)** [{tier}-toifa]"
        elif house.get("is_regional_lord"):
            feudal_title = f"🛡 **Hudud Lordi ({escape_md(reg_info.get('title', ''))})** [{tier}-toifa]"
        else:
            feudal_title = f"🗡 **Bayroqdor (Bannerman)** [{tier}-toifa] — Lord: *{escape_md(reg_info.get('lord_name', ''))}*"

        house_name = f"**{escape_md(house['name'])}** (#{house['id']})"

        # Vassallik holati
        if house["overlord_id"]:
            overlord_house = await get_user_house(house["overlord_id"])
            overlord_name = escape_md(overlord_house["name"] if overlord_house else f"Lord ({house['overlord_id']})")
            vassal_status = f"⛓ **{overlord_name}** xonadonining vassali"
        else:
            vassal_status = "👑 **Mustaqil Oliy Xonadon**"

        # Hudud Lordi bo'lsa bayroqdorlar soni
        if house.get("is_regional_lord"):
            bannermen = await get_region_bannermen(house["region"])
            bannermen_status = f"\n🎺 **Sizning bayroqdorlaringiz:** {len(bannermen)} ta faol xonadon"
        else:
            bannermen_status = ""
    else:
        house_name = "❌ Tanlanmagan (🌋 Oila tanlash bo'limiga kiring)"
        reg_name = "—"
        feudal_title = "—"
        vassal_status = "—"
        bannermen_status = ""

    # Vassallar ro'yxati
    if vassals:
        vassals_str = ", ".join([f"**{escape_md(v['name'])}**" for v in vassals])
    else:
        vassals_str = "Hozircha yo'q"

    # Qal'a va Ittifoqlar
    castle_str = f"🏰 {castle['level']}-darajali Qal'a" if castle else "Mavjud emas"

    m = alliances.get("marriage")
    if m:
        is_h1 = m["house1_id"] == house["id"]
        m_house = escape_md(m["h2_name"] if is_h1 else m["h1_name"])
        m_lord = escape_md(m["u2_name"] if is_h1 else m["u1_name"])
        marriage_str = f"**{m_house}** (Lord: {m_lord})"
    else:
        marriage_str = "Tuzilmagan"

    s = alliances.get("strategic")
    if s:
        is_h1 = s["house1_id"] == house["id"]
        s_house = escape_md(s["h2_name"] if is_h1 else s["h1_name"])
        s_lord = escape_md(s["u2_name"] if is_h1 else s["u1_name"])
        strategic_str = f"**{s_house}** (Lord: {s_lord})"
    else:
        strategic_str = "Tuzilmagan"

    # Valeriya po'lati
    valyrian_steel = (user.get("valyrian_steel", 0) or 0)
    valyrian_str = f"{valyrian_steel} dona ⚔️ (✨ Cheksiz Chakra faol!)" if valyrian_steel >= 1 else "Mavjud emas"

    # Maxluqlar va muzlash holati
    now = int(time.time())
    dragons_info = []
    dragons = [b for b in beasts if b["beast_type"] == "dragon"]
    spiders = [b for b in beasts if b["beast_type"] == "spider"]

    for d in dragons:
        d_name = escape_md(d['name'])
        if d["frozen_until"] > now:
            rem = d["frozen_until"] - now
            hours = rem // 3600
            mins = (rem % 3600) // 60
            dragons_info.append(f"🐲 {d_name} ({d['grade']}-daraja, {d['power']} ball) [❄️ Muzlagan: {hours}s {mins}d]")
        else:
            dragons_info.append(f"🐲 {d_name} ({d['grade']}-daraja, {d['power']} ball) [🔥 Faol]")

    dragons_str = "\n   ".join(dragons_info) if dragons_info else "Mavjud emas"
    spiders_str = f"{len(spiders)} ta (Har biri 500 ball, Jami: {len(spiders) * 500} ball)" if spiders else "Mavjud emas"

    essos_units = []
    if army.get('unsullied', 0) > 0:
        essos_units.append(f"🛡 Benuqson: {army['unsullied']} ta (Kuch: {army['unsullied'] * 5})")
    if army.get('faceless', 0) > 0:
        essos_units.append(f"🥷 Yuzsiz qotil: {army['faceless']} ta (Kuch: {army['faceless'] * 300})")
    if army.get('shadow', 0) > 0:
        essos_units.append(f"👣 Soya qotil: {army['shadow']} ta (Kuch: {army['shadow'] * 400})")
    if army.get('poison', 0) > 0:
        essos_units.append(f"🧪 Zahar: {army['poison']} ta (Kuch: {army['poison'] * 300})")
    essos_str = ("\n  " + "\n  ".join(essos_units)) if essos_units else ""

    # Lord ismi
    custom_name = user.get("custom_name")
    if custom_name:
        display_lord = f"Lord **{escape_md(custom_name)}**"
    else:
        display_lord = f"Lord **{escape_md(telegram_user.full_name)}**"

    profile_text = (
        f"🏛 **XONADON PROFILI: {display_lord}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 **Xonadon:** {house_name}\n"
        f"🗺 **Hudud:** {reg_name}\n"
        f"🎖 **Maqom:** {feudal_title}{bannermen_status}\n"
        f"👑 **Siyosiy mavqe:** {vassal_status}\n"
        f"🏰 **Qal'a:** {castle_str}\n"
        f"💍 **Sulolaviy Nikoh:** {marriage_str}\n"
        f"🤝 **Manfaatli Ittifoq:** {strategic_str}\n"
        f"⛓ **Sizning vassallaringiz:** {vassals_str}\n\n"
        f"💰 **Xazina (Oltin):** {user['gold']} 🪙\n"
        f"⚔️ **Valeriya Po'lati:** {valyrian_str}\n"
        f"⚡️ **JAMI FAOL KUCH:** **{power_info['total_active_power']} ball**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡 **ARMIYA TARKIBI:**\n"
        f"  🗡 Oddiy askar: {army.get('soldiers', 0)} ta (Kuch: +{army.get('soldiers', 0)})\n"
        f"  🏹 Kamonchi: {army.get('archers', 0)} ta (Kuch: +{army.get('archers', 0) * 3})\n"
        f"  🐎 Otliq: {army.get('cavalry', 0)} ta (Kuch: +{army.get('cavalry', 0) * 6})\n"
        f"  ✨ Chakra: {army.get('chakra', 0)} ta (Kuch: +{army.get('chakra', 0) * (4 if valyrian_steel >= 1 else 2)})\n"
        f"  🛡 Tilla plash: {army.get('gold_cloaks', 0)} ta (Kuch: +{army.get('gold_cloaks', 0) * 3})"
        f"{essos_str}\n\n"
        f"🐉 **MAXLUQLAR VA AJDARLAR:**\n"
        f"  {dragons_str}\n"
        f"  🕷 O'rgimchaklar: {spiders_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"ℹ️ *Eslatma: Jangda qatnashgan ajdarlar 3 kunga muzlaydi.*"
    )
    return profile_text

@router.message(F.text == "👤 Profil")
async def show_profile(message: types.Message):
    try:
        profile_text = await build_profile_text(message.from_user.id, message.from_user)
        await message.answer(profile_text, reply_markup=profile_custom_name_kb(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Profil ko'rsatishda xatolik: {e}", exc_info=True)
        await message.answer("👤 Profil ma'lumotlarini yuklashda xatolik yuz berdi.")

# --- Profilga Lord ismini qo'yish ---

@router.callback_query(F.data == "profile_change_name")
async def callback_profile_change_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ProfileStates.waiting_for_name)
    text = (
        "👑 **YANGI LORD ISMINGIZNI KIRITING:**\n\n"
        "Qadimgi Valeriya olamida boshqa Lordlar sizni qanday nom bilan atashini xohlaysiz?\n"
        "(Masalan: *Daemon Targaryen*, *Aegon The Conqueror*, *Lord Ronin*)\n\n"
        "📌 *Talab: 2 dan 32 tagacha belgi.*\n"
        "Bekor qilish uchun `/cancel` deb yozing."
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.message(ProfileStates.waiting_for_name, F.text)
async def process_custom_name(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Ismni o'zgartirish bekor qilindi.")
        return

    success, msg = await set_user_custom_name(message.from_user.id, message.text)
    if success:
        await state.clear()
        clean_name = escape_md(message.text.strip())
        await message.answer(
            f"👑 **Ajoyib! Sizning yangi Lord ismingiz o'rnatildi:**\n"
            f"🌟 **{clean_name}**\n\n"
            f"Ushbu ism profilingizda, xonadonlar ro'yxatida va umumiy reytingda aks etadi!",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"⚠️ {msg}\nIltimos, qaytadan boshqa nom kiriting:")

@router.message(Command("setname"))
async def cmd_setname(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Format: `/setname <yangi_ism>`\nMasalan: `/setname Daemon Targaryen`", parse_mode="Markdown")
        return

    new_name = parts[1].strip()
    success, msg = await set_user_custom_name(message.from_user.id, new_name)
    if success:
        clean_name = escape_md(new_name)
        await message.answer(
            f"👑 **Ismingiz o'zgartirildi:** **{clean_name}**!",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"⚠️ {msg}")
