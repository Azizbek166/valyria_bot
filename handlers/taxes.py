import time
from aiogram import Router, F, types
from database import (
    get_user_house, get_vassals, collect_vassal_taxes,
    get_user, free_vassal_by_overlord, get_house_by_id
)
from keyboards import taxes_kb
from config import escape_md
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "✨ Soliqlar")
async def show_taxes_menu(message: types.Message):
    try:
        user_id = message.from_user.id
        user = await get_user(user_id)
        user_house = await get_user_house(user_id)

        if not user_house:
            await message.answer(
                "⚠️ Soliq tizimidan foydalanish uchun avval **🌋 Oila tanlash** orqali xonadoningizni tanlang.",
                parse_mode="Markdown"
            )
            return

        vassals = await get_vassals(user_id)

        # O'zining vassallik holati
        overlord_text = ""
        if user_house["overlord_id"]:
            overlord_house = await get_user_house(user_house["overlord_id"])
            overlord_name = escape_md(overlord_house["name"] if overlord_house else "Noma'lum")
            overlord_text = f"⚠️ *Eslatma: Sizning xonadoningiz **{overlord_name}** xonadoniga qaram (vassal).* Har 24 soatda ular sizdan soliq yig'ib olishlari mumkin.\n\n"

        # Soliq taymeri tekshiruvi (24 soat)
        now = int(time.time())
        last_tax = user.get("last_tax_collected", 0) or 0
        cooldown = 24 * 3600
        if now - last_tax < cooldown:
            left_sec = cooldown - (now - last_tax)
            left_h = left_sec // 3600
            left_m = (left_sec % 3600) // 60
            timer_status = f"⏳ **Keyingi soliq olish vaqti:** {left_h} soat {left_m} daqiqadan so'ng"
        else:
            timer_status = "🟢 **Soliq tayyor!** Hoziroq yig'ib olishingiz mumkin."

        vassals_lines = []
        for v in vassals:
            v_owner = await get_user(v["owner_id"])
            owner_name = escape_md(v_owner["full_name"] if v_owner else f"Lord #{v['owner_id']}")
            v_name = escape_md(v['name'])
            vassals_lines.append(f"• ⛓ **{v_name}** (#{v['id']}) — Hukmdor: {owner_name}")

        if vassals:
            vassals_info = "\n".join(vassals_lines)
            vassal_desc = (
                f"👑 **Sizning bo'ysundirilgan vassallaringiz ({len(vassals)} ta):**\n"
                f"{vassals_info}\n\n"
                f"📌 *Qoida: Har bir vassaldan har 24 soatda bir marta 20 🪙 soliq yig'ib olinadi.*\n"
                f"🕊 *Vassalni ozod qilish uchun quyidagi tugmalardan birini bosing.*\n\n"
                f"{timer_status}"
            )
            kb = taxes_kb(vassals)
        else:
            vassal_desc = (
                "😴 **Sizda hozircha birorta ham vassal yo'q.**\n"
                "Vassalga ega bo'lish uchun **⚔️ Janglar** bo'limida boshqa xonadonlarga hujum qilib, ularni mag'lub eting!"
            )
            kb = None

        text = (
            f"✨ **VALERIYA XAZINASI VA VASSALLIK SOLIQLARI**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{overlord_text}"
            f"{vassal_desc}"
        )

        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Soliqlar menyusida xatolik: {e}", exc_info=True)
        await message.answer("✨ Soliqlar menyusini yuklashda xatolik yuz berdi.")

@router.callback_query(F.data == "collect_all_taxes")
async def callback_collect_taxes(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    total, msg = await collect_vassal_taxes(user_id)

    if total > 0:
        await callback.message.edit_text(f"💰 {msg}", parse_mode="Markdown")
        await callback.answer("Soliqlar xazinaga qo'shildi! 🪙", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("free_vassal:"))
async def callback_free_vassal(callback: types.CallbackQuery):
    house_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    success, msg = await free_vassal_by_overlord(user_id, house_id)
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    # Inform freed vassal if possible
    house = await get_house_by_id(house_id)
    if house and house.get("owner_id"):
        try:
            await callback.bot.send_message(
                house["owner_id"],
                f"🕊 **XUSHXABAR! SIZ OZOD QILINDINGIZ!**\n\nSizning Lordimiz sizni vassallik qaramligidan ozod qildi! Endi xonadoningiz mustaqil!",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await callback.message.edit_text(msg, parse_mode="Markdown")
    await callback.answer("Vassal ozod qilindi! 🕊", show_alert=True)
