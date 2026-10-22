from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_user_house, get_house_all_alliances, get_pending_alliance_proposals,
    create_alliance_proposal, respond_alliance_proposal, break_alliance,
    get_houses, get_house_by_id, get_user
)
from keyboards import alliance_main_kb, alliance_decision_kb, alliance_type_select_kb
from config import escape_md

router = Router()

def build_alliance_menu_text(user_house: dict, alliances: dict, proposals: list) -> str:
    m = alliances.get("marriage")
    if m:
        is_h1 = m["house1_id"] == user_house["id"]
        m_house = escape_md(m["h2_name"] if is_h1 else m["h1_name"])
        m_lord = escape_md(m["u2_name"] if is_h1 else m["u1_name"])
        raw_u = m.get("u2_username") if is_h1 else m.get("u1_username")
        m_user = f" (@{escape_md(raw_u)})" if raw_u else ""
        marriage_info = (
            f"• Holat: ✅ **Tuzilgan**\n"
            f"• Hamkor: **{m_house}** (Lord: **{m_lord}**{m_user})\n"
            f"• Imtiyoz: Sulh, Mudofaada +50% ko'mak, Qal'adan +15% ko'proq oltin!"
        )
    else:
        marriage_info = (
            "• Holat: ❌ **Tuzilmagan**\n"
            "• Imtiyoz: Xonadonlar sulhi, Mudofaada +50% quvvat, Qal'adan +15% soatlik daromad bonusi!"
        )

    s = alliances.get("strategic")
    if s:
        is_h1 = s["house1_id"] == user_house["id"]
        s_house = escape_md(s["h2_name"] if is_h1 else s["h1_name"])
        s_lord = escape_md(s["u2_name"] if is_h1 else s["u1_name"])
        raw_su = s.get("u2_username") if is_h1 else s.get("u1_username")
        s_user = f" (@{escape_md(raw_su)})" if raw_su else ""
        strategic_info = (
            f"• Holat: ✅ **Tuzilgan**\n"
            f"• Hamkor: **{s_house}** (Lord: **{s_lord}**{s_user})\n"
            f"• Imtiyoz: Sulh, Hujumda +25% quvvat, O'ljadan 20% ulush, Mudofaada +25% ko'mak!"
        )
    else:
        strategic_info = (
            "• Holat: ❌ **Tuzilmagan**\n"
            "• Imtiyoz: Sulh, Hujumda +25% quvvat, G'alaba o'ljasidan 20% ulush, Mudofaada +25% ko'mak!"
        )

    text = (
        "💍 **VALERIYA ITTIFOQ VA NIKOH MARKAZI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Sizning xonadoningiz: **{user_house['name']}** [{user_house.get('tier', 'B')}-toifa]\n\n"
        "💍 **1. SULOLAVIY NIKOH (Marriage):**\n"
        f"{marriage_info}\n\n"
        "🤝 **2. MANFAATLI ITTIFOQ (Strategic Pact):**\n"
        f"{strategic_info}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📬 Kutilayotgan takliflar soni: **{len(proposals)} ta**\n"
        "Quyidagi tugmalar orqali kerakli ittifoqni tuzishingiz yoki boshqarishingiz mumkin:"
    )
    return text

