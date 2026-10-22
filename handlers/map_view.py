import os
from aiogram import Router, F, types
from aiogram.types import FSInputFile

router = Router()

MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "valyria_map.jpg")

@router.message(F.text == "🗺 Valeriya Xaritasi")
async def show_valyria_map(message: types.Message):
    caption = (
        "🗺 **QADIMGI VALERIYA XARITASI (OLD VALYRIA MAP)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Valeriya yarimoroli 5 ta buyuk mintaqa va 52 ta buyuk xonadon yerlariga bo'lingan:\n\n"
        "👑 **1. Qirollik yerlari (1-10)**\n"
        "• Markaz va Poytaxt: *Targaryen* (Oliy Qirol) [A-toifa]\n"
        "• 9 ta qudratli bayroqdor xonadonlar\n\n"
        "🌋 **2. Vulqonlar lordligi (11-20)**\n"
        "• Hudud Lordi: *Zaldrizar* [A-toifa]\n"
        "• O'n To'rt Olov vulqonlari va ajdarlar makoni\n\n"
        "🌲 **3. Oʻrmon yerlari (21-30)**\n"
        "• Hudud Lordi: *Varezys* [A-toifa]\n"
        "• Qadimiy zich o'rmonlar va boy ov yerlari\n\n"
        "🔮 **4. Jodugarlar yerlari (31-40)**\n"
        "• Hudud Lordi: *Maeraxes* [A-toifa]\n"
        "• Valeriya sehrgarlari va qon jodu maskanlari\n\n"
        "🌊 **5. Dengiz Qoʻriqchilari (41-52)**\n"
        "• Hudud Lordi: *Nyzarys* [A-toifa]\n"
        "• 12 ta dengizchi va kemasoz lordlar xonadoni\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *Eslatma: [A-toifa] Lordlar o'z mintaqasidagi [B-toifa] bayroqdorlarni jangga chorlay oladilar!*"
    )

    if os.path.exists(MAP_PATH):
        photo = FSInputFile(MAP_PATH)
        await message.answer_photo(photo=photo, caption=caption, parse_mode="Markdown")
    else:
        await message.answer(caption, parse_mode="Markdown")
