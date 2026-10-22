import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS, escape_md
from database import (
    get_all_users, admin_set_gold, admin_free_house,
    admin_unfreeze_dragons, admin_unfreeze_all_dragons,
    admin_give_gold_add, get_houses, get_db_connection,
    admin_restart_game, set_user_blocked, admin_transfer_house,
    approve_donation_request, reject_donation_request, get_user
)
from keyboards import (
    admin_panel_kb, admin_restart_confirm_kb,
    admin_unfreeze_options_kb, admin_cancel_kb
)

logger = logging.getLogger(__name__)

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_give_gold = State()
    waiting_for_unfreeze_user = State()
    waiting_for_transfer_house = State()
    waiting_for_clear_house = State()

@router.message(F.text == "👑 Admin paneli")
@router.message(Command("admin"))
async def show_admin_panel(message: types.Message, state: FSMContext = None):
    if not is_admin(message.from_user.id):
        return

    if state:
        await state.clear()

    text = (
        "👑 **QADIMGI VALERIYA — BOSH ADMIN BOSHQARUV PANELI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Boshqaruv tugmalari orqali istalgan amaliyotni bajaring:\n\n"
        "• 📢 **Xabar tarqatish:** Botdagi barcha o'yinchilarga e'lon yo'llash\n"
        "• 💰 **Oltin berish:** O'yinchiga oltin o'rnatish yoki qo'shish\n"
        "• ❄️ **Ajdarlarni muzdan chiqarish:** Barcha yoki bitta Lord ajdarlarini ochish\n"
        "• 🔄 **Xonadonni ko'chirish:** O'yinchini boshqa xonadonga o'tkazish\n"
        "• 🏠 **Xonadonni bo'shatish:** Xonadonni egasidan tozalash\n"
        "• 📊 **Statistika:** Foydalanuvchilar, janglar va iqtisodiyot\n\n"
        "Shuningdek, buyruqlar: `/givegold`, `/broadcast`, `/unfreeze`, `/transferhouse`, `/freehouse`."
    )

    await message.answer(text, reply_markup=admin_panel_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_back")
async def callback_admin_back(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    text = (
        "👑 **QADIMGI VALERIYA — BOSH ADMIN BOSHQARUV PANELI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Quyidagi boshqaruv tugmalaridan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=admin_panel_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_cancel")
async def callback_admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("✅ Amaliyot bekor qilindi.", reply_markup=admin_panel_kb(), parse_mode="Markdown")
    await callback.answer("Bekor qilindi")

# --- 1. XABAR TARQATISH (BROADCAST) ---

@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
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
    if not is_admin(message.from_user.id):
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
    if not is_admin(callback.from_user.id):
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

    success, msg, new_balance = await admin_give_gold_add(user_id, amount)
    if success:
        await message.answer(f"✅ {msg}")
    else:
        await message.answer(f"⚠️ {msg}")

# --- 3. AJDARLARNI MUZDAN CHIQARISH (UNFREEZE) ---

@router.callback_query(F.data == "admin_unfreeze")
async def callback_admin_unfreeze_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
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
    if not is_admin(callback.from_user.id):
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
    if not is_admin(callback.from_user.id):
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
    if not is_admin(message.from_user.id):
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
    if not is_admin(callback.from_user.id):
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
        await message.answer(f"⚠️ {msg}")

# --- 5. XONADONNI BO'SHATISH (CLEAR HOUSE) ---

@router.callback_query(F.data == "admin_clear_house")
async def callback_admin_clear_house_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
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

# --- 6. STATISTIKA VA RESTART ---

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
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

# --- 7. BLOKLASH VA BLOKDAN CHIQARISH ---

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

# --- 8. GREEN BANK TO'LOVLARINI TASDIQLASH / RAD ETISH ---

@router.callback_query(F.data.startswith("approve_don:"))
async def callback_approve_donation(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
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
    if not is_admin(callback.from_user.id):
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
