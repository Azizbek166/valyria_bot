from aiogram import Router, F, types
from database import (
    get_user_house, get_houses, get_house_by_id,
    choose_house, get_user, calculate_player_power,
    get_user_army, get_user_beasts
)
from keyboards import (
    houses_category_kb, houses_page_kb, house_action_kb
)
from config import REGIONS, escape_md
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "🌋 Oila tanlash")
async def choose_family_menu(message: types.Message):
    try:
        user_house = await get_user_house(message.from_user.id)
        if user_house:
            reg_info = REGIONS.get(user_house.get("region", ""), {})
            reg_name = escape_md(reg_info.get("name", "Valeriya"))
            h_name = escape_md(user_house.get("name", ""))
            role_name = "👑 Oliy Qirol" if user_house["id"] == 1 else ("🛡 Hudud Lordi" if user_house.get("is_regional_lord") else "🗡 Bayroqdor")

            await message.answer(
                f"👑 Siz allaqachon **{h_name}** xonadonini ({reg_name}) boshqarmoqdasiz!\n"
                f"Sizning maqomingiz: **{role_name}**.\n\n"
                f"Qoidaga ko'ra, har bir Lord faqat bitta xonadonga ega bo'lishi mumkin.",
                parse_mode="Markdown"
            )
            return

        text = (
            "🌋 **QADIMGI VALERIYA — 5 TA YIRIK HUDUD VA XONADONLAR**\n\n"
            "Valeriya 5 ta qudratli hududga bo'lingan:\n"
            "• **👑 Qirollik yerlari (1-10)** — Oliy Qirol: *Targaryen*\n"
            "• **🌋 Vulqonlar lordligi (11-20)** — Hudud Lordi: *Zaldrizar*\n"
            "• **🌲 Oʻrmon yerlari (21-30)** — Hudud Lordi: *Varezys*\n"
            "• **🔮 Jodugarlar yerlari (31-40)** — Hudud Lordi: *Maeraxes*\n"
            "• **🌊 Dengiz Qoʻriqchilari (41-52)** — Hudud Lordi: *Nyzarys*\n\n"
            "⚠️ *Diqqat: Har bir xonadonni faqat 1 kishi egallashi mumkin! "
            "Hudud Lordlari o'z bayroqdorlarini jangga va himoyaga chorlay oladilar.*\n\n"
            "Qaysi hudud xonadonlarini ko'rmoqchisiz?"
        )
        await message.answer(text, reply_markup=houses_category_kb(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Oila tanlash menyusida xatolik: {e}", exc_info=True)
        await message.answer("🌋 Oila tanlash menyusini yuklashda xatolik yuz berdi.")

@router.callback_query(F.data == "house_cats_back")
async def callback_house_cats_back(callback: types.CallbackQuery):
    text = (
        "🌋 **Qadimgi Valeriya — 5 ta Hudud:**\n\n"
        "Qaysi hudud xonadonlari ro'yxatini ko'rmoqchisiz?"
    )
    await callback.message.edit_text(text, reply_markup=houses_category_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("house_region:"))
async def callback_house_region_page(callback: types.CallbackQuery):
    _, region_key, page_str = callback.data.split(":")
    page = int(page_str)

    houses = await get_houses(region=region_key)
    user_house = await get_user_house(callback.from_user.id)
    user_house_id = user_house["id"] if user_house else None

    reg_info = REGIONS.get(region_key, {})
    reg_title = reg_info.get("name", "Hudud")
    reg_desc = reg_info.get("desc", "")
    lord_title = reg_info.get("title", "Hudud Lordi")

    text = (
        f"📜 **{reg_title}**\n"
        f"📍 *{reg_desc}*\n\n"
        f"🌟 — Hudud Lordi xonadoni\n"
        f"🟢 — Bo'sh xonadon (egallash mumkin)\n"
        f"🔒 — Band (o'yinchi boshqarmoqda)\n"
        f"👑 — Sizning xonadoningiz\n\n"
        f"Xonadon haqida batafsil ko'rish uchun tugmani bosing:"
    )

    kb = houses_page_kb(houses, region_key, page, user_house_id=user_house_id, page_size=12)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("h_detail:"))
async def callback_house_detail(callback: types.CallbackQuery):
    try:
        house_id = int(callback.data.split(":")[1])
        house = await get_house_by_id(house_id)
        if not house:
            await callback.answer("Xonadon topilmadi!", show_alert=True)
            return

        house_name = escape_md(house.get("name", "Noma'lum"))
        is_available = house["owner_id"] is None
        is_owner = house["owner_id"] == callback.from_user.id
        reg_info = REGIONS.get(house.get("region", ""), {})
        reg_title = escape_md(reg_info.get("name", "Noma'lum"))
        tier = house.get("tier", "B")
        tier_desc = f"🌟 **[{tier}-toifa]** (Hudud Lordi)" if tier == "A" else f"🛡 **[{tier}-toifa]** (Mintaqa xonadoni)"
        lord_title_name = escape_md(reg_info.get('lord_name', ''))

        if house["id"] == 1:
            role_desc = "👑 **Oliy Qirol (The High King)**"
        elif house.get("is_regional_lord"):
            role_desc = f"🛡 **Hudud Lordi ({escape_md(reg_info.get('title', ''))})**"
        else:
            role_desc = f"🗡 **Bayroqdor (Bannerman) xonadoni** — Hudud Lordi: {lord_title_name}"

        if house["owner_id"]:
            owner_user = await get_user(house["owner_id"])
            raw_name = owner_user.get("custom_name") or owner_user.get("full_name") if owner_user else f"Lord #{house['owner_id']}"
            clean_name = str(raw_name).replace("[", "").replace("]", "").replace("`", "").replace("*", "")
            u_raw = owner_user.get("username") if owner_user else None
            user_tag = f"@{escape_md(u_raw)}" if u_raw else f"[Profil](tg://user?id={house['owner_id']})"

            # Lord stats
            power_info = await calculate_player_power(house["owner_id"])
            owner_army = await get_user_army(house["owner_id"]) or {}
            owner_beasts = await get_user_beasts(house["owner_id"]) or []
            active_dragons = [b for b in owner_beasts if b.get("beast_type") == "dragon"]

            overlord_info = ""
            if house.get("overlord_id"):
                overlord_user = await get_user(house["overlord_id"])
                ov_raw = overlord_user.get("custom_name") or overlord_user.get("full_name") if overlord_user else f"#{house['overlord_id']}"
                ov_name = escape_md(ov_raw)
                ov_u = overlord_user.get("username") if overlord_user else None
                ov_u_str = f" (@{escape_md(ov_u)})" if ov_u else ""
                overlord_info = f"\n⛓ **Qaramlik (Vassal):** Lord **{ov_name}**{ov_u_str} xonadoniga qaram"

            castle_txt = f"{house['castle_level']}-darajali Qal'a" if house.get("castle_level") else "Qal'a hali qurilmagan"

            detail_text = (
                f"🏛 **XONADON: {house_name}** (#{house['id']})\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 **Hukmdor (Lord):** [{clean_name}](tg://user?id={house['owner_id']})\n"
                f"👤 **Lord Useri:** {user_tag} (ID: `{house['owner_id']}`)\n"
                f"⚡️ **Harbiy qudrati:** **{power_info.get('total_active_power', 0)} ball**\n"
                f"🗡 **Armiya:** {owner_army.get('soldiers', 0)} askar, {owner_army.get('archers', 0)} kamonchi, {owner_army.get('cavalry', 0)} otliq\n"
                f"🐲 **Ajdarlar:** {len(active_dragons)} ta\n"
                f"🏰 **Qal'a:** {castle_txt}\n"
                f"🗺 **Hudud:** **{reg_title}**\n"
                f"🎖 **Toifasi:** {tier_desc}\n"
                f"👑 **Maqomi:** {role_desc}{overlord_info}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            detail_text = (
                f"🏛 **XONADON: {house_name}** (#{house['id']})\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 **Holati:** **BO'SH (EGALLANMAGAN)**\n"
                f"👤 **Lord Useri:** *Hozircha bo'sh — Birinchi bo'lib egallashingiz mumkin!*\n"
                f"🗺 **Hudud:** **{reg_title}**\n"
                f"🎖 **Toifasi:** {tier_desc}\n"
                f"👑 **Maqomi:** {role_desc}\n"
                f"🏰 **Qal'a:** Hali qurilmagan\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )

        try:
            await callback.message.edit_text(
                detail_text,
                reply_markup=house_action_kb(house_id, is_available, is_owner),
                parse_mode="Markdown"
            )
        except Exception:
            safe_text = detail_text.replace("*", "").replace("`", "").replace("_", "")
            await callback.message.edit_text(
                safe_text,
                reply_markup=house_action_kb(house_id, is_available, is_owner)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Xonadon tafsilotlarida xatolik: {e}", exc_info=True)
        await callback.answer("Ma'lumotlarni yuklashda xatolik yuz berdi.", show_alert=True)

@router.callback_query(F.data.startswith("h_claim:"))
async def callback_house_claim(callback: types.CallbackQuery):
    house_id = int(callback.data.split(":")[1])
    success, msg = await choose_house(callback.from_user.id, house_id)
    if success:
        await callback.message.edit_text(msg, parse_mode="Markdown")
        await callback.answer("Muvaffaqiyatli tanlandi! 👑", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)

@router.message(F.text == "🛕 Uylar")
async def show_all_houses_overview(message: types.Message):
    try:
        houses = await get_houses()
        total = len(houses)
        occupied = len([h for h in houses if h.get("owner_id") is not None])
        free = total - occupied
        vassals_count = len([h for h in houses if h.get("overlord_id") is not None])

        lines = []
        for reg_key, reg in REGIONS.items():
            reg_houses = [h for h in houses if h.get("region") == reg_key]
            reg_occupied = len([h for h in reg_houses if h.get("owner_id") is not None])
            lord_house = next((h for h in reg_houses if h.get("is_regional_lord")), None)
            lord_owner_str = ""
            if lord_house and lord_house.get("owner_id"):
                u_raw = lord_house.get("owner_username")
                u_str = f" (@{escape_md(u_raw)})" if u_raw else ""
                o_name = escape_md(lord_house.get('owner_name') or 'Lord')
                lord_owner_str = f"👑 {o_name}{u_str}"
            else:
                lord_owner_str = "🟢 Bo'sh"

            tier = lord_house.get('tier', 'A') if lord_house else 'A'
            reg_name = escape_md(reg.get('name', ''))
            lord_title_name = escape_md(reg.get('lord_name', ''))
            lines.append(
                f"• **{reg_name}**: {reg_occupied}/{len(reg_houses)} band | Lord: {lord_title_name} [{tier}-toifa] ({lord_owner_str})"
            )

        overview_text = (
            f"🛕 **QADIMGI VALERIYA 5 TA HUDUDI VA UYLAR STATISTIKASI**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Umumiy holat:**\n"
            f"• Jami xonadonlar: **{total} ta** (5 ta hudud bo'ylab)\n"
            f"• Egallangan: **{occupied} ta** | Bo'sh: **{free} ta**\n"
            f"• Bo'ysundirilgan vassallar: **{vassals_count} ta**\n\n"
            f"👑 **Toifalar:**\n"
            f"• **[A-toifa]**: 5 ta Hudud Lordlari (#1 Targaryen, #11 Zaldrizar, #21 Varezys, #31 Maeraxes, #41 Nyzarys)\n"
            f"• **[B-toifa]**: Qolgan 47 ta xonadonlar (Bayroqdorlar)\n\n"
            f"🗺 **Hududlar bo'yicha taqsimot:**\n"
            + "\n".join(lines) +
            f"\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Xonadon tanlash yoki boshqarish uchun **🌋 Oila tanlash** tugmasini bosing!"
        )

        await message.answer(overview_text, reply_markup=houses_category_kb(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Uylar statistikasini ko'rsatishda xatolik: {e}", exc_info=True)
        await message.answer("🛕 Uylar statistikasini yuklashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
