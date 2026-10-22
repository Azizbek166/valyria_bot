from aiogram import Router, F, types
from database import (
    get_user_house, get_houses, get_house_by_id,
    choose_house, get_user
)
from keyboards import (
    houses_category_kb, houses_page_kb, house_action_kb
)
from config import REGIONS

router = Router()

@router.message(F.text == "🌋 Oila tanlash")
async def choose_family_menu(message: types.Message):
    user_house = await get_user_house(message.from_user.id)
    if user_house:
        reg_info = REGIONS.get(user_house.get("region", ""), {})
        reg_name = reg_info.get("name", "Valeriya")
        role_name = "👑 Oliy Qirol" if user_house["id"] == 1 else ("🛡 Hudud Lordi" if user_house.get("is_regional_lord") else "🗡 Bayroqdor")

        await message.answer(
            f"👑 Siz allaqachon **{user_house['name']}** xonadonini ({reg_name}) boshqarmoqdasiz!\n"
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
    house_id = int(callback.data.split(":")[1])
    house = await get_house_by_id(house_id)
    if not house:
        await callback.answer("Xonadon topilmadi!", show_alert=True)
        return

    is_available = house["owner_id"] is None
    is_owner = house["owner_id"] == callback.from_user.id
    reg_info = REGIONS.get(house.get("region", ""), {})
    reg_title = reg_info.get("name", "Noma'lum")
    tier = house.get("tier", "B")
    tier_desc = f"🌟 **[{tier}-toifa]** (Hudud Lordi)" if tier == "A" else f"🛡 **[{tier}-toifa]** (Mintaqa xonadoni)"

    if house["id"] == 1:
        role_desc = "👑 **Oliy Qirol (The High King)**"
    elif house.get("is_regional_lord"):
        role_desc = f"🛡 **Hudud Lordi ({reg_info.get('title', '')})**"
    else:
        role_desc = f"🗡 **Bayroqdor (Bannerman) xonadoni** — Hudud Lordi: {reg_info.get('lord_name', '')}"

    if house["owner_id"]:
        owner_user = await get_user(house["owner_id"])
        owner_name = owner_user["full_name"] if owner_user else f"Lord #{house['owner_id']}"
        username_str = f" (@{owner_user['username']})" if (owner_user and owner_user.get("username")) else ""
        status_str = f"🔒 **Band.** Hukmdor: **{owner_name}**{username_str}"
        if house["overlord_id"]:
            overlord_user = await get_user(house["overlord_id"])
            overlord_name = overlord_user["full_name"] if overlord_user else f"#{house['overlord_id']}"
            overlord_user_str = f" (@{overlord_user['username']})" if (overlord_user and overlord_user.get("username")) else ""
            status_str += f"\n⛓ **Vassal:** Lord **{overlord_name}**{overlord_user_str} ga qaram"
    else:
        status_str = "🟢 **BO'SH!** Ushbu xonadonni hoziroq egallashingiz mumkin!"

    castle_info = f"\n🏰 **Qal'a:** {house['castle_level']}-darajali Qal'a mavjud" if house.get("castle_level") else "\n🏰 **Qal'a:** Hali qurilmagan"

    detail_text = (
        f"🏛 **XONADON: {house['name']}** (#{house['id']})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🗺 Hudud: **{reg_title}**\n"
        f"🎖 Toifasi: {tier_desc}\n"
        f"👑 Maqomi: {role_desc}\n"
        f"📌 Holati: {status_str}"
        f"{castle_info}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    await callback.message.edit_text(
        detail_text,
        reply_markup=house_action_kb(house_id, is_available, is_owner),
        parse_mode="Markdown"
    )
    await callback.answer()

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
    houses = await get_houses()
    total = len(houses)
    occupied = len([h for h in houses if h["owner_id"] is not None])
    free = total - occupied
    vassals_count = len([h for h in houses if h["overlord_id"] is not None])

    lines = []
    for reg_key, reg in REGIONS.items():
        reg_houses = [h for h in houses if h.get("region") == reg_key]
        reg_occupied = len([h for h in reg_houses if h["owner_id"] is not None])
        lord_house = next((h for h in reg_houses if h.get("is_regional_lord")), None)
        lord_owner_str = ""
        if lord_house and lord_house["owner_id"]:
            u_str = f" (@{lord_house['owner_username']})" if lord_house.get("owner_username") else ""
            lord_owner_str = f"👑 {lord_house.get('owner_name', 'Lord')}{u_str}"
        else:
            lord_owner_str = "🟢 Bo'sh"

        lines.append(
            f"• **{reg['name']}**: {reg_occupied}/{len(reg_houses)} band | Lord: {reg['lord_name']} [{lord_house.get('tier', 'A')}-toifa] ({lord_owner_str})"
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

    await message.answer(overview_text, parse_mode="Markdown")
