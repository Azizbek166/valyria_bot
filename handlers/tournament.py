import random
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user, get_user_house,
    record_tournament_battle, get_tournament_top_players,
    get_user_tournament_stats
)
from keyboards import (
    tournament_menu_kb, tournament_attack_zone_kb,
    tournament_defend_zone_kb, tournament_round_result_kb,
    tournament_top20_kb
)
from config import escape_md

logger = logging.getLogger(__name__)

router = Router()

class TournamentBattleState(StatesGroup):
    choosing_attack = State()
    choosing_defend = State()

KNIGHT_NAMES = [
    "Sir Arthur Dayne (Tong Qilichi)",
    "Sir Barristan Selmy (Jasur)",
    "Sir Jaime Lannister (Oltin Ritser)",
    "Sir Criston Cole (Qirol Yaratuvchi)",
    "Sir Gregor Clegane (Qoyatosh)",
    "Sir Loras Tyrell (Gullar Ritsari)",
    "Sir Daemon Blackfyre (Qora Ajdar)",
    "Valeriya Po'lat Ritsari",
    "Qadimgi Arena Chempioni"
]

ZONE_LABELS = {
    "bosh": "Bosh 🗣",
    "tana": "Tana 👤",
    "oyoq": "Oyoq 👣"
}

def make_hp_bar(hp: int, max_hp: int = 100) -> str:
    hp = max(0, min(max_hp, hp))
    filled = int((hp / max_hp) * 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty

@router.message(F.text == "⛓💥 Ritserlar Baxsi")
async def show_tournament_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await get_user(user_id)
    user_house = await get_user_house(user_id)
    stats = await get_user_tournament_stats(user_id)

    lord_name = user.get("custom_name") or user.get("full_name") if user else f"Lord #{user_id}"
    house_name = user_house["name"] if user_house else "Xonadonsiz"

    text = (
        "⛓💥 **1000 YILLIK QADIMGI TURNIR: RITSERLAR BAXSI** ⚔️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Valeriyaning 1000 yillik shonli an'anasi! Ushbu arenada eng jasur Lordlar "
        "va afsonaviy ritserlar yuzma-yuz kelib, zarba va himoya mahoratini sinashadi.\n\n"
        f"👑 **Sizning unvoningiz:** **{lord_name}** ({house_name})\n"
        f"🏆 **Turnir ochkolaringiz:** **{stats['points']} ball**\n"
        f"🥇 **Reytingdagi o'rningiz:** **{stats['rank']}-o'rin**\n"
        f"⚔️ **Janglar:** {stats['wins']} g'alaba / {stats['fights']} jang\n\n"
        "🔥 **Jang Qoidalari:**\n"
        "Har raundda zarba beradigan nuqtangizni va qalqon bilan himoyalaydigan nuqtangizni tanlaysiz:\n"
        "• 🗣 **Bosh** | 👤 **Tana** | 👣 **Oyoq**\n\n"
        "Maydonga tushib, Valeriya chempioni bo'lishga tayyormisiz?"
    )

    await message.answer(text, reply_markup=tournament_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "tourn_menu_back")
async def callback_tournament_menu_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = await get_user(user_id)
    user_house = await get_user_house(user_id)
    stats = await get_user_tournament_stats(user_id)

    lord_name = user.get("custom_name") or user.get("full_name") if user else f"Lord #{user_id}"
    house_name = user_house["name"] if user_house else "Xonadonsiz"

    text = (
        "⛓💥 **1000 YILLIK QADIMGI TURNIR: RITSERLAR BAXSI** ⚔️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Sizning unvoningiz:** **{lord_name}** ({house_name})\n"
        f"🏆 **Turnir ochkolaringiz:** **{stats['points']} ball**\n"
        f"🥇 **Reytingdagi o'rningiz:** **{stats['rank']}-o'rin**\n"
        f"⚔️ **Janglar:** {stats['wins']} g'alaba / {stats['fights']} jang\n\n"
        "Harakatni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=tournament_menu_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "tourn_start_fight")
async def callback_tourn_start_fight(callback: types.CallbackQuery, state: FSMContext):
    opp_name = random.choice(KNIGHT_NAMES)
    user_hp = 100
    opp_hp = 100
    round_num = 1

    await state.set_state(TournamentBattleState.choosing_attack)
    await state.update_data(
        opp_name=opp_name,
        user_hp=user_hp,
        opp_hp=opp_hp,
        round_num=round_num
    )

    user_bar = make_hp_bar(user_hp)
    opp_bar = make_hp_bar(opp_hp)

    text = (
        f"⚔️ **TURNIR JANGI BOSHLANDI!** 💥\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤺 **Raqibingiz:** **{opp_name}**\n\n"
        f"🛡 **Siz:** [{user_bar}] **{user_hp} HP**\n"
        f"⚔️ **Raqib:** [{opp_bar}] **{opp_hp} HP**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **RAUND {round_num}: HUJUM NUQTASINI TANLANG!**\n"
        f"Qilichingiz bilan dushmanning qaysi qismiga zarba berasiz?"
    )

    await callback.message.edit_text(text, reply_markup=tournament_attack_zone_kb(), parse_mode="Markdown")
    await callback.answer("Jang maydoniga tushdingiz! ⚔️")

@router.callback_query(F.data.startswith("tourn_att:"), TournamentBattleState.choosing_attack)
async def callback_tourn_attack_chosen(callback: types.CallbackQuery, state: FSMContext):
    att_zone = callback.data.split(":")[1]
    data = await state.get_data()
    opp_name = data["opp_name"]
    user_hp = data["user_hp"]
    opp_hp = data["opp_hp"]
    round_num = data["round_num"]

    await state.set_state(TournamentBattleState.choosing_defend)
    await state.update_data(att_zone=att_zone)

    user_bar = make_hp_bar(user_hp)
    opp_bar = make_hp_bar(opp_hp)

    text = (
        f"⚔️ **RAUND {round_num}: HIMOYANI BELGILANG!** 🛡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤺 Raqib: **{opp_name}**\n\n"
        f"🛡 **Siz:** [{user_bar}] **{user_hp} HP**\n"
        f"⚔️ **Raqib:** [{opp_bar}] **{opp_hp} HP**\n\n"
        f"🗡 Tanlangan zarbangiz: **{ZONE_LABELS.get(att_zone, att_zone)}**\n\n"
        f"Endi o'zingizning qaysi qismingizni qalqon bilan himoyalaysiz?"
    )

    await callback.message.edit_text(text, reply_markup=tournament_defend_zone_kb(att_zone), parse_mode="Markdown")
    await callback.answer(f"Zarba: {ZONE_LABELS.get(att_zone)}")

@router.callback_query(F.data.startswith("tourn_def:"), TournamentBattleState.choosing_defend)
async def callback_tourn_defend_chosen(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    att_zone = parts[1]
    def_zone = parts[2]

    data = await state.get_data()
    opp_name = data["opp_name"]
    user_hp = data["user_hp"]
    opp_hp = data["opp_hp"]
    round_num = data["round_num"]

    # AI opponent chooses zones randomly
    opp_att = random.choice(["bosh", "tana", "oyoq"])
    opp_def = random.choice(["bosh", "tana", "oyoq"])

    # 1. Player attack vs Opponent defend
    if att_zone == opp_def:
        opp_dmg = random.randint(0, 5)
        player_hit_desc = f"🛡 **RAQIB BLOKLADI!** {opp_name} o'z **{ZONE_LABELS[att_zone]}** qismini to'sdi! (-{opp_dmg} HP)"
    else:
        opp_dmg = random.randint(25, 35)
        player_hit_desc = f"💥 **QAHRAMONONA ZARBA!** Qilichingiz raqibning **{ZONE_LABELS[att_zone]}** qismiga tushdi! (-{opp_dmg} HP)"

    # 2. Opponent attack vs Player defend
    if opp_att == def_zone:
        user_dmg = random.randint(0, 5)
        opp_hit_desc = f"🛡 **MUVAFFAQIYATLI BLOK!** Siz qalqon bilan **{ZONE_LABELS[def_zone]}** qismini asrab qoldingiz! (-{user_dmg} HP)"
    else:
        user_dmg = random.randint(25, 35)
        opp_hit_desc = f"🩸 **OG'IR ZARBA!** {opp_name} sizning **{ZONE_LABELS[opp_att]}** qismingizga zarba berdi! (-{user_dmg} HP)"

    user_hp = max(0, user_hp - user_dmg)
    opp_hp = max(0, opp_hp - opp_dmg)

    user_bar = make_hp_bar(user_hp)
    opp_bar = make_hp_bar(opp_hp)

    # Check Game Over
    if user_hp <= 0 or opp_hp <= 0:
        await state.clear()
        user_id = callback.from_user.id
        won = (user_hp > 0 and opp_hp == 0) or (user_hp > opp_hp)

        pts, total_pts, gold = await record_tournament_battle(user_id, won=won)

        if won:
            outcome_header = "🎉 **G'ALABA! TURNIR G'OLIBI BO'LDINGIZ!** 👑"
            outcome_text = (
                f"Siz mardonavor kurashib, **{opp_name}** ustidan g'alaba qozondingiz!\n\n"
                f"🎁 **Mukofot:**\n"
                f"• 🏆 **+{pts} Turnir ochkosi** (Jami: {total_pts} ball)\n"
                f"• 💰 **+{gold} 🪙 Oltin tanga**\n\n"
                f"Reytingdagi o'rningiz ko'tarildi! Maydonda yana jang qilib, haftalik sovg'alarga yaqinlashing!"
            )
        else:
            outcome_header = "💀 **MAG'LUBIYAT! RITSER YIQILDI!** 🛡"
            outcome_text = (
                f"Bu jangda **{opp_name}** ustun keldi, ammo siz munosib kurash olib bordingiz.\n\n"
                f"🎁 **Ishtirok uchun:**\n"
                f"• 🏆 **+{pts} Turnir ochkosi** (Jami: {total_pts} ball)\n\n"
                f"Dam oling va qayta kuch to'plab maydonga kiring!"
            )

        report = (
            f"{outcome_header}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚔️ **Raund {round_num} yakuni:**\n"
            f"{player_hit_desc}\n"
            f"{opp_hit_desc}\n\n"
            f"🛡 Siz: [{user_bar}] **{user_hp} HP**\n"
            f"⚔️ Raqib: [{opp_bar}] **{opp_hp} HP**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{outcome_text}"
        )

        await callback.message.edit_text(report, reply_markup=tournament_round_result_kb(is_game_over=True), parse_mode="Markdown")
        await callback.answer("Jang yakunlandi!")
        return

    # Battle Continues to Next Round
    await state.set_state(TournamentBattleState.choosing_attack)
    await state.update_data(
        user_hp=user_hp,
        opp_hp=opp_hp,
        round_num=round_num + 1
    )

    report = (
        f"⚔️ **RAUND {round_num} NATIJASI** 💥\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{player_hit_desc}\n"
        f"{opp_hit_desc}\n\n"
        f"🛡 **Siz:** [{user_bar}] **{user_hp} HP**\n"
        f"⚔️ **Raqib ({opp_name}):** [{opp_bar}] **{opp_hp} HP**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **RAUND {round_num + 1}: HUJUM NUQTASINI TANLANG!**\n"
        f"Navbatdagi zarbani qayerga yo'llaysiz?"
    )

    await callback.message.edit_text(report, reply_markup=tournament_attack_zone_kb(), parse_mode="Markdown")
    await callback.answer("Raund natijasi hisoblandi!")

@router.callback_query(F.data == "tourn_next_round", TournamentBattleState.choosing_attack)
async def callback_tourn_next_round(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    round_num = data.get("round_num", 1)
    opp_name = data.get("opp_name", "Ritser")
    user_hp = data.get("user_hp", 100)
    opp_hp = data.get("opp_hp", 100)

    user_bar = make_hp_bar(user_hp)
    opp_bar = make_hp_bar(opp_hp)

    text = (
        f"⚔️ **RAUND {round_num}: HUJUM QILISH** 🗡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤺 Raqib: **{opp_name}**\n\n"
        f"🛡 Siz: [{user_bar}] **{user_hp} HP**\n"
        f"⚔️ Raqib: [{opp_bar}] **{opp_hp} HP**\n\n"
        f"Zarba berish nuqtasini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=tournament_attack_zone_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "tourn_retreat")
async def callback_tourn_retreat(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏳 **Siz turnir maydonidan chekindingiz.** Jang yakunlandi.",
        reply_markup=tournament_menu_kb(),
        parse_mode="Markdown"
    )
    await callback.answer("Chekindingiz.")

@router.callback_query(F.data == "tourn_top20")
async def callback_tourn_top20(callback: types.CallbackQuery):
    top_players = await get_tournament_top_players(limit=20)
    user_id = callback.from_user.id
    user_stats = await get_user_tournament_stats(user_id)

    if not top_players:
        text = (
            "🏆 **QADIMGI TURNIR: TOP 20 RITSERLAR REYTINGI** ⛓💥\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "😴 *Hozircha turnirda hech kim jang o'tkazmagan. "
            "Birinchi bo'lib jangga kiring va taxtni egallang!*\n\n"
            f"Sizning ochkolaringiz: **{user_stats['points']} ball**"
        )
    else:
        lines = []
        for idx, p in enumerate(top_players):
            pos = idx + 1
            if pos == 1:
                badge = "🥇"
            elif pos == 2:
                badge = "🥈"
            elif pos == 3:
                badge = "🥉"
            else:
                badge = f"**{pos}.**"

            p_name = escape_md(p["full_name"])
            u_str = f" (@{escape_md(p['username'])})" if p.get("username") else ""
            h_str = f" [{escape_md(p['house_name'])}]" if p.get("house_name") else ""
            lines.append(f"{badge} {p_name}{u_str}{h_str} — **{p['tournament_points']} ochko** ({p['tournament_wins']} g'alaba)")

        text = (
            "🏆 **QADIMGI TURNIR: TOP 20 RITSERLAR REYTINGI** ⛓💥\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) +
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Sizning natijangiz: **{user_stats['points']} ochko** | O'rningiz: **{user_stats['rank']}-o'rin**\n"
            f"📅 *Haftalik g'oliblarga sovg'alar hafta yakunida avtomatik topshiriladi!*"
        )

    await callback.message.edit_text(text, reply_markup=tournament_top20_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "tourn_rewards_info")
async def callback_tourn_rewards_info(callback: types.CallbackQuery):
    text = (
        "🎁 **QADIMGI TURNIR: HAFTALIK SOVG'ALAR** 🌋\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Har hafta yakunida Top 20 reytingidagi dastlabki 5 nafar eng qudratli "
        "Lordlarga Valeriya xazinasidan qimmatbaho sovg'alar ulashiladi:\n\n"
        "🥇 **1-O'RIN:**\n"
        "• **+200 🛡 Benuqson (Unsullied)**\n"
        "• **+1 ta Qadimgi Ajdar 🐲**\n\n"
        "🥈 **2-O'RIN:**\n"
        "• **+150 🛡 Benuqson (Unsullied)**\n"
        "• **+1 ta Muz Oʻrgimchagi 🕷**\n\n"
        "🥉 **3-O'RIN:**\n"
        "• **+100 🛡 Benuqson (Unsullied)**\n"
        "• **+1 ta Yuzsiz Qotil 🥷**\n\n"
        "4️⃣ **4-O'RIN:**\n"
        "• **+150 ⚙️ Chakra energiyasi**\n\n"
        "5️⃣ **5-O'RIN:**\n"
        "• **+100 ⚙️ Chakra energiyasi**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️ Maydonda kurashing, ochko to'plang va haftalik bosh mukofotlarni qo'lga kiriting!"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⚔️ Jangga Kirish", callback_data="tourn_start_fight")],
        [types.InlineKeyboardButton(text="🏆 Top 20 Reyting", callback_data="tourn_top20")],
        [types.InlineKeyboardButton(text="🔙 Turnir Maydoni", callback_data="tourn_menu_back")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "tourn_rules")
async def callback_tourn_rules(callback: types.CallbackQuery):
    text = (
        "📜 **TURNIR VA DUEL QOIDALARI** ⛓💥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Ritserlar baxsi — 3 ta hayotiy nuqta bo'yicha olib boriladi:\n"
        "• 🗣 **Bosh** (Eng xavfli va nozik nuqta)\n"
        "• 👤 **Tana** (Asosiy zirh qismi)\n"
        "• 👣 **Oyoq** (Harakatchanlik poydevori)\n\n"
        "🗡 **Hujum mexanikasi:**\n"
        "Har raundda siz qayerga zarba berishni, raqib esa qayerini himoyalashni tanlaydi. "
        "Agar raqib siz urgan joyni to'smagan bo'lsa, **DURUST ZARBA (25-35 HP)** yetkazasiz! "
        "Agar to'sgan bo'lsa, zarbangiz **QALQON BLOKI**ga uchraydi.\n\n"
        "🛡 **Himoya mexanikasi:**\n"
        "Xuddi shuningdek, siz o'z qalqoningiz bilan to'g'ri nuqtani himoyalasangiz, "
        "raqibning zarbasi qaytariladi!\n\n"
        "🏆 **Turnir Ballari:**\n"
        "• G'alaba uchun: **+20 ball** va **+25 🪙 oltin**\n"
        "• Ishtirok uchun: **+5 ball**"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⚔️ Maydonga tushish", callback_data="tourn_start_fight")],
        [types.InlineKeyboardButton(text="🔙 Turnir Maydoni", callback_data="tourn_menu_back")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
