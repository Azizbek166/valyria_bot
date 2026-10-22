import os
import aiosqlite
import time
import random
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from config import (
    DB_PATH, HOUSES_DATA, START_GOLD, START_SOLDIERS,
    UNITS, DRAGON_GRADES, DRAGON_FREEZE_SECONDS, REGIONS,
    ESSOS_MARKET, CASTLE_INCOME, CASTLE_COST, TIER_A_HOUSES,
    DONATE_PACKAGES, CHAKRA_DAILY_LIMIT, LOAN_PACKAGES,
    BATTLE_DURATION_SECONDS
)

@asynccontextmanager
async def get_db_connection():
    db_file = os.getenv("DB_PATH", DB_PATH)
    async with aiosqlite.connect(db_file) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn

async def init_db():
    async with get_db_connection() as db:
        # Users jadvali
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                gold INTEGER DEFAULT {START_GOLD},
                last_daily_claim INTEGER DEFAULT 0,
                last_tax_collected INTEGER DEFAULT 0,
                created_at INTEGER,
                is_blocked INTEGER DEFAULT 0,
                valyrian_steel INTEGER DEFAULT 0,
                daily_chakra_bought INTEGER DEFAULT 0,
                last_chakra_reset INTEGER DEFAULT 0
            )
        """)

        # Users jadvali migratsiyasi
        cursor = await db.execute("PRAGMA table_info(users)")
        u_columns = [row["name"] for row in await cursor.fetchall()]
        if "last_tax_collected" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_tax_collected INTEGER DEFAULT 0")
        if "is_blocked" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
        if "valyrian_steel" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN valyrian_steel INTEGER DEFAULT 0")
        if "daily_chakra_bought" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN daily_chakra_bought INTEGER DEFAULT 0")
        if "last_chakra_reset" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_chakra_reset INTEGER DEFAULT 0")
        if "custom_name" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN custom_name TEXT DEFAULT NULL")
        if "debt_amount" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN debt_amount INTEGER DEFAULT 0")
        if "debt_due_amount" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN debt_due_amount INTEGER DEFAULT 0")
        if "debt_taken_at" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN debt_taken_at INTEGER DEFAULT 0")
        if "last_battle_time" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_battle_time INTEGER DEFAULT 0")
        if "tournament_points" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN tournament_points INTEGER DEFAULT 0")
        if "tournament_wins" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN tournament_wins INTEGER DEFAULT 0")
        if "tournament_fights" not in u_columns:
            await db.execute("ALTER TABLE users ADD COLUMN tournament_fights INTEGER DEFAULT 0")

        # Houses jadvali (52 ta xonadon, 5 ta hudud)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS houses (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                region TEXT,
                is_regional_lord INTEGER DEFAULT 0,
                tier TEXT DEFAULT 'B',
                owner_id INTEGER UNIQUE,
                overlord_id INTEGER,
                captured_at INTEGER,
                accumulated_tax INTEGER DEFAULT 0,
                FOREIGN KEY (owner_id) REFERENCES users (telegram_id)
            )
        """)

        # Check and migrate columns if needed
        cursor = await db.execute("PRAGMA table_info(houses)")
        columns = [row["name"] for row in await cursor.fetchall()]
        if "region" not in columns:
            await db.execute("ALTER TABLE houses ADD COLUMN region TEXT")
        if "is_regional_lord" not in columns:
            await db.execute("ALTER TABLE houses ADD COLUMN is_regional_lord INTEGER DEFAULT 0")
        if "tier" not in columns:
            await db.execute("ALTER TABLE houses ADD COLUMN tier TEXT DEFAULT 'B'")

        # Armies jadvali
        await db.execute(f"""
            CREATE TABLE IF NOT EXISTS armies (
                user_id INTEGER PRIMARY KEY,
                soldiers INTEGER DEFAULT {START_SOLDIERS},
                archers INTEGER DEFAULT 0,
                cavalry INTEGER DEFAULT 0,
                chakra INTEGER DEFAULT 0,
                gold_cloaks INTEGER DEFAULT 0,
                unsullied INTEGER DEFAULT 0,
                faceless INTEGER DEFAULT 0,
                shadow INTEGER DEFAULT 0,
                poison INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)

        # Armies jadvali migratsiyasi
        cursor = await db.execute("PRAGMA table_info(armies)")
        a_columns = [row["name"] for row in await cursor.fetchall()]
        if "archers" not in a_columns:
            await db.execute("ALTER TABLE armies ADD COLUMN archers INTEGER DEFAULT 0")
        if "cavalry" not in a_columns:
            await db.execute("ALTER TABLE armies ADD COLUMN cavalry INTEGER DEFAULT 0")
        if "unsullied" not in a_columns:
            await db.execute("ALTER TABLE armies ADD COLUMN unsullied INTEGER DEFAULT 0")
        if "faceless" not in a_columns:
            await db.execute("ALTER TABLE armies ADD COLUMN faceless INTEGER DEFAULT 0")
        if "shadow" not in a_columns:
            await db.execute("ALTER TABLE armies ADD COLUMN shadow INTEGER DEFAULT 0")
        if "poison" not in a_columns:
            await db.execute("ALTER TABLE armies ADD COLUMN poison INTEGER DEFAULT 0")

        # Beasts jadvali (Ajdarlar va O'rgimchaklar)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS beasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                beast_type TEXT NOT NULL,
                name TEXT,
                grade TEXT DEFAULT 'C',
                power INTEGER DEFAULT 500,
                frozen_until INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)

        # Qal'alar jadvali (Castles)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS castles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                house_id INTEGER UNIQUE NOT NULL,
                owner_id INTEGER NOT NULL,
                level INTEGER DEFAULT 1,
                last_collected_at INTEGER DEFAULT 0,
                created_at INTEGER
            )
        """)

        # Nikoh va Manfaatli Ittifoqlar jadvali (Alliances)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                house1_id INTEGER NOT NULL,
                house2_id INTEGER NOT NULL,
                lord1_id INTEGER NOT NULL,
                lord2_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                alliance_type TEXT DEFAULT 'marriage',
                created_at INTEGER,
                updated_at INTEGER
            )
        """)

        # Kunlik hududiy topshiriqlar jadvali (Daily Territory Quests)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_territory_tasks (
                user_id INTEGER PRIMARY KEY,
                task_date TEXT NOT NULL,
                task1_done INTEGER DEFAULT 0,
                task2_done INTEGER DEFAULT 0,
                task3_done INTEGER DEFAULT 0,
                super_claimed INTEGER DEFAULT 0
            )
        """)

        # Green Bank To'lovlar (Donations) jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                package_id INTEGER NOT NULL,
                amount_uzs INTEGER NOT NULL,
                receipt_file_id TEXT,
                receipt_type TEXT DEFAULT 'photo',
                status TEXT DEFAULT 'pending',
                created_at INTEGER,
                reviewed_at INTEGER,
                admin_id INTEGER
            )
        """)

        # Ekspeditsiyalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expeditions (
                user_id INTEGER PRIMARY KEY,
                end_time INTEGER,
                duration_hours INTEGER,
                reward_gold INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)

        # Janglar tarixi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS battles_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER,
                defender_id INTEGER,
                winner_id INTEGER,
                log_text TEXT,
                timestamp INTEGER
            )
        """)

        # Call to Arms jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS call_to_arms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_house_id INTEGER NOT NULL,
                region TEXT NOT NULL,
                caller_id INTEGER NOT NULL,
                attacker_house_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                created_at INTEGER
            )
        """)

        # Bayroqdorlar qo'shilishi jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bannermen_pledges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                house_id INTEGER NOT NULL,
                contributed_power INTEGER DEFAULT 0,
                created_at INTEGER,
                FOREIGN KEY (call_id) REFERENCES call_to_arms (id)
            )
        """)

        # Faol janglar (Active Battles - 8 daqiqalik janglar) jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER NOT NULL,
                defender_house_id INTEGER NOT NULL,
                troops_json TEXT NOT NULL,
                start_time INTEGER NOT NULL,
                end_time INTEGER NOT NULL,
                call_id INTEGER DEFAULT 0,
                status TEXT DEFAULT 'marching',
                created_at INTEGER
            )
        """)

        # Boshlang'ich 52 ta xonadonni kiritish yoki hududlarini yangilash
        for house in HOUSES_DATA:
            tier = "A" if house["id"] in TIER_A_HOUSES else "B"
            await db.execute("""
                INSERT INTO houses (id, name, type, region, is_regional_lord, tier)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    region = excluded.region,
                    is_regional_lord = excluded.is_regional_lord,
                    tier = excluded.tier
            """, (house["id"], house["name"], house["type"], house["region"], 1 if house.get("is_regional_lord") else 0, tier))

        await db.commit()

# --- Foydalanuvchi funksiyalari ---

async def get_or_create_user(telegram_id: int, username: str, full_name: str) -> Dict[str, Any]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        now = int(time.time())
        if not row:
            await db.execute(
                "INSERT INTO users (telegram_id, username, full_name, gold, created_at, last_tax_collected) VALUES (?, ?, ?, ?, ?, 0)",
                (telegram_id, username or "", full_name or "", START_GOLD, now)
            )
            await db.execute(
                "INSERT INTO armies (user_id, soldiers, archers, cavalry, chakra, gold_cloaks, unsullied, faceless, shadow, poison) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0)",
                (telegram_id, START_SOLDIERS)
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
        else:
            await db.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?",
                (username or "", full_name or "", telegram_id)
            )
            await db.commit()
        return dict(row)

async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def is_user_blocked(telegram_id: int) -> bool:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT is_blocked FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return bool(row["is_blocked"]) if row and "is_blocked" in row.keys() else False

async def set_user_blocked(telegram_id: int, blocked: bool) -> bool:
    val = 1 if blocked else 0
    async with get_db_connection() as db:
        await db.execute("UPDATE users SET is_blocked = ? WHERE telegram_id = ?", (val, telegram_id))
        await db.commit()
        return True

async def update_user_gold(telegram_id: int, delta: int) -> int:
    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = MAX(0, gold + ?) WHERE telegram_id = ?", (delta, telegram_id))
        await db.commit()
        cursor = await db.execute("SELECT gold FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row["gold"] if row else 0

# --- Xonadonlar (Houses) va Hududlar ---

async def get_user_house(telegram_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT h.*, u.username as owner_username, COALESCE(u.custom_name, u.full_name) as owner_name,
                   c.level as castle_level
            FROM houses h
            LEFT JOIN users u ON h.owner_id = u.telegram_id
            LEFT JOIN castles c ON h.id = c.house_id
            WHERE h.owner_id = ?
        """, (telegram_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_house_by_id(house_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT h.*, u.username as owner_username, COALESCE(u.custom_name, u.full_name) as owner_name,
                   c.level as castle_level
            FROM houses h
            LEFT JOIN users u ON h.owner_id = u.telegram_id
            LEFT JOIN castles c ON h.id = c.house_id
            WHERE h.id = ?
        """, (house_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_houses(house_type: Optional[str] = None, region: Optional[str] = None) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        base_query = """
            SELECT h.*, u.username as owner_username, COALESCE(u.custom_name, u.full_name) as owner_name,
                   c.level as castle_level
            FROM houses h
            LEFT JOIN users u ON h.owner_id = u.telegram_id
            LEFT JOIN castles c ON h.id = c.house_id
        """
        if region:
            cursor = await db.execute(base_query + " WHERE h.region = ? ORDER BY h.id ASC", (region,))
        elif house_type:
            cursor = await db.execute(base_query + " WHERE h.type = ? ORDER BY h.id ASC", (house_type,))
        else:
            cursor = await db.execute(base_query + " ORDER BY h.id ASC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_region_bannermen(region: str) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM houses WHERE region = ? AND is_regional_lord = 0 AND owner_id IS NOT NULL",
            (region,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_regional_lord_house(region: str) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM houses WHERE region = ? AND is_regional_lord = 1",
            (region,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

async def choose_house(telegram_id: int, house_id: int) -> tuple[bool, str]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM houses WHERE owner_id = ?", (telegram_id,))
        current = await cursor.fetchone()
        if current:
            return False, f"Siz allaqachon **{current['name']}** xonadonining hukmdorisiz!"

        cursor = await db.execute("SELECT * FROM houses WHERE id = ?", (house_id,))
        house = await cursor.fetchone()
        if not house:
            return False, "Bunday xonadon topilmadi!"
        if house["owner_id"] is not None:
            return False, f"**{house['name']}** xonadoni allaqachon boshqa hukmdor tomonidan egallangan!"

        await db.execute(
            "UPDATE houses SET owner_id = ?, overlord_id = NULL WHERE id = ?",
            (telegram_id, house_id)
        )
        await db.commit()

        region_info = REGIONS.get(house["region"], {})
        reg_title = region_info.get("name", "Valeriya")
        lord_status = "👑 Oliy Qirol!" if house["id"] == 1 else ("🛡 Hudud Lordi!" if house["is_regional_lord"] else "🗡 Bayroqdor!")

        return True, f"Tabriklaymiz! Siz **{house['name']}** xonadoni ({reg_title}) hukmdori bo'ldingiz! {lord_status}"

# --- Bayroqdorlarni Yordamga Chorlash (Call to Arms) ---

async def create_call_to_arms(target_house_id: int, caller_id: int, attacker_house_id: int, region: str) -> int:
    now = int(time.time())
    async with get_db_connection() as db:
        cursor = await db.execute(
            "INSERT INTO call_to_arms (target_house_id, region, caller_id, attacker_house_id, status, created_at) VALUES (?, ?, ?, ?, 'active', ?)",
            (target_house_id, region, caller_id, attacker_house_id, now)
        )
        await db.commit()
        return cursor.lastrowid

async def get_active_call_to_arms(target_house_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM call_to_arms WHERE target_house_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1",
            (target_house_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

async def pledge_bannerman_support(call_id: int, user_id: int) -> tuple[bool, str, int]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM call_to_arms WHERE id = ? AND status = 'active'", (call_id,))
        call = await cursor.fetchone()
        if not call:
            return False, "Chorlov muddati tugagan yoki mavjud emas!", 0

        cursor = await db.execute("SELECT * FROM bannermen_pledges WHERE call_id = ? AND user_id = ?", (call_id, user_id))
        existing = await cursor.fetchone()
        if existing:
            return False, "Siz allaqachon o'z qo'shiningiz bilan yordam berdingiz!", 0

        cursor = await db.execute("SELECT * FROM houses WHERE owner_id = ?", (user_id,))
        user_house = await cursor.fetchone()
        if not user_house or user_house["region"] != call["region"]:
            return False, "Siz ushbu hududga mansub emassiz!", 0

        p_info = await calculate_player_power(user_id)
        contributed = max(10, int(p_info["total_active_power"] * 0.3))

        now = int(time.time())
        await db.execute(
            "INSERT INTO bannermen_pledges (call_id, user_id, house_id, contributed_power, created_at) VALUES (?, ?, ?, ?, ?)",
            (call_id, user_id, user_house["id"], contributed, now)
        )
        await db.commit()
        return True, f"Siz Lordimiz himoyasiga **+{contributed} ball** jangovar quvvat bilan qo'shildingiz! 🛡", contributed

async def get_call_pledged_power(call_id: int) -> int:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT SUM(contributed_power) as total FROM bannermen_pledges WHERE call_id = ?", (call_id,))
        row = await cursor.fetchone()
        return row["total"] or 0 if row and row["total"] else 0

async def get_call_pledges(call_id: int) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM bannermen_pledges WHERE call_id = ?", (call_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def resolve_call_to_arms(call_id: int):
    async with get_db_connection() as db:
        await db.execute("UPDATE call_to_arms SET status = 'resolved' WHERE id = ?", (call_id,))
        await db.commit()

# --- Armiya va Hayvonlar ---

async def get_user_army(telegram_id: int) -> Dict[str, Any]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM armies WHERE user_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO armies (user_id, soldiers, chakra, gold_cloaks, unsullied, faceless, shadow, poison) VALUES (?, ?, 0, 0, 0, 0, 0, 0)",
                (telegram_id, START_SOLDIERS)
            )
            await db.commit()
            return {
                "user_id": telegram_id, "soldiers": START_SOLDIERS, "chakra": 0, "gold_cloaks": 0,
                "unsullied": 0, "faceless": 0, "shadow": 0, "poison": 0
            }
        data = dict(row)
        for key in ["soldiers", "chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"]:
            data.setdefault(key, 0)
        return data

async def buy_troops(telegram_id: int, troop_type: str, count: int) -> tuple[bool, str]:
    if count <= 0:
        return False, "Miqdor 1 dan katta bo'lishi kerak!"

    unit_info = UNITS.get(troop_type)
    if not unit_info or troop_type in ["dragon", "spider"]:
        return False, "Noto'g'ri qo'shin turi!"

    total_cost = unit_info["cost"] * count
    user = await get_user(telegram_id)
    if not user or user["gold"] < total_cost:
        return False, f"Mablag' yetarli emas! Sizga {total_cost} tanga kerak, sizda esa {user['gold'] if user else 0} tanga bor."

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (total_cost, telegram_id))
        col_map = {
            "soldier": "soldiers",
            "chakra": "chakra",
            "gold_cloak": "gold_cloaks",
            "unsullied": "unsullied",
            "faceless": "faceless",
            "shadow": "shadow",
            "poison": "poison"
        }
        col = col_map.get(troop_type, "soldiers")
        await db.execute(f"UPDATE armies SET {col} = {col} + ? WHERE user_id = ?", (count, telegram_id))
        await db.commit()

    return True, f"Siz muvaffaqiyatli {count} ta **{unit_info['name']}** yolladingiz! (-{total_cost} tanga)"

async def buy_chakra_item(telegram_id: int, count: int) -> tuple[bool, str]:
    if count <= 0:
        return False, "Miqdor 1 dan katta bo'lishi kerak!"

    cost_per_item = ESSOS_MARKET["meereen"]["cost"]  # 2 oltin
    total_cost = cost_per_item * count

    user = await get_user(telegram_id)
    if not user or user["gold"] < total_cost:
        return False, f"Mablag' yetarli emas! Sizga {total_cost} tanga kerak, sizda esa {user['gold'] if user else 0} tanga bor."

    valyrian_steel = user.get("valyrian_steel", 0) or 0
    now = int(time.time())

    # Agar o'yinchida Valeriya po'lati bo'lsa (valyrian_steel >= 1) — chakra CHEKSIZ!
    if valyrian_steel >= 1:
        async with get_db_connection() as db:
            await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (total_cost, telegram_id))
            await db.execute("UPDATE armies SET chakra = chakra + ? WHERE user_id = ?", (count, telegram_id))
            await db.commit()
        return True, f"⚔️ **Valeriya po'lati qudrati!** Sizda Valeriya po'lati borligi sababli cheksiz miqdorda Chakra ishlatasiz!\nSiz {count} ta **Chakra ⚙️** xarid qildingiz (-{total_cost} tanga)."

    # Valeriya po'lati bo'lmaganda kunlik 500 ta limit
    last_reset = user.get("last_chakra_reset", 0) or 0
    daily_bought = user.get("daily_chakra_bought", 0) or 0

    if now - last_reset >= 86400:
        daily_bought = 0
        last_reset = now

    if daily_bought + count > CHAKRA_DAILY_LIMIT:
        rem = max(0, CHAKRA_DAILY_LIMIT - daily_bought)
        return False, (
            f"⚠️ Chakra uchun kunlik limit: **{CHAKRA_DAILY_LIMIT} ta**!\n"
            f"Bugun xarid qilingan: {daily_bought}/{CHAKRA_DAILY_LIMIT}.\n"
            f"Bugun yana ko'pi bilan **{rem} ta** olishingiz mumkin.\n\n"
            f"💡 *Eslatma: Green Bank orqali 1 dona Valeriya Po'lati xarid qilsangiz, Chakra cheksiz bo'ladi!*"
        )

    daily_bought += count

    async with get_db_connection() as db:
        await db.execute(
            "UPDATE users SET gold = gold - ?, daily_chakra_bought = ?, last_chakra_reset = ? WHERE telegram_id = ?",
            (total_cost, daily_bought, last_reset, telegram_id)
        )
        await db.execute("UPDATE armies SET chakra = chakra + ? WHERE user_id = ?", (count, telegram_id))
        await db.commit()

    return True, f"Siz muvaffaqiyatli {count} ta **Chakra ⚙️** (Meereen) xarid qildingiz! (-{total_cost} tanga)\nBugungi xaridingiz: {daily_bought}/{CHAKRA_DAILY_LIMIT} ta."

async def buy_essos_item(telegram_id: int, item_key: str, count: int = 1) -> tuple[bool, str]:
    item = ESSOS_MARKET.get(item_key)
    if not item:
        for k, v in ESSOS_MARKET.items():
            if v["unit_key"] == item_key:
                item = v
                break
    if not item:
        return False, "Noto'g'ri tovar tanlandi!"

    if count <= 0:
        return False, "Miqdor 1 dan katta bo'lishi kerak!"

    unit_key = item["unit_key"]

    if unit_key == "chakra":
        return await buy_chakra_item(telegram_id, count)

    if unit_key == "spider":
        # Spiders are stored in beasts table
        return await buy_beast(telegram_id, "spider")

    total_cost = item["cost"] * count
    user = await get_user(telegram_id)
    if not user or user["gold"] < total_cost:
        return False, f"Mablag' yetarli emas! Sizga {total_cost} tanga kerak, sizda esa {user['gold'] if user else 0} tanga bor."

    col_map = {
        "unsullied": "unsullied",
        "faceless": "faceless",
        "shadow": "shadow",
        "poison": "poison"
    }

    col = col_map.get(unit_key)
    if not col:
        return False, "Noto'g'ri birlik turi!"

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (total_cost, telegram_id))
        await db.execute(f"UPDATE armies SET {col} = {col} + ? WHERE user_id = ?", (count, telegram_id))
        await db.commit()

    return True, f"Siz muvaffaqiyatli {count} ta **{item['name']}** ({item['city']}) xarid qildingiz! (-{total_cost} tanga)"

async def get_user_beasts(telegram_id: int) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM beasts WHERE user_id = ? ORDER BY id ASC", (telegram_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def buy_beast(telegram_id: int, beast_type: str, custom_name: Optional[str] = None) -> tuple[bool, str]:
    unit_info = UNITS.get(beast_type)
    if not unit_info or beast_type not in ["dragon", "spider"]:
        return False, "Noto'g'ri maxluq turi!"

    cost = unit_info["cost"]
    user = await get_user(telegram_id)
    if not user or user["gold"] < cost:
        return False, f"Mablag' yetarli emas! {unit_info['name']} narxi: {cost} tanga. Sizda: {user['gold'] if user else 0} tanga."

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (cost, telegram_id))
        if beast_type == "dragon":
            name = custom_name or "Tessarion"
            await db.execute(
                "INSERT INTO beasts (user_id, beast_type, name, grade, power, frozen_until) VALUES (?, 'dragon', ?, 'C', 500, 0)",
                (telegram_id, name)
            )
        else:
            name = custom_name or "Muz Oʻrgimchagi"
            await db.execute(
                "INSERT INTO beasts (user_id, beast_type, name, grade, power, frozen_until) VALUES (?, 'spider', ?, 'C', 500, 0)",
                (telegram_id, name)
            )
        await db.commit()

    return True, f"Tabriklaymiz! Siz o'zingizga **{name}** nomli {unit_info['name']} sotib oldingiz! (-{cost} tanga)"

async def upgrade_dragon(telegram_id: int, beast_id: int) -> tuple[bool, str]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM beasts WHERE id = ? AND user_id = ?", (beast_id, telegram_id))
        beast = await cursor.fetchone()
        if not beast or beast["beast_type"] != "dragon":
            return False, "Bunday ajdar topilmadi!"

        current_grade = beast["grade"]
        grade_info = DRAGON_GRADES.get(current_grade)
        if not grade_info or not grade_info["next"]:
            return False, f"Bu ajdar allaqachon maksimal **S daraja**ga (2000 ball) yetgan!"

        next_grade = grade_info["next"]
        cost = grade_info["upgrade_cost"]
        new_power = DRAGON_GRADES[next_grade]["power"]

        user = await get_user(telegram_id)
        if not user or user["gold"] < cost:
            return False, f"Kuchaytirish uchun {cost} tanga kerak! Sizda: {user['gold'] if user else 0} tanga."

        await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (cost, telegram_id))
        await db.execute("UPDATE beasts SET grade = ?, power = ? WHERE id = ?", (next_grade, new_power, beast_id))
        await db.commit()

    return True, f"Ajdaringiz muvaffaqiyatli **{next_grade} daraja**ga ko'tarildi! Yangi kuchi: {new_power} ball! (-{cost} tanga)"

# --- Harbiy Kuchni Hisoblash ---

async def calculate_player_power(telegram_id: int) -> Dict[str, Any]:
    user = await get_user(telegram_id)
    army = await get_user_army(telegram_id)
    beasts = await get_user_beasts(telegram_id)
    now = int(time.time())

    valyrian_steel = (user.get("valyrian_steel", 0) or 0) if user else 0
    # Valeriya po'lati: cheksiz chakra quvvati (x2 jangovar zarba) + po'latning o'z kuchi (+500 har biri)
    chakra_multiplier = 2 if valyrian_steel >= 1 else 1
    chakra_power = army.get("chakra", 0) * UNITS["chakra"]["atk"] * chakra_multiplier
    valyrian_steel_power = valyrian_steel * 500

    troops_power = (
        army.get("soldiers", 0) * UNITS["soldier"]["atk"] +
        army.get("archers", 0) * UNITS.get("archer", {}).get("atk", 3) +
        army.get("cavalry", 0) * UNITS.get("cavalry", {}).get("atk", 6) +
        chakra_power +
        army.get("gold_cloaks", 0) * UNITS["gold_cloak"]["atk"] +
        army.get("unsullied", 0) * UNITS["unsullied"]["atk"] +
        army.get("faceless", 0) * UNITS["faceless"]["atk"] +
        army.get("shadow", 0) * UNITS["shadow"]["atk"] +
        army.get("poison", 0) * UNITS["poison"]["atk"] +
        valyrian_steel_power
    )

    spiders_power = sum(b["power"] for b in beasts if b["beast_type"] == "spider")

    dragons_active_power = 0
    dragons_frozen_power = 0
    active_dragons = []
    frozen_dragons = []

    for b in beasts:
        if b["beast_type"] == "dragon":
            if b["frozen_until"] > now:
                dragons_frozen_power += b["power"]
                frozen_dragons.append(b)
            else:
                dragons_active_power += b["power"]
                active_dragons.append(b)

    total_attack_power = troops_power + spiders_power + dragons_active_power

    return {
        "troops_power": troops_power,
        "spiders_power": spiders_power,
        "dragons_active_power": dragons_active_power,
        "dragons_frozen_power": dragons_frozen_power,
        "total_active_power": total_attack_power,
        "active_dragons": active_dragons,
        "frozen_dragons": frozen_dragons,
        "spiders_count": len([b for b in beasts if b["beast_type"] == "spider"]),
        "dragons_count": len(beasts) - len([b for b in beasts if b["beast_type"] == "spider"]),
        "valyrian_steel": valyrian_steel,
        "has_unlimited_chakra": valyrian_steel >= 1
    }

# --- Jang va Vassal Mexanikasi (8 Daqiqalik Faol Jang & Qo'shin Tanlash) ---

async def get_user_active_battle(user_id: int) -> Optional[Dict[str, Any]]:
    now = int(time.time())
    user_house = await get_user_house(user_id)
    house_id = user_house["id"] if user_house else 0
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT ab.*, 
                   h_att.name as attacker_house_name,
                   h_def.name as defender_house_name,
                   h_def.owner_id as defender_id
            FROM active_battles ab
            LEFT JOIN houses h_att ON h_att.owner_id = ab.attacker_id
            LEFT JOIN houses h_def ON h_def.id = ab.defender_house_id
            WHERE (ab.attacker_id = ? OR ab.defender_house_id = ?)
              AND ab.status = 'marching'
            ORDER BY ab.id DESC LIMIT 1
        """, (user_id, house_id))
        row = await cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["troops"] = json.loads(data["troops_json"])
        except Exception:
            data["troops"] = {}
        data["left_seconds"] = max(0, data["end_time"] - now)
        data["is_attacker"] = (data["attacker_id"] == user_id)
        data["ready"] = (now >= data["end_time"])
        return data

async def get_battle_by_id(battle_id: int) -> Optional[Dict[str, Any]]:
    now = int(time.time())
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT ab.*, 
                   h_att.name as attacker_house_name,
                   h_def.name as defender_house_name,
                   h_def.owner_id as defender_id
            FROM active_battles ab
            LEFT JOIN houses h_att ON h_att.owner_id = ab.attacker_id
            LEFT JOIN houses h_def ON h_def.id = ab.defender_house_id
            WHERE ab.id = ?
        """, (battle_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["troops"] = json.loads(data["troops_json"])
        except Exception:
            data["troops"] = {}
        data["left_seconds"] = max(0, data["end_time"] - now)
        data["ready"] = (now >= data["end_time"])
        return data

async def _refund_troops(db, attacker_id: int, troops: dict):
    await db.execute("""
        UPDATE armies SET
            soldiers = soldiers + ?,
            archers = archers + ?,
            cavalry = cavalry + ?,
            chakra = chakra + ?,
            gold_cloaks = gold_cloaks + ?,
            unsullied = unsullied + ?,
            faceless = faceless + ?,
            shadow = shadow + ?,
            poison = poison + ?
        WHERE user_id = ?
    """, (
        troops.get("soldiers", 0),
        troops.get("archers", 0),
        troops.get("cavalry", 0),
        troops.get("chakra", 0),
        troops.get("gold_cloaks", 0),
        troops.get("unsullied", 0),
        troops.get("faceless", 0),
        troops.get("shadow", 0),
        troops.get("poison", 0),
        attacker_id
    ))

async def start_house_attack(
    attacker_id: int,
    defender_house_id: int,
    selected_troops: Dict[str, Any],
    call_id: Optional[int] = None
) -> tuple[bool, str, Optional[int]]:
    now = int(time.time())

    active = await get_user_active_battle(attacker_id)
    if active:
        rem_min = active["left_seconds"] // 60
        rem_sec = active["left_seconds"] % 60
        return False, f"⚠️ Sizning qo'shiningiz allaqachon jangda! Dushman qal'asigacha: {rem_min} daqiqa {rem_sec} soniya qoldi.", None

    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM houses WHERE owner_id = ?", (attacker_id,))
        attacker_house = await cursor.fetchone()
        if not attacker_house:
            return False, "Siz hali birorta xonadonni tanlamagansiz!", None

        cursor = await db.execute("SELECT * FROM houses WHERE id = ?", (defender_house_id,))
        defender_house = await cursor.fetchone()
        if not defender_house:
            return False, "Bunday xonadon mavjud emas!", None

        if defender_house["owner_id"] is None:
            return False, "Bu xonadonda hali hukmdor yo'q, unga hujum qilib bo'lmaydi!", None

        if defender_house["owner_id"] == attacker_id:
            return False, "O'z xonadoningizga hujum qila olmaysiz!", None

        # Sulolaviy Nikoh va Manfaatli Ittifoq tekshiruvi
        is_allied, all_type = await are_houses_allied(attacker_house["id"], defender_house_id)
        if is_allied:
            all_name = "Sulolaviy Nikoh 💍" if all_type == "marriage" else "Manfaatli Ittifoq 🤝"
            return False, f"❌ Siz bu xonadon bilan **{all_name}**dasiz! O'zaro hujum qilish qat'iyan man etiladi.", None

        # Qo'shinlarni tekshirish
        cursor = await db.execute("SELECT * FROM armies WHERE user_id = ?", (attacker_id,))
        army_row = await cursor.fetchone()
        army = dict(army_row) if army_row else {}

        unit_cols = ["soldiers", "archers", "cavalry", "chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"]
        cleaned_troops = {}
        for col in unit_cols:
            qty = max(0, int(selected_troops.get(col, 0)))
            if qty > army.get(col, 0):
                return False, f"Sizda yetarli {col} yo'q! Mavjud: {army.get(col, 0)} ta.", None
            cleaned_troops[col] = qty

        # Ajdarlarni tekshirish
        dragon_ids = selected_troops.get("dragon_ids", [])
        verified_dragons = []
        if dragon_ids:
            cursor = await db.execute(
                "SELECT * FROM beasts WHERE user_id = ? AND beast_type = 'dragon' AND frozen_until <= ?",
                (attacker_id, now)
            )
            available_dragons = {d["id"]: dict(d) for d in await cursor.fetchall()}
            for did in dragon_ids:
                if did in available_dragons:
                    verified_dragons.append(did)
        cleaned_troops["dragon_ids"] = verified_dragons

        # Quvvatni hisoblash
        user_row = await get_user(attacker_id)
        valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
        chakra_mult = 2 if valyrian_steel >= 1 else 1

        power = (
            cleaned_troops["soldiers"] * UNITS["soldier"]["atk"] +
            cleaned_troops["archers"] * UNITS.get("archer", {}).get("atk", 3) +
            cleaned_troops["cavalry"] * UNITS.get("cavalry", {}).get("atk", 6) +
            cleaned_troops["chakra"] * UNITS["chakra"]["atk"] * chakra_mult +
            cleaned_troops["gold_cloaks"] * UNITS["gold_cloak"]["atk"] +
            cleaned_troops["unsullied"] * UNITS["unsullied"]["atk"] +
            cleaned_troops["faceless"] * UNITS["faceless"]["atk"] +
            cleaned_troops["shadow"] * UNITS["shadow"]["atk"] +
            cleaned_troops["poison"] * UNITS["poison"]["atk"]
        )

        for did in verified_dragons:
            d_obj = available_dragons[did]
            power += d_obj.get("power", 500)

        if power <= 0:
            return False, "⚠️ Jangga kamida bitta askar yoki ajdar tanlashingiz kerak!", None

        # Yuborilgan qo'shinlarni zaxiradan yechish (yurishda)
        await db.execute("""
            UPDATE armies SET
                soldiers = MAX(0, soldiers - ?),
                archers = MAX(0, archers - ?),
                cavalry = MAX(0, cavalry - ?),
                chakra = MAX(0, chakra - ?),
                gold_cloaks = MAX(0, gold_cloaks - ?),
                unsullied = MAX(0, unsullied - ?),
                faceless = MAX(0, faceless - ?),
                shadow = MAX(0, shadow - ?),
                poison = MAX(0, poison - ?)
            WHERE user_id = ?
        """, (
            cleaned_troops["soldiers"],
            cleaned_troops["archers"],
            cleaned_troops["cavalry"],
            cleaned_troops["chakra"],
            cleaned_troops["gold_cloaks"],
            cleaned_troops["unsullied"],
            cleaned_troops["faceless"],
            cleaned_troops["shadow"],
            cleaned_troops["poison"],
            attacker_id
        ))

        end_time = now + BATTLE_DURATION_SECONDS
        cursor = await db.execute("""
            INSERT INTO active_battles (
                attacker_id, defender_house_id, troops_json, start_time, end_time, call_id, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'marching', ?)
        """, (
            attacker_id,
            defender_house_id,
            json.dumps(cleaned_troops),
            now,
            end_time,
            call_id or 0,
            now
        ))
        battle_id = cursor.lastrowid
        await db.execute("UPDATE users SET last_battle_time = ? WHERE telegram_id = ?", (now, attacker_id))
        await db.commit()

        return True, "Qo'shin muvaffaqiyatli dushman qal'asi sari yo'l oldi!", battle_id

async def resolve_battle(battle_id: int) -> Dict[str, Any]:
    now = int(time.time())
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM active_battles WHERE id = ?", (battle_id,))
        row = await cursor.fetchone()
        if not row:
            return {"success": False, "error": "Bunday faol jang topilmadi!"}

        battle = dict(row)
        if battle["status"] != "marching":
            return {"success": False, "error": "Bu jang allaqachon yakunlangan!"}

        if now < battle["end_time"]:
            left = battle["end_time"] - now
            return {
                "success": False,
                "ready": False,
                "left_seconds": left,
                "error": f"Jang hali davom etmoqda! Dushman qal'asigacha {left // 60} daqiqa {left % 60} soniya qoldi."
            }

        attacker_id = battle["attacker_id"]
        defender_house_id = battle["defender_house_id"]
        call_id = battle.get("call_id", 0)
        troops = json.loads(battle["troops_json"])

        cursor = await db.execute("SELECT * FROM houses WHERE owner_id = ?", (attacker_id,))
        attacker_house = await cursor.fetchone()
        cursor = await db.execute("SELECT * FROM houses WHERE id = ?", (defender_house_id,))
        defender_house = await cursor.fetchone()

        if not attacker_house or not defender_house:
            await _refund_troops(db, attacker_id, troops)
            await db.execute("UPDATE active_battles SET status = 'cancelled' WHERE id = ?", (battle_id,))
            await db.commit()
            return {"success": False, "error": "Xonadon ma'lumotlarida o'zgarish bo'lganligi sababli jang bekor qilindi va qo'shinlar qaytarildi."}

        defender_id = defender_house["owner_id"]
        if defender_id is None:
            await _refund_troops(db, attacker_id, troops)
            await db.execute("UPDATE active_battles SET status = 'cancelled' WHERE id = ?", (battle_id,))
            await db.commit()
            return {"success": False, "error": "Himoyachi xonadon egasiz qolgan. Qo'shinlar qal'angizga qaytarildi."}

        # Hujumchi kuchi (faqat yuborilgan qo'shinlardan)
        user_row = await get_user(attacker_id)
        valyrian_steel = user_row.get("valyrian_steel", 0) if user_row else 0
        chakra_mult = 2 if valyrian_steel >= 1 else 1

        att_power = (
            troops.get("soldiers", 0) * UNITS["soldier"]["atk"] +
            troops.get("archers", 0) * UNITS.get("archer", {}).get("atk", 3) +
            troops.get("cavalry", 0) * UNITS.get("cavalry", {}).get("atk", 6) +
            troops.get("chakra", 0) * UNITS["chakra"]["atk"] * chakra_mult +
            troops.get("gold_cloaks", 0) * UNITS["gold_cloak"]["atk"] +
            troops.get("unsullied", 0) * UNITS["unsullied"]["atk"] +
            troops.get("faceless", 0) * UNITS["faceless"]["atk"] +
            troops.get("shadow", 0) * UNITS["shadow"]["atk"] +
            troops.get("poison", 0) * UNITS["poison"]["atk"] +
            (valyrian_steel * 500)
        )

        sent_dragon_ids = troops.get("dragon_ids", [])
        if sent_dragon_ids:
            for did in sent_dragon_ids:
                cursor = await db.execute("SELECT power FROM beasts WHERE id = ?", (did,))
                d_row = await cursor.fetchone()
                if d_row:
                    att_power += d_row["power"]

        # Hujumchining Manfaatli Ittifoqchisi ko'magi (+25%)
        att_strategic = await get_house_alliance(attacker_house["id"], "strategic")
        if att_strategic:
            att_strat_lord_id = att_strategic["lord2_id"] if att_strategic["lord1_id"] == attacker_id else att_strategic["lord1_id"]
            att_ally_info = await calculate_player_power(att_strat_lord_id)
            att_ally_power = max(10, int(att_ally_info["total_active_power"] * 0.25))
            att_power += att_ally_power

        # Himoyachi kuchi
        def_power_info = await calculate_player_power(defender_id)
        def_power = def_power_info["total_active_power"]

        bannermen_power = 0
        bannermen_count = 0
        if call_id:
            bannermen_power = await get_call_pledged_power(call_id)
            pledges = await get_call_pledges(call_id)
            bannermen_count = len(pledges)
            def_power += bannermen_power

        ally_support_power = 0
        ally_house_name = ""
        def_marriage = await get_house_alliance(defender_house_id, "marriage")
        if def_marriage:
            ally_lord_id = def_marriage["lord2_id"] if def_marriage["lord1_id"] == defender_id else def_marriage["lord1_id"]
            ally_house_name = def_marriage["h2_name"] if def_marriage["lord1_id"] == defender_id else def_marriage["h1_name"]
            ally_power_info = await calculate_player_power(ally_lord_id)
            marriage_bonus = max(15, int(ally_power_info["total_active_power"] * 0.5))
            ally_support_power += marriage_bonus
            def_power += marriage_bonus

        def_strategic = await get_house_alliance(defender_house_id, "strategic")
        if def_strategic:
            strat_lord_id = def_strategic["lord2_id"] if def_strategic["lord1_id"] == defender_id else def_strategic["lord1_id"]
            strat_h_name = def_strategic["h2_name"] if def_strategic["lord1_id"] == defender_id else def_strategic["h1_name"]
            strat_power_info = await calculate_player_power(strat_lord_id)
            strat_bonus = max(10, int(strat_power_info["total_active_power"] * 0.25))
            ally_support_power += strat_bonus
            def_power += strat_bonus
            if not ally_house_name:
                ally_house_name = strat_h_name

        att_roll = round(att_power * random.uniform(0.9, 1.15))
        def_roll = round(def_power * random.uniform(0.9, 1.15))
        attacker_won = att_roll > def_roll

        # Ajdarlarni muzlatish (faqat jangda qatnashgan ajdarlar!)
        freeze_end = now + DRAGON_FREEZE_SECONDS
        if sent_dragon_ids:
            for did in sent_dragon_ids:
                await db.execute("UPDATE beasts SET frozen_until = ? WHERE id = ?", (freeze_end, did))
        for dragon in def_power_info["active_dragons"]:
            await db.execute("UPDATE beasts SET frozen_until = ? WHERE id = ?", (freeze_end, dragon["id"]))

        # Talafotlar (faqat yuborilgan askarlardan yo'qotish hisoblanadi!)
        loss_rate_att = random.uniform(0.1, 0.25) if attacker_won else random.uniform(0.3, 0.55)
        att_losses = {}
        att_survivors = {}
        total_att_lost = 0

        unit_cols = ["soldiers", "archers", "cavalry", "chakra", "gold_cloaks", "unsullied", "faceless", "shadow", "poison"]
        for col in unit_cols:
            sent_cnt = troops.get(col, 0)
            if sent_cnt > 0:
                lost = max(0, min(sent_cnt, int(sent_cnt * loss_rate_att)))
                if lost == 0 and not attacker_won and sent_cnt >= 1:
                    lost = 1
                survived = sent_cnt - lost
                att_losses[col] = lost
                att_survivors[col] = survived
                total_att_lost += lost
            else:
                att_losses[col] = 0
                att_survivors[col] = 0

        # Omon qolgan askarlarni qal'aga qaytarish!
        await db.execute("""
            UPDATE armies SET
                soldiers = soldiers + ?,
                archers = archers + ?,
                cavalry = cavalry + ?,
                chakra = chakra + ?,
                gold_cloaks = gold_cloaks + ?,
                unsullied = unsullied + ?,
                faceless = faceless + ?,
                shadow = shadow + ?,
                poison = poison + ?
            WHERE user_id = ?
        """, (
            att_survivors["soldiers"],
            att_survivors["archers"],
            att_survivors["cavalry"],
            att_survivors["chakra"],
            att_survivors["gold_cloaks"],
            att_survivors["unsullied"],
            att_survivors["faceless"],
            att_survivors["shadow"],
            att_survivors["poison"],
            attacker_id
        ))

        # Himoyachining yo'qotishlari
        def_army = await get_user_army(defender_id)
        loss_rate_def = random.uniform(0.2, 0.4) if attacker_won else random.uniform(0.1, 0.2)
        def_loss_soldiers = max(1, int(def_army.get("soldiers", 0) * loss_rate_def))
        def_loss_archers = int(def_army.get("archers", 0) * loss_rate_def)
        def_loss_cavalry = int(def_army.get("cavalry", 0) * loss_rate_def)

        await db.execute("""
            UPDATE armies SET
                soldiers = MAX(0, soldiers - ?),
                archers = MAX(0, archers - ?),
                cavalry = MAX(0, cavalry - ?)
            WHERE user_id = ?
        """, (def_loss_soldiers, def_loss_archers, def_loss_cavalry, defender_id))
        total_def_lost = def_loss_soldiers + def_loss_archers + def_loss_cavalry

        # O'lja va Vassal qilish
        loot_gold = 0
        vassalized = False

        if attacker_won:
            def_user = await get_user(defender_id)
            if def_user and def_user["gold"] > 0:
                loot_gold = max(10, int(def_user["gold"] * 0.2))
                await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (loot_gold, defender_id))
                await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (loot_gold, attacker_id))

                if att_strategic:
                    strat_partner_id = att_strategic["lord2_id"] if att_strategic["lord1_id"] == attacker_id else att_strategic["lord1_id"]
                    ally_loot_share = max(5, int(loot_gold * 0.2))
                    await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (ally_loot_share, strat_partner_id))

            await db.execute(
                "UPDATE houses SET overlord_id = ?, captured_at = ? WHERE id = ?",
                (attacker_id, now, defender_house_id)
            )
            vassalized = True
        else:
            if defender_house["overlord_id"] == attacker_id:
                await db.execute("UPDATE houses SET overlord_id = NULL WHERE id = ?", (defender_house_id,))

            if call_id and bannermen_count > 0:
                pledges = await get_call_pledges(call_id)
                for pl in pledges:
                    await db.execute("UPDATE users SET gold = gold + 30 WHERE telegram_id = ?", (pl["user_id"],))

        if call_id:
            await db.execute("UPDATE call_to_arms SET status = 'resolved' WHERE id = ?", (call_id,))

        await db.execute("UPDATE active_battles SET status = 'resolved' WHERE id = ?", (battle_id,))
        await db.commit()

        log_text = (
            f"Jang: {'Hujumchi' if attacker_won else 'Himoyachi'} g'alaba. "
            f"Hujum: {att_roll}, Himoya: {def_roll} (Bayroqdorlar: {bannermen_power}, Ittifoqchi: {ally_support_power}). "
            f"Hujumchi yo'qotishi: {total_att_lost}, Himoyachi: {total_def_lost}. "
            f"O'lja: {loot_gold} 🪙. Vassal: {vassalized}"
        )
        await db.execute(
            "INSERT INTO battles_log (attacker_id, defender_id, winner_id, log_text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (attacker_id, defender_id, attacker_id if attacker_won else defender_id, log_text, now)
        )
        await db.commit()

        return {
            "success": True,
            "ready": True,
            "battle_id": battle_id,
            "attacker_id": attacker_id,
            "defender_id": defender_id,
            "attacker_won": attacker_won,
            "attacker_house": attacker_house["name"],
            "defender_house": defender_house["name"],
            "attacker_power": att_roll,
            "defender_power": def_roll,
            "bannermen_power": bannermen_power,
            "bannermen_count": bannermen_count,
            "ally_support_power": ally_support_power,
            "ally_house_name": ally_house_name,
            "attacker_loss": total_att_lost,
            "attacker_losses_detail": att_losses,
            "attacker_survivors": att_survivors,
            "defender_loss": total_def_lost,
            "loot_gold": loot_gold,
            "vassalized": vassalized,
            "dragons_frozen": len(sent_dragon_ids)
        }

async def execute_battle(attacker_id: int, defender_house_id: int, call_id: Optional[int] = None) -> Dict[str, Any]:
    army = await get_user_army(attacker_id)
    beasts = await get_user_beasts(attacker_id)
    now = int(time.time())
    active_dragons = [b["id"] for b in beasts if b["beast_type"] == "dragon" and b["frozen_until"] <= now]
    selected_troops = {
        "soldiers": army.get("soldiers", 0),
        "archers": army.get("archers", 0),
        "cavalry": army.get("cavalry", 0),
        "chakra": army.get("chakra", 0),
        "gold_cloaks": army.get("gold_cloaks", 0),
        "unsullied": army.get("unsullied", 0),
        "faceless": army.get("faceless", 0),
        "shadow": army.get("shadow", 0),
        "poison": army.get("poison", 0),
        "dragon_ids": active_dragons
    }
    success, msg, battle_id = await start_house_attack(attacker_id, defender_house_id, selected_troops, call_id)
    if not success:
        return {"success": False, "error": msg}
    async with get_db_connection() as db:
        await db.execute("UPDATE active_battles SET end_time = ? WHERE id = ?", (now - 1, battle_id))
        await db.commit()
    return await resolve_battle(battle_id)

# --- Vassallar va Soliq Tizimi (1 kunda 1 marta) ---

async def get_vassals(overlord_id: int) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM houses WHERE overlord_id = ?", (overlord_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def collect_vassal_taxes(overlord_id: int) -> tuple[int, str]:
    now = int(time.time())
    user = await get_user(overlord_id)
    if not user:
        return 0, "Foydalanuvchi topilmadi."

    last_tax = user.get("last_tax_collected", 0) or 0
    cooldown = 24 * 3600  # 24 soat (1 kun)

    if now - last_tax < cooldown:
        left_seconds = cooldown - (now - last_tax)
        left_hours = left_seconds // 3600
        left_mins = (left_seconds % 3600) // 60
        return 0, f"⏳ Soliqni kuniga faqat 1 marta yig'ish mumkin! Keyingi safar **{left_hours} soat {left_mins} daqiqa**dan so'ng yig'a olasiz."

    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM houses WHERE overlord_id = ?", (overlord_id,))
        vassals = await cursor.fetchall()
        if not vassals:
            return 0, "Sizning hech qanday vassalingiz yo'q! Janglarda xonadonlarni bosib oling."

        total_collected = 0
        for vassal in vassals:
            vassal_owner = vassal["owner_id"]
            if vassal_owner:
                vassal_user = await get_user(vassal_owner)
                if vassal_user and vassal_user["gold"] >= 20:
                    tax_amount = 20
                    await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (tax_amount, vassal_owner))
                    total_collected += tax_amount

        if total_collected > 0:
            await db.execute(
                "UPDATE users SET gold = gold + ?, last_tax_collected = ? WHERE telegram_id = ?",
                (total_collected, now, overlord_id)
            )
            await db.commit()
            return total_collected, f"Siz o'z vassallaringizdan jami **{total_collected} tanga** soliq yig'ib oldingiz! 💰 (Keyingi soliq 24 soatdan so'ng)"
        else:
            return 0, "Hozircha yig'ish uchun soliqlar mavjud emas (vassallarda yetarli mablag' yo'q)."

# --- Ekspeditsiya (Valeria Ekspiditsya) ---

async def start_expedition(user_id: int, hours: int) -> tuple[bool, str]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM expeditions WHERE user_id = ?", (user_id,))
        exp = await cursor.fetchone()
        now = int(time.time())
        if exp and exp["end_time"] > now:
            left_mins = (exp["end_time"] - now) // 60
            return False, f"Sizning ekspeditsiyangiz hali yakunlanmagan! Qolgan vaqt: {left_mins} daqiqa."

        duration_seconds = hours * 3600
        end_time = now + duration_seconds
        reward = hours * random.randint(40, 75)

        await db.execute(
            "INSERT OR REPLACE INTO expeditions (user_id, end_time, duration_hours, reward_gold) VALUES (?, ?, ?, ?)",
            (user_id, end_time, hours, reward)
        )
        await db.commit()
        return True, f"Qadimgi Valeriya xarobalariga **{hours} soatlik** ekspeditsiya jo'natildi! 🏞 Kutilayotgan o'lja: ~{reward} tanga."

async def check_expedition(user_id: int) -> Dict[str, Any]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM expeditions WHERE user_id = ?", (user_id,))
        exp = await cursor.fetchone()
        if not exp:
            return {"active": False, "finished": False}

        now = int(time.time())
        if exp["end_time"] <= now:
            reward = exp["reward_gold"]
            await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (reward, user_id))
            await db.execute("DELETE FROM expeditions WHERE user_id = ?", (user_id,))
            await db.commit()
            return {"active": False, "finished": True, "reward": reward}
        else:
            return {"active": True, "finished": False, "left_seconds": exp["end_time"] - now}

# --- Kunlik Bonus (Golden Bank) ---

async def claim_daily_bonus(user_id: int) -> tuple[bool, str]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT last_daily_claim, gold FROM users WHERE telegram_id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            return False, "Foydalanuvchi topilmadi."

        now = int(time.time())
        last_claim = user["last_daily_claim"] or 0
        cooldown = 24 * 3600

        if now - last_claim < cooldown:
            left_hours = (cooldown - (now - last_claim)) // 3600
            left_mins = ((cooldown - (now - last_claim)) % 3600) // 60
            return False, f"Kunlik bonusni allaqachon olgansiz! Keyingi safar {left_hours} soat {left_mins} daqiqadan so'ng olishingiz mumkin."

        bonus = random.randint(50, 120)
        await db.execute(
            "UPDATE users SET gold = gold + ?, last_daily_claim = ? WHERE telegram_id = ?",
            (bonus, now, user_id)
        )
        await db.commit()
        return True, f"Tabriklaymiz! Bank sizga bugun **{bonus} tanga** kunlik daromad berdi! 🏦"

# --- Reyting (Leaderboard) ---

async def get_top_players(limit: int = 10) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT u.telegram_id, COALESCE(u.custom_name, u.full_name) as full_name, u.username, u.gold, 
                   h.name as house_name, h.type as house_type, h.region, h.tier
            FROM users u
            LEFT JOIN houses h ON h.owner_id = u.telegram_id
            WHERE h.id IS NOT NULL
            ORDER BY u.gold DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

# --- 1000 Yillik Qadimgi Turnir: Ritserlar Baxsi ---

async def record_tournament_battle(user_id: int, won: bool) -> tuple[int, int, int]:
    points_gained = 20 if won else 5
    gold_gained = 25 if won else 0
    win_inc = 1 if won else 0

    async with get_db_connection() as db:
        await db.execute("""
            UPDATE users SET
                tournament_points = tournament_points + ?,
                tournament_wins = tournament_wins + ?,
                tournament_fights = tournament_fights + 1,
                gold = gold + ?
            WHERE telegram_id = ?
        """, (points_gained, win_inc, gold_gained, user_id))
        await db.commit()

        cursor = await db.execute("SELECT tournament_points FROM users WHERE telegram_id = ?", (user_id,))
        row = await cursor.fetchone()
        new_total = row["tournament_points"] if row else points_gained

    return points_gained, new_total, gold_gained

async def get_tournament_top_players(limit: int = 20) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT u.telegram_id, COALESCE(u.custom_name, u.full_name) as full_name, u.username,
                   u.tournament_points, u.tournament_wins, u.tournament_fights,
                   h.name as house_name, h.tier
            FROM users u
            LEFT JOIN houses h ON h.owner_id = u.telegram_id
            WHERE u.tournament_points > 0 OR u.tournament_fights > 0
            ORDER BY u.tournament_points DESC, u.tournament_wins DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_user_tournament_stats(user_id: int) -> Dict[str, Any]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT tournament_points, tournament_wins, tournament_fights
            FROM users WHERE telegram_id = ?
        """, (user_id,))
        row = await cursor.fetchone()
        if not row:
            return {"points": 0, "wins": 0, "fights": 0, "rank": "-"}

        pts = row["tournament_points"] or 0
        cursor = await db.execute("SELECT COUNT(*) as higher_rank FROM users WHERE tournament_points > ?", (pts,))
        higher = (await cursor.fetchone())["higher_rank"]
        rank = higher + 1 if pts > 0 else "-"

        return {
            "points": pts,
            "wins": row["tournament_wins"] or 0,
            "fights": row["tournament_fights"] or 0,
            "rank": rank
        }

