from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import DONATE_CARD, DONATE_CARD_HOLDER, DONATE_PACKAGES, ADMIN_IDS, escape_md
from database import get_user, create_donation_request
from keyboards import (
    green_bank_packages_kb, green_bank_package_detail_kb,
    admin_donation_verify_kb
)

router = Router()

class GreenBankStates(StatesGroup):
    waiting_for_receipt = State()

@router.message(F.text == "💳 Green Bank")
async def show_green_bank_main(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    valyrian_steel = (user.get("valyrian_steel", 0) or 0) if user else 0

    text = (
        "💳 **GREEN BANK (DONATE) — RASMIY HAMKORLIK XAZINASI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Green Bank orqali o'zbek so'mida to'lov qilib, eng nodir resurslar, "
        "Valeriya po'lati, Benuqson jangchilar, Zahar va Yuzsiz qotillarni xarid qilishingiz mumkin!\n\n"
        f"💳 **To'lov kartasi:** `{DONATE_CARD}`\n"
        f"👤 **Karta egasi:** {DONATE_CARD_HOLDER}\n\n"
        f"🗡 **Sizdagi Valeriya po'lati:** {valyrian_steel} dona "
        f"({'✨ Cheksiz Chakra faol!' if valyrian_steel >= 1 else '❌ Mavjud emas'})\n\n"
        "📦 **Mavjud paketlar:**\n"
        "1. **Kichik Fath Paketi** — 15,000 so'm\n"
        "   └ 2,000 🪙 Oltin + 200 Benuqson 🛡 + 5 Zahar 🧪 + 200 Chakra ⚙️\n"
        "2. **Jangovar Gvardiya** — 35,000 so'm\n"
        "   └ 6,000 🪙 + 500 Benuqson 🛡 + 1 Valeriya Po'lati ⚔️ + 10 Yuzsiz 🥷 + 5 Soya 👣 + 15 Zahar 🧪 + 500 Chakra ⚙️\n"
        "3. **Valeriya Qudrati** — 70,000 so'm\n"
        "   └ 15,000 🪙 + 1,500 Benuqson 🛡 + 3 Valeriya Po'lati ⚔️ + 25 Yuzsiz 🥷 + 15 Soya 👣 + 35 Zahar 🧪 + 1,000 Chakra ⚙️\n"
        "4. **Oliy Hukmdor Xazinasi** — 120,000 so'm\n"
        "   └ 35,000 🪙 + 4,000 Benuqson 🛡 + 6 Valeriya Po'lati ⚔️ + 60 Yuzsiz 🥷 + 40 Soya 👣 + 80 Zahar 🧪 + 2,500 Chakra ⚙️\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Batafsil ma'lumot va to'lov uchun paketni tanlang:"
    )

    await message.answer(text, reply_markup=green_bank_packages_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "gb_back")
async def callback_gb_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "💳 **GREEN BANK (DONATE) PAKETLARI**\n\n"
        f"💳 Karta: `{DONATE_CARD}` ({DONATE_CARD_HOLDER})\n\n"
        "Kerakli paketni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=green_bank_packages_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("gb_view:"))
async def callback_gb_view(callback: types.CallbackQuery):
    pkg_id = int(callback.data.split(":")[1])
    pkg = DONATE_PACKAGES.get(pkg_id)
    if not pkg:
        await callback.answer("Paket topilmadi!", show_alert=True)
        return

    text = (
        f"📦 **PAKET: {pkg['name']}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Narxi: **{pkg['cost_uzs']:,} so'm**\n"
        f"🎁 Tarkibi: **{pkg['desc']}**\n\n"
        f"💳 **To'lov uchun karta:**\n"
        f"`{DONATE_CARD}`\n"
        f"👤 Qabul qiluvchi: **{DONATE_CARD_HOLDER}**\n\n"
        f"📌 **Ko'rsatma:**\n"
        f"1. Yuqoridagi kartaga to'liq **{pkg['cost_uzs']:,} so'm** o'tkazing.\n"
        f"2. To'lov cheki skrinshotini oling.\n"
        f"3. Quyidagi **🧾 Chekni yuborish** tugmasini bosib, chekni yuboring.\n"
        f"4. Admin tasdiqlashi bilan barcha resurslar hisobingizga tushadi!"
    )

    await callback.message.edit_text(text, reply_markup=green_bank_package_detail_kb(pkg_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("gb_send_receipt:"))
async def callback_gb_send_receipt(callback: types.CallbackQuery, state: FSMContext):
    pkg_id = int(callback.data.split(":")[1])
    pkg = DONATE_PACKAGES.get(pkg_id)
    if not pkg:
        await callback.answer("Paket topilmadi!", show_alert=True)
        return

    await state.set_state(GreenBankStates.waiting_for_receipt)
    await state.update_data(package_id=pkg_id)

    prompt = (
        f"🧾 **{pkg['name']} ({pkg['cost_uzs']:,} so'm) uchun chekni yuboring:**\n\n"
        f"Iltimos, kartaga pul o'tkazilgan to'lov kvitansiyasining skrinshotini (rasm yoki fayl ko'rinishida) shu yerga jo'nating.\n\n"
        f"⚠️ Bekor qilish uchun istalgan boshqa bo'limga o'tishingiz mumkin."
    )
    await callback.message.answer(prompt, parse_mode="Markdown")
    await callback.answer()

@router.message(GreenBankStates.waiting_for_receipt, F.photo)
async def handle_receipt_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pkg_id = data.get("package_id")
    pkg = DONATE_PACKAGES.get(pkg_id)

    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    user_fullname = escape_md(message.from_user.full_name)
    username = f"@{escape_md(message.from_user.username)}" if message.from_user.username else "username yo'q"

    # Save to database
    donation_id = await create_donation_request(user_id, pkg_id, photo_id, "photo")
    await state.clear()

    # Inform user
    await message.answer(
        "✅ **To'lov cheki qabul qilindi!**\n\n"
        "Admin so'rovingizni tekshirib chiqqach, resurslar avtomatik tarzda profilingizga qo'shiladi. "
        "Odatda bu 5-15 daqiqa vaqt oladi. Sabringiz uchun rahmat!",
        parse_mode="Markdown"
    )

    # Notify Admins
    admin_caption = (
        "💳 **YANGI GREEN BANK DONATE TO'LOVI!** 🔔\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 So'rov ID: #{donation_id}\n"
        f"👤 O'yinchi: **{user_fullname}** ({username})\n"
        f"🆔 Telegram ID: `{user_id}`\n"
        f"📦 Paket: **{pkg['name']}**\n"
        f"💵 Summa: **{pkg['cost_uzs']:,} so'm**\n"
        f"🎁 Beriladigan resurslar:\n{pkg['desc']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "To'lovni tasdiqlaysizmi yoki rad etasizmi?"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=admin_caption,
                reply_markup=admin_donation_verify_kb(donation_id),
                parse_mode="Markdown"
            )
        except Exception:
            pass

@router.message(GreenBankStates.waiting_for_receipt, F.document)
async def handle_receipt_document(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pkg_id = data.get("package_id")
    pkg = DONATE_PACKAGES.get(pkg_id)

    doc_id = message.document.file_id
    user_id = message.from_user.id
    user_fullname = escape_md(message.from_user.full_name)
    username = f"@{escape_md(message.from_user.username)}" if message.from_user.username else "username yo'q"

    donation_id = await create_donation_request(user_id, pkg_id, doc_id, "document")
    await state.clear()

    await message.answer(
        "✅ **To'lov cheki qabul qilindi!**\n\n"
        "Admin so'rovingizni tekshirib chiqqach, resurslar hisobingizga qo'shiladi. "
        "Sabringiz uchun rahmat!",
        parse_mode="Markdown"
    )

    admin_caption = (
        "💳 **YANGI GREEN BANK DONATE TO'LOVI (Fayl)!** 🔔\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 So'rov ID: #{donation_id}\n"
        f"👤 O'yinchi: **{user_fullname}** ({username})\n"
        f"🆔 Telegram ID: `{user_id}`\n"
        f"📦 Paket: **{pkg['name']}**\n"
        f"💵 Summa: **{pkg['cost_uzs']:,} so'm**\n"
        f"🎁 Resurslar: {pkg['desc']}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_document(
                chat_id=admin_id,
                document=doc_id,
                caption=admin_caption,
                reply_markup=admin_donation_verify_kb(donation_id),
                parse_mode="Markdown"
            )
        except Exception:
            pass
