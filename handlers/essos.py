from aiogram import Router, F, types
from database import get_user, get_user_army, get_user_beasts, buy_essos_item
from keyboards import essos_market_kb, essos_item_detail_kb
from config import ESSOS_MARKET

router = Router()

@router.message(F.text == "🌍 Esos Savdosi")
async def show_essos_market(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)

    spiders_count = len([b for b in beasts if b["beast_type"] == "spider"])

    text = (
        "🌍 **ESOS SAVDOSI — ERKIN SHAHARLAR BOZORI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Valeriya bo'g'ozidan naridagi Esos qit'asining afsonaviy shaharlaridan "
        "noyob kuchlar, pinhona qotillar va halokatli qurollar:\n\n"
        f"💰 Sizning xazinangiz: **{user['gold'] if user else 0} 🪙**\n\n"
        "🏛 **Bozor tovarlari:**\n"
        "• **Asshai**: Oʻrgimchak 🕷 (500 ball) — 300 🪙\n"
        "• **Astapor**: Benuqson 🛡 (5/5 elit piyoda) — 5 🪙\n"
        "• **Braavos**: Yuzsiz qotil 🥷 (300 ball) — 150 🪙\n"
        "• **Lorath**: Soya qotil 👣 (400 ball) — 200 🪙\n"
        "• **Lys**: Zahar 🧪 (300 ball) — 150 🪙\n"
        "• **Meereen**: Chakra ⚙️ (2/2) — 2 🪙\n\n"
        "🛡 **Sizdagi Esos kuchlari:**\n"
        f"  🕷 O'rgimchak: {spiders_count} ta\n"
        f"  🛡 Benuqson: {army.get('unsullied', 0)} ta\n"
        f"  🥷 Yuzsiz qotil: {army.get('faceless', 0)} ta\n"
        f"  👣 Soya qotil: {army.get('shadow', 0)} ta\n"
        f"  🧪 Zahar: {army.get('poison', 0)} ta\n"
        f"  ⚙️ Chakra: {army.get('chakra', 0)} ta\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Xarid qilish uchun shaharni tanlang:"
    )

    await message.answer(text, reply_markup=essos_market_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "essos_back")
async def callback_essos_back(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    army = await get_user_army(user_id)
    beasts = await get_user_beasts(user_id)

    spiders_count = len([b for b in beasts if b["beast_type"] == "spider"])

    text = (
        "🌍 **ESOS SAVDOSI — ERKIN SHAHARLAR BOZORI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Sizning xazinangiz: **{user['gold'] if user else 0} 🪙**\n\n"
        "🛡 **Sizdagi Esos kuchlari:**\n"
        f"  🕷 O'rgimchak: {spiders_count} ta\n"
        f"  🛡 Benuqson: {army.get('unsullied', 0)} ta\n"
        f"  🥷 Yuzsiz qotil: {army.get('faceless', 0)} ta\n"
        f"  👣 Soya qotil: {army.get('shadow', 0)} ta\n"
        f"  🧪 Zahar: {army.get('poison', 0)} ta\n"
        f"  ⚙️ Chakra: {army.get('chakra', 0)} ta\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Xarid qilish uchun shaharni tanlang:"
    )

    await callback.message.edit_text(text, reply_markup=essos_market_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("essos_view:"))
async def callback_essos_view(callback: types.CallbackQuery):
    item_key = callback.data.split(":")[1]
    item = ESSOS_MARKET.get(item_key)
    if not item:
        await callback.answer("Tovar topilmadi!", show_alert=True)
        return

    user = await get_user(callback.from_user.id)
    army = await get_user_army(callback.from_user.id)

    unit_k = item["unit_key"]
    if unit_k == "spider":
        beasts = await get_user_beasts(callback.from_user.id)
        current_count = len([b for b in beasts if b["beast_type"] == "spider"])
    else:
        current_count = army.get(unit_k, 0)

    valyrian_steel = (user.get("valyrian_steel", 0) or 0) if user else 0
    extra_note = ""
    if unit_k == "chakra":
        if valyrian_steel >= 1:
            extra_note = "\n⚔️ **VALERIYA PO'LATI QUDRATI:**\nSizda Valeriya po'lati borligi tufayli kunlik limit CHEKSIZ va zarba kuchi 2 barobar yuqori!\n"
        else:
            daily_bought = user.get("daily_chakra_bought", 0) or 0
            extra_note = f"\n⚙️ **Kunlik limit:** {daily_bought}/500 ta.\n💡 *Green Bankdan Valeriya po'lati xarid qilsangiz, Chakra cheksiz bo'ladi!*\n"

    text = (
        f"🏛 **SHAHAR: {item['city']}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ **Nomi:** {item['name']}\n"
        f"⚡️ **Jangovar kuchi:** {item['power']} ball\n"
        f"💰 **Birlik narxi:** {item['cost']} 🪙\n"
        f"📜 **Tavsifi:** {item['desc']}\n"
        f"{extra_note}\n"
        f"🎒 Sizda mavjud: **{current_count} ta**\n"
        f"💰 Xazinangiz: **{user['gold'] if user else 0} 🪙**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Qancha miqdorda xarid qilmoqchisiz?"
    )

    await callback.message.edit_text(text, reply_markup=essos_item_detail_kb(item_key), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("essos_buy:"))
async def callback_essos_buy(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    item_key = parts[1]
    count = int(parts[2])

    user_id = callback.from_user.id
    success, msg = await buy_essos_item(user_id, item_key, count)

    if success:
        await callback.answer("Xarid muvaffaqiyatli amalga oshirildi! 🎉", show_alert=False)

        user = await get_user(user_id)
        item = ESSOS_MARKET.get(item_key)
        army = await get_user_army(user_id)

        unit_k = item["unit_key"]
        if unit_k == "spider":
            beasts = await get_user_beasts(user_id)
            current_count = len([b for b in beasts if b["beast_type"] == "spider"])
        else:
            current_count = army.get(unit_k, 0)

        text = (
            f"✅ **{msg}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏛 **Shahar:** {item['city']} | {item['name']}\n"
            f"🎒 Sizdagi jami soni: **{current_count} ta**\n"
            f"💰 Qolgan oltin: **{user['gold']} 🪙**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Yana xarid qilmoqchimisiz?"
        )
        await callback.message.edit_text(text, reply_markup=essos_item_detail_kb(item_key), parse_mode="Markdown")
    else:
        await callback.answer(msg, show_alert=True)