async def distribute_weekly_tournament_rewards() -> tuple[bool, str]:
    top_players = await get_tournament_top_players(limit=5)
    if not top_players:
        return False, "Turnirda hali ishtirokchilar mavjud emas."

    async with get_db_connection() as db:
        for idx, player in enumerate(top_players):
            uid = player["telegram_id"]
            rank = idx + 1
            if rank == 1:
                await db.execute("UPDATE armies SET unsullied = unsullied + 200 WHERE user_id = ?", (uid,))
                await db.execute(
                    "INSERT INTO beasts (user_id, beast_type, name, grade, power, frozen_until) VALUES (?, 'dragon', 'Turnir Ajdari', 'C', 500, 0)",
                    (uid,)
                )
            elif rank == 2:
                await db.execute("UPDATE armies SET unsullied = unsullied + 150 WHERE user_id = ?", (uid,))
                await db.execute(
                    "INSERT INTO beasts (user_id, beast_type, name, grade, power, frozen_until) VALUES (?, 'spider', 'Turnir Oʻrgimchagi', 'C', 500, 0)",
                    (uid,)
                )
            elif rank == 3:
                await db.execute("UPDATE armies SET unsullied = unsullied + 100, faceless = faceless + 1 WHERE user_id = ?", (uid,))
            elif rank == 4:
                await db.execute("UPDATE armies SET chakra = chakra + 150 WHERE user_id = ?", (uid,))
            elif rank == 5:
                await db.execute("UPDATE armies SET chakra = chakra + 100 WHERE user_id = ?", (uid,))

        await db.execute("UPDATE users SET tournament_points = 0")
        await db.commit()

    return True, f"Haftalik turnir sovg'alari {len(top_players)} nafar g'olibga topshirildi va ochkolar yangilandi!"

