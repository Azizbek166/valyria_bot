import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from database import (
    get_user, get_user_army, claim_daily_bonus, update_user_gold,
    buy_sword_bank_troops, take_bank_loan, repay_bank_loan
)
from keyboards import (
    sword_bank_main_kb, troop_buy_kb, loan_packages_kb, loan_repay_kb
)
from config import escape_md, UNITS, LOAN_PACKAGES

logger = logging.getLogger(__name__)

router = Router()

async def build_sword_bank_text(user_id: int) -> tuple[str, bool]:
    user = await get_user(user_id)
    army = await get_user_army(user_id)
    gold = user.get("gold", 0) if user else 0
    debt = user.get("debt_amount", 0) if user else 0
    due = user.get("debt_due_amount", 0) if user else 0

    soldiers = army.get("soldiers", 0)
    archers = army.get("archers", 0)
    cavalry = army.get("cavalry", 0)

    debt_status = f"🔴 **{debt} 🪙** (Qaytarish: **{due} 🪙**)" if due > 0 else "🟢 **Qarzingiz yo'q**"

    text = (
        "⚔️ **VALERIYA SWORD BANKI (HARBIY MOLIYA VA ZARBXONA)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Xazinangizdagi jami boylik: **{gold} 🪙**\n"
        f"💳 Qarz holati: {debt_status}\n\n"
        "🛡 **Sizning harbiy qismlaringiz:**\n"
        f"• 🗡 Oddiy askar: **{soldiers} ta** (Kuch: +{soldiers})\n"
        f"• 🏹 Kamonchi: **{archers} ta** (Kuch: +{archers * 3})\n"
        f"• 🐎 Otliq: **{cavalry} ta** (Kuch: +{cavalry * 6})\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🗡 **Qo'shin xaridi:** Askar, Kamonchi yoki Otliq yollang!\n"
        "💳 **Qarz tizimi:** Janglar yoki ehtiyoj uchun qarz oling!\n"
        "🎁 **Kunlik bonus:** Har 24 soatda bepul oltin oling.\n"
        "💸 **O'tkazma:** `/pay <telegram_id> <miqdor>`"
    )
    return text, due > 0

