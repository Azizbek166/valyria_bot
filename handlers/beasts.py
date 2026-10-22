import time
import random
from aiogram import Router, F, types
from database import (
    get_user, get_user_beasts, buy_beast,
    upgrade_dragon, get_user_army, buy_troops
)
from keyboards import (
    beasts_main_kb, dragons_upgrade_kb, barracks_recruitment_kb
)

router = Router()

DRAGON_NAMES_POOL = [
    "Balerion", "Vhagar", "Meraxes", "Vermithor", "Caraxes",
    "Silverwing", "Meleys", "Sunfyre", "Tessarion", "Syrax",
    "Seasmoke", "Sheepstealer", "Cannibal", "Grey Ghost",
    "Moondancer", "Morning", "Tyraxes", "Vermax", "Arrax",
    "Stormcloud", "Terrax", "Morghul", "Shrykos", "Urrax"
]

@router.message(F.text == "🐉 Hayvonlarim 🕷")
async def show_beasts_menu(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())

    dragons = [b for b in beasts if b["beast_type"] == "dragon"]
    spiders = [b for b in beasts if b["beast_type"] == "spider"]

    dragons_lines = []
    for d in dragons:
        if d["frozen_until"] > now:
            rem = d["frozen_until"] - now
            d_days = rem // 86400
            d_hours = (rem % 86400) // 3600
            d_mins = (rem % 3600) // 60
            status = f"❄️ *Muzlagan:* {d_days}k {d_hours}s {d_mins}d"
        else:
            status = "🔥 *Faol (Jangga tayyor)*"

        dragons_lines.append(
            f"• 🐲 **{d['name']}** [{d['grade']}-daraja | {d['power']} ball] — {status}"
        )

    dragons_text = "\n".join(dragons_lines) if dragons_lines else "Sizda hali birorta ham ajdar yo'q."
    spiders_text = f"🕷 **Oʻrgimchaklar:** {len(spiders)} ta (Har biri 500 ball, Jami: {len(spiders) * 500} ball)" if spiders else "🕷 Oʻrgimchaklar yo'q."

    text = (
        f"🐉 **VALERIYA MAXLUQLARI VA HARBIY GVARDIYA**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Sizning hisobingiz: **{user['gold'] if user else 0} 🪙**\n\n"
        f"🐲 **AJIDARLARINGIZ ({len(dragons)} ta):**\n"
        f"{dragons_text}\n\n"
        f"{spiders_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **QOIDALAR VA NARXLAR:**\n"
        f"• **Ajdar 🐲**: 400 🪙 (C-daraja: 500 ball)\n"
        f"• **Kuchaytirish ⚡️**: Har bir daraja uchun 150 🪙 (B: 1000, A: 1500, S: 2000 ball)\n"
        f"• **Muzlash ❄️**: Ajdar jangda qatnashgach **3 kun (72 soat) muzlaydi**!\n"
        f"• **Oʻrgimchak 🕷**: 300 🪙 (500 ball, muzlamaydi)\n"
    )

    await message.answer(text, reply_markup=beasts_main_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "back_beasts")
