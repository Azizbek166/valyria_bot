from aiogram import Router, F, types
from aiogram.filters import Command
from config import ADMIN_IDS
from database import (
    get_all_users, admin_set_gold, admin_free_house,
    admin_unfreeze_dragons, get_houses, get_db_connection,
    admin_restart_game, set_user_blocked, admin_transfer_house,
    approve_donation_request, reject_donation_request
)
from keyboards import admin_panel_kb, admin_restart_confirm_kb

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == "👑 Admin paneli")
@router.message(Command("admin"))
async def show_admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    text = (
        "👑 **QADIMGI VALERIYA — BOSH ADMIN BOSHQARUV PANELI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Buyruqlar va imkoniyatlar:\n\n"
        "• `/givegold <user_id> <miqdor>` — O'yinchiga oltin o'rnatish\n"
        "• `/unfreeze <user_id>` — O'yinchining ajdarlarini muddatidan oldin muzdan chiqarish\n"
        "• `/freehouse <house_id>` — Xonadonni bo'shatish (egani olib tashlash)\n"
        "• `/transferhouse <user_id> <house_id>` — O'yinchini boshqa xonadonga ko'chirish\n"
        "• `/block <user_id>` — O'yinchini bloklash\n"
        "• `/unblock <user_id>` — O'yinchini blokdan ochish\n"
        "• `/broadcast <xabar>` — Botdagi barcha o'yinchilarga xabar yuborish\n"
        "• `/restartgame` — O'yinni to'liq restart qilish (Reset)\n\n"
        "Quyidagi tezkor tugmalardan ham foydalanishingiz mumkin:"
    )

    await message.answer(text, reply_markup=admin_panel_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    users = await get_all_users()
    houses = await get_houses()

    occupied = len([h for h in houses if h["owner_id"] is not None])
    vassals = len([h for h in houses if h["overlord_id"] is not None])
    total_gold = sum(u["gold"] for u in users)

    async with get_db_connection() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM beasts")
        total_beasts = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM battles_log")
        total_battles = (await cursor.fetchone())[0]

    stats_text = (
        "📊 **BOTNING UMUMIY STATISTIKASI:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Barcha o'yinchilar: **{len(users)} nafar**\n"
        f"🏰 Egallangan xonadonlar: **{occupied}/52**\n"
        f"⛓ Jami vassallar soni: **{vassals} ta**\n"
        f"🐉 Jami maxluqlar: **{total_beasts} ta**\n"
        f"⚔️ O'tkazilgan janglar: **{total_battles} ta**\n"
        f"💰 Valeriya xazinasidagi jami oltin: **{total_gold} 🪙**\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    await callback.message.edit_text(stats_text, reply_markup=admin_panel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_restart_prompt")
async def callback_admin_restart_prompt(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    warn_text = (
        "⚠️ **DIQQAT! O'YINNI TO'LIQ RESTART QILISH!**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Ushbu amal bajarilsa:\n"
        "1. Barcha o'yinchilarning xonadonlari, armiyalari va ajdarlari o'chiriladi.\n"
        "2. Barcha 52 ta xonadon noldan bo'shatiladi.\n"
        "3. Janglar tarixi, vassallar va soliqlar tozalanadi.\n"
        "4. Barcha o'yinchilar yana qaytadan xonadon tanlashi kerak bo'ladi.\n\n"
        "Haqiqatan ham o'yinni restart qilmoqchimisiz?"
    )

    await callback.message.edit_text(warn_text, reply_markup=admin_restart_confirm_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_cancel_restart")
async def callback_admin_cancel_restart(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text("✅ Restart bekor qilindi.", reply_markup=admin_panel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_do_restart")
async def callback_admin_do_restart(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await admin_restart_game()
    success_text = (
        "🔄 **O'YIN TO'LIQ RESTART QILINDI!** 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• Barcha 52 ta Valeriya xonadoni yana bo'shatildi.\n"
        "• Barcha armiyalar va janglar tarixi tozalandi.\n"
        "• O'yin noldan yangidan boshlandi!"
    )
    await callback.message.edit_text(success_text, reply_markup=admin_panel_kb(), parse_mode="Markdown")
    await callback.answer("O'yin muvaffaqiyatli restart qilindi!", show_alert=True)

@router.message(Command("restartgame"))
async def cmd_restartgame(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    warn_text = (
        "⚠️ **DIQQAT! O'YINNI TO'LIQ RESTART QILISH!**\n\n"
        "Barcha xonadonlar, armiyalar va ma'lumotlar tozalanadi. Tasdiqlaysizmi?"
    )
    await message.answer(warn_text, reply_markup=admin_restart_confirm_kb(), parse_mode="Markdown")

@router.message(Command("givegold"))
async def cmd_givegold(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("⚠️ Format: `/givegold <user_id> <miqdor>`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("⚠️ Raqamlarda kiriting!")
        return

    await admin_set_gold(user_id, amount)
    await message.answer(f"✅ {user_id} foydalanuvchiga {amount} oltin o'rnatildi!")

@router.message(Command("unfreeze"))
async def cmd_unfreeze(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: `/unfreeze <user_id>`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ ID raqam bo'lishi kerak!")
        return

    count = await admin_unfreeze_dragons(user_id)
    await message.answer(f"✅ {user_id} ning {count} ta ajdari muzdan chiqarildi va jangga tayyor!")

@router.message(Command("freehouse"))
async def cmd_freehouse(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: `/freehouse <house_id>` (1 dan 52 gacha)", parse_mode="Markdown")
        return

    try:
        house_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ House ID raqam bo'lishi kerak!")
        return

    await admin_free_house(house_id)
    await message.answer(f"✅ #{house_id} xonadon bo'shatildi va yana tanlash uchun ochiq!")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        await message.answer("⚠️ Xabar matnini kiriting! Masalan: `/broadcast Hurmatli Lordlar! Yangi o'yin boshlandi!`", parse_mode="Markdown")
        return

    users = await get_all_users()
    sent_count = 0
    fail_count = 0

    status_msg = await message.answer(f"📢 Xabar {len(users)} ta o'yinchiga yuborilmoqda...")

    for u in users:
        try:
            await message.bot.send_message(
                u["telegram_id"],
                f"📢 **VALERIYA HUKMDORLARIDAN MUHIM XABAR:**\n\n{text_to_send}",
                parse_mode="Markdown"
            )
            sent_count += 1
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"✅ Xabar tarqatish yakunlandi!\n"
        f"• Yetkazildi: {sent_count} ta\n"
        f"• Yetkazilmadi (bloklagan): {fail_count} ta"
    )

@router.message(Command("block"))
async def cmd_block_user(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: `/block <user_id>`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ ID raqam bo'lishi kerak!")
        return

    await set_user_blocked(user_id, True)
    await message.answer(f"🚫 Foydalanuvchi `{user_id}` muvaffaqiyatli bloklandi!", parse_mode="Markdown")

@router.message(Command("unblock"))
async def cmd_unblock_user(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: `/unblock <user_id>`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ ID raqam bo'lishi kerak!")
        return

    await set_user_blocked(user_id, False)
    await message.answer(f"✅ Foydalanuvchi `{user_id}` blokdan ochildi!", parse_mode="Markdown")

@router.message(Command("transferhouse"))
async def cmd_transfer_house(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("⚠️ Format: `/transferhouse <user_id> <new_house_id>`", parse_mode="Markdown")
        return

    try:
        user_id = int(parts[1])
        new_house_id = int(parts[2])
    except ValueError:
        await message.answer("⚠️ Raqamlarda kiriting!")
        return

    success, msg = await admin_transfer_house(user_id, new_house_id)
    if success:
        await message.answer(f"✅ {msg}")
    else:
        await message.answer(f"⚠️ Xatolik: {msg}")

@router.callback_query(F.data.startswith("approve_don:"))
async def callback_approve_donation(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    donation_id = int(callback.data.split(":")[1])
    success, msg, info = await approve_donation_request(donation_id, callback.from_user.id)

    if success:
        await callback.answer("To'lov tasdiqlandi! ✅", show_alert=True)
        admin_name = callback.from_user.full_name
        new_caption = (
            f"{callback.message.caption or ''}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ **TASDIQLANDI!** (Admin: {admin_name})\n"
            f"Resurslar o'yinchiga to'liq yetkazildi!"
        )
        try:
            await callback.message.edit_caption(caption=new_caption, reply_markup=None, parse_mode="Markdown")
        except Exception:
            pass

        # Send notification to the user
        if info:
            user_notify = (
                "🎉 **TABRIKLAYMIZ! GREEN BANK TO'LOVINGIZ TASDIQLANDI!** 👑\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 Paket: **{info['package_name']}**\n"
                f"💵 To'langan: **{info['amount_uzs']:,} so'm**\n\n"
                f"🎁 **Hisobingizga qo'shildi:**\n{info['desc']}\n\n"
                "Valeriya taxti sari janglarda zafarlar tilaymiz!"
            )
            try:
                await callback.bot.send_message(info["user_id"], user_notify, parse_mode="Markdown")
            except Exception:
                pass
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("reject_don:"))
async def callback_reject_donation(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    donation_id = int(callback.data.split(":")[1])
    success, msg, user_id = await reject_donation_request(donation_id, callback.from_user.id)

    if success:
        await callback.answer("To'lov rad etildi! ❌", show_alert=True)
        admin_name = callback.from_user.full_name
        new_caption = (
            f"{callback.message.caption or ''}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ **RAD ETILDI!** (Admin: {admin_name})"
        )
        try:
            await callback.message.edit_caption(caption=new_caption, reply_markup=None, parse_mode="Markdown")
        except Exception:
            pass

        if user_id:
            user_notify = (
                "❌ **GREEN BANK TO'LOVINGIZ RAD ETILDI**\n\n"
                "Siz yuborgan to'lov cheki admin tomonidan rad etildi. "
                "Agar to'lovda biror tushunmovchilik bo'lsa, iltimos bosh admin bilan bog'laning."
            )
            try:
                await callback.bot.send_message(user_id, user_notify, parse_mode="Markdown")
            except Exception:
                pass
    else:
        await callback.answer(msg, show_alert=True)

