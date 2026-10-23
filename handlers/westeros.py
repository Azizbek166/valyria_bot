import logging
from aiogram import Router, F, types
from database import (
    get_user, get_user_house, calculate_player_power,
    get_user_army, get_user_westeros_cooldowns,
    execute_westeros_raid, get_user_westeros_stats
)
from keyboards import (
    westeros_targets_kb, westeros_target_detail_kb,
    westeros_raid_result_kb
)
from config import WESTEROS_TARGETS, escape_md

logger = logging.getLogger(__name__)

router = Router()

async def build_westeros_menu_text(user_id: int) -> str:
    user = await get_user(user_id)
    user_house = await get_user_house(user_id)
    power_info = await calculate_player_power(user_id)
    army = await get_user_army(user_id) or {}
    stats = await get_user_westeros_stats(user_id)

    raw_name = user.get("custom_name") or user.get("full_name") if user else f"Lord #{user_id}"
    lord_name = escape_md(raw_name)
    house_name = escape_md(user_house["name"]) if user_house else "Xonadonsiz"
    total_power = power_info.get("total_active_power", 0)
    dragons_count = len(power_info.get("active_dragons", []))
    soldiers_count = army.get("soldiers", 0)

    text = (
        "🏴‍☠️ **WESTEROSNI TALON-TAROJ QILISH (WESTEROS RAIDS)** ⛵️🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Qadimgi Valeriya dengiz floti va o'tpurkar ajdarlari Tor Dengiz "
        "(Narrow Sea) orqali Westerosning boy shahar va qasrlari tomon yo'l oladi!\n\n"
        f"👑 **Hukmdor:** **{lord_name}** ({house_name})\n"
        f"⚡️ **Harbiy qudratingiz:** **{total_power} ball**\n"
        f"🗡 **Mavjud armiya:** {soldiers_count} askar | 🐲 {dragons_count} ta faol ajdar\n"
        f"🏆 **Jami talon-tarojlar:** {stats['total_raids']} marta (+{stats['total_gold']} 🪙 oltin, +{stats['total_chakra']} ⚙️ chakra)\n\n"
        "🗺 **Hujum qilish uchun Westeros nishonini tanlang:**\n"
        "Har bir nishon o'z qiyinligi, talab qilinadigan kuchi va o'ljasiga ega. "
        "Talangandan so'ng, dushman qayta tiklanishi uchun vaqt kerak bo'ladi (Cooldown)."
    )
    return text

@router.message(F.text == "🏴‍☠️ Westerosni Talon-Taroj")
async def show_westeros_main(message: types.Message):
    user_id = message.from_user.id
    cooldowns = await get_user_westeros_cooldowns(user_id)
    text = await build_westeros_menu_text(user_id)
    await message.answer(text, reply_markup=westeros_targets_kb(cooldowns), parse_mode="Markdown")