# --- Qal'alar (Castles) Tizimi ---

async def get_house_castle(house_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM castles WHERE house_id = ?", (house_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def build_or_upgrade_castle(user_id: int) -> tuple[bool, str]:
    user_house = await get_user_house(user_id)
    if not user_house:
        return False, "Siz hali xonadon tanlamagansiz! Avval xonadon tanlang."

    house_id = user_house["id"]
    castle = await get_house_castle(house_id)
    user = await get_user(user_id)
    now = int(time.time())

    if not castle:
        cost = CASTLE_COST[1]
        if not user or user["gold"] < cost:
            return False, f"1-darajali qal'a qurish uchun **{cost} oltin** kerak! Sizda: {user['gold'] if user else 0} oltin."
        async with get_db_connection() as db:
            await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (cost, user_id))
            await db.execute(
                "INSERT INTO castles (house_id, owner_id, level, last_collected_at, created_at) VALUES (?, ?, 1, ?, ?)",
                (house_id, user_id, now, now)
            )
            await db.commit()
        return True, f"🏰 **{user_house['name']}** xonadoni uchun 1-darajali Qal'a qurildi! Har soatda **{CASTLE_INCOME[1]} oltin** daromad keltiradi (-{cost} oltin)."

    current_lvl = castle["level"]
    if current_lvl >= 3:
        return False, "🏰 Qal'angiz allaqachon maksimal (3-daraja) darajaga yetgan!"

    next_lvl = current_lvl + 1
    cost = CASTLE_COST[next_lvl]
    if not user or user["gold"] < cost:
        return False, f"Qal'ani {next_lvl}-darajaga ko'tarish uchun **{cost} oltin** kerak! Sizda: {user['gold'] if user else 0} oltin."

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (cost, user_id))
        await db.execute("UPDATE castles SET level = ? WHERE house_id = ?", (next_lvl, house_id))
        await db.commit()

    return True, f"🏰 Qal'angiz **{next_lvl}-darajaga** ko'tarildi! Soatlik daromad: **{CASTLE_INCOME[next_lvl]} oltin** (-{cost} oltin)."