@router.message(F.text == "💍 Ittifoq va Nikoh")
async def show_alliance_menu(message: types.Message):
    user_id = message.from_user.id
    user_house = await get_user_house(user_id)

    if not user_house:
        await message.answer(
            "⚠️ **Nikoh va Ittifoq tuzish uchun avval xonadon boshqarishingiz kerak!**\n"
            "Iltimos, **🌋 Oila tanlash** bo'limidan o'z xonadoningizni tanlang.",
            parse_mode="Markdown"
        )
        return

    alliances = await get_house_all_alliances(user_house["id"])
    proposals = await get_pending_alliance_proposals(user_house["id"])

    text = build_alliance_menu_text(user_house, alliances, proposals)
    kb = alliance_main_kb(alliances, pending_count=len(proposals))
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("alliance_choose_type:"))
async def callback_alliance_choose_type(callback: types.CallbackQuery):
    target_house_id = int(callback.data.split(":")[1])
    target_house = await get_house_by_id(target_house_id)
    if not target_house:
        await callback.answer("Xonadon topilmadi!", show_alert=True)
        return

    text = (
        f"🏛 **{target_house['name']} XONADONI BILAN RISHTA BOG'LASH**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Qaysi turdagi rishtani taklif qilmoqchisiz?\n\n"
        "💍 **Sulolaviy Nikoh:**\n"
        "• O'zaro sulh\n"
        "• Mudofaada +50% yordam\n"
        "• Qal'a daromadiga +15% soatlik bonus\n\n"
        "🤝 **Manfaatli Ittifoq:**\n"
        "• O'zaro sulh\n"
        "• Hujumlarda +25% jangovar quvvat ko'magi\n"
        "• Jang g'alabasida dushman o'ljasidan 20% ulush\n"
        "• Mudofaada +25% ko'mak\n\n"
        "Quyidan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=alliance_type_select_kb(target_house_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("alliance_list:"))
async def callback_alliance_list(callback: types.CallbackQuery):
    a_type = callback.data.split(":")[1]
    user_house = await get_user_house(callback.from_user.id)
    if not user_house:
        await callback.answer("Sizda xonadon yo'q!", show_alert=True)
        return

    type_title = "Sulolaviy Nikoh 💍" if a_type == "marriage" else "Manfaatli Ittifoq 🤝"

    all_houses = await get_houses()
    candidates = [
        h for h in all_houses
        if h["owner_id"] is not None and h["owner_id"] != callback.from_user.id
    ]

    if not candidates:
        await callback.answer("Hozircha ittifoq tuzish uchun boshqa faol Lordlar mavjud emas.", show_alert=True)
        return

    rows = []
    icon = "💍" if a_type == "marriage" else "🤝"
    for h in candidates[:14]:
        tier_tag = f" [{h.get('tier', 'B')}-toifa]"
        owner_name = h.get("owner_name") or f"Lord #{h['owner_id']}"
        username_str = f" (@{h['owner_username']})" if h.get("owner_username") else ""
        btn_text = f"{icon} {h['name']}{tier_tag} — {owner_name}{username_str}"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"propose_all:{a_type}:{h['id']}")])

    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="alliance_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    text = (
        f"{type_title} **UCHUN XONADONNI TANLANG:**\n\n"
        f"Qaysi xonadonga **{type_title}** taklifini yubormoqchisiz?"
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("propose_all:"))
async def callback_propose_alliance(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    alliance_type = parts[1]
    target_house_id = int(parts[2])

    success, msg, target_lord_id = await create_alliance_proposal(callback.from_user.id, target_house_id, alliance_type)

    if success:
        type_title = "Sulolaviy Nikoh 💍" if alliance_type == "marriage" else "Manfaatli Ittifoq 🤝"
        await callback.answer(f"{type_title} taklifi yuborildi!", show_alert=True)
        sender_house = await get_user_house(callback.from_user.id)
        sender_user = await get_user(callback.from_user.id)
        sender_name = escape_md(sender_user["full_name"] if sender_user else "Lord")
        u_raw = sender_user.get("username") if sender_user else None
        username_str = f" (@{escape_md(u_raw)})" if u_raw else ""
        s_house_name = escape_md(sender_house.get('name', 'Xonadon') if sender_house else "Xonadon")

        # Target lordga xabar yuborish
        if target_lord_id:
            try:
                perks = (
                    "• O'zaro sulh\n• Mudofaada +50% quvvat\n• Qal'a daromadiga +15% bonus!"
                    if alliance_type == "marriage" else
                    "• O'zaro sulh\n• Hujumda +25% quvvat\n• O'ljadan 20% ulush\n• Mudofaada +25% ko'mak!"
                )
                alert_text = (
                    f"💍 **SIZNING XONADONINGIZGA {type_title.upper()} TAKLIFI KELDI!**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 Yuboruvchi: **{sender_name}**{username_str}\n"
                    f"🏰 Xonadon: **{s_house_name}**\n\n"
                    f"🌟 **Taklif etilayotgan rishta:** {type_title}\n"
                    f"{perks}\n\n"
                    "Qabul qilasizmi yoki rad etasizmi?"
                )
                proposals = await get_pending_alliance_proposals(target_house_id)
                prop_id = proposals[0]["id"] if proposals else 0
                if prop_id:
                    await callback.bot.send_message(
                        target_lord_id,
                        alert_text,
                        reply_markup=alliance_decision_kb(prop_id),
                        parse_mode="Markdown"
                    )
            except Exception:
                pass

        await callback.message.edit_text(f"{msg}\n\nMenyuga qaytish uchun quyidagi tugmani bosing.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="alliance_back")]]), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "alliance_pending_list")
async def callback_alliance_pending_list(callback: types.CallbackQuery):
    user_house = await get_user_house(callback.from_user.id)
    if not user_house:
        await callback.answer("Sizda xonadon yo'q!", show_alert=True)
        return

    proposals = await get_pending_alliance_proposals(user_house["id"])
    if not proposals:
        await callback.answer("Hozircha sizga kelgan yangi takliflar yo'q.", show_alert=True)
        return

    prop = proposals[0]
    raw_pu = prop.get('sender_username')
    username_str = f" (@{escape_md(raw_pu)})" if raw_pu else ""
    prop_house_name = escape_md(prop.get('sender_house_name', ''))
    prop_sender_name = escape_md(prop.get('sender_name', ''))
    all_type = prop.get("alliance_type", "marriage")
    type_title = "Sulolaviy Nikoh 💍" if all_type == "marriage" else "Manfaatli Ittifoq 🤝"
    perks = (
        "• Mudofaada +50% quvvat\n• Qal'a daromadiga +15% bonus"
        if all_type == "marriage" else
        "• Hujumlarda +25% quvvat\n• G'alaba o'ljasidan 20% ulush\n• Mudofaada +25% ko'mak"
    )

    text = (
        f"📬 **SIZGA KELGAN TAKLIF:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 Rishta turi: **{type_title}**\n"
        f"🏰 Xonadon: **{prop_house_name}**\n"
        f"👑 Hukmdor: **{prop_sender_name}**{username_str}\n\n"
        f"Imtiyozlar:\n{perks}\n\n"
        "Ushbu taklifni tasdiqlaysizmi?"
    )
    await callback.message.edit_text(text, reply_markup=alliance_decision_kb(prop["id"]), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("accept_all:"))
async def callback_accept_alliance(callback: types.CallbackQuery):
    prop_id = int(callback.data.split(":")[1])
    success, msg, sender_id = await respond_alliance_proposal(prop_id, callback.from_user.id, accept=True)

    if success:
        await callback.answer("Ittifoq tuzildi! 💍", show_alert=True)
        await callback.message.edit_text(
            f"{msg}\n\nMenyuga qaytish uchun tugmani bosing:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="alliance_back")]]),
            parse_mode="Markdown"
        )
        if sender_id:
            try:
                await callback.bot.send_message(
                    sender_id,
                    "🎉 **Xushxabar!** Siz yuborgan Ittifoq taklifi qabul qilindi! "
                    "Endi xonadonlaringiz o'rtasida yangi rishtalar o'rnatildi.",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("reject_all:"))
async def callback_reject_alliance(callback: types.CallbackQuery):
    prop_id = int(callback.data.split(":")[1])
    success, msg, sender_id = await respond_alliance_proposal(prop_id, callback.from_user.id, accept=False)

    if success:
        await callback.answer("Rad etildi.", show_alert=True)
        await callback.message.edit_text(
            f"{msg}\n\nMenyuga qaytish:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="alliance_back")]]),
            parse_mode="Markdown"
        )
        if sender_id:
            try:
                await callback.bot.send_message(
                    sender_id,
                    "ℹ️ Siz yuborgan Ittifoq taklifi rad etildi.",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("alliance_break"))
async def callback_alliance_break(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    a_type = parts[1] if len(parts) > 1 else "marriage"

    success, msg, partner_id = await break_alliance(callback.from_user.id, a_type)
    if success:
        await callback.answer("Ittifoq bekor qilindi.", show_alert=True)
        await callback.message.edit_text(
            f"{msg}\n\nMenyuga qaytish:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="alliance_back")]]),
            parse_mode="Markdown"
        )
        if partner_id:
            try:
                type_title = "Sulolaviy Nikoh" if a_type == "marriage" else "Manfaatli Ittifoq"
                await callback.bot.send_message(
                    partner_id,
                    f"⚠️ **Diqqat!** Sizning xonadoningiz bilan tuzilgan **{type_title}** rishtalari bekor qilindi.",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "alliance_back")
async def callback_alliance_back(callback: types.CallbackQuery):
    user_house = await get_user_house(callback.from_user.id)
    if not user_house:
        await callback.answer("Sizda xonadon yo'q!", show_alert=True)
        return

    alliances = await get_house_all_alliances(user_house["id"])
    proposals = await get_pending_alliance_proposals(user_house["id"])

    text = build_alliance_menu_text(user_house, alliances, proposals)
    kb = alliance_main_kb(alliances, pending_count=len(proposals))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
