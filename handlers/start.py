from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from database import get_or_create_user, get_user_house, is_user_blocked, is_bot_admin
from keyboards import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    if await is_user_blocked(message.from_user.id):
        await message.answer("🚫 **Siz bot ma'muriyati tomonidan bloklangansiz!**", parse_mode="Markdown")
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    house = await get_user_house(message.from_user.id)
    house_text = f"Sizning xonadoningiz: **{house['name']}** 👑" if house else "Siz hali birorta ham xonadon tanlamagansiz! **🌋 Oila tanlash** tugmasi orqali xonadoningizni tanlang."

    welcome_text = (
        f"🔥 **Assalomu alaykum, Lord {message.from_user.full_name}!**\n\n"
        f"Xush kelibsiz **QADIMGI VALERIYA (OLD VALYRIA)** olamiga!\n\n"
        f"Bu yerda Qadimgi Valeriyaning afsonaviy 52 ta xonadoni (40 ta Quruqlik va 12 ta Dengiz Lordlari) "
        f"yashirin sirlar, oltinlar va cheksiz hokimiyat uchun kurashadilar.\n\n"
        f"🏛 {house_text}\n"
        f"💰 Boshlang'ich oltin: **{user['gold']} 🪙**\n\n"
        f"O'yinni boshlash uchun quyidagi tugmalardan birini tanlang:"
    )

    is_adm = await is_bot_admin(message.from_user.id)
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(message.from_user.id, is_admin=is_adm),
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📜 **Qadimgi Valeriya o'yini qo'llanmasi:**\n\n"
        "1. **🌋 Oila tanlash**: 52 ta Valeriya xonadonidan birini tanlang. Har bir xonadonni faqat 1 kishi boshqarishi mumkin!\n"
        "2. **🐉 Hayvonlarim & Armiya**: Ajdar (400🪙, 500 ball) va Oʻrgimchak (300🪙, 500 ball) xarid qiling. Ajdarni B (1000), A (1500) va S (2000) darajalarga ko'tarish mumkin!\n"
        "3. **❄️ Ajdarlarning Muzlashi**: Ajdarlar har bir jangdan so'ng **3 kun (72 soat) muzlaydi** va janglarda qatnasha olmaydi.\n"
        "4. **⚔️ Janglar**: Boshqa xonadonlarga hujum qiling. Jangda yutsangiz, mag'lub xonadon sizning **vassalingizga** aylanadi va uning 20% oltini o'lja qilib olinadi!\n"
        "5. **✨ Soliqlar**: O'z vassallaringizdan har kuni soliqlar yig'ib oling.\n"
        "6. **🏞 Valeria Ekspiditsya**: Valeriya xarobalariga qidiruv ekspeditsiyasi yuborib oltin ishlang.\n"
        "7. **⚔️ Sword Bank**: Askar, Kamonchi, Otliq yollang, qarz oling va kunlik bepul oltin bonusini oling."
    )
    await message.answer(help_text, parse_mode="Markdown")