async def collect_castle_income(user_id: int) -> tuple[int, str]:
    user_house = await get_user_house(user_id)
    if not user_house:
        return 0, "Siz hali xonadon tanlamagansiz!"

    castle = await get_house_castle(user_house["id"])
    if not castle:
        return 0, "Sizning xonadoningizda hali Qal'a qurilmagan! Avval qal'a quring."

    now = int(time.time())
    last_col = castle["last_collected_at"] or castle.get("created_at", now)
    seconds_passed = now - last_col
    hours_passed = seconds_passed // 3600

    if hours_passed < 1:
        left_mins = max(1, (3600 - (seconds_passed % 3600)) // 60)
        return 0, f"⏳ Qal'a daromadi har soatda yig'iladi! Keyingi daromadgacha **{left_mins} daqiqa** qoldi."

    income_per_hour = CASTLE_INCOME.get(castle["level"], 10)
    total_income = hours_passed * income_per_hour

    # 💍 Sulolaviy Nikoh bo'lsa +15% qal'a daromadi bonusi!
    marriage = await get_house_alliance(user_house["id"], "marriage")
    marriage_bonus = 0
    if marriage:
        marriage_bonus = max(1, int(total_income * 0.15))
        total_income += marriage_bonus

    new_last_col = last_col + (hours_passed * 3600)

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (total_income, user_id))
        await db.execute("UPDATE castles SET last_collected_at = ? WHERE house_id = ?", (new_last_col, user_house["id"]))
        await db.commit()

    bonus_str = f" (💍 Nikoh bonusi: +{marriage_bonus} 🪙)" if marriage_bonus > 0 else ""
    return total_income, f"🏰 Qal'angizdan {hours_passed} soatlik daromad: **+{total_income} oltin**{bonus_str} xazinangizga qo'shildi! 💰"