async def callback_back_beasts(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    beasts = await get_user_beasts(user_id)
    now = int(time.time())

    dragons = [b for b in beasts if b["beast_type"] == "dragon"]
    spiders = [b for b in beasts if b["beast_type"] == "spider"]

    dragons_lines = []
    for d in dragons:
        if d["frozen_until"] > now:
            rem = d["frozen_until"] - now
            d_days = rem // 86400
            d_hours = (rem % 86400) // 3600
            d_mins = (rem % 3600) // 60
            status = f"❄️ *Muzlagan:* {d_days}k {d_hours}s {d_mins}d"
        else:
            status = "🔥 *Faol (Jangga tayyor)*"

        dragons_lines.append(
            f"• 🐲 **{d['name']}** [{d['grade']}-daraja | {d['power']} ball] — {status}"
        )

    dragons_text = "\n".join(dragons_lines) if dragons_lines else "Sizda hali birorta ham ajdar yo'q."
    spiders_text = f"🕷 **Oʻrgimchaklar:** {len(spiders)} ta (Har biri 500 ball)" if spiders else "🕷 Oʻrgimchaklar yo'q."

    text = (
        f"🐉 **VALERIYA MAXLUQLARI VA HARBIY GVARDIYA**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Sizning hisobingiz: **{user['gold'] if user else 0} 🪙**\n\n"
        f"🐲 **Ajdarlaringiz ({len(dragons)} ta):**\n"
        f"{dragons_text}\n\n"
        f"{spiders_text}\n"
    )

    await callback.message.edit_text(text, reply_markup=beasts_main_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_beast:"))
async def callback_buy_beast(callback: types.CallbackQuery):
    beast_type = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if beast_type == "dragon":
        dragon_name = random.choice(DRAGON_NAMES_POOL)
        success, msg = await buy_beast(user_id, "dragon", custom_name=dragon_name)
    else:
        success, msg = await buy_beast(user_id, "spider")

    if success:
        await callback.answer("Muvaffaqiyatli xarid qilindi! 🎉", show_alert=True)
        # Menuni yangilash
        user = await get_user(user_id)
        beasts = await get_user_beasts(user_id)
        now = int(time.time())
        dragons = [b for b in beasts if b["beast_type"] == "dragon"]
        spiders = [b for b in beasts if b["beast_type"] == "spider"]

        text = (
            f"🐉 **Xarid amalga oshirildi!**\n\n"
            f"{msg}\n\n"
            f"💰 Qolgan oltin: **{user['gold']} 🪙**\n"
            f"🐲 Ajdarlar: {len(dragons)} ta | 🕷 O'rgimchaklar: {len(spiders)} ta"
        )
        await callback.message.edit_text(text, reply_markup=beasts_main_kb(), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "beast_upgrades_list")
async def callback_beast_upgrades_list(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    beasts = await get_user_beasts(user_id)
    dragons = [b for b in beasts if b["beast_type"] == "dragon"]

    if not dragons:
        await callback.answer("Sizda hali birorta ham ajdar yo'q!", show_alert=True)
        return

    text = (
        "⚡️ **AJIDARNI KUCHAYTIRISH (150 🪙)**\n\n"
        "Kuchaytirish bosqichlari:\n"
        "• **C -> B**: 500 ball ➡️ 1000 ball\n"
        "• **B -> A**: 1000 ball ➡️ 1500 ball\n"
        "• **A -> S**: 1500 ball ➡️ 2000 ball (Maksimal)\n\n"
        "Qaysi ajdaringizni kuchaytirmoqchisiz?"
    )

    await callback.message.edit_text(text, reply_markup=dragons_upgrade_kb(dragons), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("upgrade_d:"))
async def callback_upgrade_dragon(callback: types.CallbackQuery):
    beast_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success, msg = await upgrade_dragon(user_id, beast_id)
    if success:
        await callback.answer("Daraja oshirildi! ⚡️", show_alert=True)
        beasts = await get_user_beasts(user_id)
        dragons = [b for b in beasts if b["beast_type"] == "dragon"]
        text = (
            f"⚡️ **Ajdar kuchaytirildi!**\n\n"
            f"{msg}\n\n"
            f"Yana boshqa ajdarni kuchaytirmoqchimisiz?"
        )
        await callback.message.edit_text(text, reply_markup=dragons_upgrade_kb(dragons), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "noop")
async def callback_noop(callback: types.CallbackQuery):
    await callback.answer("Ushbu ajdar allaqachon maksimal S-darajada!", show_alert=True)

@router.callback_query(F.data == "open_barracks")
async def callback_open_barracks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    army = await get_user_army(user_id)

    text = (
        "🛡 **KAZARMA — ASKARLAR YOLLASH**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Sizning hisobingiz: **{user['gold']} 🪙**\n\n"
        f"Hozirgi qo'shinlaringiz:\n"
        f"🗡 **Oddiy askar**: {army['soldiers']} ta (1 tanga = 1 ball)\n"
        f"✨ **Chakra**: {army['chakra']} ta (2 tanga = 2 ball)\n"
        f"🛡 **Tilla plash**: {army['gold_cloaks']} ta (3 tanga = 3 ball)\n\n"
        f"Yollamoqchi bo'lgan askaringiz miqdorini tanlang:"
    )

    await callback.message.edit_text(text, reply_markup=barracks_recruitment_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("recruit:"))
async def callback_recruit(callback: types.CallbackQuery):
    _, troop_type, count_str = callback.data.split(":")
    count = int(count_str)
    user_id = callback.from_user.id

    success, msg = await buy_troops(user_id, troop_type, count)
    if success:
        await callback.answer("Askarlar yollindi! 🛡", show_alert=False)
        user = await get_user(user_id)
        army = await get_user_army(user_id)
        text = (
            f"🛡 **KAZARMA — ASKARLAR YOLLASH**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ {msg}\n\n"
            f"💰 Sizning hisobingiz: **{user['gold']} 🪙**\n\n"
            f"🗡 **Oddiy askar**: {army['soldiers']} ta\n"
            f"✨ **Chakra**: {army['chakra']} ta\n"
            f"🛡 **Tilla plash**: {army['gold_cloaks']} ta\n"
        )
        await callback.message.edit_text(text, reply_markup=barracks_recruitment_kb(), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)
