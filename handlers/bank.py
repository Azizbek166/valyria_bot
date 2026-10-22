from aiogram import Router, F, types
from aiogram.filters import Command
from database import (
    get_user, claim_daily_bonus, update_user_gold
)
from keyboards import bank_kb

router = Router()

@router.message(F.text == "🏦 Golden")
async def show_bank_menu(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    text = (
        f"🏦 **VALERIYA OLTIN BANKI (THE GOLDEN BANK)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Xazinangizdagi jami boylik: **{user['gold'] if user else 0} 🪙**\n\n"
        f"Bank imkoniyatlari:\n"
        f"• **Kunlik Oltin Bonusi**: Har 24 soatda bepul 50 - 120 🪙 oling.\n"
        f"• **O'tkazmalar**: Boshqa Lordga oltin jo'natish uchun `/pay <telegram_id> <miqdor>` buyrug'idan foydalaning.\n\n"
        f"Oltin bonusingizni olish uchun quyidagi tugmani bosing:"
    )

    await message.answer(text, reply_markup=bank_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "bank_claim_daily")
async def callback_claim_daily(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    success, msg = await claim_daily_bonus(user_id)

    if success:
        user = await get_user(user_id)
        text = (
            f"🎁 **Kunlik bonus muvaffaqiyatli olindi!**\n\n"
            f"{msg}\n"
            f"💰 Hozirgi balansingiz: **{user['gold']} 🪙**"
        )
        await callback.message.edit_text(text, reply_markup=bank_kb(), parse_mode="Markdown")
        await callback.answer("Bonus olindi! 🪙", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "bank_info")
async def callback_bank_info(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    await callback.answer(f"Sizning xazinangizda: {user['gold']} 🪙 mavjud.", show_alert=True)

@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("⚠️ To'g'ri format: `/pay <telegram_id> <miqdor>`\nMasalan: `/pay 7009689119 50`", parse_mode="Markdown")
        return

    try:
        target_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("⚠️ ID va miqdor faqat raqamlardan iborat bo'lishi kerak!")
        return

    if amount <= 0:
        await message.answer("⚠️ Miqdor 1 dan katta bo'lishi kerak!")
        return

    sender_id = message.from_user.id
    if sender_id == target_id:
        await message.answer("⚠️ O'zingizga pul o'tkaza olmaysiz!")
        return

    sender = await get_user(sender_id)
    if not sender or sender["gold"] < amount:
        await message.answer("⚠️ Xazinangizda yetarli oltin yo'q!")
        return

    target = await get_user(target_id)
    if not target:
        await message.answer("⚠️ Qabul qiluvchi o'yinchi botda topilmadi!")
        return

    await update_user_gold(sender_id, -amount)
    await update_user_gold(target_id, amount)

    await message.answer(
        f"✅ Muvaffaqiyatli o'tkazildi!\n"
        f"Lord **{target['full_name']}**ga **{amount} 🪙** yuborildi.",
        parse_mode="Markdown"
    )

    try:
        await message.bot.send_message(
            target_id,
            f"💰 Sizga Lord **{sender['full_name']}** tomonidan **+{amount} 🪙** o'tkazildi!",
            parse_mode="Markdown"
        )
    except Exception:
        pass