# --- Nikoh va Manfaatli Ittifoq (Alliances) Tizimi ---

async def get_house_alliance(house_id: int, alliance_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        if alliance_type:
            cursor = await db.execute("""
                SELECT a.*, 
                       h1.name as h1_name, u1.full_name as u1_name, u1.username as u1_username,
                       h2.name as h2_name, u2.full_name as u2_name, u2.username as u2_username
                FROM alliances a
                JOIN houses h1 ON a.house1_id = h1.id
                JOIN houses h2 ON a.house2_id = h2.id
                JOIN users u1 ON a.lord1_id = u1.telegram_id
                JOIN users u2 ON a.lord2_id = u2.telegram_id
                WHERE (a.house1_id = ? OR a.house2_id = ?) AND a.status = 'active' AND a.alliance_type = ?
            """, (house_id, house_id, alliance_type))
        else:
            cursor = await db.execute("""
                SELECT a.*, 
                       h1.name as h1_name, u1.full_name as u1_name, u1.username as u1_username,
                       h2.name as h2_name, u2.full_name as u2_name, u2.username as u2_username
                FROM alliances a
                JOIN houses h1 ON a.house1_id = h1.id
                JOIN houses h2 ON a.house2_id = h2.id
                JOIN users u1 ON a.lord1_id = u1.telegram_id
                JOIN users u2 ON a.lord2_id = u2.telegram_id
                WHERE (a.house1_id = ? OR a.house2_id = ?) AND a.status = 'active'
            """, (house_id, house_id))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_house_all_alliances(house_id: int) -> Dict[str, Optional[Dict[str, Any]]]:
    marriage = await get_house_alliance(house_id, "marriage")
    strategic = await get_house_alliance(house_id, "strategic")
    return {"marriage": marriage, "strategic": strategic}

async def are_houses_allied(house1_id: int, house2_id: int) -> tuple[bool, Optional[str]]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT alliance_type FROM alliances
            WHERE ((house1_id = ? AND house2_id = ?) OR (house1_id = ? AND house2_id = ?))
              AND status = 'active'
        """, (house1_id, house2_id, house2_id, house1_id))
        row = await cursor.fetchone()
        if row:
            return True, row["alliance_type"]
        return False, None

async def get_pending_alliance_proposals(house_id: int) -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT a.*, h1.name as sender_house_name, u1.full_name as sender_name, u1.username as sender_username
            FROM alliances a
            JOIN houses h1 ON a.house1_id = h1.id
            JOIN users u1 ON a.lord1_id = u1.telegram_id
            WHERE a.house2_id = ? AND a.status = 'pending'
            ORDER BY a.id DESC
        """, (house_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def create_alliance_proposal(sender_id: int, target_house_id: int, alliance_type: str = "marriage") -> tuple[bool, str, Optional[int]]:
    sender_house = await get_user_house(sender_id)
    if not sender_house:
        return False, "Siz hali xonadon tanlamagansiz!", None

    if sender_house["id"] == target_house_id:
        return False, "O'z xonadoningiz bilan ittifoq tuza olmaysiz!", None

    target_house = await get_house_by_id(target_house_id)
    if not target_house or not target_house["owner_id"]:
        return False, "Bu xonadonda hali hukmdor yo'q!", None

    target_lord_id = target_house["owner_id"]
    type_title = "Sulolaviy Nikoh 💍" if alliance_type == "marriage" else "Manfaatli Ittifoq 🤝"

    existing_sender = await get_house_alliance(sender_house["id"], alliance_type)
    if existing_sender:
        return False, f"Sizning xonadoningiz allaqachon boshqa xonadon bilan **{type_title}** tuzgan!", None

    existing_target = await get_house_alliance(target_house_id, alliance_type)
    if existing_target:
        return False, f"**{target_house['name']}** xonadoni allaqachon boshqa xonadon bilan **{type_title}** tuzgan!", None

    now = int(time.time())
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT * FROM alliances 
            WHERE house1_id = ? AND house2_id = ? AND alliance_type = ? AND status = 'pending'
        """, (sender_house["id"], target_house_id, alliance_type))
        if await cursor.fetchone():
            return False, f"Siz ushbu xonadonga allaqachon **{type_title}** taklifini yuborgansiz!", None

        await db.execute("""
            INSERT INTO alliances (house1_id, house2_id, lord1_id, lord2_id, status, alliance_type, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (sender_house["id"], target_house_id, sender_id, target_lord_id, alliance_type, now))
        await db.commit()

    return True, f"✅ **{target_house['name']}** xonadoniga **{type_title}** taklifi yuborildi!", target_lord_id

async def respond_alliance_proposal(proposal_id: int, responder_id: int, accept: bool) -> tuple[bool, str, Optional[int]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM alliances WHERE id = ? AND lord2_id = ? AND status = 'pending'", (proposal_id, responder_id))
        prop = await cursor.fetchone()
        if not prop:
            return False, "Bunday taklif topilmadi yoki allaqachon ko'rib chiqilgan!", None

        now = int(time.time())
        sender_id = prop["lord1_id"]
        all_type = prop["alliance_type"]
        type_title = "Sulolaviy Nikoh 💍" if all_type == "marriage" else "Manfaatli Ittifoq 🤝"

        if accept:
            await db.execute("UPDATE alliances SET status = 'active', updated_at = ? WHERE id = ?", (now, proposal_id))
            await db.commit()
            if all_type == "marriage":
                msg = "💍 **Sulolaviy Nikoh rishtalari bog'landi!**\nEndi xonadonlaringiz o'rtasida buzilmas sulh, mudofaada +50% quvvat va qal'adan +15% ko'proq oltin ta'minlanadi."
            else:
                msg = "🤝 **Manfaatli Ittifoq pakti imzolandi!**\nEndi xonadonlaringiz bir-biriga hujum qilolmaydi, hujumlarda +25% quvvat, g'alaba o'ljasidan 20% ulush va mudofaada +25% ko'mak beriladi."
            return True, msg, sender_id
        else:
            await db.execute("UPDATE alliances SET status = 'rejected', updated_at = ? WHERE id = ?", (now, proposal_id))
            await db.commit()
            return True, f"❌ {type_title} taklifi rad etildi.", sender_id

async def break_alliance(user_id: int, alliance_type: str = "marriage") -> tuple[bool, str, Optional[int]]:
    user_house = await get_user_house(user_id)
    if not user_house:
        return False, "Sizda xonadon yo'q!", None

    alliance = await get_house_alliance(user_house["id"], alliance_type)
    if not alliance:
        type_title = "Sulolaviy Nikoh" if alliance_type == "marriage" else "Manfaatli Ittifoq"
        return False, f"Sizda faol **{type_title}** mavjud emas!", None

    partner_id = alliance["lord2_id"] if alliance["lord1_id"] == user_id else alliance["lord1_id"]
    now = int(time.time())
    async with get_db_connection() as db:
        await db.execute("UPDATE alliances SET status = 'broken', updated_at = ? WHERE id = ?", (now, alliance["id"]))
        await db.commit()

    type_title = "Sulolaviy Nikoh" if alliance_type == "marriage" else "Manfaatli Ittifoq"
    return True, f"💔 **{type_title}** rishtalari bekor qilindi!", partner_id

# --- Kunlik Hududiy Topshiriqlar (Daily Territory Quests) Tizimi ---

async def get_user_daily_tasks(user_id: int) -> Dict[str, Any]:
    today_str = datetime.now().strftime("%Y-%m-%d")
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM daily_territory_tasks WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            await db.execute("""
                INSERT INTO daily_territory_tasks (user_id, task_date, task1_done, task2_done, task3_done, super_claimed)
                VALUES (?, ?, 0, 0, 0, 0)
            """, (user_id, today_str))
            await db.commit()
            cursor = await db.execute("SELECT * FROM daily_territory_tasks WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row)

        row_dict = dict(row)
        if row_dict["task_date"] != today_str:
            await db.execute("""
                UPDATE daily_territory_tasks
                SET task_date = ?, task1_done = 0, task2_done = 0, task3_done = 0, super_claimed = 0
                WHERE user_id = ?
            """, (today_str, user_id))
            await db.commit()
            cursor = await db.execute("SELECT * FROM daily_territory_tasks WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row)

        return row_dict

async def perform_daily_patrol(user_id: int) -> tuple[bool, str]:
    tasks = await get_user_daily_tasks(user_id)
    if tasks["task1_done"] == 1:
        return False, "Siz bugun chegaralarni allaqachon patrul qildingiz! Yangi patrul ertaga ochiladi."

    user = await get_user(user_id)
    army = await get_user_army(user_id)
    valyrian_steel = user.get("valyrian_steel", 0) or 0

    chakra_spend = 0
    if valyrian_steel <= 0:
        if army["chakra"] < 5:
            return False, "⚠️ Chegarani patrul qilish uchun kamida **5 ta Chakra ⚙️** kerak!\nChakrani **🌍 Esos Savdosi** bo'limidan xarid qilishingiz mumkin."
        chakra_spend = 5

    user_house = await get_user_house(user_id)
    region = user_house["region"] if user_house else "default"

    if region == "crownlands":
        narrative = "👑 **Qirollik Yerlari Chegara Patruli:**\nQirollik yo'llarida pistirma qo'ygan dushman ayg'oqchilarini tor-mor etdingiz va qirollik savdogarlarini qutqardingiz!"
        gold_rew = 80; troop_rew = 8; chakra_rew = 0; poison_rew = 0
    elif region == "volcanoes":
        narrative = "🌋 **Valeriya Vulqonlari Patruli:**\nZaldizar vulqonlari bag'ridan issiq lavasimon qimmatbaho rudalar va yangi ajdar uyasini aniqladingiz!"
        gold_rew = 95; troop_rew = 0; chakra_rew = 15; poison_rew = 0
    elif region == "forest":
        narrative = "🌲 **Varezys O'rmonlari Patruli:**\nVarezys o'rmonlarining chuqurligidagi qadimiy xazina sandig'ini topdingiz va botir ovchilarni saflaringizga qo'shdingiz!"
        gold_rew = 85; troop_rew = 10; chakra_rew = 0; poison_rew = 0
    elif region == "sorcerers":
        narrative = "🔮 **Jodugarlar Yerlari Patruli:**\nMaeraxes qadimiy harobalaridan sirli sehrli bitiklar, oltin tangalar va qadimiy chakra energiyasini qo'lga kiritdingiz!"
        gold_rew = 120; troop_rew = 0; chakra_rew = 35; poison_rew = 0
    elif region == "sea_guardians":
        narrative = "🌊 **Dengiz Qo'riqchilari Patruli:**\nNyzarys qirg'oqlarida Valeriya bo'g'ozi qaroqchilari kemasini yondirib, boy o'lja bilan qaytdingiz!"
        gold_rew = 90; troop_rew = 7; chakra_rew = 0; poison_rew = 0
    else:
        narrative = "🗺 **Valeriya Dashtlari Patruli:**\nValeriya sarhadlarida ot choptirib, qadimiy tangalar va ko'ngilli jangchilarni to'pladingiz!"
        gold_rew = 70; troop_rew = 6; chakra_rew = 0; poison_rew = 0

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (gold_rew, user_id))
        await db.execute("""
            UPDATE armies SET 
                chakra = MAX(0, chakra - ? + ?),
                soldiers = soldiers + ?,
                poison = poison + ?
            WHERE user_id = ?
        """, (chakra_spend, chakra_rew, troop_rew, poison_rew, user_id))
        await db.execute("UPDATE daily_territory_tasks SET task1_done = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    rewards_desc = [f"+{gold_rew} 🪙 Oltin"]
    if troop_rew > 0:
        rewards_desc.append(f"+{troop_rew} 🛡 Askar")
    if chakra_rew > 0:
        rewards_desc.append(f"+{chakra_rew} ⚙️ Chakra")
    if poison_rew > 0:
        rewards_desc.append(f"+{poison_rew} 🧪 Zahar")

    chakra_msg = " (-0 ⚙️ Valeriya po'lati tufayli tekin)" if valyrian_steel > 0 else f" (-{chakra_spend} ⚙️ Chakra)"
    res_text = (
        f"{narrative}\n\n"
        f"🎁 **Mukofot:** {', '.join(rewards_desc)}{chakra_msg}\n"
        "✅ **1-topshiriq bajarildi!**"
    )
    return True, res_text

async def perform_daily_fortification(user_id: int) -> tuple[bool, str]:
    tasks = await get_user_daily_tasks(user_id)
    if tasks["task2_done"] == 1:
        return False, "Siz bugun garnizon va qal'a mudofaasini allaqachon ko'rikdan o'tkazgansiz!"

    user_house = await get_user_house(user_id)
    castle = await get_house_castle(user_house["id"]) if user_house else None
    army = await get_user_army(user_id)
    total_troops = army["soldiers"] + army.get("unsullied", 0)

    if not castle and total_troops < 25:
        return False, (
            "⚠️ Ushbu vazifani bajarish uchun xonadoningizda **Qal'a** qurilgan bo'lishi yoki "
            f"kamida **25 ta askaringiz** bo'lishi kerak! (Sizda: {total_troops} ta askar)"
        )

    gold_rew = 110
    unsullied_rew = 10
    chakra_rew = 15

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (gold_rew, user_id))
        await db.execute("""
            UPDATE armies SET 
                unsullied = unsullied + ?,
                chakra = chakra + ?
            WHERE user_id = ?
        """, (unsullied_rew, chakra_rew, user_id))
        await db.execute("UPDATE daily_territory_tasks SET task2_done = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    castle_txt = f"{castle['level']}-darajali Qal'a istehkomlari" if castle else "Hududiy garnizon istehkomlari"
    res_text = (
        f"🏰 **Garnizon Mudofaasi Mustahkamlandi!**\n"
        f"{castle_txt} to'liq ko'rikdan o'tkazildi, qurol-yarog'lar sozlandi va jangchilar eng yuqori shaylik holatiga keltirildi!\n\n"
        f"🎁 **Mukofot:** +{gold_rew} 🪙 Oltin, +{unsullied_rew} 🛡 Benuqson, +{chakra_rew} ⚙️ Chakra!\n"
        "✅ **2-topshiriq bajarildi!**"
    )
    return True, res_text

async def perform_daily_expedition(user_id: int) -> tuple[bool, str]:
    tasks = await get_user_daily_tasks(user_id)
    if tasks["task3_done"] == 1:
        return False, "Siz bugungi harbiy yurishni allaqachon muvaffaqiyatli yakunladingiz!"

    user = await get_user(user_id)
    army = await get_user_army(user_id)
    valyrian_steel = user.get("valyrian_steel", 0) or 0

    chakra_spend = 0
    if valyrian_steel <= 0:
        if army["chakra"] < 10:
            return False, "⚠️ Harbiy yurishga chiqish uchun kamida **10 ta Chakra ⚙️** kerak!\nUni **🌍 Esos Savdosi** bo'limidan olishingiz mumkin."
        chakra_spend = 10

    gold_rew = 150
    shadow_rew = 1
    chakra_gain = 25

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (gold_rew, user_id))
        await db.execute("""
            UPDATE armies SET 
                chakra = MAX(0, chakra - ? + ?),
                shadow = shadow + ?
            WHERE user_id = ?
        """, (chakra_spend, chakra_gain, shadow_rew, user_id))
        await db.execute("UPDATE daily_territory_tasks SET task3_done = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    chakra_msg = " (-0 ⚙️ Valeriya po'lati tufayli tekin)" if valyrian_steel > 0 else f" (-{chakra_spend} ⚙️ Chakra)"
    res_text = (
        "⚔️ **Valeriya Bo'ylab Qahramonona Harbiy Yurish!**\n"
        "Siz o'z qo'shiningiz bilan sarhadlardagi dushman qo'shiniga to'satdan zarba berib, qaqshatqich g'alabaga erishdingiz va hudud xavfsizligini ta'minladingiz!\n\n"
        f"🎁 **Mukofot:** +{gold_rew} 🪙 Oltin, +{shadow_rew} 👣 Soya Qotil, +{chakra_gain} ⚙️ Chakra!{chakra_msg}\n"
        "✅ **3-topshiriq bajarildi!**"
    )
    return True, res_text

async def claim_daily_super_bonus(user_id: int) -> tuple[bool, str]:
    tasks = await get_user_daily_tasks(user_id)
    if tasks["super_claimed"] == 1:
        return False, "Siz bugungi Super-Bonusni allaqachon olgansiz! Ertangi yangi topshiriqlarni kuting."

    if not (tasks["task1_done"] == 1 and tasks["task2_done"] == 1 and tasks["task3_done"] == 1):
        return False, "⚠️ Kunlik Super-Bonusni olish uchun avval barcha 3 ta topshiriqni bajarishingiz kerak!"

    gold_rew = 600
    chakra_rew = 300

    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold + ? WHERE telegram_id = ?", (gold_rew, user_id))
        await db.execute("""
            UPDATE armies SET 
                chakra = chakra + ?
            WHERE user_id = ?
        """, (chakra_rew, user_id))
        await db.execute("UPDATE daily_territory_tasks SET super_claimed = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    res_text = (
        "🏆 **VALERIYA KUNLIK HUDUDIY SUPER-BONUSI QO'LGA KIRITILDI!**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Siz bugun barcha 3 ta hududiy topshiriqni a'lo darajada bajardingiz va Valeriya Oliy Kengashi sizni boy xazina bilan taqdirladi:\n\n"
        f"💰 **+{gold_rew} 🪙 Oltin tanga**\n"
        f"⚙️ **+{chakra_rew} ⚙️ Chakra energiyasi**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 Xazinangiz va ruhiy qudratingiz yanada ortdi! Ertaga yana yangi g'alabalar sari olg'a!"
    )
    return True, res_text

# --- Green Bank To'lovlar (Donations) Tizimi ---

async def create_donation_request(user_id: int, package_id: int, receipt_file_id: str, receipt_type: str = "photo") -> int:
    package = DONATE_PACKAGES.get(package_id, {})
    amount = package.get("cost_uzs", 0)
    now = int(time.time())
    async with get_db_connection() as db:
        cursor = await db.execute("""
            INSERT INTO donations (user_id, package_id, amount_uzs, receipt_file_id, receipt_type, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """, (user_id, package_id, amount, receipt_file_id, receipt_type, now))
        await db.commit()
        return cursor.lastrowid

async def get_donation(donation_id: int) -> Optional[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM donations WHERE id = ?", (donation_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def approve_donation_request(donation_id: int, admin_id: int) -> tuple[bool, str, Optional[Dict[str, Any]]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM donations WHERE id = ? AND status = 'pending'", (donation_id,))
        don = await cursor.fetchone()
        if not don:
            return False, "To'lov so'rovi topilmadi yoki allaqachon ko'rib chiqilgan!", None

        pkg = DONATE_PACKAGES.get(don["package_id"])
        if not pkg:
            return False, "Noma'lum paket!", None

        user_id = don["user_id"]
        now = int(time.time())

        gold = pkg.get("gold", 0)
        unsullied = pkg.get("unsullied", 0)
        valyrian_steel = pkg.get("valyrian_steel", 0)
        faceless = pkg.get("faceless", 0)
        shadow = pkg.get("shadow", 0)
        poison = pkg.get("poison", 0)
        chakra = pkg.get("chakra", 0)

        await db.execute("""
            UPDATE users SET 
                gold = gold + ?,
                valyrian_steel = valyrian_steel + ?
            WHERE telegram_id = ?
        """, (gold, valyrian_steel, user_id))

        await db.execute("""
            UPDATE armies SET 
                unsullied = unsullied + ?,
                faceless = faceless + ?,
                shadow = shadow + ?,
                poison = poison + ?,
                chakra = chakra + ?
            WHERE user_id = ?
        """, (unsullied, faceless, shadow, poison, chakra, user_id))

        await db.execute("""
            UPDATE donations SET 
                status = 'approved',
                reviewed_at = ?,
                admin_id = ?
            WHERE id = ?
        """, (now, admin_id, donation_id))

        await db.commit()
        return True, "To'lov muvaffaqiyatli tasdiqlandi va resurslar berildi!", {
            "user_id": user_id,
            "package_name": pkg["name"],
            "desc": pkg["desc"],
            "amount_uzs": don["amount_uzs"]
        }

async def reject_donation_request(donation_id: int, admin_id: int) -> tuple[bool, str, Optional[int]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM donations WHERE id = ? AND status = 'pending'", (donation_id,))
        don = await cursor.fetchone()
        if not don:
            return False, "To'lov so'rovi topilmadi yoki allaqachon ko'rib chiqilgan!", None

        now = int(time.time())
        await db.execute("""
            UPDATE donations SET 
                status = 'rejected',
                reviewed_at = ?,
                admin_id = ?
            WHERE id = ?
        """, (now, admin_id, donation_id))
        await db.commit()
        return True, "To'lov rad etildi.", don["user_id"]

# --- Admin amallari & O'yinni Restart qilish ---

async def admin_set_gold(user_id: int, amount: int) -> bool:
    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = ? WHERE telegram_id = ?", (amount, user_id))
        await db.commit()
        return True

async def admin_free_house(house_id: int) -> bool:
    async with get_db_connection() as db:
        await db.execute("UPDATE houses SET owner_id = NULL, overlord_id = NULL WHERE id = ?", (house_id,))
        await db.commit()
        return True

async def admin_transfer_house(user_id: int, new_house_id: int) -> tuple[bool, str]:
    if new_house_id < 1 or new_house_id > 52:
        return False, "Xonadon ID 1 dan 52 gacha bo'lishi kerak!"

    user = await get_user(user_id)
    if not user:
        return False, f"Foydalanuvchi #{user_id} topilmadi!"

    target_house = await get_house_by_id(new_house_id)
    if not target_house:
        return False, "Yangi xonadon topilmadi!"

    async with get_db_connection() as db:
        # Eski xonadondan bo'shatish
        await db.execute("UPDATE houses SET owner_id = NULL WHERE owner_id = ?", (user_id,))
        # Yangi xonadondagi boshqa egasini bo'shatish
        await db.execute("UPDATE houses SET owner_id = NULL WHERE id = ?", (new_house_id,))
        # Yangi xonadonga biriktirish
        await db.execute("UPDATE houses SET owner_id = ?, overlord_id = NULL WHERE id = ?", (user_id, new_house_id))
        # Qal'a egasini ham moslashtirish
        await db.execute("UPDATE castles SET owner_id = ? WHERE house_id = ?", (user_id, new_house_id))
        await db.commit()

    return True, f"Foydalanuvchi {user.get('full_name', user_id)} muvaffaqiyatli #{new_house_id} ({target_house['name']}) xonadoniga ko'chirildi!"

async def admin_unfreeze_dragons(user_id: int) -> int:
    async with get_db_connection() as db:
        cursor = await db.execute("UPDATE beasts SET frozen_until = 0 WHERE user_id = ? AND beast_type = 'dragon'", (user_id,))
        await db.commit()
        return cursor.rowcount

async def admin_restart_game() -> bool:
    async with get_db_connection() as db:
        # Barcha xonadonlarni bo'shatish
        await db.execute("""
            UPDATE houses SET 
                owner_id = NULL, 
                overlord_id = NULL, 
                captured_at = NULL, 
                accumulated_tax = 0
        """)
        # Barcha o'yin ma'lumotlarini tozalash
        await db.execute("DELETE FROM users")
        await db.execute("DELETE FROM armies")
        await db.execute("DELETE FROM beasts")
        await db.execute("DELETE FROM expeditions")
        await db.execute("DELETE FROM battles_log")
        await db.execute("DELETE FROM call_to_arms")
        await db.execute("DELETE FROM bannermen_pledges")
        await db.execute("DELETE FROM castles")
        await db.execute("DELETE FROM alliances")
        await db.execute("DELETE FROM donations")
        try:
            await db.execute("DELETE FROM completed_tasks")
            await db.execute("DELETE FROM daily_territory_tasks")
        except Exception:
            pass

        # 52 ta xonadonni to'liq qayta tekshirib toza saqlash
        for house in HOUSES_DATA:
            tier = "A" if house["id"] in TIER_A_HOUSES else "B"
            await db.execute("""
                INSERT INTO houses (id, name, type, region, is_regional_lord, tier)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    region = excluded.region,
                    is_regional_lord = excluded.is_regional_lord,
                    tier = excluded.tier,
                    owner_id = NULL,
                    overlord_id = NULL
            """, (house["id"], house["name"], house["type"], house["region"], 1 if house.get("is_regional_lord") else 0, tier))

        await db.commit()
        return True

async def get_all_users() -> List[Dict[str, Any]]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def set_user_custom_name(telegram_id: int, custom_name: str) -> tuple[bool, str]:
    cleaned = custom_name.strip()
    if len(cleaned) < 2 or len(cleaned) > 32:
        return False, "Ism uzunligi 2 dan 32 ta belgiga teng bo'lishi kerak!"
    async with get_db_connection() as db:
        await db.execute("UPDATE users SET custom_name = ? WHERE telegram_id = ?", (cleaned, telegram_id))
        await db.commit()
    return True, f"Ismingiz muvaffaqiyatli o'zgartirildi: **{cleaned}**"

async def buy_sword_bank_troops(telegram_id: int, unit_type: str, count: int) -> tuple[bool, str]:
    if count <= 0:
        return False, "Miqdor kamida 1 ta bo'lishi kerak!"

    unit_map = {
        "soldier": {"col": "soldiers", "cost": 1, "name": "Oddiy askar 🗡"},
        "archer": {"col": "archers", "cost": 3, "name": "Kamonchi 🏹"},
        "cavalry": {"col": "cavalry", "cost": 5, "name": "Otliq 🐎"}
    }

    info = unit_map.get(unit_type)
    if not info:
        return False, "Noto'g'ri harbiy qism tanlandi!"

    total_cost = info["cost"] * count
    user = await get_user(telegram_id)
    if not user or user["gold"] < total_cost:
        return False, f"Xazinangizda yetarli oltin yo'q! Kerak: {total_cost} 🪙, sizda: {user['gold'] if user else 0} 🪙."

    col = info["col"]
    async with get_db_connection() as db:
        await db.execute("UPDATE users SET gold = gold - ? WHERE telegram_id = ?", (total_cost, telegram_id))
        await db.execute(f"UPDATE armies SET {col} = {col} + ? WHERE user_id = ?", (count, telegram_id))
        await db.commit()

    return True, f"Tabriklaymiz! Siz {count} ta **{info['name']}** yolladingiz! (-{total_cost} 🪙)"

async def take_bank_loan(telegram_id: int, package_id: int) -> tuple[bool, str]:
    pkg = LOAN_PACKAGES.get(package_id)
    if not pkg:
        return False, "Noto'g'ri qarz paketi tanlandi!"

    user = await get_user(telegram_id)
    if not user:
        return False, "Foydalanuvchi topilmadi!"

    if (user.get("debt_due_amount") or 0) > 0:
        return False, f"⚠️ Sizda to'lanmagan faol qarzingiz mavjud: **{user['debt_due_amount']} 🪙**!\nYangi qarz olishdan oldin mavjud qarzni to'lang."

    now = int(time.time())
    loan_amount = pkg["amount"]
    due_amount = pkg["due_amount"]

    async with get_db_connection() as db:
        await db.execute("""
            UPDATE users SET
                gold = gold + ?,
                debt_amount = ?,
                debt_due_amount = ?,
                debt_taken_at = ?
            WHERE telegram_id = ?
        """, (loan_amount, loan_amount, due_amount, now, telegram_id))
        await db.commit()

    return True, f"✅ Siz Sword Bankdan **+{loan_amount} 🪙** qarz oldingiz!\nQaytarilishi kerak bo'lgan miqdor: **{due_amount} 🪙** (+15% foiz bilan)."

async def repay_bank_loan(telegram_id: int, amount: Optional[int] = None) -> tuple[bool, str]:
    user = await get_user(telegram_id)
    if not user:
        return False, "Foydalanuvchi topilmadi!"

    due = user.get("debt_due_amount", 0) or 0
    if due <= 0:
        return False, "Sizda to'lanishi kerak bo'lgan faol qarz yo'q!"

    user_gold = user.get("gold", 0) or 0
    if user_gold <= 0:
        return False, "Xazinangizda qarz to'lash uchun yetarli oltin yo'q!"

    if amount is None or amount >= due:
        pay_amount = min(due, user_gold)
    else:
        pay_amount = min(amount, user_gold)

    if pay_amount <= 0:
        return False, "To'lov miqdori kamida 1 🪙 bo'lishi kerak!"

    new_due = due - pay_amount
    new_debt_amount = user.get("debt_amount", 0) if new_due > 0 else 0

    async with get_db_connection() as db:
        await db.execute("""
            UPDATE users SET
                gold = gold - ?,
                debt_amount = ?,
                debt_due_amount = ?
            WHERE telegram_id = ?
        """, (pay_amount, new_debt_amount, new_due, telegram_id))
        await db.commit()

    if new_due == 0:
        return True, f"🎉 **Tabriklaymiz! Qarzingiz to'liq yopildi (-{pay_amount} 🪙)!**\nSword Bank sizga minnatdorchilik bildiradi."
    else:
        return True, f"✅ Qarzning bir qismi to'landi: **-{pay_amount} 🪙**.\nQolgan qarz miqdori: **{new_due} 🪙**."

async def admin_unfreeze_all_dragons() -> int:
    async with get_db_connection() as db:
        now = int(time.time())
        cursor = await db.execute(
            "SELECT COUNT(*) FROM beasts WHERE beast_type = 'dragon' AND frozen_until > ?",
            (now,)
        )
        count = (await cursor.fetchone())[0]
        await db.execute("UPDATE beasts SET frozen_until = 0 WHERE beast_type = 'dragon'")
        await db.commit()
        return count

async def admin_give_gold_add(telegram_id: int, amount: int) -> tuple[bool, str, int]:
    async with get_db_connection() as db:
        cursor = await db.execute("SELECT gold FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if not row:
            return False, f"ID `{telegram_id}` bo'lgan o'yinchi topilmadi!", 0
        current_gold = row["gold"]
        new_gold = max(0, current_gold + amount)
        await db.execute("UPDATE users SET gold = ? WHERE telegram_id = ?", (new_gold, telegram_id))
        await db.commit()
        return True, f"O'yinchiga {amount} 🪙 oltin berildi! Yangi balans: {new_gold} 🪙", new_gold
