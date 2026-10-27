import os
import shutil
import logging
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from config import ADMIN_IDS, escape_md
from database import (
    get_all_users, admin_set_gold, admin_free_house,
    admin_unfreeze_dragons, admin_unfreeze_all_dragons,
    admin_give_gold_add, get_houses, get_db_connection,
    admin_restart_game, set_user_blocked, admin_transfer_house,
    approve_donation_request, reject_donation_request, get_user,
    distribute_weekly_tournament_rewards,
    get_war_status, toggle_war_status, set_war_status,
    is_bot_admin, is_super_admin, get_all_bot_admins,
    add_bot_admin, remove_bot_admin
)
from keyboards import (
    admin_panel_kb, admin_restart_confirm_kb,
    admin_unfreeze_options_kb, admin_cancel_kb,
    admin_manage_admins_kb, main_menu_keyboard
)

logger = logging.getLogger(__name__)

router = Router()

async def is_admin(user_id: int) -> bool:
    return await is_bot_admin(user_id)

async def get_admin_panel_kb(user_id: int):
    is_war = await get_war_status()
    is_super = is_super_admin(user_id)
    return admin_panel_kb(is_war_open=is_war, is_super_admin=is_super)

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_give_gold = State()
    waiting_for_unfreeze_user = State()
    waiting_for_transfer_house = State()
    waiting_for_clear_house = State()
    waiting_for_add_admin = State()
    waiting_for_db_file = State()

@router.message(F.text == "👑 Admin paneli")
@router.message(Command("admin"))
async def show_admin_panel(message: types.Message, state: FSMContext = None):
    if not await is_admin(message.from_user.id):
        return

    if state:
        await state.clear()

    is_war = await get_war_status()
    war_badge = "🟢 **Ochiq**" if is_war else "🔴 **Sulh davri**"
    role_badge = "👑 **Bosh Admin**" if is_super_admin(message.from_user.id) else "🛡 **Admin**"

    text = (
        f"👑 **QADIMGI VALERIYA — BOSHQARUV PANELI**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Maqomingiz: {role_badge}\n"
        f"Urush holati: {war_badge}\n\n"
        f"Boshqaruv tugmalari orqali istalgan amaliyotni bajaring:\n\n"
        f"• ⚔️ **Urush holati:** Urushni ochish yoki sulh e'lon qilish\n"
        f"• 📢 **Xabar tarqatish:** Botdagi barcha o'yinchilarga e'lon yo'llash\n"
        f"• 💰 **Oltin berish:** O'yinchiga oltin qo'shish yoki belgilash\n"
        f"• ❄️ **Ajdarlarni muzdan chiqarish:** Barcha yoki bitta Lord ajdarlarini ochish\n"
        f"• 🔄 **Xonadonni ko'chirish / bo'shatish:** Xonadonlarni boshqarish\n"
        f"• 💾 **Baza zaxirasi:** Bot ma'lumotlar bazasini yuklab olish yoki tiklash\n"
        f"• 📊 **Statistika:** Foydalanuvchilar va janglar statistikasi"
    )

    kb = await get_admin_panel_kb(message.from_user.id)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "admin_back")