@router.callback_query(F.data.in_(["w_back", "w_refresh"]))
async def callback_westeros_back(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cooldowns = await get_user_westeros_cooldowns(user_id)
    text = await build_westeros_menu_text(user_id)
    try:
        await callback.message.edit_text(text, reply_markup=westeros_targets_kb(cooldowns), parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Yangilandi! 🔄")

@router.callback_query(F.data.startswith("w_target:"))
async def callback_westeros_target_detail(callback: types.CallbackQuery):
    target_id = callback.data.split(":")[1]
    target = WESTEROS_TARGETS.get(target_id)
    if not target:
        await callback.answer("Nishon topilmadi!", show_alert=True)
        return

    user_id = callback.from_user.id
    power_info = await calculate_player_power(user_id)
    total_power = power_info.get("total_active_power", 0)
    dragons_count = len(power_info.get("active_dragons", []))
    cooldowns = await get_user_westeros_cooldowns(user_id)
    cd_info = cooldowns.get(target_id, {})
    is_ready = cd_info.get("ready", True)

    power_badge = "✅ Yetarli" if total_power >= target["min_power"] else "❌ Kamlik qiladi"
    dragon_req_text = "🐲 Majburiy (Kamida 1 ta)" if target.get("requires_dragon") else "Kerak emas"
    dragon_badge = "✅ Bor" if (dragons_count > 0 or not target.get("requires_dragon")) else "❌ Ajdar yo'q"

    steel_bonus_text = ""
    if target.get("valyrian_steel_chance", 0) > 0:
        chance_pct = int(target["valyrian_steel_chance"] * 100)
        steel_bonus_text = f"• ⚔️ **Valeriya Po'lati:** {chance_pct}% ehtimol bilan\n"

    unsullied_bonus_text = ""
    if target.get("unsullied_loot", 0) > 0:
        unsullied_bonus_text = f"• 🛡 **Asir olingan Benuqsonlar:** +{target['unsullied_loot']} ta\n"

    status_text = "🟢 **Hozir hujum qilishga TAYYOR!**" if is_ready else f"⏳ **Qayta tiklanish vaqti:** {cd_info.get('left_str', '')} qoldi"

    text = (
        f"🏰 **NISHON: {target['name']}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **Mintaqa:** {target['region_name']}\n"
        f"🎖 **Qiyinchilik darajasi:** {target['difficulty']}\n"
        f"📖 *{target['desc']}*\n\n"
        f"⚖️ **Talablar va Harbiy Tayyorgarlik:**\n"
        f"• Kerakli quvvat: kamida **{target['min_power']} ball** (Sizda: **{total_power} ball** — {power_badge})\n"
        f"• Ajdar talabi: {dragon_req_text} ({dragon_badge})\n"
        f"• Kutilayotgan talafot: ~{target['loss_min']}-{target['loss_max']} piyoda askar\n\n"
        f"🎁 **Kutilayotgan o'ljalar:**\n"
        f"• 💰 **Oltin tangalar:** {target['gold_min']} – {target['gold_max']} 🪙\n"
        f"• ⚙️ **Chakra energiyasi:** {target['chakra_min']} – {target['chakra_max']} ⚙️\n"
        f"{unsullied_bonus_text}"
        f"{steel_bonus_text}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_text}\n\n"
        "Kemalar va ajdarlarni jangga yo'llashga tayyormisiz?"
    )

    await callback.message.edit_text(
        text,
        reply_markup=westeros_target_detail_kb(target_id, is_ready),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("w_attack:"))
async def callback_westeros_attack(callback: types.CallbackQuery):
    target_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    success, msg, report = await execute_westeros_raid(user_id, target_id)
    if not success:
        await callback.answer(msg, show_alert=True)
        return

    target = report["target"]
    looted_gold = report["looted_gold"]
    looted_chakra = report["looted_chakra"]
    looted_unsullied = report["looted_unsullied"]
    got_steel = report["got_steel"]
    loss_soldiers = report["loss_soldiers"]

    steel_msg = "\n• ⚔️ **Noyob O'lja:** +1 ta **Valeriya Po'lati** qo'lga kiritildi! 🌟" if got_steel else ""
    unsullied_msg = f"\n• 🛡 **Asir olingan qo'shin:** +{looted_unsullied} ta **Benuqson (Unsullied)** saflaringizga qo'shildi!" if looted_unsullied > 0 else ""
    loss_msg = f"• 💀 **Talafot:** {loss_soldiers} ta jasur piyoda askar jangda shahid bo'ldi." if loss_soldiers > 0 else "• 🛡 **Talafot:** Askarlardan yo'qotish bo'lmadi!"

    text = (
        "🏴‍☠️ **TALON-TAROJ MUVAFFAQIYATLI YAKUNLANDI!** 💥⛵️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 **Zabt etilgan nishon:** **{target['name']}**\n"
        f"📍 **Mintaqa:** {target['region_name']}\n\n"
        "📜 **Jangnoma:**\n"
        "Sizning harbiy flotingiz Tor Dengiz to'lqinlarini yorib o'tib, Westeros sohillariga qaqshatqich "
        "zarba berdi! O'tpurkar ajdarlar qal'a minoralarini o'rab oldi, dushman mudofaasi yorildi va "
        "barcha asosiy xazina omborlari talon-taroj qilindi!\n\n"
        "🎁 **Qo'lga kiritilgan boyliklar:**\n"
        f"• 💰 **+{looted_gold} 🪙 Oltin tanga**\n"
        f"• ⚙️ **+{looted_chakra} Chakra energiyasi**"
        f"{unsullied_msg}"
        f"{steel_msg}\n\n"
        "🩸 **Jang natijasi:**\n"
        f"{loss_msg}\n\n"
        f"⏳ *Bu nishon dushmanlari qayta tiklanishi uchun {target['cooldown_seconds'] // 60} daqiqa vaqt oladi.*"
    )

    await callback.message.edit_text(
        text,
        reply_markup=westeros_raid_result_kb(target_id),
        parse_mode="Markdown"
    )
    await callback.answer("Talon-taroj muvaffaqiyatli o'tdi! 💰", show_alert=True)

@router.callback_query(F.data == "w_stats")
async def callback_westeros_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    stats = await get_user_westeros_stats(user_id)
    cooldowns = await get_user_westeros_cooldowns(user_id)

    lines = []
    for t_id, target in WESTEROS_TARGETS.items():
        cd_info = cooldowns.get(t_id, {})
        status = cd_info.get("left_str", "Tayyor ⚔️")
        lines.append(f"• **{target['name']}:** {status}")

    text = (
        "📊 **SIZNING WESTEROS REYDLARINGIZ STATISTIKASI** 🏴‍☠️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ **Jami harbiy yurishlar:** **{stats['total_raids']} marta**\n"
        f"💰 **Jami o'lja qilingan oltin:** **+{stats['total_gold']} 🪙**\n"
        f"⚙️ **Jami o'lja qilingan chakra:** **+{stats['total_chakra']} ⚙️**\n\n"
        "⏱ **Nishonlarning hozirgi holati:**\n"
        + "\n".join(lines) +
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        "Qo'shinlaringizni to'plang va navbatdagi boyliklar sari otlaning!"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Nishonlar ro'yxatiga qaytish", callback_data="w_back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
