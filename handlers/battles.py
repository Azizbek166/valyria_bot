import random
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_user_house, get_houses, get_house_by_id,
    calculate_player_power, execute_battle, get_user,
    create_call_to_arms, get_active_call_to_arms,
    pledge_bannerman_support, get_region_bannermen,
    get_call_pledged_power
)
from keyboards import battle_confirm_kb, call_to_arms_bannermen_kb
from config import REGIONS

router = Router()

@router.message(F.text == "⚔️ Janglar")
async def show_battles_menu(message: types.Message):
    user_id = message.from_user.id
    user_house = await get_user_house(user_id)

    if not user_house:
        await message.answer(
            "⚠️ **Siz hali birorta xonadonni boshqarmayapsiz!**\n"
            "Jangga kirishdan oldin **🌋 Oila tanlash** bo'limidan o'z xonadoningizni tanlang.",
            parse_mode="Markdown"
        )
        return

    power_info = await calculate_player_power(user_id)
    houses = await get_houses()

    occupied_houses = [
        h for h in houses
        if h["owner_id"] is not None and h["owner_id"] != user_id
    ]

    reg_info = REGIONS.get(user_house.get("region", ""), {})
    role_tag = "👑 Oliy Qirol" if user_house["id"] == 1 else ("🛡 Hudud Lordi" if user_house.get("is_regional_lord") else "🗡 Bayroqdor")

    text = (
        f"⚔️ **QADIMGI VALERIYA URUSHLARI VA JANG MAYDONI**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏰 Sizning xonadoningiz: **{user_house['name']}** ({reg_info.get('name', '')})\n"
        f"🎖 Maqomingiz: **{role_tag}**\n"
        f"⚡️ Faol jangovar kuchingiz: **{power_info['total_active_power']} ball**\n"
        f"🐲 Faol ajdarlaringiz: {len(power_info['active_dragons'])} ta\n"
        f"❄️ Muzlagan ajdarlaringiz: {len(power_info['frozen_dragons'])} ta\n\n"
        f"🔥 **Jang va Hududiy Qoidalar:**\n"
        f"1. G'alaba qozonsangiz, mag'lub xonadon sizning **vassalingizga** aylanadi!\n"
        f"2. Mag'lub xonadon xazinasidagi oltinlarning 20% qismi o'lja qilinadi.\n"
        f"3. Jangda qatnashgan ajdarlaringiz **3 kunga (72 soat) muzlaydi**!\n"
        f"4. 🎺 **Hudud Lordlari himoyasi:** Agar Hudud Lordiga hujum qilinsa, u o'zining bayroqdorlarini yordamga chorlay oladi!\n\n"
        f"Hujum qilish uchun raqib xonadonni tanlang:"
    )

    if not occupied_houses:
        text += "\n\n😴 *Hozircha boshqa o'yinchilar xonadon tanlamagan. Boshqa o'yinchilar botga kirib xonadon tanlashi kutilmoqda.*"
        await message.answer(text, parse_mode="Markdown")
        return

    rows = []
    for h in occupied_houses[:12]:
        h_owner = await get_user(h["owner_id"])
        owner_name = h_owner["full_name"] if h_owner else f"Lord #{h['owner_id']}"
        username_str = f" (@{h_owner['username']})" if (h_owner and h_owner.get("username")) else ""
        vassal_tag = " (Vassal)" if h["overlord_id"] else ""
        tier_tag = f" [{h.get('tier', 'B')}-toifa]"
        btn_text = f"⚔️ {h['name']}{tier_tag}{vassal_tag} — {owner_name}{username_str}"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"attack_confirm:{h['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("attack_confirm:"))