async def callback_admin_back(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.clear()
    is_war = await get_war_status()
    war_badge = "🟢 **Ochiq**" if is_war else "🔴 **Sulh davri**"
    text = (
        "👑 **QADIMGI VALERIYA — BOSHQARUV PANELI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Urush holati: {war_badge}\n\n"
        "Quyidagi boshqaruv tugmalaridan birini tanlang:"
    )
    kb = await get_admin_panel_kb(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_cancel")
async def callback_admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.clear()
    kb = await get_admin_panel_kb(callback.from_user.id)
    await callback.message.edit_text("✅ Amaliyot bekor qilindi.", reply_markup=kb, parse_mode="Markdown")
    await callback.answer("Bekor qilindi")

# --- 1. XABAR TARQATISH (BROADCAST) ---

@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_broadcast)
    text = (
        "📢 **BARCHA O'YINCHILARGA XABAR TARQATISH:**\n\n"
        "Barcha o'yinchilarga yubormoqchi bo'lgan xabaringizni matn yoki rasm ko'rinishida yuboring:\n\n"
        "🔙 *Bekor qilish uchun /cancel deb yozing yoki tugmani bosing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_broadcast)
async def process_admin_broadcast(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Xabar tarqatish bekor qilindi.", reply_markup=admin_panel_kb())
        return

    users = await get_all_users()
    sent_count = 0
    fail_count = 0

    status_msg = await message.answer(f"📢 Xabar {len(users)} ta o'yinchiga yuborilmoqda...")

    for u in users:
        t_id = u["telegram_id"]
        try:
            if message.photo:
                photo_id = message.photo[-1].file_id
                caption = f"📢 **VALERIYA HUKMDORLARIDAN MUHIM XABAR:**\n\n{message.caption or ''}"
                await message.bot.send_photo(t_id, photo=photo_id, caption=caption, parse_mode="Markdown")
            elif message.text:
                await message.bot.send_message(
                    t_id,
                    f"📢 **VALERIYA HUKMDORLARIDAN MUHIM XABAR:**\n\n{message.text}",
                    parse_mode="Markdown"
                )
            sent_count += 1
        except Exception:
            fail_count += 1

    await state.clear()
    await status_msg.edit_text(
        f"✅ **Xabar tarqatish yakunlandi!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• Yetkazildi: **{sent_count} ta**\n"
        f"• Yetkazilmadi (bloklagan): **{fail_count} ta**",
        reply_markup=admin_panel_kb(),
        parse_mode="Markdown"
    )

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if not await is_admin(message.from_user.id):
        return

    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        await message.answer("⚠️ Format: `/broadcast <xabar_matni>`", parse_mode="Markdown")
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
        f"✅ **Xabar tarqatish yakunlandi!**\n"
        f"• Yetkazildi: {sent_count} ta\n"
        f"• Yetkazilmadi: {fail_count} ta"
    )

# --- 2. O'YINCHIGA OLTIN BERISH (GIVE GOLD) ---

@router.callback_query(F.data == "admin_give_gold")
async def callback_admin_give_gold_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_give_gold)
    text = (
        "💰 **O'YINCHIGA OLTIN BERISH:**\n\n"
        "O'yinchining Telegram ID si va beriladigan oltin miqdorini kiriting:\n\n"
        "Format: `<user_id> <miqdor>`\n"
        "Masalan: `7009689119 5000`\n\n"
        "🔙 *Bekor qilish uchun /cancel deb yozing yoki tugmani bosing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_give_gold, F.text)
async def process_admin_give_gold(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Oltin berish bekor qilindi.", reply_markup=admin_panel_kb())
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Noto'g'ri format! Format: `<user_id> <miqdor>`\nMasalan: `7009689119 500`")
        return

    try:
        user_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqamlarda kiriting!")
        return

    success, msg, new_balance = await admin_give_gold_add(user_id, amount)
    await state.clear()

    if success:
        await message.answer(f"✅ {msg}", reply_markup=admin_panel_kb(), parse_mode="Markdown")
        try:
            await message.bot.send_message(
                user_id,
                f"👑 **Valeriya Oliy Hukmdoridan tuhfa!**\nSizning xazinangizga **+{amount} 🪙** oltin qo'shildi!\nHozirgi balansingiz: **{new_balance} 🪙**.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    else:
        await message.answer(f"⚠️ {msg}", reply_markup=admin_panel_kb())

@router.message(Command("givegold"))
async def cmd_givegold(message: types.Message):
    if not await is_admin(message.from_user.id):
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

    success, msg, new_balance = await admin_give_gold_add(user_id, amount)
    if success:
        await message.answer(f"✅ {msg}")
    else:
        await message.answer(f"⚠️ {msg}")

# --- 3. AJDARLARNI MUZDAN CHIQARISH (UNFREEZE) ---

@router.callback_query(F.data == "admin_unfreeze")
async def callback_admin_unfreeze_menu(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    text = (
        "❄️ **AJDARLARNI MUZDAN CHIQARISH:**\n\n"
        "Qaysi usuldan foydalanmoqchisiz?\n"
        "• **Barcha o'yinchilar:** Barcha o'yinchilarning ajdarlari shu zahoti ochiladi.\n"
        "• **Bitta o'yinchi:** Faqat tanlangan o'yinchi ID si bo'yicha."
    )
    await callback.message.edit_text(text, reply_markup=admin_unfreeze_options_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_unfreeze_all")
async def callback_admin_unfreeze_all(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    count = await admin_unfreeze_all_dragons()
    await callback.message.edit_text(
        f"🔥 **Muvaffaqiyatli!** Valeriyadagi jami **{count} ta** muzlagan ajdarlar to'liq muzdan chiqarildi va jangga tayyor!",
        reply_markup=admin_panel_kb(),
        parse_mode="Markdown"
    )
    await callback.answer("Barcha ajdarlar muzdan chiqarildi! 🔥", show_alert=True)

@router.callback_query(F.data == "admin_unfreeze_single")
async def callback_admin_unfreeze_single_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_unfreeze_user)
    text = (
        "❄️ **BITTA O'YINCHI AJDARLARINI MUZDAN CHIQARISH:**\n\n"
        "O'yinchining Telegram ID sini kiriting:\n"
        "Masalan: `7009689119`\n\n"
        "🔙 *Bekor qilish uchun /cancel deb yozing yoki tugmani bosing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_unfreeze_user, F.text)
async def process_admin_unfreeze_single(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_kb())
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Iltimos, Telegram ID raqamini to'g'ri kiriting!")
        return

    count = await admin_unfreeze_dragons(user_id)
    await state.clear()
    await message.answer(
        f"🔥 Foydalanuvchi `{user_id}` ning **{count} ta** ajdari muzdan chiqarildi va jangga tayyor!",
        reply_markup=admin_panel_kb(),
        parse_mode="Markdown"
    )

@router.message(Command("unfreeze"))
async def cmd_unfreeze(message: types.Message):
    if not await is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: `/unfreeze <user_id>` yoki `/unfreeze all`", parse_mode="Markdown")
        return

    param = parts[1].strip().lower()
    if param == "all":
        count = await admin_unfreeze_all_dragons()
        await message.answer(f"🔥 Barcha {count} ta ajdar muzdan chiqarildi!")
    else:
        try:
            user_id = int(param)
        except ValueError:
            await message.answer("⚠️ ID raqam bo'lishi kerak!")
            return
        count = await admin_unfreeze_dragons(user_id)
        await message.answer(f"🔥 {user_id} ning {count} ta ajdari muzdan chiqarildi!")

# --- 4. XONADONNI KO'CHIRISH (TRANSFER HOUSE) ---

@router.callback_query(F.data == "admin_transfer_house")
async def callback_admin_transfer_house_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_transfer_house)
    text = (
        "🔄 **O'YINCHINI BOSHQA XONADONGA KO'CHIRISH:**\n\n"
        "O'yinchining Telegram ID si va yangi xonadon raqamini kiriting:\n\n"
        "Format: `<user_id> <yangi_house_id>`\n"
        "Masalan: `7009689119 1` (1 dan 52 gacha)\n\n"
        "🔙 *Bekor qilish uchun /cancel deb yozing yoki tugmani bosing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_transfer_house, F.text)
async def process_admin_transfer_house(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Xonadon ko'chirish bekor qilindi.", reply_markup=admin_panel_kb())
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("⚠️ Format: `<user_id> <new_house_id>`\nMasalan: `7009689119 1`")
        return

    try:
        user_id = int(parts[0])
        new_house_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ Iltimos, raqamlarda kiriting!")
        return

    success, msg = await admin_transfer_house(user_id, new_house_id)
    await state.clear()

    if success:
        await message.answer(f"✅ {msg}", reply_markup=admin_panel_kb(), parse_mode="Markdown")
        try:
            await message.bot.send_message(
                user_id,
                f"👑 **Boshqaruv o'zgardi!**\nAdmin sizning xonadoningizni **#{new_house_id}** xonadoniga ko'chirdi!\nProfilingizdan tekshirishingiz mumkin.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    else:
        await message.answer(f"⚠️ {msg}", reply_markup=admin_panel_kb())

@router.message(Command("transferhouse"))
async def cmd_transfer_house(message: types.Message):
    if not await is_admin(message.from_user.id):
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
        await message.answer(f"⚠️ {msg}")

# --- 5. XONADONNI BO'SHATISH (CLEAR HOUSE) ---

@router.callback_query(F.data == "admin_clear_house")
async def callback_admin_clear_house_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_clear_house)
    text = (
        "🏠 **XONADONNI BO'SHATISH (Egani chiqarib tashlash):**\n\n"
        "Bo'shatmoqchi bo'lgan xonadon raqamini kiriting (1 dan 52 gacha):\n"
        "Masalan: `11`\n\n"
        "🔙 *Bekor qilish uchun /cancel deb yozing yoki tugmani bosing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_clear_house, F.text)
async def process_admin_clear_house(message: types.Message, state: FSMContext):
    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Xonadonni bo'shatish bekor qilindi.", reply_markup=admin_panel_kb())
        return

    try:
        house_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Iltimos, xonadon raqamini kiriting (1 dan 52 gacha)!")
        return

    if house_id < 1 or house_id > 52:
        await message.answer("⚠️ Xonadon raqami 1 dan 52 gacha bo'lishi kerak!")
        return

    await admin_free_house(house_id)
    await state.clear()
    await message.answer(f"✅ **#{house_id} xonadon muvaffaqiyatli bo'shatildi!**", reply_markup=admin_panel_kb(), parse_mode="Markdown")

@router.message(Command("freehouse"))
async def cmd_freehouse(message: types.Message):
    if not await is_admin(message.from_user.id):
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

# --- 6. STATISTIKA VA RESTART ---

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return

    users = await get_all_users()
    houses = await get_houses()

    occupied = len([h for h in houses if h["owner_id"] is not None])
    vassals = len([h for h in houses if h["overlord_id"] is not None])
    total_gold = sum(u.get("gold", 0) for u in users)

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
    if not is_super_admin(callback.from_user.id):
        await callback.answer("O'yinni restart qilish faqat Bosh Admin uchun!", show_alert=True)
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
    if not await is_admin(callback.from_user.id):
        return

    kb = await get_admin_panel_kb(callback.from_user.id)
    await callback.message.edit_text("✅ Restart bekor qilindi.", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_do_restart")
async def callback_admin_do_restart(callback: types.CallbackQuery):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("O'yinni restart qilish faqat Bosh Admin uchun!", show_alert=True)
        return

    await admin_restart_game()
    success_text = (
        "🔄 **O'YIN TO'LIQ RESTART QILINDI!** 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• Barcha 52 ta Valeriya xonadoni yana bo'shatildi.\n"
        "• Barcha armiyalar va janglar tarixi tozalandi.\n"
        "• O'yin noldan yangidan boshlandi!"
    )
    kb = await get_admin_panel_kb(callback.from_user.id)
    await callback.message.edit_text(success_text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer("O'yin muvaffaqiyatli restart qilindi!", show_alert=True)

@router.message(Command("restartgame"))
async def cmd_restartgame(message: types.Message):
    if not is_super_admin(message.from_user.id):
        return

    warn_text = (
        "⚠️ **DIQQAT! O'YINNI TO'LIQ RESTART QILISH!**\n\n"
        "Barcha xonadonlar, armiyalar va ma'lumotlar tozalanadi. Tasdiqlaysizmi?"
    )
    await message.answer(warn_text, reply_markup=admin_restart_confirm_kb(), parse_mode="Markdown")

# --- 7. BLOKLASH VA BLOKDAN CHIQARISH ---

@router.message(Command("block"))
async def cmd_block_user(message: types.Message):
    if not await is_admin(message.from_user.id):
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
    if not await is_admin(message.from_user.id):
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

# --- 8. GREEN BANK TO'LOVLARINI TASDIQLASH / RAD ETISH ---

@router.callback_query(F.data.startswith("approve_don:"))
async def callback_approve_donation(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    donation_id = int(callback.data.split(":")[1])
    success, msg, info = await approve_donation_request(donation_id, callback.from_user.id)

    if success:
        await callback.answer("To'lov tasdiqlandi! ✅", show_alert=True)
        admin_name = escape_md(callback.from_user.full_name)
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
    if not await is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    donation_id = int(callback.data.split(":")[1])
    success, msg, user_id = await reject_donation_request(donation_id, callback.from_user.id)

    if success:
        await callback.answer("To'lov rad etildi! ❌", show_alert=True)
        admin_name = escape_md(callback.from_user.full_name)
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

@router.callback_query(F.data == "admin_distribute_tournament")
async def callback_admin_distribute_tournament(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    success, msg = await distribute_weekly_tournament_rewards()
    await callback.answer(msg, show_alert=True)
    if success:
        await callback.message.answer(
            f"🎁 **Haftalik Turnir Sovg'alari Tarqatildi!**\n\n{msg}",
            parse_mode="Markdown"
        )

# --- 7. URUSH HOLATINI OCHISH / YOPISH ---

@router.callback_query(F.data == "admin_toggle_war")
async def callback_admin_toggle_war(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    new_st = await toggle_war_status()
    st_text = "🟢 **URUSH OCHIQ** (Lordlar bir-biriga hujum qilishi mumkin)" if new_st else "🔴 **SULH DAVRI** (Barcha janglar va hujumlar to'xtatildi)"
    await callback.answer(f"Urush holati: {'Ochiq' if new_st else 'Sulh davri'}", show_alert=True)

    text = (
        "👑 **QADIMGI VALERIYA — BOSHQARUV PANELI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ Joriy Urush Holati: {st_text}\n\n"
        "Quyidagi boshqaruv tugmalaridan birini tanlang:"
    )
    kb = await get_admin_panel_kb(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- 8. ADMINLARNI BOSHQARISH (KATTA ADMIN UCHUN) ---

@router.callback_query(F.data == "admin_manage_admins")
async def callback_admin_manage_admins(callback: types.CallbackQuery):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Bu bo'lim faqat Bosh Admin uchun!", show_alert=True)
        return

    admins = await get_all_bot_admins()
    text = (
        "👑 **BOT ADMINLARINI BOSHQARISH (KATTA ADMIN)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Siz botga yangi admin tayinlashingiz yoki mavjud adminlarni ro'yxatdan o'chirishingiz mumkin.\n\n"
        "📋 **Joriy adminlar ro'yxati:**\n"
    )
    for adm in admins:
        role_label = "👑 Bosh Admin" if adm.get("role") == "super_admin" else "🛡 Admin"
        u_str = f" (@{adm['username']})" if adm.get("username") else ""
        text += f"• {role_label}: **{adm['full_name']}**{u_str} — ID: `{adm['telegram_id']}`\n"

    kb = admin_manage_admins_kb(admins)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_admin:"))
async def callback_admin_del_admin(callback: types.CallbackQuery):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat Bosh Admin o'chira oladi!", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    success, msg = await remove_bot_admin(target_id)
    await callback.answer(msg, show_alert=True)

    admins = await get_all_bot_admins()
    text = (
        "👑 **BOT ADMINLARINI BOSHQARISH (KATTA ADMIN)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{msg}\n\n"
        "📋 **Joriy adminlar ro'yxati:**\n"
    )
    for adm in admins:
        role_label = "👑 Bosh Admin" if adm.get("role") == "super_admin" else "🛡 Admin"
        u_str = f" (@{adm['username']})" if adm.get("username") else ""
        text += f"• {role_label}: **{adm['full_name']}**{u_str} — ID: `{adm['telegram_id']}`\n"

    kb = admin_manage_admins_kb(admins)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "admin_add_admin_prompt")
async def callback_admin_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat Bosh Admin tayinlay oladi!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_add_admin)
    text = (
        "➕ **YANGI ADMIN TAYINLASH:**\n\n"
        "Admin qilmoqchi bo'lgan o'yinchining **Telegram ID** raqamini yuboring:\n"
        "(Masalan: `7009689119`)\n\n"
        "*(Eslatma: Foydalanuvchi botga avval kamida 1 marta /start bosgan bo'lishi kerak)*\n\n"
        "🔙 *Bekor qilish uchun /cancel deb yozing yoki tugmani bosing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_add_admin)
async def process_admin_add_admin(message: types.Message, state: FSMContext):
    if not is_super_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        kb = await get_admin_panel_kb(message.from_user.id)
        await message.answer("Admin tayinlash bekor qilindi.", reply_markup=kb)
        return

    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat Telegram ID raqamini kiriting. Masalan: `7009689119`")
        return

    success, msg = await add_bot_admin(target_id, message.from_user.id)
    await state.clear()
    kb = await get_admin_panel_kb(message.from_user.id)
    if success:
        await message.answer(msg, reply_markup=kb, parse_mode="Markdown")
        try:
            await message.bot.send_message(
                target_id,
                "👑 **TABRIKLAYMIZ!**\nSiz Katta Admin tomonidan Valeriya Boshqaruv Admini etib tayinlandingiz! /admin buyrug'i orqali boshqaruv paneliga kirishingiz mumkin.",
                reply_markup=main_menu_keyboard(target_id, is_admin=True)
            )
        except Exception:
            pass
    else:
        await message.answer(f"❌ {msg}", reply_markup=kb)

# --- 9. BAZA ZAXIRASINI YUKLAB OLISH VA TIKLASH ---

@router.callback_query(F.data == "admin_backup_db")
async def callback_admin_backup_db(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return

    db_path = "valyria.db"
    if not os.path.exists(db_path):
        await callback.answer("valyria.db fayli topilmadi!", show_alert=True)
        return

    file_size_kb = round(os.path.getsize(db_path) / 1024, 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    caption = (
        f"💾 **VALERIYA MA'LUMOTLAR BAZASI ZAXIRASI (BACKUP)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Sana: `{now_str}`\n"
        f"📦 Hajmi: `{file_size_kb} KB`\n\n"
        f"Ushbu faylda barcha o'yinchilar, xonadonlar, armiyalar va barcha sozlamalar saqlangan."
    )

    await callback.answer("Baza fayli yuborilmoqda...")
    try:
        doc = FSInputFile(db_path, filename=f"valyria_backup_{int(datetime.now().timestamp())}.db")
        await callback.message.answer_document(doc, caption=caption, parse_mode="Markdown")
    except Exception as e:
        await callback.message.answer(f"❌ Faylni yuborishda xatolik: {e}")

@router.callback_query(F.data == "admin_restore_db")
async def callback_admin_restore_db(callback: types.CallbackQuery, state: FSMContext):
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Bazani tiklash faqat Bosh Admin uchun ruxsat etilgan!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_db_file)
    text = (
        "📥 **BAZANI FAYLDAN TIKLASH (DATABASE RESTORE):**\n\n"
        "Tiklamoqchi bo'lgan `.db` yoki `.sqlite` ma'lumotlar bazasi faylini botga **Fayl (Hujjat/Document)** ko'rinishida yuboring.\n\n"
        "⚠️ *Ogohlantirish: Mavjud bazaning zaxira nusxasi (valyria.db.bak) yaratiladi va yangi fayl o'rniga qo'yiladi!*"
        "\n\n🔙 *Bekor qilish uchun /cancel deb yozing.*"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminStates.waiting_for_db_file)
async def process_admin_db_restore_file(message: types.Message, state: FSMContext):
    if not is_super_admin(message.from_user.id):
        return
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        kb = await get_admin_panel_kb(message.from_user.id)
        await message.answer("Bazani tiklash bekor qilindi.", reply_markup=kb)
        return

    if not message.document:
        await message.answer("❌ Iltimos, `.db` kengaytmali ma'lumotlar bazasi faylini yuboring!")
        return

    doc = message.document
    if not (doc.file_name.endswith(".db") or doc.file_name.endswith(".sqlite") or doc.file_name.endswith(".sqlite3")):
        await message.answer("❌ Faqat `.db` yoki `.sqlite` fayllari qabul qilinadi!")
        return

    try:
        # 1. Zaxira nusxa yaratish
        if os.path.exists("valyria.db"):
            shutil.copyfile("valyria.db", "valyria.db.bak")

        # 2. Yangi faylni yuklab olish
        file = await message.bot.get_file(doc.file_id)
        await message.bot.download_file(file.file_path, "valyria.db")

        await state.clear()
        kb = await get_admin_panel_kb(message.from_user.id)
        await message.answer(
            "✅ **MA'LUMOTLAR BAZASI MUVAFFAQIYATLI TIKLANDI!**\n\n"
            f"Fayl: `{doc.file_name}`\n"
            "Avvalgi baza `valyria.db.bak` nomli zaxiraga olindi.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception as e:
        await state.clear()
        kb = await get_admin_panel_kb(message.from_user.id)
        await message.answer(f"❌ Bazani tiklashda xatolik yuz berdi: {e}", reply_markup=kb)

