from aiogram import Router, F, types
from database import start_expedition, check_expedition, get_user
from keyboards import expedition_kb

router = Router()

@router.message(F.text == "🏞 Valeria Ekspiditsya")
async def show_expedition_menu(message: types.Message):
    user_id = message.from_user.id
    exp_status = await check_expedition(user_id)

    if exp_status["finished"]:
        status_text = f"🎉 **Oldingi ekspeditsiya yakunlandi!** Xazinangizga **+{exp_status['reward']} 🪙** qo'shildi!"
    elif exp_status["active"]:
        rem_seconds = exp_status["left_seconds"]
        hours = rem_seconds // 3600
        mins = (rem_seconds % 3600) // 60
        status_text = f"⏳ **Hozirda ekspeditsiya davom etmoqda.** Qolgan vaqt: **{hours} soat {mins} daqiqa**."
    else:
        status_text = "🏕 Hozirda faol ekspeditsiya yo'q. Qadimgi Valeriya xarobalariga qidiruv guruhini jo'natishingiz mumkin."

    text = (
        f"🏞 **QADIMGI VALERIYA XARO BALARIGA EKSPEDITSIYA**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Qadimgi Valeriya shahrining vulqon qoldiqlari va afsonaviy xarobalari "
        f"ichida ko'plab qadimiy oltinlar va xazinalar yashiringan.\n\n"
        f"Holat: {status_text}\n\n"
        f"Ekspeditsiya muddatini tanlang:"
    )

    await message.answer(text, reply_markup=expedition_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("exp_start:"))
async def callback_exp_start(callback: types.CallbackQuery):
    hours = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success, msg = await start_expedition(user_id, hours)
    if success:
        await callback.message.edit_text(f"🏞 {msg}", reply_markup=expedition_kb(), parse_mode="Markdown")
        await callback.answer("Ekspeditsiya jo'natildi! 🗺", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "exp_check")
async def callback_exp_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    exp_status = await check_expedition(user_id)

    if exp_status["finished"]:
        text = f"🎉 **Tabriklaymiz! Ekspeditsiya xazinani olib qaytdi!**\nSiz **+{exp_status['reward']} 🪙** oltin qo'lga kiritdingiz!"
        await callback.message.edit_text(text, reply_markup=expedition_kb(), parse_mode="Markdown")
        await callback.answer("Mukofot olindi! 🪙", show_alert=True)
    elif exp_status["active"]:
        rem = exp_status["left_seconds"]
        hours = rem // 3600
        mins = (rem % 3600) // 60
        await callback.answer(f"Ekspeditsiya hali qaytmadi! Qolgan vaqt: {hours} soat {mins} daqiqa.", show_alert=True)
    else:
        await callback.answer("Hozirda faol ekspeditsiya yo'q. Yangisini boshlang!", show_alert=True)