async def callback_attack_confirm(callback: types.CallbackQuery):
    house_id = int(callback.data.split(":")[1])
    target_house = await get_house_by_id(house_id)
    if not target_house:
        await callback.answer("Xonadon topilmadi!", show_alert=True)
        return

    user_house = await get_user_house(callback.from_user.id)
    if not user_house:
        await callback.answer("Sizda xonadon yo'q!", show_alert=True)
        return

    power_info = await calculate_player_power(callback.from_user.id)
    if power_info["total_active_power"] <= 0:
        await callback.answer("Sizda jangga kiradigan askar yoki ajdar yo'q!", show_alert=True)
        return

    target_reg = REGIONS.get(target_house.get("region", ""), {})
    is_target_lord = target_house.get("is_regional_lord") or target_house["id"] == 1

    active_cta = await get_active_call_to_arms(house_id)
    call_id = active_cta["id"] if active_cta else 0

    lord_warning = ""
    can_call_bannermen = False

    if is_target_lord:
        bannermen = await get_region_bannermen(target_house["region"])
        can_call_bannermen = len(bannermen) > 0
        lord_warning = (
            f"\n\n⚠️ **DIQQAT!** Bu xonadon **{target_reg.get('name', '')}** Hudud Lordi hisoblanadi!\n"
            f"Hududda {len(bannermen)} ta faol bayroqdor xonadonlar mavjud. "
            f"Lord yordamga bayroqdorlarni chorlashi mumkin!"
        )

    if active_cta:
        pledged_pwr = await get_call_pledged_power(active_cta["id"])
        lord_warning += f"\n\n🎺 *Bayroqdorlar allaqachon himoyaga yetib kelgan (+{pledged_pwr} ball quvvat)!*"

    text = (
        f"⚔️ **URUSH E'LON QILISH!**\n\n"
        f"Raqib: **{target_house['name']}** (#{target_house['id']})\n"
        f"Hudud: **{target_reg.get('name', '')}**\n"
        f"{lord_warning}\n\n"
        f"Sizning faol kuchingiz: **{power_info['total_active_power']} ball**\n"
        f"⚠️ *Eslatma: Jangdan so'ng barcha faol ajdarlaringiz 3 kunga muzlaydi!*"
    )

    kb = battle_confirm_kb(house_id, can_call_bannermen=can_call_bannermen and not active_cta, call_id=call_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("trigger_cta:"))
