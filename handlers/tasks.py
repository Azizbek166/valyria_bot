from aiogram import Router, F, types
from typing import Dict, Any, Optional
from database import (
    get_top_players, get_user_house,
    get_user_daily_tasks, perform_daily_patrol,
    perform_daily_fortification, perform_daily_expedition,
    claim_daily_super_bonus
)
from keyboards import daily_tasks_kb
from config import REGIONS, escape_md
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "🥇 Reyting")
async def show_leaderboard(message: types.Message):
    try:
        top_players = await get_top_players(limit=10)

        if not top_players:
            await message.answer("🥇 Reyting jadvali hozircha bo'sh.", parse_mode="Markdown")
            return

        medals = ["🥇", "🥈", "🥉", "4.", "5.", "6.", "7.", "8.", "9.", "10."]
        lines = []
        for i, p in enumerate(top_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            h_type_icon = "🏰" if p.get("house_type") == "land" else "🌊"
            u_raw = p.get("username")
            username_str = f" (@{escape_md(u_raw)})" if u_raw else ""
            f_name = escape_md(p.get("full_name") or "Lord")
            h_name = escape_md(p.get("house_name") or "Xonadon")
            tier_tag = f"[{p.get('tier', 'B')}-toifa]"
            lines.append(
                f"{medal} **{h_name}** {tier_tag} — {f_name}{username_str} — **{p['gold']} 🪙** {h_type_icon}"
            )

        text = (
            "🥇 **VALERIYA ENG QUDRATLI VA BOY LORDLARI REYTINGI**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) +
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            "Reytingda yuqorilash uchun jang qiling va xazinangizni boyiting!"
        )

        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Reyting ko'rsatishda xatolik: {e}")
        await message.answer("🥇 Reyting ma'lumotlarini yuklashda xatolik yuz berdi.")

def build_daily_tasks_text(user_house: Optional[Dict[str, Any]], daily: Dict[str, Any]) -> str:
    if user_house:
        reg_info = REGIONS.get(user_house.get("region", ""), {})
        reg_name = escape_md(reg_info.get("name", "Valeriya"))
        h_name = escape_md(user_house.get('name', ''))
        house_name = f"{h_name} [{user_house.get('tier', 'B')}-toifa]"
    else:
        reg_name = "Valeriya sarhadlari"
        house_name = "Tanlanmagan"

    t1_status = "✅ Bajarildi" if daily.get("task1_done") == 1 else "⏳ Bajarilmagan"
    t2_status = "✅ Bajarildi" if daily.get("task2_done") == 1 else "⏳ Bajarilmagan"
    t3_status = "✅ Bajarildi" if daily.get("task3_done") == 1 else "⏳ Bajarilmagan"

    if daily.get("super_claimed") == 1:
        super_status = "🌟 Bugungi Super-Bonus qabul qilingan!"
    elif daily.get("task1_done") == 1 and daily.get("task2_done") == 1 and daily.get("task3_done") == 1:
        super_status = "🎁 **TAYYOR! Quyidagi tugma orqali Super-Bonusni oling!**"
    else:
        done_cnt = sum([1 for k in ["task1_done", "task2_done", "task3_done"] if daily.get(k) == 1])
        super_status = f"⏳ Ochilishi uchun yana {3 - done_cnt} ta vazifa bajarilishi kerak"

    text = (
        "🛘 **VALERIYA KUNLIK HUDUDIY TOPSHIRIQLARI**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Sana: **{daily['task_date']}** (Har 24 soatda yangilanadi)\n"
        f"🏰 Xonadon: **{house_name}**\n"
        f"🗺 Hudud: **{reg_name}**\n\n"
        "Har kuni o'z hududingizni rivojlantiring va qimmatbaho resurslarni qo'lga kiriting:\n\n"
        f"1. 🛡 **Chegara Patruli va Razvedka:**\n"
        "   • Sarhadlarni ko'zdan kechirish va xavflarni bartaraf etish.\n"
        "   • Sarf: 5 ⚙️ Chakra (Valeriya po'lati bilan tekin)\n"
        "   • Mukofot: +70..120 🪙 Oltin + askar / chakra\n"
        f"   • Holat: **{t1_status}**\n\n"
        f"2. 🏰 **Garnizon Mudofaasini Kuchaytirish:**\n"
        "   • Qal'a devorlari va harbiy garnizon shayligini ta'minlash.\n"
        "   • Talab: Qal'a qurilgan bo'lishi yoki 25+ askar\n"
        "   • Mukofot: +110 🪙 Oltin, +10 🛡 Benuqson, +15 ⚙️ Chakra\n"
        f"   • Holat: **{t2_status}**\n\n"
        f"3. ⚔️ **Valeriya Bo'ylab Qahramonona Harbiy Yurish:**\n"
        "   • Hudud yaqinidagi dushmanlarga zarba berish.\n"
        "   • Sarf: 10 ⚙️ Chakra (Valeriya po'lati bilan tekin)\n"
        "   • Mukofot: +150 🪙 Oltin, +1 👣 Soya Qotil, +25 ⚙️ Chakra\n"
        f"   • Holat: **{t3_status}**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏆 **KUNLIK HUDUDIY SUPER-BONUS (3/3):**\n"
        "• Mukofot: **+600 🪙 Oltin tanga + 300 ⚙️ Chakra energiyasi!**\n"
        f"• Holat: {super_status}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    return text

@router.message(F.text == "🛘 Hududiy topshiriqlar")
async def show_territory_tasks(message: types.Message):
    try:
        user_id = message.from_user.id
        user_house = await get_user_house(user_id)
        daily = await get_user_daily_tasks(user_id)

        text = build_daily_tasks_text(user_house, daily)
        kb = daily_tasks_kb(daily)
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Hududiy topshiriqlarda xatolik: {e}", exc_info=True)
        await message.answer("🛘 Hududiy topshiriqlarni yuklashda xatolik yuz berdi.")

@router.callback_query(F.data == "daily_task_1")
async def callback_daily_task_1(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ok, msg = await perform_daily_patrol(user_id)

    if ok:
        await callback.answer("Patrul yakunlandi! 🛡", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)
        return

    user_house = await get_user_house(user_id)
    daily = await get_user_daily_tasks(user_id)
    text = build_daily_tasks_text(user_house, daily)
    kb = daily_tasks_kb(daily)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass

@router.callback_query(F.data == "daily_task_2")
async def callback_daily_task_2(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ok, msg = await perform_daily_fortification(user_id)

    if ok:
        await callback.answer("Garnizon mudofaasi mustahkamlandi! 🏰", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)
        return

    user_house = await get_user_house(user_id)
    daily = await get_user_daily_tasks(user_id)
    text = build_daily_tasks_text(user_house, daily)
    kb = daily_tasks_kb(daily)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass

@router.callback_query(F.data == "daily_task_3")
async def callback_daily_task_3(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ok, msg = await perform_daily_expedition(user_id)

    if ok:
        await callback.answer("Harbiy yurish zafar bilan yakunlandi! ⚔️", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)
        return

    user_house = await get_user_house(user_id)
    daily = await get_user_daily_tasks(user_id)
    text = build_daily_tasks_text(user_house, daily)
    kb = daily_tasks_kb(daily)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass

@router.callback_query(F.data == "daily_super_bonus")
async def callback_daily_super_bonus(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ok, msg = await claim_daily_super_bonus(user_id)

    if ok:
        await callback.answer("SUPER-BONUS QABUL QILINDI! 🏆", show_alert=True)
        try:
            await callback.bot.send_message(user_id, msg, parse_mode="Markdown")
        except Exception:
            pass
    else:
        await callback.answer(msg, show_alert=True)
        return

    user_house = await get_user_house(user_id)
    daily = await get_user_daily_tasks(user_id)
    text = build_daily_tasks_text(user_house, daily)
    kb = daily_tasks_kb(daily)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass

@router.callback_query(F.data == "daily_tasks_refresh")
async def callback_daily_tasks_refresh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_house = await get_user_house(user_id)
    daily = await get_user_daily_tasks(user_id)

    text = build_daily_tasks_text(user_house, daily)
    kb = daily_tasks_kb(daily)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Yangilandi! 🔄")
