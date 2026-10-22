import time
from aiogram import Router, F, types
from database import (
    get_user_house, get_house_castle,
    build_or_upgrade_castle, collect_castle_income,
    get_user
)
from keyboards import castle_menu_kb
from config import CASTLE_INCOME, CASTLE_COST

router = Router()

@router.message(F.text == "🏰 Qal'a")
async def show_castle_menu(message: types.Message):
    user_id = message.from_user.id
    user_house = await get_user_house(user_id)

    if not user_house:
        await message.answer(
            "⚠️ **Qal'a boshqaruvi uchun avval xonadoningiz bo'lishi kerak!**\n"
            "Iltimos, **🌋 Oila tanlash** bo'limidan o'z xonadoningizni tanlang.",
            parse_mode="Markdown"
        )
        return

    castle = await get_house_castle(user_house["id"])
    user = await get_user(user_id)
    user_gold = user["gold"] if user else 0

    now = int(time.time())

    if not castle:
        text = (
            f"🏰 **{user_house['name']} XONADONI QAL'ASI**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Sizning xonadoningizda hali mustahkam Qal'a qurilmagan!\n\n"
            "🏰 **Qal'a nima beradi?**\n"
            "• Qal'a — xonadoningizning doimiy tayanchi va xazinasi.\n"
            "• Har soatda avtomatik ravishda passiv oltin ishlab chiqaradi!\n"
            "• Uni 1, 2 va 3-darajagacha kuchaytirib, daromadni oshirish mumkin.\n\n"
            f"💰 Sizdagi oltin: **{user_gold} 🪙**\n"
            f"🔨 1-darajali qal'a narxi: **{CASTLE_COST[1]} 🪙**\n"
            f"📈 Soatlik daromad: **+{CASTLE_INCOME[1]} 🪙/soat**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Qal'a qurishni xohlaysizmi?"
        )
        kb = castle_menu_kb(castle=None, can_collect=False)
    else:
        lvl = castle["level"]
        inc = CASTLE_INCOME.get(lvl, 10)
        last_col = castle["last_collected_at"] or castle.get("created_at", now)
        diff = now - last_col
        hours_passed = diff // 3600
        uncollected = hours_passed * inc
        mins_left = max(1, (3600 - (diff % 3600)) // 60)

        upgrade_info = ""
        if lvl < 3:
            next_lvl = lvl + 1
            cost = CASTLE_COST[next_lvl]
            next_inc = CASTLE_INCOME[next_lvl]
            upgrade_info = (
                f"\n⚡️ **Keyingi daraja ({next_lvl}-daraja):**\n"
                f"• Kuchaytirish narxi: **{cost} 🪙**\n"
                f"• Yangi daromad: **+{next_inc} 🪙/soat**\n"
            )
        else:
            upgrade_info = "\n⭐️ **Qal'angiz eng yuqori (3-daraja) cho'qqisiga yetgan!**\n"

        can_collect = hours_passed >= 1

        text = (
            f"🏰 **{user_house['name']} XONADONI QAL'ASI**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🎖 Qal'a darajasi: **{lvl}-daraja**\n"
            f"📈 Soatlik daromad: **+{inc} 🪙 / soat**\n"
            f"💰 Hozir yig'ilishi mumkin bo'lgan hosil: **+{uncollected} 🪙** ({hours_passed} soatlik)\n"
            f"⏳ Keyingi soatlik daromadgacha: **{mins_left} daqiqa**\n"
            f"💰 Sizning xazinangiz: **{user_gold} 🪙**\n"
            f"{upgrade_info}"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        kb = castle_menu_kb(castle=castle, can_collect=can_collect, hours_passed=hours_passed, income=uncollected)

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "castle_build_or_upgrade")
async def callback_castle_build_or_upgrade(callback: types.CallbackQuery):
    success, msg = await build_or_upgrade_castle(callback.from_user.id)
    if success:
        await callback.answer("Muvaffaqiyatli! 🏰", show_alert=True)
        # Update view
        user_house = await get_user_house(callback.from_user.id)
        castle = await get_house_castle(user_house["id"]) if user_house else None
        user = await get_user(callback.from_user.id)
        user_gold = user["gold"] if user else 0
        lvl = castle["level"] if castle else 1
        inc = CASTLE_INCOME.get(lvl, 10)

        updated_text = (
            f"🏰 **{user_house['name']} QAL'ASI YANGILANDI!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{msg}\n\n"
            f"🎖 Yangi daraja: **{lvl}-daraja**\n"
            f"📈 Soatlik daromad: **+{inc} 🪙/soat**\n"
            f"💰 Qolgan oltin: **{user_gold} 🪙**\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await callback.message.edit_text(updated_text, reply_markup=castle_menu_kb(castle, can_collect=False), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "castle_collect_gold")
async def callback_castle_collect_gold(callback: types.CallbackQuery):
    income, msg = await collect_castle_income(callback.from_user.id)
    if income > 0:
        await callback.answer(f"+{income} oltin olindi! 💰", show_alert=True)
        user_house = await get_user_house(callback.from_user.id)
        castle = await get_house_castle(user_house["id"]) if user_house else None
        user = await get_user(callback.from_user.id)

        updated_text = (
            f"🏰 **{user_house['name']} QAL'ASI HOSILI YIG'ILDI!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{msg}\n\n"
            f"💰 Umumiy xazinangiz: **{user['gold']} 🪙**\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await callback.message.edit_text(updated_text, reply_markup=castle_menu_kb(castle, can_collect=False), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)