async def callback_trigger_cta(callback: types.CallbackQuery):
    target_house_id = int(callback.data.split(":")[1])
    target_house = await get_house_by_id(target_house_id)
    user_house = await get_user_house(callback.from_user.id)

    if not target_house:
        await callback.answer("Xonadon topilmadi!", show_alert=True)
        return

    # Call to Arms yaratish
    region = target_house["region"]
    call_id = await create_call_to_arms(target_house_id, callback.from_user.id, user_house["id"], region)

    # Hududdagi bayroqdorlarga xabar tarqatish
    bannermen = await get_region_bannermen(region)
    reg_info = REGIONS.get(region, {})
    sent_count = 0

    for bm in bannermen:
        if bm["owner_id"] and bm["owner_id"] != callback.from_user.id:
            try:
                alert_text = (
                    f"🎺 **SHOSHILINCH CHORLOV (CALL TO ARMS)!**\n\n"
                    f"Hurmatli Lord! Bizning **{reg_info.get('name', '')}** Hudud Lordimiz "
                    f"**{target_house['name']}** xonadoniga dushman (**{user_house['name']}**) hujum qilmoqda!\n\n"
                    f"Lordimizni himoya qilish uchun qo'shin jo'natasizmi?\n"
                    f"*(Armiyangizning 30% kuchi himoyaga qo'shiladi va g'alabadan so'ng sizga +30 🪙 mukofot beriladi)*"
                )
                await callback.bot.send_message(
                    bm["owner_id"],
                    alert_text,
                    reply_markup=call_to_arms_bannermen_kb(call_id),
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception:
                pass

    await callback.answer(f"🎺 {sent_count} ta bayroqdor xonadonga yordam so'rovi yuborildi!", show_alert=True)

    # Menuni yangilash
    power_info = await calculate_player_power(callback.from_user.id)
    target_reg = REGIONS.get(region, {})
    text = (
        f"⚔️ **URUSH E'LON QILISH (BAYROQDORLAR CHORLANDI)!**\n\n"
        f"Raqib: **{target_house['name']}** (#{target_house['id']})\n"
        f"Hudud: **{target_reg.get('name', '')}**\n\n"
        f"🎺 *Hududdagi {sent_count} ta bayroqdorga shoshilinch yordam xabari jo'natildi!*\n"
        f"Ular xohlasa himoyaga qo'shiladi.\n\n"
        f"Sizning faol kuchingiz: **{power_info['total_active_power']} ball**"
    )
    kb = battle_confirm_kb(target_house_id, can_call_bannermen=False, call_id=call_id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("pledge_cta:"))
async def callback_pledge_cta(callback: types.CallbackQuery):
    call_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    success, msg, power = await pledge_bannerman_support(call_id, user_id)
    if success:
        await callback.message.edit_text(
            f"🛡 **SADOQAT VA YORDAM!**\n\n{msg}\n\nLordimiz uchun mardonavor kurashing!",
            parse_mode="Markdown"
        )
        await callback.answer("Qo'shin jo'natildi! 🛡", show_alert=True)
    else:
        await callback.answer(msg, show_alert=True)

@router.callback_query(F.data.startswith("decline_cta:"))
async def callback_decline_cta(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🙅 **Siz chorlovni rad etdingiz.** Qo'shinlaringiz o'z qal'angizda qoldi.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("attack_exec:"))
async def callback_attack_execute(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    house_id = int(parts[1])
    call_id = int(parts[2]) if len(parts) > 2 else 0

    attacker_id = callback.from_user.id

    res = await execute_battle(attacker_id, house_id, call_id=call_id if call_id > 0 else None)
    if not res.get("success"):
        await callback.answer(res.get("error", "Xatolik yuz berdi!"), show_alert=True)
        return

    bannermen_info = ""
    if res.get("bannermen_power", 0) > 0:
        bannermen_info = f"\n🎺 **Bayroqdorlar yordami:** +{res['bannermen_power']} ball ({res['bannermen_count']} ta xonadon)!"

    ally_info = ""
    if res.get("ally_support_power", 0) > 0:
        ally_info = f"\n💍 **Ittifoqdosh himoyasi:** {res['ally_house_name']} xonadoni +{res['ally_support_power']} mudofaa kuchi berdi!"

    if res["attacker_won"]:
        report = (
            f"🎉 **BUYUK G'ALABA! VALERIYA QON BILAN SUG'ORILDI!** 🩸\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{res['attacker_house']}**\n"
            f"🛡 Himoyachi: **{res['defender_house']}**\n\n"
            f"⚡️ Jangdagi zarba kuchi: **{res['attacker_power']}** vs **{res['defender_power']}**{bannermen_info}{ally_info}\n"
            f"🗡 Qurbon bo'lgan askarlaringiz: **{res['attacker_loss']} ta**\n"
            f"💀 Dushmanning yo'qotishlari: **{res['defender_loss']} ta** askar\n"
            f"💰 Qo'lga kiritilgan o'lja: **+{res['loot_gold']} 🪙**\n\n"
            f"👑 **SIYOSIY NATIJA:**\n"
            f"**{res['defender_house']}** xonadoni tizzaga cho'kdi va sizning **VASSALINGIZGA** aylandi! "
            f"Endi siz ulardan muntazam soliq yig'ib olasiz.\n\n"
            f"❄️ *Muzlash holati:* Jangda qatnashgan barcha ajdarlaringiz **3 kunga muzladi**."
        )
    else:
        reward_bannermen_note = "\n💰 *Yordamga kelgan barcha bayroqdorlarga +30 🪙 mukofot berildi!*" if res.get("bannermen_count", 0) > 0 else ""
        report = (
            f"💀 **MAG'LUBIYAT! HUJUM QAYTARILDI!** 🛡\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏰 Hujum qiluvchi: **{res['attacker_house']}**\n"
            f"🛡 Himoyachi: **{res['defender_house']}**\n\n"
            f"⚡️ Jangdagi zarba kuchi: **{res['attacker_power']}** vs **{res['defender_power']}**{bannermen_info}\n"
            f"🗡 Halok bo'lgan askarlaringiz: **{res['attacker_loss']} ta**\n"
            f"🛡 Qal'a va uning bayroqdorlari hujumni muvaffaqiyatli qaytardi!{reward_bannermen_note}\n\n"
            f"❄️ *Muzlash holati:* Jangda qatnashgan ajdarlaringiz **3 kunga muzladi**."
        )

    await callback.message.edit_text(report, parse_mode="Markdown")
    await callback.answer()