@router.message(F.text.in_(["⚔️ Sword Bank", "🏦 Sword Bank", "🏦 Golden"]))
async def show_bank_menu(message: types.Message):
    try:
        user_id = message.from_user.id
        text, has_debt = await build_sword_bank_text(user_id)
        await message.answer(text, reply_markup=sword_bank_main_kb(has_debt=has_debt), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Sword Bank menyusida xatolik: {e}", exc_info=True)
        await message.answer("⚔️ Sword Bank menyusini ochishda xatolik yuz berdi.")

@router.callback_query(F.data == "sword_bank_back")
async def callback_sword_bank_back(callback: types.CallbackQuery):
    try:
        user_id = callback.from_user.id
        text, has_debt = await build_sword_bank_text(user_id)
        await callback.message.edit_text(text, reply_markup=sword_bank_main_kb(has_debt=has_debt), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Sword bank back xatolik: {e}")
        await callback.answer()

# --- Harbiy qismlar xaridi (Askar, Kamonchi, Otliq) ---

@router.callback_query(F.data.startswith("buy_unit_menu:"))
async def callback_buy_unit_menu(callback: types.CallbackQuery):
    unit_type = callback.data.split(":")[1]
    unit_info = {
        "soldier": {"title": "ODDIY ASKAR 🗡", "cost": 1, "power": 1, "desc": "Ishonchli va arzon piyoda jangchi."},
        "archer": {"title": "KAMONCHI 🏹", "cost": 3, "power": 3, "desc": "Uzoq masofadan aniq zarba beruvchi mergan."},
        "cavalry": {"title": "OTLIQ ASKAR 🐎", "cost": 5, "power": 6, "desc": "Tezkor va yorib o'tuvchi og'ir otliq qo'shin."}
    }.get(unit_type, {"title": "HARBIY QISM", "cost": 1, "power": 1, "desc": ""})

    user = await get_user(callback.from_user.id)
    user_gold = user.get("gold", 0) if user else 0

    text = (
        f"⚔️ **{unit_info['title']} YOLLASH**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📜 {unit_info['desc']}\n\n"
        f"💰 1 ta jangchi narxi: **{unit_info['cost']} 🪙**\n"
        f"⚡️ Jangovar quvvati: **+{unit_info['power']} ball**\n"
        f"🪙 Xazinangizdagi oltin: **{user_gold} 🪙**\n\n"
        f"Qancha miqdorda yollamoqchisiz? Quyidagi tugmalardan birini tanlang:"
    )

    await callback.message.edit_text(text, reply_markup=troop_buy_kb(unit_type), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_unit_exec:"))
async def callback_buy_unit_exec(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    unit_type = parts[1]
    count = int(parts[2])

    success, msg = await buy_sword_bank_troops(callback.from_user.id, unit_type, count)
    if success:
        await callback.answer("Qo'shin saflarga qo'shildi! ⚔️", show_alert=True)
        text, has_debt = await build_sword_bank_text(callback.from_user.id)
        await callback.message.edit_text(
            f"✅ {msg}\n\n{text}",
            reply_markup=sword_bank_main_kb(has_debt=has_debt),
            parse_mode="Markdown"
        )
    else:
        await callback.answer(msg, show_alert=True)

# --- Qarz Tizimi (Loans) ---

@router.callback_query(F.data == "loan_take_menu")
async def callback_loan_take_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    due = user.get("debt_due_amount", 0) if user else 0

    if due > 0:
        await callback.answer(f"Sizda allaqachon to'lanmagan {due} 🪙 qarz mavjud! Avval uni to'lang.", show_alert=True)
        return

    text = (
        "💳 **SWORD BANK QARZ TIZIMI (KREDIT)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Urushlar, yangi askarlar yollash yoki xonadoningizni rivojlantirish uchun "
        "Sword Bankdan darhol foizli qarz olishingiz mumkin!\n\n"
        "📌 **Shartlar:**\n"
        "• Foiz stavkasi: bor-yo'g'i **+15%** ustama.\n"
        "• Olingan oltin shu zahoti xazinangizga qo'shiladi.\n"
        "• Qarzni xohlagan vaqtingizda bo'lib yoki to'liq to'lashingiz mumkin.\n"
        "• To'lanmagan qarz turganda yangi qarz olish mumkin emas.\n\n"
        "Kerakli qarz paketini tanlang:"
    )

    await callback.message.edit_text(text, reply_markup=loan_packages_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("loan_take:"))
async def callback_loan_take(callback: types.CallbackQuery):
    package_id = int(callback.data.split(":")[1])
    success, msg = await take_bank_loan(callback.from_user.id, package_id)

    if success:
        await callback.answer("Qarz hisobingizga o'tkazildi! 🪙", show_alert=True)
        text, has_debt = await build_sword_bank_text(callback.from_user.id)
        await callback.message.edit_text(
            f"{msg}\n\n{text}",
            reply_markup=sword_bank_main_kb(has_debt=has_debt),
            parse_mode="Markdown"
        )
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "loan_repay_menu")
async def callback_loan_repay_menu(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    due = user.get("debt_due_amount", 0) if user else 0
    gold = user.get("gold", 0) if user else 0

    if due <= 0:
        await callback.answer("Sizda faol qarz yo'q!", show_alert=True)
        return

    text = (
        "💸 **SWORD BANK QARZINI TO'LASH**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 To'lanishi kerak bo'lgan jami qarz: **{due} 🪙**\n"
        f"💰 Xazinangizdagi mavjud oltin: **{gold} 🪙**\n\n"
        "Qarzni to'lash usulini tanlang:"
    )

    await callback.message.edit_text(text, reply_markup=loan_repay_kb(due), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "loan_repay_full")
async def callback_loan_repay_full(callback: types.CallbackQuery):
    success, msg = await repay_bank_loan(callback.from_user.id, amount=None)
    if success:
        await callback.answer("To'lov amalga oshirildi! 💸", show_alert=True)
        text, has_debt = await build_sword_bank_text(callback.from_user.id)
        await callback.message.edit_text(
            f"{msg}\n\n{text}",
            reply_markup=sword_bank_main_kb(has_debt=has_debt),
            parse_mode="Markdown"
        )
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "loan_repay_all_gold")
async def callback_loan_repay_all_gold(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    user_gold = user.get("gold", 0) if user else 0
    if user_gold <= 0:
        await callback.answer("Xazinangizda qarz to'lash uchun oltin yo'q!", show_alert=True)
        return

    success, msg = await repay_bank_loan(callback.from_user.id, amount=user_gold)
    if success:
        await callback.answer("To'lov qilindi! 💸", show_alert=True)
        text, has_debt = await build_sword_bank_text(callback.from_user.id)
        await callback.message.edit_text(
            f"{msg}\n\n{text}",
            reply_markup=sword_bank_main_kb(has_debt=has_debt),
            parse_mode="Markdown"
        )
    else:
        await callback.answer(msg, show_alert=True)

# --- Kunlik Oltin Bonusi va Moliyaviy hisobot ---

@router.callback_query(F.data == "bank_claim_daily")
async def callback_claim_daily(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    success, msg = await claim_daily_bonus(user_id)

    if success:
        await callback.answer("Bonus olindi! 🪙", show_alert=True)
        text, has_debt = await build_sword_bank_text(user_id)
        await callback.message.edit_text(
            f"🎁 {msg}\n\n{text}",
            reply_markup=sword_bank_main_kb(has_debt=has_debt),
            parse_mode="Markdown"
        )
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data == "bank_info")
async def callback_bank_info(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    gold = user.get("gold", 0) if user else 0
    due = user.get("debt_due_amount", 0) if user else 0
    await callback.answer(f"Xazinangizda: {gold} 🪙\nQarzingiz: {due} 🪙", show_alert=True)

# --- Oltin o'tkazmasi (/pay) ---

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

    target_name = escape_md(target.get("custom_name") or target.get("full_name") or "Lord")
    sender_name = escape_md(sender.get("custom_name") or sender.get("full_name") or "Lord")

    await message.answer(
        f"✅ Muvaffaqiyatli o'tkazildi!\n"
        f"Lord **{target_name}**ga **{amount} 🪙** yuborildi.",
        parse_mode="Markdown"
    )

    try:
        await message.bot.send_message(
            target_id,
            f"💰 Sizga Lord **{sender_name}** tomonidan **+{amount} 🪙** o'tkazildi!",
            parse_mode="Markdown"
        )
    except Exception:
        pass
